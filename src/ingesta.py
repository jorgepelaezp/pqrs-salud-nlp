
"""
Ingesta, validacion y reentrenamiento de PQRS.

Flujo:
    leer_archivo()
    validar()
    guardar_lote()
    reentrenar()

El reentrenamiento conserva TF-IDF + Naive Bayes.

Por defecto, reentrenar() solamente evalua un candidato.
No reemplaza el modelo actual ni sus metricas historicas.
"""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
import unicodedata
import uuid

from datetime import datetime
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURACION
# ============================================================

RAIZ = Path(__file__).resolve().parents[1]

DATA_DIR = RAIZ / "data"

BASE_CSV = DATA_DIR / "pqrs_dataset_sintetico.csv"
NUEVOS_CSV = DATA_DIR / "pqrs_nuevos.csv"
STAGING_DIR = DATA_DIR / "staging"

MODELO_PATH = RAIZ / "models" / "modelo_urgencia.joblib"
BACKUP_DIR = RAIZ / "models" / "backups"

METRICAS_PATH = (
    RAIZ / "models" / "metricas_reentrenamiento.json"
)

EVALUACION_PATH = (
    RAIZ / "models" / "evaluacion_candidato.json"
)

MAX_FILAS = 50_000
MAX_BYTES = 20 * 1024 * 1024

MIN_CARACTERES = 15
MAX_CARACTERES = 5_000

MAX_ERRORES_MOSTRADOS = 200

EXTENSIONES = {
    ".csv", ".tsv", ".txt", ".xlsx", ".json"
}

OBLIGATORIAS = ("texto", "urgencia")

ALIAS = {
    "texto": {
        "texto",
        "descripcion",
        "descripcion_pqrs",
        "pqrs",
        "mensaje",
        "comentario",
        "detalle",
        "contenido",
        "text",
        "queja",
    },
    "urgencia": {
        "urgencia",
        "nivel_urgencia",
        "prioridad",
        "nivel",
        "etiqueta",
        "label",
        "clase",
        "urgency",
    },
}

NIVELES = {
    "baja": "Baja",
    "bajo": "Baja",
    "low": "Baja",
    "1": "Baja",

    "media": "Media",
    "medio": "Media",
    "normal": "Media",
    "medium": "Media",
    "2": "Media",

    "alta": "Alta",
    "alto": "Alta",
    "high": "Alta",
    "urgente": "Alta",
    "critica": "Alta",
    "critico": "Alta",
    "3": "Alta",

    "riesgo_simple": "Baja",
    "simple": "Baja",

    "riesgo_priorizado": "Media",
    "priorizado": "Media",

    "riesgo_vital": "Alta",
    "vital": "Alta",
}


# ============================================================
# UTILIDADES
# ============================================================

def _norm(s) -> str:
    """Normaliza texto para comparar nombres y etiquetas."""

    s = unicodedata.normalize(
        "NFKD", str(s)
    ).encode(
        "ascii", "ignore"
    ).decode()

    return re.sub(
        r"[^a-z0-9]+", "_", s.lower()
    ).strip("_")


def _limpiar_texto(s) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


def _clave_texto(s: str) -> str:
    return _norm(s)


def _nivel(valor) -> str | None:

    v = _norm(valor)

    if re.fullmatch(r"\d+_0+", v):
        v = v.split("_")[0]

    return NIVELES.get(v)


# ============================================================
# LECTURA DE ARCHIVOS
# ============================================================

def leer_archivo(
    nombre: str,
    contenido: bytes
) -> pd.DataFrame:

    ext = Path(nombre).suffix.lower()

    if ext not in EXTENSIONES:
        raise ValueError(
            f"Formato '{ext}' no soportado. "
            f"Use: {', '.join(sorted(EXTENSIONES))}"
        )

    if len(contenido) > MAX_BYTES:
        raise ValueError(
            "El archivo supera el limite de 20 MB."
        )

    if not contenido.strip():
        raise ValueError("El archivo esta vacio.")

    try:

        if ext == ".xlsx":

            return pd.read_excel(
                io.BytesIO(contenido),
                dtype=str,
                engine="openpyxl"
            ).fillna("")

        if ext == ".json":

            datos = json.loads(
                contenido.decode("utf-8-sig")
            )

            if isinstance(datos, dict):

                datos = next(
                    (
                        v for v in datos.values()
                        if isinstance(v, list)
                    ),
                    [datos]
                )

            if not isinstance(datos, list) or not datos:
                raise ValueError(
                    "El JSON debe contener una lista de registros."
                )

            return (
                pd.json_normalize(datos)
                .astype(str)
                .replace({"None": "", "nan": ""})
            )

        try:
            texto = contenido.decode("utf-8-sig")

        except UnicodeDecodeError:
            texto = contenido.decode("latin-1")

        try:
            sep = csv.Sniffer().sniff(
                texto[:5000],
                delimiters=",;\t|"
            ).delimiter

        except csv.Error:
            sep = "\t" if ext == ".tsv" else ","

        return pd.read_csv(
            io.StringIO(texto),
            sep=sep,
            dtype=str,
            keep_default_na=False,
            on_bad_lines="error"
        )

    except ValueError:
        raise

    except Exception as e:
        raise ValueError(
            f"No se pudo leer el archivo: {e}"
        ) from e


# ============================================================
# DETECCION DE TEXTOS EXISTENTES
# ============================================================

def textos_existentes() -> set[str]:

    claves = set()

    for ruta in (BASE_CSV, NUEVOS_CSV):

        if not ruta.exists():
            continue

        try:

            df = _renombrar(
                pd.read_csv(
                    ruta,
                    dtype=str,
                    keep_default_na=False
                )
            )[0]

            if "texto" in df.columns:

                claves.update(
                    _clave_texto(t)
                    for t in df["texto"]
                )

        except Exception:
            pass

    return claves


# ============================================================
# NORMALIZACION DE COLUMNAS
# ============================================================

def _renombrar(df: pd.DataFrame):

    mapeo = {}
    avisos = []
    usados = set()
    nuevas = []

    for col in df.columns:

        n = _norm(col) or "columna"

        canon = next(
            (
                c for c, al in ALIAS.items()
                if n in al
            ),
            None
        )

        if canon:

            if canon in usados:

                avisos.append(
                    f"La columna '{col}' tambien equivale "
                    f"a '{canon}'; se ignora la duplicada."
                )

                canon = n

            else:

                usados.add(canon)

                if str(col) != canon:
                    mapeo[str(col)] = canon

                n = canon

        nuevas.append(n)

    vistos = {}
    finales = []

    for n in nuevas:

        vistos[n] = vistos.get(n, 0) + 1

        finales.append(
            n if vistos[n] == 1
            else f"{n}_{vistos[n]}"
        )

    out = df.copy()
    out.columns = finales

    return out, mapeo, avisos


# ============================================================
# VALIDACION DE DATOS
# ============================================================

def validar(
    df: pd.DataFrame,
    comparar_existentes: bool = True
):

    rep = {
        "ok": False,
        "total_filas": int(len(df)),
        "validas": 0,
        "invalidas": 0,
        "duplicadas_en_archivo": 0,
        "duplicadas_ya_existentes": 0,
        "columnas_detectadas": [
            str(c) for c in df.columns
        ],
        "columnas_renombradas": {},
        "columnas_extra": [],
        "errores_fatales": [],
        "advertencias": [],
        "errores_filas": [],
        "distribucion_urgencia": {},
    }

    if df.empty:

        rep["errores_fatales"].append(
            "El archivo no contiene filas."
        )

        return pd.DataFrame(), rep

    if len(df) > MAX_FILAS:

        rep["errores_fatales"].append(
            f"El archivo supera {MAX_FILAS} filas."
        )

        return pd.DataFrame(), rep

    df, mapeo, avisos = _renombrar(df)

    rep["columnas_renombradas"] = mapeo
    rep["advertencias"] = avisos

    faltan = [
        c for c in OBLIGATORIAS
        if c not in df.columns
    ]

    if faltan:

        rep["errores_fatales"].append(
            "Faltan columnas obligatorias: "
            + ", ".join(faltan)
        )

        return pd.DataFrame(), rep

    extras = [
        c for c in df.columns
        if c not in OBLIGATORIAS
    ]

    rep["columnas_extra"] = extras

    if extras:

        rep["advertencias"].append(
            f"{len(extras)} columnas adicionales "
            "se conservaran, pero no se usaran "
            "para entrenar."
        )

    existentes = (
        textos_existentes()
        if comparar_existentes
        else set()
    )

    vistos = set()
    filas_ok = []
    errores = []

    for i, fila in enumerate(
        df.to_dict("records")
    ):

        n_fila = i + 2

        texto = _limpiar_texto(
            fila.get("texto", "")
        )

        nivel = _nivel(
            fila.get("urgencia", "")
        )

        motivo = None

        if not texto:
            motivo = "Texto vacio"

        elif len(texto) < MIN_CARACTERES:
            motivo = "Texto demasiado corto"

        elif len(texto) > MAX_CARACTERES:
            motivo = "Texto demasiado largo"

        elif nivel is None:
            motivo = "Urgencia no valida"

        if motivo:

            errores.append({
                "fila": n_fila,
                "motivo": motivo
            })

            continue

        clave = _clave_texto(texto)

        if clave in vistos:

            rep["duplicadas_en_archivo"] += 1
            continue

        if clave in existentes:

            rep["duplicadas_ya_existentes"] += 1
            continue

        vistos.add(clave)

        nueva = {
            k: _limpiar_texto(v)
            for k, v in fila.items()
            if k in extras
        }

        filas_ok.append({
            "texto": texto,
            "urgencia": nivel,
            **nueva
        })

    limpio = pd.DataFrame(
        filas_ok,
        columns=[
            "texto",
            "urgencia",
            *extras
        ]
    )

    rep["validas"] = int(len(limpio))
    rep["invalidas"] = len(errores)

    rep["errores_filas"] = (
        errores[:MAX_ERRORES_MOSTRADOS]
    )

    if len(errores) > MAX_ERRORES_MOSTRADOS:

        rep["advertencias"].append(
            "Solo se muestran los primeros "
            f"{MAX_ERRORES_MOSTRADOS} errores."
        )

    if rep["duplicadas_en_archivo"]:

        rep["advertencias"].append(
            f"{rep['duplicadas_en_archivo']} "
            "filas repetidas dentro del archivo."
        )

    if rep["duplicadas_ya_existentes"]:

        rep["advertencias"].append(
            f"{rep['duplicadas_ya_existentes']} "
            "filas ya existentes."
        )

    if len(limpio):

        rep["distribucion_urgencia"] = {
            k: int(v)
            for k, v in limpio[
                "urgencia"
            ].value_counts().items()
        }

    rep["ok"] = len(limpio) > 0

    if not rep["ok"]:

        rep["errores_fatales"].append(
            "Ninguna fila paso la validacion."
        )

    return limpio, rep


# ============================================================
# STAGING
# ============================================================

def guardar_staging(df: pd.DataFrame) -> str:

    STAGING_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    token = uuid.uuid4().hex

    df.to_csv(
        STAGING_DIR / f"{token}.csv",
        index=False,
        encoding="utf-8"
    )

    return token


def cargar_staging(token: str) -> pd.DataFrame:

    if not re.fullmatch(
        r"[0-9a-f]{32}",
        token or ""
    ):

        raise ValueError(
            "Token de lote invalido."
        )

    ruta = STAGING_DIR / f"{token}.csv"

    if not ruta.exists():

        raise ValueError(
            "El lote no existe o ya fue confirmado."
        )

    return pd.read_csv(
        ruta,
        dtype=str,
        keep_default_na=False
    )


def descartar_staging(token: str) -> None:

    if re.fullmatch(
        r"[0-9a-f]{32}",
        token or ""
    ):

        (
            STAGING_DIR / f"{token}.csv"
        ).unlink(missing_ok=True)


# ============================================================
# GUARDADO DE REGISTROS NUEVOS
# ============================================================

def guardar_lote(
    df: pd.DataFrame,
    fuente: str
) -> dict:

    lote = uuid.uuid4().hex[:8]

    df = df.copy()

    df["lote_id"] = lote

    df["fecha_carga"] = (
        datetime.now().isoformat(
            timespec="seconds"
        )
    )

    df["fuente"] = fuente[:80]

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if NUEVOS_CSV.exists():

        previo = pd.read_csv(
            NUEVOS_CSV,
            dtype=str,
            keep_default_na=False
        )

        df = pd.concat(
            [previo, df],
            ignore_index=True
        ).fillna("")

    tmp = NUEVOS_CSV.with_suffix(".tmp")

    df.to_csv(
        tmp,
        index=False,
        encoding="utf-8"
    )

    tmp.replace(NUEVOS_CSV)

    return {
        "lote_id": lote,
        "guardados": int(
            (df["lote_id"] == lote).sum()
        ),
        "total_nuevos": int(len(df))
    }


# ============================================================
# ESTADO DE DATOS Y MODELO
# ============================================================

def estado() -> dict:

    def contar(ruta):

        if not ruta.exists():
            return 0

        return int(
            len(
                pd.read_csv(
                    ruta,
                    usecols=[0],
                    dtype=str
                )
            )
        )

    metricas = None

    if METRICAS_PATH.exists():

        metricas = json.loads(
            METRICAS_PATH.read_text(
                encoding="utf-8"
            )
        )

    return {
        "registros_base": contar(BASE_CSV),
        "registros_nuevos": contar(NUEVOS_CSV),
        "ultimo_reentrenamiento": metricas
    }


# ============================================================
# CARGAR DATOS PARA ENTRENAMIENTO
# ============================================================

def _cargar_entrenamiento() -> pd.DataFrame:

    partes = []

    for ruta in (BASE_CSV, NUEVOS_CSV):

        if not ruta.exists():
            continue

        df, _, _ = _renombrar(
            pd.read_csv(
                ruta,
                dtype=str,
                keep_default_na=False
            )
        )

        if not set(OBLIGATORIAS) <= set(
            df.columns
        ):

            raise ValueError(
                f"{ruta.name} no tiene "
                "las columnas texto/urgencia."
            )

        df = df[
            list(OBLIGATORIAS)
        ].copy()

        df["urgencia_norm"] = (
            df["urgencia"].map(_nivel)
        )

        partes.append(
            df.dropna(
                subset=["urgencia_norm"]
            )
        )

    if not partes:

        raise ValueError(
            "No hay datos para entrenar."
        )

    return pd.concat(
        partes,
        ignore_index=True
    )


# ============================================================
# REENTRENAMIENTO SEGURO
# ============================================================

def reentrenar(
    actualizar_modelo: bool = False,
    entrenamiento: int = 70,
    validacion: int = 15,
    prueba: int = 15
) -> dict:

    """
    Evalua TF-IDF + Naive Bayes.

    Por defecto:
      - No modifica el modelo actual.
      - No reemplaza metricas anteriores.
      - Genera evaluacion_candidato.json.

    Con actualizar_modelo=True:
      - Entrena con todos los registros.
      - Respalda el modelo anterior.
      - Publica el nuevo modelo.
      - Actualiza las metricas registradas.

    La actualizacion no garantiza una mejora.
    """

    porcentajes = (entrenamiento, validacion, prueba)
    if any(type(v) is not int or v < 5 or v > 90 for v in porcentajes) or sum(porcentajes) != 100:
        raise ValueError("Los porcentajes deben ser enteros entre 5 y 90 y sumar 100.")

    import joblib

    from sklearn.base import clone

    from sklearn.feature_extraction.text import (
        TfidfVectorizer
    )

    from sklearn.metrics import (
        f1_score,
        recall_score,
        precision_score,
        classification_report,
        confusion_matrix
    )

    from sklearn.model_selection import (
        GroupShuffleSplit
    )

    from sklearn.naive_bayes import (
        MultinomialNB
    )

    from sklearn.pipeline import Pipeline

    try:
        from .preprocesamiento import preprocesar

    except ImportError:
        from src.preprocesamiento import preprocesar

    # --------------------------------------------------------
    # 1. CARGAR DATOS
    # --------------------------------------------------------

    datos = _cargar_entrenamiento()

    estilo = {}

    if BASE_CSV.exists():

        base = _renombrar(
            pd.read_csv(
                BASE_CSV,
                dtype=str,
                keep_default_na=False
            )
        )[0]

        estilo = {
            _norm(v): v
            for v in base["urgencia"].unique()
        }

    y = datos["urgencia_norm"].map(
        lambda v: estilo.get(
            _norm(v), v
        )
    )

    X = datos["texto"].map(
        preprocesar
    )

    # --------------------------------------------------------
    # 2. ELIMINAR TEXTOS VACIOS
    # --------------------------------------------------------

    mask = X.str.strip().astype(bool)

    X = X[mask].reset_index(
        drop=True
    )

    y = y[mask].reset_index(
        drop=True
    )

    if (
        y.nunique() != 3
        or y.value_counts().min() < 5
    ):

        raise ValueError(
            "Se necesitan las tres clases "
            "y al menos cinco ejemplos "
            "por clase."
        )

    # --------------------------------------------------------
    # 3. CONSERVAR NAIVE BAYES
    # --------------------------------------------------------

    if MODELO_PATH.exists():

        modelo_actual = joblib.load(
            MODELO_PATH
        )

        if (
            not isinstance(
                modelo_actual,
                Pipeline
            )
            or not isinstance(
                modelo_actual.steps[-1][1],
                MultinomialNB
            )
        ):

            raise ValueError(
                "El modelo actual no utiliza "
                "MultinomialNB. No se modifico "
                "ningun archivo."
            )

        plantilla = clone(
            modelo_actual
        )

    else:

        plantilla = Pipeline([
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=2,
                    sublinear_tf=True
                )
            ),
            (
                "clf",
                MultinomialNB(
                    alpha=0.5
                )
            )
        ])

    # --------------------------------------------------------
    # 4. SEPARACION POR GRUPOS
    # --------------------------------------------------------

    grupos = pd.factorize(X)[0]

    # Separamos grupos de textos idénticos para evitar fuga de información.
    separador = GroupShuffleSplit(n_splits=1, test_size=prueba / 100, random_state=42)
    tr_val, te = next(separador.split(X, y, groups=grupos))
    separador_val = GroupShuffleSplit(
        n_splits=1, test_size=validacion / (entrenamiento + validacion), random_state=43
    )
    tr_rel, val_rel = next(separador_val.split(
        X.iloc[tr_val], y.iloc[tr_val], groups=grupos[tr_val]
    ))
    tr, va = tr_val[tr_rel], tr_val[val_rel]
    for nombre, indices in (("entrenamiento", tr), ("validacion", va), ("prueba", te)):
        if len(indices) < 3 or set(y.iloc[indices]) != set(y):
            raise ValueError(
                f"La división dejó el conjunto de {nombre} sin suficientes ejemplos de todas las clases. "
                "Pruebe otros porcentajes o agregue más datos etiquetados."
            )

    # --------------------------------------------------------
    # 5. ENTRENAR CANDIDATO TEMPORAL
    # --------------------------------------------------------

    candidato = clone(
        plantilla
    )

    candidato.fit(
        X.iloc[tr],
        y.iloc[tr]
    )

    pred_validacion = candidato.predict(X.iloc[va])
    pred = candidato.predict(
        X.iloc[te]
    )

    # --------------------------------------------------------
    # 6. CALCULAR METRICAS
    # --------------------------------------------------------

    etiquetas = [
        c for c in (
            "Baja",
            "Media",
            "Alta"
        )
        if c in set(y)
    ]

    if len(etiquetas) != 3:
        etiquetas = sorted(y.unique())

    recall = recall_score(
        y.iloc[te],
        pred,
        labels=etiquetas,
        average=None,
        zero_division=0
    )

    precision = precision_score(
        y.iloc[te],
        pred,
        labels=etiquetas,
        average=None,
        zero_division=0
    )

    matriz = confusion_matrix(
        y.iloc[te],
        pred,
        labels=etiquetas
    )

    f1 = f1_score(
        y.iloc[te],
        pred,
        average="macro"
    )

    reporte = classification_report(
        y.iloc[te],
        pred,
        labels=etiquetas,
        output_dict=True,
        zero_division=0
    )

    # --------------------------------------------------------
    # 7. ORGANIZAR RESULTADOS
    # --------------------------------------------------------

    metricas = {

        "fecha": datetime.now().isoformat(
            timespec="seconds"
        ),

        # Compatibilidad con interfaz existente
        "registros_entrenamiento": int(
            len(X)
        ),

        "registros_totales": int(
            len(X)
        ),

        "registros_ajuste_evaluacion": int(
            len(tr)
        ),

        "registros_prueba": int(len(te)),
        "registros_validacion": int(len(va)),
        "registros_entrenamiento_real": int(len(tr)),
        "porcentajes_solicitados": {"entrenamiento": entrenamiento, "validacion": validacion, "prueba": prueba},
        "porcentajes_reales": {"entrenamiento": round(len(tr)*100/len(X), 2), "validacion": round(len(va)*100/len(X), 2), "prueba": round(len(te)*100/len(X), 2)},
        "f1_validacion": round(float(f1_score(y.iloc[va], pred_validacion, average="macro")), 4),

        "f1_macro": round(
            float(f1), 4
        ),

        "recall_por_clase": {
            c: round(float(r), 4)
            for c, r in zip(
                etiquetas,
                recall
            )
        },

        "precision_por_clase": {
            c: round(float(p), 4)
            for c, p in zip(
                etiquetas,
                precision
            )
        },

        "matriz_confusion": (
            matriz.tolist()
        ),

        "orden_clases_matriz": etiquetas,

        "reporte_por_clase": reporte,

        "distribucion": {
            k: int(v)
            for k, v in y.value_counts().items()
        },

        "separacion": (
            "GroupShuffleSplit por texto preprocesado, semillas 42 y 43; tres conjuntos sin solapamiento"
        ),

        "modelo_actualizado": False,

        "nota": (
            "Evaluacion de un candidato "
            "entrenado con una particion "
            "de los datos. No constituye "
            "una evaluacion independiente "
            "del modelo vigente entrenado "
            "con todos los registros."
        )
    }

    # --------------------------------------------------------
    # 8. ACTUALIZACION OPCIONAL DEL MODELO
    # --------------------------------------------------------

    if actualizar_modelo:

        final = clone(
            plantilla
        )

        final.fit(X, y)

        MODELO_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Respaldo del modelo anterior
        if MODELO_PATH.exists():

            BACKUP_DIR.mkdir(
                parents=True,
                exist_ok=True
            )

            copia = BACKUP_DIR / (
                "modelo_urgencia_"
                f"{datetime.now():%Y%m%d_%H%M%S_%f}"
                ".joblib"
            )

            shutil.copy2(
                MODELO_PATH,
                copia
            )

        # Guardado mediante archivo temporal
        temporal = MODELO_PATH.with_name(
            MODELO_PATH.name + ".tmp"
        )

        joblib.dump(
            final,
            temporal
        )

        temporal.replace(
            MODELO_PATH
        )

        metricas[
            "modelo_actualizado"
        ] = True

        METRICAS_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        METRICAS_PATH.write_text(
            json.dumps(
                metricas,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

    else:

        # ----------------------------------------------------
        # 9. GUARDAR EVALUACION SIN MODIFICAR MODELO
        # ----------------------------------------------------

        EVALUACION_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        EVALUACION_PATH.write_text(
            json.dumps(
                metricas,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

    return metricas
