"""Panel web del modelo de urgencia de PQRS.
Uso:  pip install -r requirements.txt  ->  python app.py  ->  abrir http://127.0.0.1:5000
Puede ejecutarse desde cualquier carpeta: las rutas se construyen desde la raíz del repositorio."""
import os, sys, time
import joblib

from catalogos import CATALOGOS
from flask import Flask, jsonify, render_template, request

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
from src.preprocesamiento import preprocesar  # noqa: E402

RUTA = os.path.join(RAIZ, "models", "modelo_urgencia.joblib")
modelo = joblib.load(RUTA)
app = Flask(__name__)

from src.carga_api import registrar_carga
registrar_carga(app)

from models_db import Session, Solicitante, Pqrs
from correo import enviar_comprobante


@app.route("/")
def inicio():
    return render_template("formulario.html")


@app.route("/panel")
def panel():
    return render_template("index.html")


@app.route("/api/catalogos")
def catalogos():
    return jsonify(CATALOGOS)


@app.route("/api/info")
def info():
    pasos = []
    if hasattr(modelo, "steps"):
        for nombre, paso in modelo.steps:
            d = {"nombre": nombre, "tipo": type(paso).__name__}
            if hasattr(paso, "vocabulary_"):
                d["vocabulario"] = len(paso.vocabulary_)
            pasos.append(d)
    return jsonify(
        tipo=type(modelo).__name__,
        pasos=pasos,
        clases=[str(c) for c in modelo.classes_],
        kb=round(os.path.getsize(RUTA) / 1024, 1),
        modificado=time.ctime(os.path.getmtime(RUTA)),
    )


@app.route("/api/predecir", methods=["POST"])
def predecir():
    cuerpo = request.get_json(silent=True)
    if not isinstance(cuerpo, dict):
        return jsonify(error="El cuerpo debe ser un objeto JSON con el campo «texto»."), 400
    texto = cuerpo.get("texto")
    if not isinstance(texto, str):
        return jsonify(error="El campo «texto» debe ser una cadena de caracteres."), 400
    texto = texto.strip()
    if not texto:
        return jsonify(error="Escribe el texto de una PQRS."), 400
    limpio = preprocesar(texto)
    if not limpio:
        return jsonify(error="El texto no tiene contenido aprovechable: escribe palabras que describan la solicitud."), 400
    pred = str(modelo.predict([limpio])[0])
    probs = {}
    if hasattr(modelo, "predict_proba"):
        # Claves en minúscula para que coincidan con las de la interfaz (baja / media / alta)
        probs = {str(c).lower(): float(p) for c, p in zip(modelo.classes_, modelo.predict_proba([limpio])[0])}
    return jsonify(procesado=limpio, urgencia=pred, probabilidades=probs)


@app.post("/api/radicar")
def radicar():
    d = request.get_json(silent=True)
    if not isinstance(d, dict):
        return jsonify(error="Se esperaba un objeto JSON"), 400
    if not d.get("correo") or not d.get("texto") or not d.get("acepta_datos"):
        return jsonify(error="Faltan campos obligatorios"), 400

    limpio = preprocesar(d["texto"])
    if not limpio:
        return jsonify(error="El texto está vacío"), 400
    urgencia = modelo.predict([limpio])[0]
    prob = float(modelo.predict_proba([limpio])[0].max())

    with Session() as s:
        sol = Solicitante(nombre=d.get("nombre"), correo=d["correo"], acepta_datos=True)
        p = Pqrs(solicitante=sol, texto=d["texto"], entidad=d.get("entidad"),
                 ciudad=d.get("ciudad"), regimen=d.get("regimen"),
                 tipo=d.get("tipo"), tema=d.get("tema"),
                 urgencia_predicha=urgencia, prob_urgencia=prob)
        s.add(p)
        s.flush()
        p.radicado = f"PQRS-{p.fecha_radicacion.year}-{p.id:06d}"
        s.commit()

        p.correo_enviado = enviar_comprobante(sol.correo, p.radicado, p.fecha_radicacion,
                                              p.entidad or "-", p.tipo, p.urgencia_predicha)
        s.commit()
        return jsonify(radicado=p.radicado, urgencia=urgencia,
                       correo_enviado=p.correo_enviado), 201

if __name__ == "__main__":
    app.run(debug=False)
