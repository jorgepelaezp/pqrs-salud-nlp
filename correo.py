import os, smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from normas import plazo_legal

load_dotenv()

def enviar_comprobante(correo, radicado, fecha, entidad, tipo, urgencia):
    pl = plazo_legal(tipo, urgencia, fecha)

    msg = EmailMessage()
    msg["Subject"] = f"Comprobante de radicación {radicado}"
    msg["From"] = os.environ["GMAIL_USER"]
    msg["To"] = correo
    msg.set_content(
        f"Tu PQRS fue radicada correctamente.\n\n"
        f"Radicado: {radicado}\n"
        f"Fecha de radicación: {fecha:%d/%m/%Y %H:%M}\n"
        f"Entidad: {entidad}\n\n"
        f"CLASIFICACIÓN Y PLAZO\n"
        f"De acuerdo con la normatividad vigente ({pl['norma']}), "
        f"tu solicitud se clasifica de forma preliminar como: {pl['clasificacion']}.\n"
        f"La entidad tiene un plazo máximo de {pl['plazo']} para darte una respuesta "
        f"de fondo, es decir, hasta el {pl['limite']:%d/%m/%Y %H:%M}.\n\n"
        f"Esta clasificación fue generada automáticamente y la entidad puede ajustarla "
        f"según tu caso.\n\n"
        f"Si no recibes respuesta en el plazo, o no estás de acuerdo con ella, puedes "
        f"presentar una PQR ante la Superintendencia Nacional de Salud.\n\n"
        f"Si se trata de una emergencia médica, no esperes este trámite: "
        f"acude de inmediato a urgencias o llama al 123.\n"
    )
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as s:
            s.login(os.environ["GMAIL_USER"], os.environ["GMAIL_APP_PASSWORD"])
            s.send_message(msg)
        return True
    except Exception as e:
        print("Error enviando correo:", e)
        return False