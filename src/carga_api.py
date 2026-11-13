"""Rutas Flask para la carga de datos (masiva y registro por registro).

Integración en app.py (3 líneas):

    from src.carga_api import registrar_carga
    registrar_carga(app, on_reentrenado=recargar_modelo)   # recargar_modelo es opcional

Si define la variable de entorno PQRS_ADMIN_TOKEN, confirmar/registro/reentrenar
exigen la cabecera X-Admin-Token con ese valor.
"""
from __future__ import annotations

import os
import threading

import pandas as pd
from flask import Blueprint, Response, jsonify, render_template, request

from . import ingesta

bp = Blueprint("carga", __name__)
_lock_entrenamiento = threading.Lock()
_callback = {"fn": None}


def registrar_carga(app, on_reentrenado=None):
    """Registra el blueprint y fija el límite de tamaño de subida."""
    _callback["fn"] = on_reentrenado
    app.config["MAX_CONTENT_LENGTH"] = max(app.config.get("MAX_CONTENT_LENGTH") or 0,
                                           ingesta.MAX_BYTES + 1024 * 1024)
    app.register_blueprint(bp)


def _autorizado() -> bool:
    token = os.environ.get("PQRS_ADMIN_TOKEN")
    return not token or request.headers.get("X-Admin-Token") == token


def _prohibido():
    return jsonify(error="Token de administrador inválido o ausente."), 403


@bp.get("/carga")
def pagina_carga():
    return render_template("carga.html", requiere_token=bool(os.environ.get("PQRS_ADMIN_TOKEN")))


@bp.get("/api/carga/estado")
def api_estado():
    return jsonify(ingesta.estado())


@bp.get("/api/carga/plantilla")
def api_plantilla():
    csv_txt = ("texto,urgencia\n"
               '"Mi madre no ha recibido la insulina y su salud empeora cada hora",Alta\n'
               '"Solicito cambio de fecha de mi cita de control con medicina general",Baja\n'
               '"Llevo dos semanas esperando la autorización de mis exámenes de laboratorio",Media\n')
    return Response("\ufeff" + csv_txt, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=plantilla_pqrs.csv"})


@bp.post("/api/carga/validar")
def api_validar():
    """Paso 1: sube el archivo, lo valida y deja el lote en espera de confirmación."""
    archivo = request.files.get("archivo")
    if not archivo or not archivo.filename:
        return jsonify(error="Adjunte un archivo en el campo 'archivo'."), 400
    try:
        df = ingesta.leer_archivo(archivo.filename, archivo.read())
    except ValueError as e:
        return jsonify(error=str(e)), 400
    limpio, reporte = ingesta.validar(df)
    reporte["archivo"] = archivo.filename
    if reporte["ok"]:
        reporte["token"] = ingesta.guardar_staging(limpio)
        reporte["vista_previa"] = limpio.head(10).to_dict("records")
    return jsonify(reporte), (200 if reporte["ok"] else 422)


@bp.post("/api/carga/confirmar")
def api_confirmar():
    """Paso 2: el usuario confirma y el lote validado se agrega al dataset."""
    if not _autorizado():
        return _prohibido()
    cuerpo = request.get_json(silent=True)
    if not isinstance(cuerpo, dict):
        return jsonify(error="Se esperaba un objeto JSON con 'token'."), 400
    token = cuerpo.get("token", "")
    try:
        df = ingesta.cargar_staging(token)
        res = ingesta.guardar_lote(df, fuente=str(cuerpo.get("archivo") or "carga_masiva"))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    ingesta.descartar_staging(token)
    return jsonify(res)


@bp.post("/api/carga/registro")
def api_registro():
    """Carga de un solo registro (texto, urgencia y campos adicionales opcionales)."""
    if not _autorizado():
        return _prohibido()
    cuerpo = request.get_json(silent=True)
    if not isinstance(cuerpo, dict):
        return jsonify(error="Se esperaba un objeto JSON."), 400
    limpio, reporte = ingesta.validar(pd.DataFrame([{k: str(v) for k, v in cuerpo.items()}]))
    if not reporte["ok"]:
        motivos = [e["motivo"] for e in reporte["errores_filas"]] + reporte["errores_fatales"]
        if reporte["duplicadas_ya_existentes"]:
            motivos.append("Este texto ya existe en el dataset.")
        return jsonify(error="; ".join(motivos) or "Registro inválido.", reporte=reporte), 422
    return jsonify({**ingesta.guardar_lote(limpio, fuente="registro_manual"), "reporte": reporte})


@bp.post("/api/carga/reentrenar")
def api_reentrenar():
    if not _autorizado():
        return _prohibido()
    if not _lock_entrenamiento.acquire(blocking=False):
        return jsonify(error="Ya hay un reentrenamiento en curso."), 409
    try:
        metricas = ingesta.reentrenar()
        if _callback["fn"]:
            _callback["fn"]()
        return jsonify(metricas)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    finally:
        _lock_entrenamiento.release()
