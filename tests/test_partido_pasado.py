"""
Script para probar notificaciones con datos de un partido pasado de Liga MX
"""
import asyncio
import logging
import os
import sys
import json

# Agregar el directorio raíz al path para poder importar los módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.telegram_client import TelegramClient
from core.formatter import MatchFormatter
from core.livescore_client import LiveScoreClient
from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, LIVESCORE_API_KEY, LIVESCORE_API_SECRET

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ID de un partido pasado de Liga MX (ejemplo)
MATCH_ID = "1073746"  # Reemplazar con un ID válido de un partido pasado

# Directorio para guardar datos
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

def obtener_y_guardar_datos(client, match_id):
    """
    Obtiene y guarda los datos de un partido pasado
    """
    logger.info(f"Obteniendo datos del partido {match_id}...")
    
    # Obtener detalles del partido
    try:
        match_details = client.get_match_details(match_id)
        with open(os.path.join(DATA_DIR, f"match_details_{match_id}.json"), "w", encoding="utf-8") as f:
            json.dump(match_details, f, ensure_ascii=False, indent=2)
        logger.info(f"Detalles del partido guardados en match_details_{match_id}.json")
    except Exception as e:
        logger.error(f"Error al obtener detalles del partido: {e}")
        match_details = {}
    
    # Obtener eventos del partido
    try:
        events = client.get_match_events(match_id)
        with open(os.path.join(DATA_DIR, f"match_events_{match_id}.json"), "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        logger.info(f"Eventos del partido guardados en match_events_{match_id}.json")
    except Exception as e:
        logger.error(f"Error al obtener eventos del partido: {e}")
        events = []
    
    # Obtener estadísticas del partido
    try:
        statistics = client.get_match_statistics(match_id)
        with open(os.path.join(DATA_DIR, f"match_statistics_{match_id}.json"), "w", encoding="utf-8") as f:
            json.dump(statistics, f, ensure_ascii=False, indent=2)
        logger.info(f"Estadísticas del partido guardadas en match_statistics_{match_id}.json")
    except Exception as e:
        logger.error(f"Error al obtener estadísticas del partido: {e}")
        statistics = {}
    
    return match_details, events, statistics

async def simular_notificaciones(match_details, events, statistics):
    """
    Simula las notificaciones de un partido pasado
    """
    # Inicializar cliente de Telegram
    telegram_client = TelegramClient(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Formatear mensajes
    formatter = MatchFormatter()
    
    print("=" * 80)
    print("  SIMULACIÓN DE NOTIFICACIONES DE UN PARTIDO PASADO")
    print("=" * 80)
    
    # 1. Notificación de partido próximo a comenzar (simulado)
    print("\n1. Enviando notificación de partido próximo a comenzar...")
    # Crear un mensaje simple para la notificación previa al partido
    home_team = match_details.get("home_name", "Equipo Local")
    away_team = match_details.get("away_name", "Equipo Visitante")
    competition = match_details.get("competition", {}).get("name", "Liga MX")
    round_info = match_details.get("round", {}).get("name", "")
    stadium = match_details.get("venue", {}).get("name", "Estadio no disponible")
    
    mensaje_previo = f"""
🔜 *PARTIDO PRÓXIMO A COMENZAR*
⚽ *{home_team} vs {away_team}*
🏆 {competition} - {round_info}
🏟️ {stadium}
⏰ Comienza en 1 hora
"""
    await telegram_client.send_message(mensaje_previo)
    
    # Pequeña pausa entre mensajes
    await asyncio.sleep(1)
    
    # 2. Notificación de inicio de partido
    print("\n2. Enviando notificación de inicio de partido...")
    mensaje_inicio = f"""
🎮 *INICIA EL PARTIDO*
⚽ *{home_team} vs {away_team}*
🏆 {competition} - {round_info}
🏟️ {stadium}
⏰ ¡El partido ha comenzado!
"""
    await telegram_client.send_message(mensaje_inicio)
    await asyncio.sleep(1)
    
    # 3. Notificación de actualización del partido (medio tiempo)
    print("\n3. Enviando notificación de medio tiempo...")
    # Filtrar eventos hasta el medio tiempo
    eventos_primer_tiempo = [e for e in events if int(e.get("minute", "0").replace("+", "")) <= 45]
    mensaje_medio_tiempo = formatter.format_match_update(match_details, eventos_primer_tiempo, statistics)
    await telegram_client.send_message(mensaje_medio_tiempo)
    await asyncio.sleep(1)
    
    # 4. Notificación de final del partido
    print("\n4. Enviando notificación de final del partido...")
    mensaje_final = formatter.format_match_update(match_details, events, statistics)
    await telegram_client.send_message(mensaje_final)
    
    print("\n" + "=" * 80)
    print("  SIMULACIÓN DE NOTIFICACIONES COMPLETADA")
    print("=" * 80)

def cargar_datos_guardados(match_id):
    """
    Carga los datos guardados de un partido pasado
    """
    match_details = {}
    events = []
    statistics = {}
    
    # Cargar detalles del partido
    try:
        with open(os.path.join(DATA_DIR, f"match_details_{match_id}.json"), "r", encoding="utf-8") as f:
            match_details = json.load(f)
        logger.info(f"Detalles del partido cargados de match_details_{match_id}.json")
    except Exception as e:
        logger.error(f"Error al cargar detalles del partido: {e}")
    
    # Cargar eventos del partido
    try:
        with open(os.path.join(DATA_DIR, f"match_events_{match_id}.json"), "r", encoding="utf-8") as f:
            events = json.load(f)
        logger.info(f"Eventos del partido cargados de match_events_{match_id}.json")
    except Exception as e:
        logger.error(f"Error al cargar eventos del partido: {e}")
    
    # Cargar estadísticas del partido
    try:
        with open(os.path.join(DATA_DIR, f"match_statistics_{match_id}.json"), "r", encoding="utf-8") as f:
            statistics = json.load(f)
        logger.info(f"Estadísticas del partido cargadas de match_statistics_{match_id}.json")
    except Exception as e:
        logger.error(f"Error al cargar estadísticas del partido: {e}")
    
    return match_details, events, statistics

async def main():
    """Función principal"""
    try:
        # Inicializar cliente de LiveScore
        livescore_client = LiveScoreClient(LIVESCORE_API_KEY, LIVESCORE_API_SECRET)
        
        # Verificar si ya tenemos los datos guardados
        match_details_path = os.path.join(DATA_DIR, f"match_details_{MATCH_ID}.json")
        
        if os.path.exists(match_details_path):
            # Cargar datos guardados
            logger.info("Usando datos guardados del partido...")
            match_details, events, statistics = cargar_datos_guardados(MATCH_ID)
        else:
            # Obtener y guardar datos
            logger.info("Obteniendo datos nuevos del partido...")
            match_details, events, statistics = obtener_y_guardar_datos(livescore_client, MATCH_ID)
        
        # Simular notificaciones
        await simular_notificaciones(match_details, events, statistics)
        
    except Exception as e:
        logger.error(f"Error en la simulación: {e}")

if __name__ == "__main__":
    asyncio.run(main())
