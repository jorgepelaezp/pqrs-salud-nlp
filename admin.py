"""Panel administrativo de PQRS Salud, puerto 5001.
Conserva la predicción original y registra correcciones humanas por separado.
"""
from __future__ import annotations

import csv
import hmac
import io
import os
import secrets
from datetime import datetime, timedelta

from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func, or_, text, select

from models_db import Pqrs, Session, Solicitante
from src.carga_api import registrar_carga
from correo_estado import enviar_cambio_estado
from estadisticas_pqrs import obtener_estadisticas

ADMIN_USUARIO = os.environ.get("PQRS_ADMIN_USUARIO", "admin")
ADMIN_CLAVE = os.environ.get("PQRS_ADMIN_CLAVE", "admin")
ESTADOS = ["radicada", "en_revision", "respondida", "cerrada"]
URGENCIAS = ["Alta", "Media", "Baja"]

app = Flask(__name__)
app.secret_key = os.environ.get("PQRS_SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
registrar_carga(app)

# Tabla independiente: no modifica Pqrs.urgencia_predicha ni los archivos joblib.
# La tabla se crea automáticamente en la misma SQLite de models_db.Session.
def preparar_correcciones():
    with Session() as db:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS pqrs_correcciones_riesgo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pqrs_id INTEGER NOT NULL,
                urgencia_anterior TEXT NOT NULL,
                urgencia_nueva TEXT NOT NULL,
                motivo TEXT NOT NULL,
                usuario_admin TEXT NOT NULL,
                fecha TEXT NOT NULL
            )
        """))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_correcciones_pqrs ON pqrs_correcciones_riesgo(pqrs_id, id)"))
        db.commit()

preparar_correcciones()


def correccion_actual(db, pid):
    return db.execute(text("""
        SELECT urgencia_nueva, motivo, usuario_admin, fecha
        FROM pqrs_correcciones_riesgo
        WHERE pqrs_id=:pid ORDER BY id DESC LIMIT 1
    """), {"pid": pid}).mappings().first()


def urgencia_efectiva():
    ultima = (select(text("urgencia_nueva"))
              .select_from(text("pqrs_correcciones_riesgo"))
              .where(text("pqrs_id = pqrs.id"))
              .order_by(text("id DESC"))
              .limit(1).scalar_subquery())
    return func.coalesce(ultima, Pqrs.urgencia_predicha)


def _credenciales_validas(usuario, clave):
    return hmac.compare_digest(usuario or "", ADMIN_USUARIO) and hmac.compare_digest(clave or "", ADMIN_CLAVE)


def _autenticado():
    return session.get("admin") is True


PROTEGIDAS = ("/admin", "/api/admin", "/carga", "/api/carga")


@app.before_request
def proteger():
    p = request.path
    if p == "/admin/login" or not p.startswith(PROTEGIDAS):
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


@app.get("/admin/estadisticas")
def pagina_estadisticas():
    return render_template("admin_estadisticas.html")


@app.get("/api/admin/estadisticas")
def api_estadisticas():
    return jsonify(obtener_estadisticas())


@app.get("/admin")
def panel():
    return render_template("admin.html", estados=ESTADOS, urgencias=URGENCIAS)


def _fila(p, db):
    s = p.solicitante
    c = correccion_actual(db, p.id)
    return {
        "id": p.id,
        "radicado": p.radicado,
        "fecha": p.fecha_radicacion.strftime("%Y-%m-%d %H:%M") if p.fecha_radicacion else "",
        "nombre": s.nombre if s else "",
        "correo": s.correo if s else "",
        "entidad": p.entidad, "ciudad": p.ciudad, "regimen": p.regimen,
        "tipo": p.tipo, "tema": p.tema, "texto": p.texto,
        "urgencia": p.urgencia_predicha,  # Predicción ORIGINAL del modelo
        "urgencia_final": c["urgencia_nueva"] if c else p.urgencia_predicha,
        "corregida": bool(c),
        "motivo_correccion": c["motivo"] if c else None,
        "fecha_correccion": c["fecha"] if c else None,
        "prob": round(p.prob_urgencia, 3) if p.prob_urgencia is not None else None,
        "estado": p.estado, "canal": p.canal,
        "correo_enviado": bool(p.correo_enviado),
    }


def _consulta(db):
    q = db.query(Pqrs).outerjoin(Solicitante, Pqrs.solicitante_id == Solicitante.id)
    a = request.args
    if a.get("urgencia") in URGENCIAS:
        q = q.filter(urgencia_efectiva() == a["urgencia"])
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
    try:
        pagina = max(int(request.args.get("pagina", 1) or 1), 1)
        por_pagina = min(max(int(request.args.get("por_pagina", 20) or 20), 1), 100)
    except ValueError:
        return jsonify(error="Paginación inválida."), 400
    with Session() as db:
        q = _consulta(db)
        total = q.count()
        filas = (q.order_by(Pqrs.fecha_radicacion.desc(), Pqrs.id.desc())
                 .offset((pagina - 1) * por_pagina).limit(por_pagina).all())
        return jsonify(total=total, pagina=pagina, por_pagina=por_pagina,
                       items=[_fila(p, db) for p in filas])


@app.get("/api/admin/resumen")
def api_resumen():
    with Session() as db:
        total = db.query(func.count(Pqrs.id)).scalar() or 0
        por_urg = dict(db.query(urgencia_efectiva(), func.count(Pqrs.id))
                       .group_by(urgencia_efectiva()).all())
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


@app.post("/api/admin/pqrs/<int:pid>/riesgo")
def api_corregir_riesgo(pid):
    cuerpo = request.get_json(silent=True) or {}
    nuevo = cuerpo.get("urgencia")
    motivo = str(cuerpo.get("motivo") or "").strip()
    if nuevo not in URGENCIAS:
        return jsonify(error="Nivel de riesgo inválido."), 400
    if not 10 <= len(motivo) <= 1000:
        return jsonify(error="La justificación debe tener entre 10 y 1000 caracteres."), 400
    with Session() as db:
        p = db.get(Pqrs, pid)
        if not p:
            return jsonify(error="PQRS no encontrada."), 404
        anterior = correccion_actual(db, pid)
        anterior_nivel = anterior["urgencia_nueva"] if anterior else p.urgencia_predicha
        if nuevo == anterior_nivel:
            return jsonify(error="El nivel seleccionado ya es el vigente."), 400
        db.execute(text("""
            INSERT INTO pqrs_correcciones_riesgo
            (pqrs_id, urgencia_anterior, urgencia_nueva, motivo, usuario_admin, fecha)
            VALUES (:pid, :anterior, :nuevo, :motivo, :admin, :fecha)
        """), {"pid": pid, "anterior": anterior_nivel, "nuevo": nuevo,
                "motivo": motivo, "admin": ADMIN_USUARIO,
                "fecha": datetime.now().isoformat(timespec="seconds")})
        db.commit()
        return jsonify(ok=True, urgencia_predicha=p.urgencia_predicha,
                       urgencia_final=nuevo, corregida=True, motivo_correccion=motivo)


@app.get("/api/admin/pqrs/<int:pid>/historial-riesgo")
def api_historial_riesgo(pid):
    with Session() as db:
        if not db.get(Pqrs, pid):
            return jsonify(error="PQRS no encontrada."), 404
        rows = db.execute(text("""
            SELECT urgencia_anterior, urgencia_nueva, motivo, usuario_admin, fecha
            FROM pqrs_correcciones_riesgo WHERE pqrs_id=:pid ORDER BY id DESC
        """), {"pid": pid}).mappings().all()
        return jsonify(items=[dict(r) for r in rows])


@app.post("/api/admin/pqrs/<int:pid>/estado")
def api_estado(pid):
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
        notificado = None
        sol = p.solicitante
        if notificar and nuevo != anterior and sol and sol.correo:
            c = correccion_actual(db, pid)
            riesgo_final = c["urgencia_nueva"] if c else p.urgencia_predicha
            notificado = enviar_cambio_estado(
                sol.correo, sol.nombre, p.radicado, p.entidad,
                anterior, nuevo, nota,
                urgencia_original=p.urgencia_predicha,
                urgencia_final=riesgo_final,
            )
        return jsonify(ok=True, estado=nuevo, notificado=notificado)


def _celda_csv(v):
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s


@app.get("/api/admin/exportar.csv")
def api_exportar():
    with Session() as db:
        filas = [_fila(p, db) for p in _consulta(db).order_by(Pqrs.fecha_radicacion.desc()).all()]
    campos = ["radicado", "fecha", "nombre", "correo", "entidad", "ciudad", "regimen",
              "tipo", "tema", "urgencia", "urgencia_final", "corregida", "motivo_correccion",
              "prob", "estado", "canal", "texto"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(campos)
    for f in filas:
        w.writerow([_celda_csv(f[c]) for c in campos])
    return Response("\ufeff" + buf.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=pqrs_export.csv"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
