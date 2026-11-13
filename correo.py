
import os
import smtplib
import ssl
import html

from email.message import EmailMessage
from dotenv import load_dotenv
from normas import plazo_legal


# ============================================================
# CONFIGURACIÓN DE GMAIL
# ============================================================

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

NOMBRE_REMITENTE = "Atención al Usuario · PQRS Salud"


# ============================================================
# GENERAR CORREO HTML PROFESIONAL
# ============================================================

def generar_html(radicado, fecha, entidad, pl):

    e = html.escape

    fecha_texto = fecha.strftime("%d/%m/%Y %H:%M")
    limite_texto = pl["limite"].strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>

<body style="
    margin:0;
    padding:0;
    background:#f1f5f9;
    font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;
">

<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
style="background:#f1f5f9;padding:32px 12px;">

<tr>
<td align="center">

<table role="presentation" width="600" cellpadding="0" cellspacing="0"
style="
    max-width:600px;
    width:100%;
    background:#ffffff;
    border-radius:14px;
    overflow:hidden;
    border:1px solid #e2e8f0;
">

    <!-- ENCABEZADO -->
    <tr>
        <td style="
            background:linear-gradient(135deg,#4f46e5,#7c3aed);
            padding:28px 32px;
            color:#ffffff;
        ">

            <div style="
                font-size:13px;
                letter-spacing:.08em;
                text-transform:uppercase;
                opacity:.85;
            ">
                PQRS en salud
            </div>

            <div style="
                font-size:24px;
                font-weight:600;
                margin-top:6px;
            ">
                ¡Tu solicitud fue radicada!
            </div>

        </td>
    </tr>

    <!-- MENSAJE INICIAL -->
    <tr>
        <td style="padding:28px 32px 8px;">

            <p style="
                margin:0 0 12px;
                font-size:16px;
                color:#0f172a;
            ">
                Hola,
            </p>

            <p style="
                margin:0;
                font-size:15px;
                line-height:1.6;
                color:#334155;
            ">
                Hemos recibido correctamente tu petición, queja o reclamo.
                A continuación encontrarás los datos de tu radicación.
            </p>

        </td>
    </tr>

    <!-- INFORMACIÓN DE RADICACIÓN -->
    <tr>
        <td style="padding:20px 32px;">

            <table role="presentation" width="100%" cellpadding="0"
            cellspacing="0" style="
                border:1px solid #e2e8f0;
                border-radius:10px;
            ">

                <tr>
                    <td style="
                        padding:14px 16px;
                        font-size:13px;
                        color:#64748b;
                        width:38%;
                    ">
                        Radicado
                    </td>

                    <td style="
                        padding:14px 16px;
                        font-size:15px;
                        font-weight:600;
                        color:#0f172a;
                    ">
                        {e(str(radicado))}
                    </td>
                </tr>

                <tr>
                    <td style="
                        padding:14px 16px;
                        font-size:13px;
                        color:#64748b;
                        border-top:1px solid #e2e8f0;
                    ">
                        Fecha de radicación
                    </td>

                    <td style="
                        padding:14px 16px;
                        font-size:15px;
                        color:#0f172a;
                        border-top:1px solid #e2e8f0;
                    ">
                        {e(fecha_texto)}
                    </td>
                </tr>

                <tr>
                    <td style="
                        padding:14px 16px;
                        font-size:13px;
                        color:#64748b;
                        border-top:1px solid #e2e8f0;
                    ">
                        Entidad
                    </td>

                    <td style="
                        padding:14px 16px;
                        font-size:15px;
                        color:#0f172a;
                        border-top:1px solid #e2e8f0;
                    ">
                        {e(str(entidad))}
                    </td>
                </tr>

            </table>

        </td>
    </tr>

    <!-- CLASIFICACIÓN -->
    <tr>
        <td style="padding:0 32px 24px;">

            <div style="
                background:#f8fafc;
                border:1px solid #e2e8f0;
                border-radius:10px;
                padding:18px;
            ">

                <div style="
                    font-size:12px;
                    letter-spacing:.06em;
                    text-transform:uppercase;
                    color:#64748b;
                    margin-bottom:10px;
                ">
                    Clasificación de tu solicitud
                </div>

                <div style="
                    font-size:18px;
                    font-weight:600;
                    color:#4f46e5;
                    margin-bottom:10px;
                ">
                    {e(str(pl["clasificacion"]))}
                </div>

                <p style="
                    margin:0;
                    font-size:14px;
                    line-height:1.6;
                    color:#334155;
                ">
                    De acuerdo con la normatividad vigente
                    ({e(str(pl["norma"]))}), tu solicitud se clasifica
                    de forma preliminar como:
                    <strong>{e(str(pl["clasificacion"]))}</strong>.
                </p>

            </div>

        </td>
    </tr>

    <!-- PLAZO LEGAL -->
    <tr>
        <td style="padding:0 32px 24px;">

            <div style="
                background:#eff6ff;
                border-left:4px solid #2563eb;
                border-radius:8px;
                padding:18px;
            ">

                <div style="
                    font-size:12px;
                    letter-spacing:.06em;
                    text-transform:uppercase;
                    color:#1d4ed8;
                    margin-bottom:8px;
                ">
                    Plazo máximo de respuesta
                </div>

                <div style="
                    font-size:20px;
                    font-weight:700;
                    color:#1e40af;
                    margin-bottom:8px;
                ">
                    {e(str(pl["plazo"]))}
                </div>

                <p style="
                    margin:0;
                    font-size:14px;
                    line-height:1.6;
                    color:#1e3a8a;
                ">
                    La entidad tiene este plazo máximo para darte
                    una respuesta de fondo.
                </p>

                <p style="
                    margin:12px 0 0;
                    font-size:14px;
                    font-weight:600;
                    color:#1e40af;
                ">
                    Fecha límite estimada: {e(limite_texto)}
                </p>

            </div>

        </td>
    </tr>

    <!-- INFORMACIÓN ADICIONAL -->
    <tr>
        <td style="padding:0 32px 24px;">

            <p style="
                margin:0 0 14px;
                font-size:14px;
                line-height:1.6;
                color:#334155;
            ">
                Esta clasificación fue generada automáticamente y la
                entidad puede ajustarla según tu caso.
            </p>

            <p style="
                margin:0 0 14px;
                font-size:14px;
                line-height:1.6;
                color:#334155;
            ">
                Si no recibes respuesta en el plazo, o no estás de
                acuerdo con ella, puedes presentar una PQR ante la
                Superintendencia Nacional de Salud.
            </p>

            <div style="
                background:#fff7ed;
                border-left:4px solid #ea580c;
                border-radius:6px;
                padding:14px 16px;
            ">

                <div style="
                    font-size:13px;
                    font-weight:600;
                    color:#c2410c;
                    margin-bottom:6px;
                ">
                    Importante
                </div>

                <p style="
                    margin:0;
                    font-size:13px;
                    line-height:1.6;
                    color:#9a3412;
                ">
                    Si se trata de una emergencia médica, no esperes
                    este trámite: acude de inmediato a urgencias o
                    llama al 123.
                </p>

            </div>

        </td>
    </tr>

    <!-- PIE DEL CORREO -->
    <tr>
        <td style="
            padding:20px 32px;
            background:#f8fafc;
            border-top:1px solid #e2e8f0;
            font-size:12px;
            line-height:1.6;
            color:#94a3b8;
        ">

            Este es un mensaje automático, por favor no respondas
            a este correo.

            <br>

            Conserva tu número de radicado para cualquier consulta posterior.

        </td>
    </tr>

</table>

</td>
</tr>

</table>

</body>
</html>"""


# ============================================================
# ENVIAR COMPROBANTE DE RADICACIÓN
# ============================================================

def enviar_comprobante(correo, radicado, fecha, entidad, tipo, urgencia):

    # Calcular clasificación y plazo legal
    pl = plazo_legal(tipo, urgencia, fecha)

    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("[correo] Faltan GMAIL_USER / GMAIL_APP_PASSWORD.")
        return False

    if not correo:
        print("[correo] No se proporcionó un correo destinatario.")
        return False

    # Crear mensaje
    msg = EmailMessage()

    msg["Subject"] = f"Comprobante de radicación {radicado}"
    msg["From"] = GMAIL_USER
    msg["To"] = correo

    # Versión de texto plano como alternativa
    msg.set_content(
        f"Tu PQRS fue radicada correctamente.\n\n"

        f"Radicado: {radicado}\n"
        f"Fecha de radicación: {fecha:%d/%m/%Y %H:%M}\n"
        f"Entidad: {entidad}\n\n"

        f"CLASIFICACIÓN Y PLAZO\n"

        f"De acuerdo con la normatividad vigente ({pl['norma']}), "
        f"tu solicitud se clasifica de forma preliminar como: "
        f"{pl['clasificacion']}.\n"

        f"La entidad tiene un plazo máximo de {pl['plazo']} "
        f"para darte una respuesta de fondo, es decir, hasta el "
        f"{pl['limite']:%d/%m/%Y %H:%M}.\n\n"

        f"Esta clasificación fue generada automáticamente y la "
        f"entidad puede ajustarla según tu caso.\n\n"

        f"Si no recibes respuesta en el plazo, o no estás de "
        f"acuerdo con ella, puedes presentar una PQR ante la "
        f"Superintendencia Nacional de Salud.\n\n"

        f"Si se trata de una emergencia médica, no esperes este "
        f"trámite: acude de inmediato a urgencias o llama al 123.\n\n"

        f"Conserva tu número de radicado para cualquier consulta posterior."
    )

    # Versión HTML profesional
    msg.add_alternative(
        generar_html(radicado, fecha, entidad, pl),
        subtype="html"
    )

    try:
        contexto = ssl.create_default_context()

        with smtplib.SMTP_SSL(
            SMTP_HOST,
            SMTP_PORT,
            context=contexto,
            timeout=15
        ) as servidor:

            servidor.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            servidor.send_message(msg)

        print(f"[correo] Comprobante enviado correctamente a {correo}")
        return True

    except Exception as e:
        print(f"[correo] Error enviando correo a {correo}: {e}")
        return False
