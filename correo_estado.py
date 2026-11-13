"""Notificación por correo cuando cambia el estado de una PQRS.

Configura el servidor SMTP con variables de entorno (usa las mismas credenciales
que ya tienes en correo.py):

    SMTP_HOST   (por defecto smtp.gmail.com)
    SMTP_PORT   (por defecto 587; con 465 se usa SSL directo)
    SMTP_USER   usuario / correo remitente
    SMTP_PASS   contraseña o "contraseña de aplicación"
    SMTP_FROM   (opcional) remitente; por defecto SMTP_USER
"""
from __future__ import annotations

import html
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
REMITENTE = os.environ.get("SMTP_FROM", SMTP_USER)
NOMBRE_REMITENTE = "Atención al Usuario · PQRS Salud"

ETIQUETAS = {
    "radicada": "Radicada",
    "en_revision": "En revisión",
    "respondida": "Respondida",
    "cerrada": "Cerrada",
}
COLORES = {
    "radicada": "#475569",
    "en_revision": "#d97706",
    "respondida": "#0284c7",
    "cerrada": "#059669",
}
EXPLICACION = {
    "radicada": "Tu solicitud fue recibida y está en cola para ser atendida.",
    "en_revision": "Nuestro equipo está revisando tu solicitud en este momento.",
    "respondida": "Tu solicitud ya tiene una respuesta. Si no la has recibido, revisa tu bandeja de entrada y la carpeta de spam.",
    "cerrada": "Tu solicitud fue cerrada. Si consideras que no se resolvió, puedes radicar una nueva PQRS haciendo referencia a este radicado.",
}


def _html(nombre, radicado, entidad, anterior, nuevo, nota) -> str:
    e = html.escape
    color = COLORES.get(nuevo, "#4f46e5")
    saludo = f"Hola, {e(nombre)}" if nombre else "Hola"
    bloque_nota = ""
    if nota:
        bloque_nota = f"""
        <tr><td style="padding:0 32px 24px">
          <div style="background:#f8fafc;border-left:4px solid {color};border-radius:6px;padding:14px 16px">
            <div style="font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#64748b;margin-bottom:6px">Mensaje del equipo</div>
            <div style="font-size:15px;line-height:1.55;color:#0f172a;white-space:pre-wrap">{e(nota)}</div>
          </div>
        </td></tr>"""
    return f"""<!doctype html>
<html lang="es"><body style="margin:0;background:#f1f5f9;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:32px 12px">
<tr><td align="center">
  <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e2e8f0">
    <tr><td style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:28px 32px;color:#ffffff">
      <div style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;opacity:.85">PQRS en salud</div>
      <div style="font-size:24px;font-weight:600;margin-top:6px">Actualización de tu solicitud</div>
    </td></tr>
    <tr><td style="padding:28px 32px 8px">
      <p style="margin:0 0 12px;font-size:16px;color:#0f172a">{saludo},</p>
      <p style="margin:0;font-size:15px;line-height:1.6;color:#334155">El estado de tu PQRS cambió. Este es el resumen:</p>
    </td></tr>
    <tr><td style="padding:20px 32px">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:10px">
        <tr>
          <td style="padding:14px 16px;font-size:13px;color:#64748b;width:38%">Radicado</td>
          <td style="padding:14px 16px;font-size:15px;font-weight:600;color:#0f172a">{e(radicado or "-")}</td>
        </tr>
        <tr>
          <td style="padding:14px 16px;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0">Entidad</td>
          <td style="padding:14px 16px;font-size:15px;color:#0f172a;border-top:1px solid #e2e8f0">{e(entidad or "-")}</td>
        </tr>
        <tr>
          <td style="padding:14px 16px;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0">Estado anterior</td>
          <td style="padding:14px 16px;font-size:15px;color:#64748b;border-top:1px solid #e2e8f0">{e(ETIQUETAS.get(anterior, anterior or "-"))}</td>
        </tr>
        <tr>
          <td style="padding:14px 16px;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0">Estado actual</td>
          <td style="padding:14px 16px;border-top:1px solid #e2e8f0">
            <span style="display:inline-block;background:{color};color:#ffffff;font-size:13px;font-weight:600;padding:5px 14px;border-radius:999px">{e(ETIQUETAS.get(nuevo, nuevo))}</span>
          </td>
        </tr>
      </table>
    </td></tr>
    <tr><td style="padding:0 32px 24px">
      <p style="margin:0;font-size:15px;line-height:1.6;color:#334155">{e(EXPLICACION.get(nuevo, ""))}</p>
    </td></tr>
    {bloque_nota}
    <tr><td style="padding:20px 32px;background:#f8fafc;border-top:1px solid #e2e8f0;font-size:12px;line-height:1.6;color:#94a3b8">
      Este es un mensaje automático, por favor no respondas a este correo.<br>
      Conserva tu número de radicado para cualquier consulta posterior.
    </td></tr>
  </table>
</td></tr></table></body></html>"""


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
        partes += ["", "Mensaje del equipo:", nota]
    partes += ["", "Mensaje automático, por favor no respondas a este correo."]
    return "\n".join(partes)


def enviar_cambio_estado(destino, nombre, radicado, entidad, anterior, nuevo, nota="") -> bool:
    """Envía el correo. Devuelve True si el servidor SMTP lo aceptó, False si falló."""
    if not (SMTP_USER and SMTP_PASS):
        print("[correo_estado] Faltan SMTP_USER / SMTP_PASS: no se envió el correo.")
        return False
    msg = EmailMessage()
    msg["Subject"] = f"PQRS {radicado}: tu solicitud está {ETIQUETAS.get(nuevo, nuevo).lower()}"
    msg["From"] = formataddr((NOMBRE_REMITENTE, REMITENTE or SMTP_USER))
    msg["To"] = destino
    msg.set_content(_texto(nombre, radicado, entidad, anterior, nuevo, nota))
    msg.add_alternative(_html(nombre, radicado, entidad, anterior, nuevo, nota), subtype="html")
    try:
        ctx = ssl.create_default_context()
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=15) as s:
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
                s.starttls(context=ctx)
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
        return True
    except Exception as exc:  # no tumbar el panel por un fallo de correo
        print(f"[correo_estado] Error enviando a {destino}: {exc}")
        return False
