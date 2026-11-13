"""Ingesta, validación y reentrenamiento con nuevos registros PQRS.

Flujo:
    leer_archivo()  ->  validar()  ->  guardar_lote()  ->  reentrenar()

Reglas de validación (ver CONFIGURACIÓN):
  * Columnas OBLIGATORIAS: texto y urgencia (lo mínimo para entrenar).
  * Cualquier columna adicional (8, 10 o las que sean) se ACEPTA y se conserva
    en data/pqrs_nuevos.csv, pero no se usa para entrenar.
  * Los nombres de columna se normalizan (mayúsculas, tildes, espacios) y se
    reconocen sinónimos: "Descripción", "mensaje", "prioridad", etc.
  * Las filas inválidas se descartan y se reportan con su motivo; las válidas
    pasan. Nada se guarda hasta que el usuario confirme.
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

# ───────────────────────── CONFIGURACIÓN (ajustar al proyecto) ─────────────────────────
RAIZ = Path(__file__).resolve().parents[1]
DATA_DIR = RAIZ / "data"
BASE_CSV = DATA_DIR / "pqrs_dataset_sintetico.csv"   # dataset original
NUEVOS_CSV = DATA_DIR / "pqrs_nuevos.csv"            # registros cargados por la app
STAGING_DIR = DATA_DIR / "staging"                   # lotes validados esperando confirmación
MODELO_PATH = RAIZ / "models" / "modelo_urgencia.joblib"
BACKUP_DIR = RAIZ / "models" / "backups"
METRICAS_PATH = RAIZ / "models" / "metricas_reentrenamiento.json"

MAX_FILAS = 50_000            # tope por archivo
MAX_BYTES = 20 * 1024 * 1024  # 20 MB
MIN_CARACTERES = 15           # texto más corto se considera inválido
MAX_CARACTERES = 5_000
EXTENSIONES = {".csv", ".tsv", ".txt", ".xlsx", ".json"}

# Columna canónica -> sinónimos aceptados (ya normalizados)
ALIAS = {
    "texto": {"texto", "descripcion", "descripcion_pqrs", "pqrs", "mensaje",
              "comentario", "detalle", "contenido", "text", "queja"},
    "urgencia": {"urgencia", "nivel_urgencia", "prioridad", "nivel", "etiqueta",
                 "label", "clase", "urgency"},
}
OBLIGATORIAS = ("texto", "urgencia")

# Valor recibido (normalizado) -> nivel canónico
NIVELES = {
    "baja": "Baja", "bajo": "Baja", "low": "Baja", "1": "Baja",
    "media": "Media", "medio": "Media", "normal": "Media", "medium": "Media", "2": "Media",
    "alta": "Alta", "alto": "Alta", "high": "Alta", "urgente": "Alta",
    "critica": "Alta", "critico": "Alta", "3": "Alta",
        # Clasificación Supersalud (Circular Externa 2023151000000010-5 de 2023)
    "riesgo_simple": "Baja", "simple": "Baja",
    "riesgo_priorizado": "Media", "priorizado": "Media",
    "riesgo_vital": "Alta", "vital": "Alta",
}
MAX_ERRORES_MOSTRADOS = 200
# ───────────────────────────────────────────────────────────────────────────────────────


# ───────────────────────────── utilidades ─────────────────────────────
def _norm(s) -> str:
    """minúsculas, sin tildes, solo [a-z0-9_]."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _limpiar_texto(s) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


def _clave_texto(s: str) -> str:
    return _norm(s)


def _nivel(valor) -> str | None:
    v = _norm(valor)
    if re.fullmatch(r"\d+_0+", v):          # "1.0" de Excel -> "1_0"
        v = v.split("_")[0]
    return NIVELES.get(v)


# ───────────────────────────── lectura ─────────────────────────────
def leer_archivo(nombre: str, contenido: bytes) -> pd.DataFrame:
    """Lee CSV/TSV/TXT/XLSX/JSON a DataFrame de strings. Lanza ValueError si no se puede."""
    ext = Path(nombre).suffix.lower()
    if ext not in EXTENSIONES:
        raise ValueError(f"Formato '{ext or 'sin extensión'}' no soportado. "
                         f"Use: {', '.join(sorted(EXTENSIONES))}.")
    if len(contenido) > MAX_BYTES:
        raise ValueError(f"El archivo supera {MAX_BYTES // (1024 * 1024)} MB.")
    if not contenido.strip():
        raise ValueError("El archivo está vacío.")

    try:
        if ext == ".xlsx":
            return pd.read_excel(io.BytesIO(contenido), dtype=str, engine="openpyxl").fillna("")

        if ext == ".json":
            datos = json.loads(contenido.decode("utf-8-sig"))
            if isinstance(datos, dict):
                datos = next((v for v in datos.values() if isinstance(v, list)), [datos])
            if not isinstance(datos, list) or not datos:
                raise ValueError("El JSON debe ser una lista de registros (objetos).")
            return pd.json_normalize(datos).astype(str).replace({"None": "", "nan": ""})

        # CSV / TSV / TXT: codificación y separador automáticos
        try:
            texto = contenido.decode("utf-8-sig")
        except UnicodeDecodeError:
            texto = contenido.decode("latin-1")
        try:
            sep = csv.Sniffer().sniff(texto[:5000], delimiters=",;\t|").delimiter
        except csv.Error:
            sep = "\t" if ext == ".tsv" else ","
        return pd.read_csv(io.StringIO(texto), sep=sep, dtype=str,
                           keep_default_na=False, on_bad_lines="error")
    except ValueError:
        raise
    except Exception as e:  # pandas.errors.ParserError, BadZipFile, etc.
        raise ValueError(f"No se pudo leer el archivo: {e}") from e


# ───────────────────────────── validación ─────────────────────────────
def textos_existentes() -> set[str]:
    """Claves de los textos ya presentes en el dataset base y en los nuevos."""
    claves: set[str] = set()
    for ruta in (BASE_CSV, NUEVOS_CSV):
        if ruta.exists():
            try:
                df = _renombrar(pd.read_csv(ruta, dtype=str, keep_default_na=False))[0]
                if "texto" in df:
                    claves.update(_clave_texto(t) for t in df["texto"])
            except Exception:
                pass
    return claves


def _renombrar(df: pd.DataFrame):
    """Normaliza nombres de columna y aplica sinónimos. -> (df, mapeo, avisos)."""
    mapeo, avisos, usados, nuevas = {}, [], set(), []
    for col in df.columns:
        n = _norm(col) or "columna"
        canon = next((c for c, al in ALIAS.items() if n in al), None)
        if canon:
            if canon in usados:
                avisos.append(f"La columna '{col}' también equivale a '{canon}'; se ignora (se usa la primera).")
                canon = n
            else:
                usados.add(canon)
                if str(col) != canon:
                    mapeo[str(col)] = canon
                n = canon
        nuevas.append(n)
    # nombres repetidos tras normalizar
    vistos: dict[str, int] = {}
    finales = []
    for n in nuevas:
        vistos[n] = vistos.get(n, 0) + 1
        finales.append(n if vistos[n] == 1 else f"{n}_{vistos[n]}")
    out = df.copy()
    out.columns = finales
    return out, mapeo, avisos


def validar(df: pd.DataFrame, comparar_existentes: bool = True):
    """Valida un DataFrame. Devuelve (df_limpio, reporte)."""
    rep = {
        "ok": False, "total_filas": int(len(df)), "validas": 0, "invalidas": 0,
        "duplicadas_en_archivo": 0, "duplicadas_ya_existentes": 0,
        "columnas_detectadas": [str(c) for c in df.columns], "columnas_renombradas": {},
        "columnas_extra": [], "errores_fatales": [], "advertencias": [],
        "errores_filas": [], "distribucion_urgencia": {},
    }
    if df.empty:
        rep["errores_fatales"].append("El archivo no contiene filas de datos.")
        return pd.DataFrame(), rep
    if len(df) > MAX_FILAS:
        rep["errores_fatales"].append(f"El archivo tiene {len(df):,} filas; el máximo es {MAX_FILAS:,}. Divídalo en lotes.")
        return pd.DataFrame(), rep

    df, mapeo, avisos = _renombrar(df)
    rep["columnas_renombradas"], rep["advertencias"] = mapeo, avisos
    faltan = [c for c in OBLIGATORIAS if c not in df.columns]
    if faltan:
        rep["errores_fatales"].append(
            f"Faltan columnas obligatorias: {', '.join(faltan)}. "
            f"Columnas encontradas: {', '.join(rep['columnas_detectadas'])}.")
        return pd.DataFrame(), rep

    extras = [c for c in df.columns if c not in OBLIGATORIAS]
    rep["columnas_extra"] = extras
    if extras:
        rep["advertencias"].append(
            f"{len(extras)} columna(s) adicional(es) aceptada(s) y conservadas; "
            f"no se usan para entrenar: {', '.join(extras)}.")

    existentes = textos_existentes() if comparar_existentes else set()
    vistos: set[str] = set()
    filas_ok, errores = [], []
    for i, fila in enumerate(df.to_dict("records")):
        n_fila = i + 2  # +1 por encabezado, +1 por base 1 (coincide con Excel)
        texto = _limpiar_texto(fila.get("texto", ""))
        nivel = _nivel(fila.get("urgencia", ""))
        motivo = None
        if not texto:
            motivo = "texto vacío"
        elif len(texto) < MIN_CARACTERES:
            motivo = f"texto demasiado corto (< {MIN_CARACTERES} caracteres)"
        elif len(texto) > MAX_CARACTERES:
            motivo = f"texto demasiado largo (> {MAX_CARACTERES} caracteres)"
        elif nivel is None:
            motivo = f"urgencia no válida: '{str(fila.get('urgencia', ''))[:20]}' (use Baja, Media o Alta)"
        if motivo:
            errores.append({"fila": n_fila, "motivo": motivo})
            continue
        clave = _clave_texto(texto)
        if clave in vistos:
            rep["duplicadas_en_archivo"] += 1
            continue
        if clave in existentes:
            rep["duplicadas_ya_existentes"] += 1
            continue
        vistos.add(clave)
        nueva = {k: _limpiar_texto(v) for k, v in fila.items() if k in extras}
        filas_ok.append({"texto": texto, "urgencia": nivel, **nueva})

    limpio = pd.DataFrame(filas_ok, columns=["texto", "urgencia", *extras])
    rep["validas"] = int(len(limpio))
    rep["invalidas"] = len(errores)
    rep["errores_filas"] = errores[:MAX_ERRORES_MOSTRADOS]
    if len(errores) > MAX_ERRORES_MOSTRADOS:
        rep["advertencias"].append(f"Se muestran solo los primeros {MAX_ERRORES_MOSTRADOS} errores de {len(errores)}.")
    if rep["duplicadas_en_archivo"]:
        rep["advertencias"].append(f"{rep['duplicadas_en_archivo']} fila(s) repetida(s) dentro del archivo: se descartaron.")
    if rep["duplicadas_ya_existentes"]:
        rep["advertencias"].append(f"{rep['duplicadas_ya_existentes']} fila(s) ya existen en el dataset: se descartaron.")
    if len(limpio):
        rep["distribucion_urgencia"] = {k: int(v) for k, v in limpio["urgencia"].value_counts().items()}
    rep["ok"] = len(limpio) > 0
    if not rep["ok"]:
        rep["errores_fatales"].append("Ninguna fila pasó la validación.")
    return limpio, rep


# ───────────────────────────── staging y guardado ─────────────────────────────
def guardar_staging(df: pd.DataFrame) -> str:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    df.to_csv(STAGING_DIR / f"{token}.csv", index=False, encoding="utf-8")
    return token


def cargar_staging(token: str) -> pd.DataFrame:
    if not re.fullmatch(r"[0-9a-f]{32}", token or ""):
        raise ValueError("Token de lote inválido.")
    ruta = STAGING_DIR / f"{token}.csv"
    if not ruta.exists():
        raise ValueError("El lote no existe o ya fue confirmado. Vuelva a cargar el archivo.")
    return pd.read_csv(ruta, dtype=str, keep_default_na=False)


def descartar_staging(token: str) -> None:
    if re.fullmatch(r"[0-9a-f]{32}", token or ""):
        (STAGING_DIR / f"{token}.csv").unlink(missing_ok=True)


def guardar_lote(df: pd.DataFrame, fuente: str) -> dict:
    """Agrega el lote validado a data/pqrs_nuevos.csv (unión de columnas)."""
    lote = uuid.uuid4().hex[:8]
    df = df.copy()
    df["lote_id"] = lote
    df["fecha_carga"] = datetime.now().isoformat(timespec="seconds")
    df["fuente"] = fuente[:80]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if NUEVOS_CSV.exists():
        previo = pd.read_csv(NUEVOS_CSV, dtype=str, keep_default_na=False)
        df = pd.concat([previo, df], ignore_index=True).fillna("")
    tmp = NUEVOS_CSV.with_suffix(".tmp")
    df.to_csv(tmp, index=False, encoding="utf-8")
    tmp.replace(NUEVOS_CSV)
    return {"lote_id": lote, "guardados": int((df["lote_id"] == lote).sum()), "total_nuevos": int(len(df))}


def estado() -> dict:
    def contar(p):
        return int(len(pd.read_csv(p, usecols=[0], dtype=str))) if p.exists() else 0
    metricas = json.loads(METRICAS_PATH.read_text()) if METRICAS_PATH.exists() else None
    return {"registros_base": contar(BASE_CSV), "registros_nuevos": contar(NUEVOS_CSV),
            "ultimo_reentrenamiento": metricas}


# ───────────────────────────── reentrenamiento ─────────────────────────────
def _cargar_entrenamiento() -> pd.DataFrame:
    partes = []
    for ruta in (BASE_CSV, NUEVOS_CSV):
        if not ruta.exists():
            continue
        df, _, _ = _renombrar(pd.read_csv(ruta, dtype=str, keep_default_na=False))
        if not set(OBLIGATORIAS) <= set(df.columns):
            raise ValueError(f"{ruta.name} no tiene las columnas texto/urgencia.")
        df = df[list(OBLIGATORIAS)].copy()
        df["urgencia_norm"] = df["urgencia"].map(_nivel)
        partes.append(df.dropna(subset=["urgencia_norm"]))
    if not partes:
        raise ValueError("No hay datos para entrenar.")
    return pd.concat(partes, ignore_index=True)


def reentrenar() -> dict:
    """Reentrena con base + nuevos, evalúa en un 20 % reservado y guarda el modelo.

    Reutiliza la arquitectura (TF-IDF + clasificador) del modelo vigente con sus
    mismos hiperparámetros; si no existe, usa TF-IDF + Naive Bayes.
    """
    import joblib
    import numpy as np
    from sklearn.base import clone
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics import f1_score, recall_score
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline

    try:
        from .preprocesamiento import preprocesar
    except ImportError:  # ejecución fuera del paquete
        from src.preprocesamiento import preprocesar

    datos = _cargar_entrenamiento()
    # Mismo estilo de etiquetas que el dataset base (p. ej. 'Alta' o 'alta')
    estilo = {}
    if BASE_CSV.exists():
        base = _renombrar(pd.read_csv(BASE_CSV, dtype=str, keep_default_na=False))[0]
        estilo = {_norm(v): v for v in base["urgencia"].unique()}
    y = datos["urgencia_norm"].map(lambda v: estilo.get(_norm(v), v))
    X = datos["texto"].map(preprocesar)
    mask = X.str.strip().astype(bool)
    X, y = X[mask].reset_index(drop=True), y[mask].reset_index(drop=True)
    if y.nunique() < 2 or y.value_counts().min() < 5:
        raise ValueError("Se necesitan al menos 5 ejemplos de cada nivel de urgencia.")

    if MODELO_PATH.exists():
        try:
            plantilla = clone(joblib.load(MODELO_PATH))
        except Exception:
            plantilla = None
    else:
        plantilla = None
    if plantilla is None:
        plantilla = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
                              ("clf", MultinomialNB(alpha=0.5))])

    # Evaluación: textos idénticos quedan en la misma partición (evita fuga de datos)
    grupos = pd.factorize(X)[0]
    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42).split(X, y, grupos))
    ev = clone(plantilla).fit(X.iloc[tr], y.iloc[tr])
    pred = ev.predict(X.iloc[te])
    etiquetas = sorted(y.unique())
    metricas = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "registros_entrenamiento": int(len(X)),
        "registros_prueba": int(len(te)),
        "f1_macro": round(float(f1_score(y.iloc[te], pred, average="macro")), 4),
        "recall_por_clase": {c: round(float(r), 4) for c, r in zip(
            etiquetas, recall_score(y.iloc[te], pred, labels=etiquetas, average=None, zero_division=0))},
        "distribucion": {k: int(v) for k, v in y.value_counts().items()},
    }

    # Modelo final con todos los datos; respaldo del anterior
    final = clone(plantilla).fit(X, y)
    MODELO_PATH.parent.mkdir(parents=True, exist_ok=True)
    if MODELO_PATH.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MODELO_PATH, BACKUP_DIR / f"modelo_urgencia_{datetime.now():%Y%m%d_%H%M%S}.joblib")
    joblib.dump(final, MODELO_PATH)
    METRICAS_PATH.write_text(json.dumps(metricas, ensure_ascii=False, indent=2))
    return metricas
