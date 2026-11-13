from datetime import timedelta
import holidays

FESTIVOS = holidays.country_holidays("CO")

def sumar_dias_habiles(inicio, n):
    f = inicio
    while n > 0:
        f += timedelta(days=1)
        if f.weekday() < 5 and f.date() not in FESTIVOS:
            n -= 1
    return f

RECLAMO = {
    "baja":  ("Reclamo de riesgo simple", 72, "3.3.2.1"),
    "media": ("Reclamo de riesgo priorizado", 48, "3.3.2.2"),
    "alta":  ("Reclamo de riesgo vital", 24, "3.3.2.3"),
}

def plazo_legal(tipo, urgencia, fecha):
    t = (tipo or "").strip().lower()
    u = (urgencia or "").strip().lower()

    if t.startswith("reclamo"):
        nombre, horas, num = RECLAMO.get(u, RECLAMO["baja"])
        return {
            "clasificacion": nombre,
            "plazo": f"{horas} horas",
            "limite": fecha + timedelta(hours=horas),
            "norma": ("Circular Externa 047 de 2007 de la Superintendencia Nacional de Salud, "
                      f"numeral {num}, modificada por la Circular Externa 2023151000000010-5 de 2023"),
        }

    nombre = {"petición": "Petición", "peticion": "Petición",
              "queja": "Queja", "sugerencia": "Sugerencia"}.get(t, "Petición")
    return {
        "clasificacion": nombre,
        "plazo": "15 días hábiles",
        "limite": sumar_dias_habiles(fecha, 15),
        "norma": "Ley 1755 de 2015 y Circular Externa 047 de 2007, numeral 3.3.2.4",
    }