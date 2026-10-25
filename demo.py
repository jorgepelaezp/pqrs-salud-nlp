import joblib
from src.preprocesamiento import preprocesar

modelo = joblib.load("models/modelo_urgencia.joblib")

textos = [
    "Mi madre no ha recibido la insulina",
    "Sugiero cambiar el horario de atencion de la sala de espera",
]
for t in textos:
    print(modelo.predict([preprocesar(t)])[0], "<-", t)