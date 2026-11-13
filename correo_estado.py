
"""Notificación por correo cuando cambia el estado de una PQRS.

Utiliza las mismas credenciales de Gmail definidas en el archivo .env:

    GMAIL_USER
    GMAIL_APP_PASSWORD
"""

from __future__ import annotations

import html
import os
import smtplib
import ssl

from email.message import EmailMessage
from email.utils import formataddr
from dotenv import load_dotenv


# ============================================================
# CONFIGURACIÓN DE GMAIL
# ============================================================

# Cargar las variables del archivo .env
load_dotenv()

# Credenciales de Gmail
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# Configuración SMTP de Gmail
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

REMITENTE = GMAIL_USER
NOMBRE_REMITENTE = "Atención al Usuario · PQRS Salud"


# ============================================================
# ETIQUETAS DE LOS ESTADOS
# ============================================================

ETIQUETAS = {
    "radicada": "Radicada",
    "en_revision": "En revisión",
    "respondida": "Respondida",
    "cerrada": "Cerrada",
}


# ============================================================
# COLORES DE LOS ESTADOS
# ============================================================

COLORES = {
    "radicada": "#475569",
    "en_revision": "#d97706",
    "respondida": "#0284c7",
    "cerrada": "#059669",
}


# ============================================================
# EXPLICACIÓN DE LOS ESTADOS
# ============================================================

EXPLICACION = {
    "radicada": (
        "Tu solicitud fue recibida y está en cola para ser atendida."
    ),
    "en_revision": (
        "Nuestro equipo está revisando tu solicitud en este momento."
    ),
    "respondida": (
        "Tu solicitud ya tiene una respuesta. Si no la has recibido, "
        "revisa tu bandeja de entrada y la carpeta de spam."
    ),
    "cerrada": (
        "Tu solicitud fue cerrada. Si consideras que no se resolvió, "
        "puedes radicar una nueva PQRS haciendo referencia a este radicado."
    ),
}


# ============================================================
# GENERAR CORREO HTML
# ============================================================

def _html(nombre, radicado, entidad, anterior, nuevo, nota) -> str:

    e = html.escape
    color = COLORES.get(nuevo, "#4f46e5")

    saludo = f"Hola, {e(nombre)}" if nombre else "Hola"

    bloque_nota = ""

    if nota:
        bloque_nota = f"""
        <tr>
            <td style="padding:0 32px 24px">
                <div style="
                    background:#f8fafc;
                    border-left:4px solid {color};
                    border-radius:6px;
                    padding:14px 16px
                ">
                    <div style="
                        font-size:12px;
                        letter-spacing:.06em;
                        text-transform:uppercase;
                        color:#64748b;
                        margin-bottom:6px
                    ">
                        Mensaje del equipo
                    </div>

                    <div style="
                        font-size:15px;
                        line-height:1.55;
                        color:#0f172a;
                        white-space:pre-wrap
                    ">
                        {e(nota)}
                    </div>
                </div>
            </td>
        </tr>
        """

    return f"""<!doctype html>
<html lang="es">
<body style="
    margin:0;
    background:#f1f5f9;
    font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif
">

<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
style="background:#f1f5f9;padding:32px 12px">

<tr>
<td align="center">

<table role="presentation" width="600" cellpadding="0" cellspacing="0"
style="
    max-width:600px;
    width:100%;
    background:#ffffff;
    border-radius:14px;
    overflow:hidden;
    border:1px solid #e2e8f0
">

    <tr>
        <td style="
            background:linear-gradient(135deg,#4f46e5,#7c3aed);
            padding:28px 32px;
            color:#ffffff
        ">
            <div style="
                font-size:13px;
                letter-spacing:.08em;
                text-transform:uppercase;
                opacity:.85
            ">
                PQRS en salud
            </div>

            <div style="
                font-size:24px;
                font-weight:600;
                margin-top:6px
            ">
                Actualización de tu solicitud
            </div>
        </td>
    </tr>

    <tr>
        <td style="padding:28px 32px 8px">

            <p style="
                margin:0 0 12px;
                font-size:16px;
                color:#0f172a
            ">
                {saludo},
            </p>

            <p style="
                margin:0;
                font-size:15px;
                line-height:1.6;
                color:#334155
            ">
                El estado de tu PQRS cambió. Este es el resumen:
            </p>

        </td>
    </tr>

    <tr>
        <td style="padding:20px 32px">

            <table role="presentation" width="100%" cellpadding="0"
            cellspacing="0" style="
                border:1px solid #e2e8f0;
                border-radius:10px
            ">

                <tr>
                    <td style="
                        padding:14px 16px;
                        font-size:13px;
                        color:#64748b;
                        width:38%
                    ">
                        Radicado
                    </td>

                    <td style="
                        padding:14px 16px;
                        font-size:15px;
                        font-weight:600;
                        color:#0f172a
                    ">
                        {e(str(radicado or "-"))}
                    </td>
                </tr>

                <tr>
                    <td style="
                        padding:14px 16px;
                        font-size:13px;
                        color:#64748b;
                        border-top:1px solid #e2e8f0
                    ">
                        Entidad
                    </td>

                    <td style="
                        padding:14px 16px;
                        font-size:15px;
                        color:#0f172a;
                        border-top:1px solid #e2e8f0
                    ">
                        {e(str(entidad or "-"))}
                    </td>
                </tr>

                <tr>
                    <td style="
                        padding:14px 16px;
                        font-size:13px;
                        color:#64748b;
                        border-top:1px solid #e2e8f0
                    ">
                        Estado anterior
                    </td>

                    <td style="
                        padding:14px 16px;
                        font-size:15px;
                        color:#64748b;
                        border-top:1px solid #e2e8f0
                    ">
                        {e(ETIQUETAS.get(anterior, anterior or "-"))}
                    </td>
                </tr>

                <tr>
                    <td style="
                        padding:14px 16px;
                        font-size:13px;
                        color:#64748b;
                        border-top:1px solid #e2e8f0
                    ">
                        Estado actual
                    </td>

                    <td style="
                        padding:14px 16px;
                        border-top:1px solid #e2e8f0
                    ">
                        <span style="
                            display:inline-block;
                            background:{color};
                            color:#ffffff;
                            font-size:13px;
                            font-weight:600;
                            padding:5px 14px;
                            border-radius:999px
                        ">
                            {e(ETIQUETAS.get(nuevo, nuevo))}
                        </span>
                    </td>
                </tr>

            </table>
        </td>
    </tr>

    <tr>
        <td style="padding:0 32px 24px">
            <p style="
                margin:0;
                font-size:15px;
                line-height:1.6;
                color:#334155
            ">
                {e(EXPLICACION.get(nuevo, ""))}
            </p>
        </td>
    </tr>

    {bloque_nota}

    <tr>
        <td style="
            padding:20px 32px;
            background:#f8fafc;
            border-top:1px solid #e2e8f0;
            font-size:12px;
            line-height:1.6;
            color:#94a3b8
        ">
            Este es un mensaje automático, por favor no respondas a este correo.
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
# GENERAR CORREO DE TEXTO PLANO
# ============================================================

def _texto(nombre, radicado, entidad, anterior, nuevo, nota) -> str:

    partes = [
        f"Hola{', ' + nombre if nombre else ''}.",
        "",
        "El estado de tu PQRS cambió.",
        f"Radicado: {radicado or '-'}",
        f"Entidad: {entidad or '-'}",
        f"Estado anterior: {ETIQUETAS.get(anterior, anterior or '-')}",
        f"Estado actual: {ETIQUETAS.get(nuevo, nuevo)}",
        "",
        EXPLICACION.get(nuevo, ""),
    ]

    if nota:
        partes += [
            "",
            "Mensaje del equipo:",
            nota
        ]

    partes += [
        "",
        "Mensaje automático, por favor no respondas a este correo."
    ]

    return "\n".join(partes)


# ============================================================
# ENVIAR NOTIFICACIÓN DE CAMBIO DE ESTADO
# ============================================================

def enviar_cambio_estado(
    destino,
    nombre,
    radicado,
    entidad,
    anterior,
    nuevo,
    nota=""
) -> bool:

    """Envía el correo de actualización de estado de una PQRS.

    Devuelve True si Gmail aceptó el mensaje.
    Devuelve False si ocurrió un error.
    """

    # Verificar credenciales
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print(
            "[correo_estado] Faltan GMAIL_USER / "
            "GMAIL_APP_PASSWORD. No se envió el correo."
        )
        return False

    # Verificar destinatario
    if not destino:
        print("[correo_estado] No se proporcionó un correo destinatario.")
        return False

    # Crear mensaje
    msg = EmailMessage()

    msg["Subject"] = (
        f"PQRS {radicado}: tu solicitud está "
        f"{ETIQUETAS.get(nuevo, nuevo).lower()}"
    )

    msg["From"] = formataddr((NOMBRE_REMITENTE, REMITENTE))
    msg["To"] = destino

    # Agregar versión de texto
    msg.set_content(
        _texto(nombre, radicado, entidad, anterior, nuevo, nota)
    )

    # Agregar versión HTML
    msg.add_alternative(
        _html(nombre, radicado, entidad, anterior, nuevo, nota),
        subtype="html"
    )

    try:
        contexto = ssl.create_default_context()

        # Conexión segura SSL con Gmail
        with smtplib.SMTP_SSL(
            SMTP_HOST,
            SMTP_PORT,
            context=contexto,
            timeout=15
        ) as servidor:

            servidor.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            servidor.send_message(msg)

        print(
            f"[correo_estado] Notificación enviada correctamente a {destino}"
        )

        return True

    except Exception as exc:

        print(
            f"[correo_estado] Error enviando a {destino}: {exc}"
        )

        return False
