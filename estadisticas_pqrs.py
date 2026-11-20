"""Estadística descriptiva de PQRS y archivos CSV del dataset; sin dependencias nuevas."""
from __future__ import annotations

import csv
import re
import statistics
import unicodedata
from collections import Counter
from pathlib import Path

from sqlalchemy import func, text
from models_db import Pqrs, Session

RAIZ = Path(__file__).resolve().parent
# Configurable por variable PQRS_DATASET_DIR; por defecto usa data/.
import os
DATASET_DIR = Path(os.environ.get('PQRS_DATASET_DIR', str(RAIZ / 'data'))).resolve()
STOP = set('a al algo algunas algunos ante antes asi aun aunque bajo bien cada como con contra cual cuando de del desde donde dos el ella ellas ellos en entre era es esa esas ese eso esos esta estaba estan estar estas este esto estos fue ha habia han hasta hay la las le les lo los mas me mi mis muy ni no nos o para pero por porque que quien quienes se sea ser si sin sobre son su sus tan te tiene tienen todo todos tras tu tus un una unas uno unos ya y e u'.split())
STOP |= {'pqrs', 'salud', 'solicitud', 'solicitudes', 'favor', 'gracias', 'buenos', 'dias', 'buenas', 'tardes'}


def palabras(cadena):
    sin_tildes = ''.join(c for c in unicodedata.normalize('NFKD', str(cadena or '').lower()) if not unicodedata.combining(c))
    return [p for p in re.findall(r'[a-zñ]{3,}', sin_tildes) if p not in STOP]


def histograma(x, grupos=8):
    """Histograma de frecuencia absoluta; intervalos [inicio, fin), salvo el último."""
    if not x:
        return []
    minimo, maximo = min(x), max(x)
    if minimo == maximo:
        return [{'nombre': f'{minimo:.2f}', 'cantidad': len(x)}]
    paso = (maximo - minimo) / grupos
    conteo = [0] * grupos
    for v in x:
        indice = min(grupos - 1, int((v - minimo) / paso))
        conteo[indice] += 1
    return [{'nombre': f'{minimo + i*paso:.1f}–{minimo + (i+1)*paso:.1f}', 'cantidad': n}
            for i, n in enumerate(conteo)]


def resumen_numerico(valores):
    x = sorted(float(v) for v in valores if v is not None)
    if not x:
        return {'n': 0, 'media': None, 'mediana': None, 'moda': None, 'desviacion': None, 'minimo': None, 'maximo': None, 'q1': None, 'q3': None, 'histograma': []}
    def pct(p):
        i = (len(x) - 1) * p
        a = int(i)
        return x[a] + (x[min(a + 1, len(x) - 1)] - x[a]) * (i - a)
    freq = Counter(x)
    max_freq = max(freq.values())
    moda = min(v for v, n in freq.items() if n == max_freq) if max_freq > 1 else None
    def r(v): return round(v, 2) if v is not None else None
    return {'n': len(x), 'media': r(statistics.mean(x)), 'mediana': r(statistics.median(x)),
            'moda': r(moda), 'desviacion': r(statistics.pstdev(x)), 'minimo': r(x[0]),
            'maximo': r(x[-1]), 'q1': r(pct(.25)), 'q3': r(pct(.75)), 'histograma': histograma(x)}


def conteos(datos, limite=12):
    return [{'nombre': str(k), 'cantidad': int(v)} for k, v in Counter(str(x).strip() for x in datos if x is not None and str(x).strip()).most_common(limite)]


def patrones(textos):
    uni, bi = Counter(), Counter()
    for texto in textos:
        p = palabras(texto)
        uni.update(p)
        bi.update(' '.join(par) for par in zip(p, p[1:]))
    return {'palabras': [{'nombre': k, 'cantidad': v} for k, v in uni.most_common(20)],
            'frases': [{'nombre': k, 'cantidad': v} for k, v in bi.most_common(20)],
            'palabras_distintas': len(uni), 'frases_distintas': len(bi)}


def _leer_csvs():
    archivos = []
    total = 0
    textos = []
    longitudes = []
    categorias = Counter()
    tipos = Counter()
    # Solo CSV directos en data/; no lee backups ni subcarpetas para evitar duplicaciones accidentales.
    if not DATASET_DIR.is_dir():
        return {'directorio': str(DATASET_DIR), 'archivos': [], 'total_registros': 0, 'textos_analizados': 0,
                'advertencias': ['No existe la carpeta del dataset. Configura PQRS_DATASET_DIR.'], 'patrones': patrones([]), 'longitud_palabras': resumen_numerico([]), 'etiquetas': [], 'tipos': []}
    advertencias = []
    for path in sorted(DATASET_DIR.glob('*.csv')):
        try:
            with path.open('r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                campos = reader.fieldnames or []
                lookup = {c.strip().lower(): c for c in campos if c}
                columna_texto = next((lookup[k] for k in ('texto', 'text', 'descripcion', 'descripcion_pqrs', 'contenido', 'mensaje', 'solicitud') if k in lookup), None)
                columna_tipo = next((lookup[k] for k in ('tipo', 'tipo_pqrs', 'tipo_solicitud') if k in lookup), None)
                columna_clase = next((lookup[k] for k in ('urgencia', 'urgencia_predicha', 'clasificacion', 'etiqueta', 'label', 'categoria') if k in lookup), None)
                n = 0
                for row in reader:
                    if not any(v and str(v).strip() for v in row.values()):
                        continue
                    n += 1
                    if columna_texto and row.get(columna_texto):
                        contenido = row[columna_texto]
                        textos.append(contenido)
                        longitudes.append(len(str(contenido).split()))
                    if columna_clase and row.get(columna_clase):
                        categorias[str(row[columna_clase]).strip()] += 1
                    if columna_tipo and row.get(columna_tipo):
                        tipos[str(row[columna_tipo]).strip()] += 1
                total += n
                archivos.append({'archivo': path.name, 'registros': n, 'columna_texto': columna_texto, 'columna_etiqueta': columna_clase})
        except (UnicodeError, csv.Error, OSError) as exc:
            advertencias.append(f'No se pudo leer {path.name}: {exc}')
    if not archivos:
        advertencias.append('No se encontraron archivos CSV en data/. Si entrenas desde XLSX, expórtalos a CSV o configura una carpeta con CSV.')
    return {'directorio': str(DATASET_DIR), 'archivos': archivos, 'total_registros': total,
            'textos_analizados': len(textos), 'advertencias': advertencias,
            'patrones': patrones(textos), 'longitud_palabras': resumen_numerico(longitudes),
            'etiquetas': [{'nombre': k, 'cantidad': v} for k, v in categorias.most_common(20)],
            'tipos': [{'nombre': k, 'cantidad': v} for k, v in tipos.most_common(20)]}




def obtener_evaluacion():
    """Última evaluación de candidato; no equivale al modelo publicado."""
    import json
    carpeta = RAIZ / 'models'
    for nombre in ('evaluacion_candidato.json', 'metricas_reentrenamiento.json'):
        ruta = carpeta / nombre
        if not ruta.is_file():
            continue
        try:
            with ruta.open(encoding='utf-8') as archivo:
                datos = json.load(archivo)
            if isinstance(datos, dict):
                datos['archivo_origen'] = nombre
                return datos
        except (OSError, ValueError):
            continue
    return {'advertencia': 'Aún no hay una evaluación de reentrenamiento guardada.'}


def obtener_estadisticas():
    with Session() as db:
        filas = db.query(Pqrs).all()
        textos = [p.texto or '' for p in filas]
        probabilidades = [float(p.prob_urgencia) * 100 for p in filas if p.prob_urgencia is not None]
        riesgo_original = conteos([p.urgencia_predicha for p in filas])
        estado = conteos([p.estado for p in filas])
        entidades = conteos([p.entidad for p in filas])
        temas = conteos([p.tema for p in filas])
        tipos = conteos([p.tipo for p in filas])
        meses = Counter(p.fecha_radicacion.strftime('%Y-%m') for p in filas if p.fecha_radicacion)
        try:
            correcciones = db.execute(text('SELECT pqrs_id, urgencia_nueva FROM pqrs_correcciones_riesgo ORDER BY id ASC')).all()
        except Exception:
            correcciones = []
        ultimas = {int(pid): nivel for pid, nivel in correcciones}
        riesgo_final = conteos([ultimas.get(p.id, p.urgencia_predicha) for p in filas])
        return {'evaluacion': obtener_evaluacion(), 'dataset': _leer_csvs(), 'pqrs': {
            'total': len(filas), 'correcciones_eventos': len(correcciones), 'pqrs_corregidas': len(ultimas),
            'textos_analizados': len(textos), 'riesgo_original': riesgo_original, 'riesgo_final': riesgo_final,
            'estados': estado, 'entidades': entidades, 'temas': temas, 'tipos': tipos,
            'meses': [{'nombre': k, 'cantidad': meses[k]} for k in sorted(meses)],
            'confianza_porcentaje': resumen_numerico(probabilidades),
            'longitud_palabras': resumen_numerico([len(t.split()) for t in textos]),
            'longitud_caracteres': resumen_numerico([len(t) for t in textos]),
            'patrones': patrones(textos)}}
