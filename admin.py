"""Panel de administración de PQRS (proceso separado del formulario público).

Uso:
    python admin.py        ->  http://127.0.0.1:5001/admin   (usuario: admin / contraseña: admin)

El formulario público sigue en app.py (puerto 5000). Ambos procesos leen la misma
base de datos SQLite (data/pqrs.db).
"""
from __future__ import annotations

import csv
import hmac
import io
import os
import secrets
import sys
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, Response, jsonify, redirect, render_template,
                   request, session, url_for)
from sqlalchemy import func, or_

from models_db import Pqrs, Session, Solicitante
from src.carga_api import registrar_carga
from correo_estado import enviar_cambio_estado

ADMIN_USUARIO = "admin"
ADMIN_CLAVE = "admin"

ESTADOS = ["radicada", "en_revision", "respondida", "cerrada"]
URGENCIAS = ["Alta", "Media", "Baja"]

app = Flask(__name__)
app.secret_key = os.environ.get("PQRS_SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

# Carga masiva / registro manual / reentrenamiento (ya los tienes en src/carga_api.py).
# Si el modelo se reentrena aquí, app.py debe reiniciarse para usar el nuevo .joblib.
registrar_carga(app)


# ---------------------------------------------------------------- autenticación
def _credenciales_validas(usuario: str, clave: str) -> bool:
    return (hmac.compare_digest(usuario or "", ADMIN_USUARIO)
            and hmac.compare_digest(clave or "", ADMIN_CLAVE))


def _autenticado() -> bool:
    return session.get("admin") is True


PROTEGIDAS = ("/admin", "/api/admin", "/carga", "/api/carga")


@app.before_request
def proteger():
    p = request.path
    if p in ("/admin/login",) or not p.startswith(PROTEGIDAS):
        return None
    if _autenticado():
        return None
    if p.startswith("/api/"):
        return jsonify(error="No autorizado."), 401
    return redirect(url_for("login", next=p))


@app.route("/admin/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if _credenciales_validas(request.form.get("usuario", ""), request.form.get("clave", "")):
            session.clear()
            session["admin"] = True
            destino = request.args.get("next", "")
            return redirect(destino if destino.startswith("/") and not destino.startswith("//") else url_for("panel"))
        error = "Usuario o contraseña incorrectos."
    return render_template("admin_login.html", error=error)


@app.get("/admin/salir")
def salir():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
def raiz():
    return redirect(url_for("panel"))


@app.get("/admin")
def panel():
    return render_template("admin.html", estados=ESTADOS, urgencias=URGENCIAS)


# ---------------------------------------------------------------- API de datos
def _fila(p: Pqrs) -> dict:
    s = p.solicitante
    return {
        "id": p.id,
        "radicado": p.radicado,
        "fecha": p.fecha_radicacion.strftime("%Y-%m-%d %H:%M") if p.fecha_radicacion else "",
        "nombre": s.nombre if s else "",
        "correo": s.correo if s else "",
        "entidad": p.entidad, "ciudad": p.ciudad, "regimen": p.regimen,
        "tipo": p.tipo, "tema": p.tema,
        "texto": p.texto,
        "urgencia": p.urgencia_predicha,
        "prob": round(p.prob_urgencia, 3) if p.prob_urgencia is not None else None,
        "estado": p.estado,
        "canal": p.canal,
        "correo_enviado": bool(p.correo_enviado),
    }


def _consulta(db):
    q = db.query(Pqrs).outerjoin(Solicitante, Pqrs.solicitante_id == Solicitante.id)
    a = request.args
    if a.get("urgencia") in URGENCIAS:
        q = q.filter(Pqrs.urgencia_predicha == a["urgencia"])
    if a.get("estado") in ESTADOS:
        q = q.filter(Pqrs.estado == a["estado"])
    if a.get("entidad"):
        q = q.filter(Pqrs.entidad == a["entidad"])
    if a.get("buscar"):
        like = f"%{a['buscar'].strip()}%"
        q = q.filter(or_(Pqrs.radicado.like(like), Pqrs.texto.like(like),
                         Solicitante.correo.like(like), Solicitante.nombre.like(like)))
    return q


@app.get("/api/admin/pqrs")
def api_pqrs():
    pagina = max(int(request.args.get("pagina", 1) or 1), 1)
    por_pagina = min(max(int(request.args.get("por_pagina", 20) or 20), 1), 100)
    with Session() as db:
        q = _consulta(db)
        total = q.count()
        filas = (q.order_by(Pqrs.fecha_radicacion.desc(), Pqrs.id.desc())
                  .offset((pagina - 1) * por_pagina).limit(por_pagina).all())
        return jsonify(total=total, pagina=pagina, por_pagina=por_pagina,
                       items=[_fila(p) for p in filas])


@app.get("/api/admin/resumen")
def api_resumen():
    with Session() as db:
        total = db.query(func.count(Pqrs.id)).scalar() or 0
        por_urg = dict(db.query(Pqrs.urgencia_predicha, func.count(Pqrs.id))
                         .group_by(Pqrs.urgencia_predicha).all())
        por_est = dict(db.query(Pqrs.estado, func.count(Pqrs.id))
                         .group_by(Pqrs.estado).all())
        hace7 = datetime.now() - timedelta(days=7)
        ultimos7 = (db.query(func.count(Pqrs.id))
                      .filter(Pqrs.fecha_radicacion >= hace7).scalar() or 0)
        entidades = [e for (e,) in db.query(Pqrs.entidad).distinct().order_by(Pqrs.entidad).all() if e]
        return jsonify(total=total, ultimos7=ultimos7,
                       urgencia={u: por_urg.get(u, 0) for u in URGENCIAS},
                       estado={e: por_est.get(e, 0) for e in ESTADOS},
                       entidades=entidades)


@app.post("/api/admin/pqrs/<int:pid>/estado")
def api_estado(pid: int):
    cuerpo = request.get_json(silent=True) or {}
    nuevo = cuerpo.get("estado")
    if nuevo not in ESTADOS:
        return jsonify(error="Estado inválido."), 400
    notificar = bool(cuerpo.get("notificar", True))
    nota = str(cuerpo.get("nota") or "").strip()[:500]
    with Session() as db:
        p = db.get(Pqrs, pid)
        if not p:
            return jsonify(error="PQRS no encontrada."), 404
        anterior = p.estado
        p.estado = nuevo
        db.commit()
        # None = no se intentó enviar; True/False = resultado del envío
        notificado = None
        sol = p.solicitante
        if notificar and nuevo != anterior and sol and sol.correo:
            notificado = enviar_cambio_estado(sol.correo, sol.nombre, p.radicado,
                                              p.entidad, anterior, nuevo, nota)
        return jsonify(ok=True, estado=nuevo, notificado=notificado)


def _celda_csv(v) -> str:
    """Evita inyección de fórmulas al abrir el CSV en Excel."""
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s


@app.get("/api/admin/exportar.csv")
def api_exportar():
    with Session() as db:
        filas = [_fila(p) for p in _consulta(db).order_by(Pqrs.fecha_radicacion.desc()).all()]
    campos = ["radicado", "fecha", "nombre", "correo", "entidad", "ciudad", "regimen",
              "tipo", "tema", "urgencia", "prob", "estado", "canal", "texto"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(campos)
    for f in filas:
        w.writerow([_celda_csv(f[c]) for c in campos])
    return Response("\ufeff" + buf.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=pqrs_export.csv"})


if __name__ == "__main__":
    # 127.0.0.1: solo accesible desde este equipo. Cambia a 0.0.0.0 únicamente detrás de HTTPS.
    app.run(host="127.0.0.1", port=5001, debug=False)
