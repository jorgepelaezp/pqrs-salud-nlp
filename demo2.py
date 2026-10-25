import joblib
from src.preprocesamiento import preprocesar

modelo = joblib.load("models/modelo_urgencia.joblib")

casos = [
    # (texto, urgencia esperada)
    ("Mi madre no ha recibido la insulina y es de vida o muerte para su tratamiento", "alta"),
    ("Le negaron la autorizacion de la cirugia y existe riesgo vital para el paciente", "alta"),
    ("Rechazaron la atencion en urgencias a un paciente con dolor en el pecho", "alta"),
    ("Tengo un tramite administrativo estancado desde hace meses sin justificacion", "media"),
    ("Hay demora en la entrega de medicamentos y la atencion ha sido deficiente", "media"),
    ("Llevo semanas esperando que me asignen la cita de ortopedia", "media"),
    ("Sugiero poner ventiladores en la sala de espera", "baja"),
    ("Pido que amplien el horario de atencion de la oficina", "baja"),
    ("Recomiendo mejorar la vigilancia en el parqueadero de la clinica", "baja"),
    ("URGENTE: sugiero cambiar el color de las sillas de la sala", "baja"),  # falsa urgencia
]

aciertos = 0
for texto, esperado in casos:
    pred = str(modelo.predict([preprocesar(texto)])[0])
    ok = "OK " if pred.lower() == esperado else "DIF"
    aciertos += pred.lower() == esperado
    print(f"[{ok}] predicho: {pred:<6} esperado: {esperado:<6} | {texto}")
print(f"\nAciertos: {aciertos}/{len(casos)}")

