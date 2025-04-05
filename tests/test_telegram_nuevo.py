"""
Script simple para probar las notificaciones de Telegram
"""
import asyncio
import logging
import os
import sys

# Agregar el directorio raíz al path para poder importar los módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.telegram_client import TelegramClient
from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def enviar_notificaciones_prueba():
    """Enviar notificaciones de prueba a Telegram"""
    print("=" * 80)
    print("  PRUEBA DE NOTIFICACIONES DE TELEGRAM")
    print("=" * 80)
    
    # Inicializar cliente de Telegram
    telegram_client = TelegramClient(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Datos de un partido de ejemplo
    home_team = "Cruz Azul"
    away_team = "América"
    jornada = "10"
    estadio = "Estadio Azteca"
    
    # 1. Notificación de partido próximo a comenzar
    mensaje_proximo = f"""
🔜 *PARTIDO PRÓXIMO A COMENZAR*
⚽ *{home_team} vs {away_team}*
🏆 Liga MX - Jornada {jornada}
🏟️ {estadio}
⏰ Comienza en 1 hora
"""
    await telegram_client.send_message(mensaje_proximo)
    await asyncio.sleep(2)
    
    # 2. Notificación de inicio del partido
    mensaje_inicio = f"""
🎮 *INICIA EL PARTIDO*
⚽ *{home_team} vs {away_team}*
🏆 Liga MX - Jornada {jornada}
🏟️ {estadio}
⏰ ¡El partido ha comenzado!
"""
    await telegram_client.send_message(mensaje_inicio)
    await asyncio.sleep(2)
    
    # 3. Notificación de gol (equipo local)
    mensaje_gol_local = f"""
⚽ *¡GOOOOOOL!*
*{home_team}* 1-0 {away_team}
⏱️ 23'
👤 Goleador: Carlos Rodríguez
🅰️ Asistencia: Uriel Antuna
"""
    await telegram_client.send_message(mensaje_gol_local)
    await asyncio.sleep(2)
    
    # 4. Notificación de tarjeta amarilla
    mensaje_amarilla = f"""
🟨 *TARJETA AMARILLA*
*{away_team}*
⏱️ 35'
👤 Jugador: Richard Sánchez
📝 Motivo: Falta táctica
"""
    await telegram_client.send_message(mensaje_amarilla)
    await asyncio.sleep(2)
    
    # 5. Notificación de sustitución
    mensaje_sustitucion = f"""
🔄 *SUSTITUCIÓN*
*{home_team}*
⏱️ 41'
➡️ Entra: Ignacio Rivero
⬅️ Sale: Carlos Rodríguez (Lesionado)
"""
    await telegram_client.send_message(mensaje_sustitucion)
    await asyncio.sleep(2)
    
    # 6. Notificación de medio tiempo
    mensaje_medio_tiempo = f"""
⏱️ *MEDIO TIEMPO*
*{home_team}* 1-0 *{away_team}*

📊 *Estadísticas:*
👟 Posesión: 55% - 45%
🎯 Tiros a gol: 4 - 2
🚩 Tiros de esquina: 3 - 1
🟨 Tarjetas amarillas: 0 - 1
"""
    await telegram_client.send_message(mensaje_medio_tiempo)
    await asyncio.sleep(2)
    
    # 7. Notificación de gol (equipo visitante)
    mensaje_gol_visitante = f"""
⚽ *¡GOOOOOOL!*
{home_team} 1-1 *{away_team}*
⏱️ 67'
👤 Goleador: Henry Martín
🅰️ Asistencia: Álvaro Fidalgo
"""
    await telegram_client.send_message(mensaje_gol_visitante)
    await asyncio.sleep(2)
    
    # 8. Notificación de gol (equipo local)
    mensaje_gol_local_2 = f"""
⚽ *¡GOOOOOOL!*
*{home_team}* 2-1 {away_team}
⏱️ 82'
👤 Goleador: Uriel Antuna
🅰️ Asistencia: Ángel Sepúlveda
"""
    await telegram_client.send_message(mensaje_gol_local_2)
    await asyncio.sleep(2)
    
    # 9. Notificación de final del partido
    mensaje_final = f"""
🏁 *FINAL DEL PARTIDO*
*{home_team}* 2-1 *{away_team}*
🏆 Liga MX - Jornada {jornada}

⚽ *Goles:*
• 23' Carlos Rodríguez ({home_team})
• 67' Henry Martín ({away_team})
• 82' Uriel Antuna ({home_team})

📊 *Estadísticas finales:*
👟 Posesión: 52% - 48%
🎯 Tiros a gol: 7 - 5
🚩 Tiros de esquina: 5 - 3
🟨 Tarjetas amarillas: 1 - 2
🔄 Sustituciones: 3 - 3

✅ {home_team} se lleva la victoria en un partido muy disputado.
"""
    await telegram_client.send_message(mensaje_final)
    
    print("=" * 80)
    print("  PRUEBA DE NOTIFICACIONES COMPLETADA")
    print("=" * 80)

async def main():
    """Función principal"""
    await enviar_notificaciones_prueba()

if __name__ == "__main__":
    asyncio.run(main())
