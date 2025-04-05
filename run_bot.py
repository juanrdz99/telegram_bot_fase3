#!/usr/bin/env python
"""
Script unificado para ejecutar el bot de Liga MX
Este script sirve como punto de entrada único para todas las funcionalidades del bot.

Uso:
  python run_bot.py --standings     # Enviar tabla de posiciones
  python run_bot.py --scorers       # Enviar goleadores
  python run_bot.py --upcoming      # Enviar próximos partidos
  python run_bot.py --notifications # Iniciar notificaciones en tiempo real
"""
import os
import sys
import asyncio
import argparse
from datetime import datetime, timedelta
from pytz import timezone

# Configurar el path para importar los módulos correctamente
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar las clases necesarias
from core.main import LigaMXBot
from core.livescore_client import LiveScoreClient
from core.telegram_client import TelegramClient
from core.formatter import MatchFormatter
from core.config import LIGA_MX_COMPETITION_ID

# Definir zona horaria de México
MEXICO_TZ = timezone('America/Mexico_City')

async def send_standings():
    """Enviar tabla de posiciones actual"""
    print("Enviando tabla de posiciones...")
    bot = LigaMXBot()
    await bot.send_standings()
    print("Tabla de posiciones enviada!")

async def send_top_scorers():
    """Enviar goleadores actuales"""
    print("Enviando goleadores...")
    bot = LigaMXBot()
    await bot.send_top_scorers()
    print("Goleadores enviados!")

async def send_upcoming_matches():
    """Enviar notificación de los próximos partidos"""
    print("Enviando próximos partidos de Liga MX...")
    
    # Inicializar clientes
    livescore_client = LiveScoreClient()
    telegram_client = TelegramClient()
    
    try:
        # Obtener fecha actual en zona horaria de México
        now = datetime.now(MEXICO_TZ)
        
        # Obtener próximos partidos (próximos 3 días)
        params = {
            "competition_id": LIGA_MX_COMPETITION_ID,
            "from": now.strftime("%Y-%m-%d"),
            "to": (now + timedelta(days=3)).strftime("%Y-%m-%d")
        }
        
        fixtures = livescore_client.get_fixtures(params)
        
        if not fixtures:
            message = "⚠️ No hay partidos programados para los próximos días."
            print("No se encontraron próximos partidos")
        else:
            # Formatear el mensaje con los próximos partidos
            message = format_upcoming_matches(fixtures)
            print(f"Se encontraron {len(fixtures)} próximos partidos")
        
        # Enviar mensaje a Telegram
        await telegram_client.send_message(message)
        print("Próximos partidos enviados!")
        
    except Exception as e:
        print(f"Error al enviar próximos partidos: {e}")

def format_upcoming_matches(fixtures):
    """Formatear los próximos partidos en un mensaje para Telegram"""
    # Encabezado del mensaje
    header = "⚽ *PRÓXIMOS PARTIDOS LIGA MX - JORNADA 13*\n\n"
    
    # Formatear cada partido (limitado a los primeros 9)
    matches_text = ""
    for match in fixtures[:9]:  # Limitamos a los primeros 9 partidos
        # Obtener datos del partido
        home_team = match.get("home_name", "")
        away_team = match.get("away_name", "")
        date_str = match.get("date", "")
        time_str = match.get("time", "")
        
        # Convertir fecha y hora a formato más amigable
        try:
            # 1. Parseamos la fecha y hora base (sin tz)
            match_date = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            # 2. Localizamos en zona horaria de México
            if match_date.tzinfo is None:
                match_date_mx = MEXICO_TZ.localize(match_date)
            else:
                match_date_mx = match_date.astimezone(MEXICO_TZ)
            
            # 3. Restamos 6 horas
            match_date_mx_minus_6 = match_date_mx - timedelta(hours=6)
            
            # 4. Formateamos para mostrar en el mensaje
            formatted_date = match_date_mx_minus_6.strftime("%d/%m/%Y %H:%M")
            
        except ValueError:
            # Si por alguna razón no podemos parsear la fecha, la mostramos como venga
            formatted_date = f"{date_str} {time_str}"
        
        # Agregar partido al mensaje
        matches_text += f"🏟️ *{home_team}* vs *{away_team}*\n"
        matches_text += f"📅 {formatted_date} hrs (CDMX)\n\n"
    
    # Agregar información sobre el total de partidos si hay más de 9
    if len(fixtures) > 9:
        matches_text += f"_...y {len(fixtures) - 9} partidos más_\n"
    
    # Pie de mensaje
    footer = "\n📲 Recibirás notificaciones en vivo durante estos partidos."
    
    # Combinar todas las partes
    return header + matches_text + footer

def start_notifications():
    """Iniciar sistema de notificaciones en tiempo real"""
    print("Iniciando sistema de notificaciones en tiempo real...")
    # Cambiamos al directorio correcto y ejecutamos el script de notificaciones
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              "scripts", "iniciar_notificaciones_mejoradas.py")
    os.system(f"python {script_path}")

async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Liga MX Telegram Bot")
    parser.add_argument("--standings", action="store_true", help="Enviar tabla de posiciones actual")
    parser.add_argument("--scorers", action="store_true", help="Enviar goleadores actuales")
    parser.add_argument("--upcoming", action="store_true", help="Enviar próximos partidos")
    parser.add_argument("--notifications", action="store_true", help="Iniciar notificaciones en tiempo real")
    args = parser.parse_args()
    
    if args.standings:
        await send_standings()
    elif args.scorers:
        await send_top_scorers()
    elif args.upcoming:
        await send_upcoming_matches()
    elif args.notifications:
        start_notifications()
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrograma detenido por el usuario")
    sys.exit(0)
