"""Panel web del modelo de urgencia de PQRS.
Uso:  pip install flask  ->  python app.py  ->  abrir http://127.0.0.1:5000
Ejecútalo desde la carpeta raíz del repositorio (donde están models/ y src/)."""
import os, time
import joblib
from flask import Flask, jsonify, render_template, request
from src.preprocesamiento import preprocesar

RUTA = os.path.join("models", "modelo_urgencia.joblib")
modelo = joblib.load(RUTA)
app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("index.html")


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
    texto = (request.get_json(silent=True) or {}).get("texto", "").strip()
    if not texto:
        return jsonify(error="Escribe el texto de una PQRS."), 400
    limpio = preprocesar(texto)
    pred = str(modelo.predict([limpio])[0])
    probs = {}
    if hasattr(modelo, "predict_proba"):
        probs = {str(c): float(p) for c, p in zip(modelo.classes_, modelo.predict_proba([limpio])[0])}
    return jsonify(procesado=limpio, urgencia=pred, probabilidades=probs)


if __name__ == "__main__":
    app.run(debug=False)