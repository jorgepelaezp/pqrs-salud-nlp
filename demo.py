import os, sys, time, joblib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.preprocesamiento import preprocesar

ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "modelo_urgencia.joblib")
print("=== ARCHIVO DEL MODELO ===")
print("Ruta:      ", os.path.abspath(ruta))
print("Tamaño:    ", round(os.path.getsize(ruta) / 1024, 1), "KB")
print("Modificado:", time.ctime(os.path.getmtime(ruta)))

modelo = joblib.load(ruta)

print("\n=== QUÉ CONTIENE ===")
print("Tipo:  ", type(modelo).__name__)
if hasattr(modelo, "steps"):
    for nombre, paso in modelo.steps:
        print(f"Paso '{nombre}':", type(paso).__name__)
        if hasattr(paso, "vocabulary_"):
            print("   Vocabulario aprendido:", len(paso.vocabulary_), "términos")
print("Clases:", list(modelo.classes_))

print("\n=== PRUEBA EN VIVO ===")
while True:
    t = input("\nEscribe una PQRS (o 'salir'): ")
    if t.strip().lower() == "salir":
        break
    limpio = preprocesar(t)
    print("Texto procesado:", limpio)
    x = [limpio]
    print("Urgencia predicha:", modelo.predict(x)[0])
    if hasattr(modelo, "predict_proba"):
        for c, p in zip(modelo.classes_, modelo.predict_proba(x)[0]):
            print(f"   {c}: {p:.1%}")