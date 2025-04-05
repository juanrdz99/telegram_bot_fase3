"""
Script para probar el procesamiento de datos locales
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
from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directorio para los datos de ejemplo
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "ejemplos")

def cargar_datos_locales():
    """
    Carga los datos locales de un partido de ejemplo
    
    Returns:
        Tupla con detalles, eventos y estadísticas del partido
    """
    match_details = {}
    events = []
    statistics = {}
    
    # Cargar detalles del partido
    try:
        with open(os.path.join(DATA_DIR, "match_details.json"), "r", encoding="utf-8") as f:
            match_details = json.load(f)
        logger.info("Detalles del partido cargados correctamente")
    except Exception as e:
        logger.error(f"Error al cargar detalles del partido: {e}")
    
    # Cargar eventos del partido
    try:
        with open(os.path.join(DATA_DIR, "match_events.json"), "r", encoding="utf-8") as f:
            events = json.load(f)
        logger.info("Eventos del partido cargados correctamente")
    except Exception as e:
        logger.error(f"Error al cargar eventos del partido: {e}")
    
    # Cargar estadísticas del partido
    try:
        with open(os.path.join(DATA_DIR, "match_statistics.json"), "r", encoding="utf-8") as f:
            statistics = json.load(f)
        logger.info(f"Estadísticas del partido cargadas correctamente")
    except Exception as e:
        logger.error(f"Error al cargar estadísticas del partido: {e}")
    
    return match_details, events, statistics

async def simular_notificaciones(match_details, events, statistics):
    """
    Simula las notificaciones de un partido con datos locales
    
    Args:
        match_details: Detalles del partido
        events: Eventos del partido
        statistics: Estadísticas del partido
    """
    # Verificar si tenemos datos válidos
    if not match_details:
        logger.error("No hay detalles del partido para simular notificaciones")
        return
    
    # Inicializar cliente de Telegram
    telegram_client = TelegramClient(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Formatear mensajes
    formatter = MatchFormatter()
    
    print("=" * 80)
    print("  SIMULACIÓN DE NOTIFICACIONES CON DATOS LOCALES")
    print("=" * 80)
    
    # 1. Notificación de partido próximo a comenzar
    print("\n1. Enviando notificación de partido próximo a comenzar...")
    match_data = {
        "home_name": match_details.get("home_name", "Equipo Local"),
        "away_name": match_details.get("away_name", "Equipo Visitante"),
        "date": match_details.get("date", ""),
        "time": match_details.get("time", ""),
        "location": match_details.get("venue", {}).get("name", "Estadio no disponible"),
        "competition": match_details.get("competition", {}),
        "round": match_details.get("round", "")
    }
    mensaje_previo = formatter.format_match_notification(match_data)
    await telegram_client.send_message(mensaje_previo)
    
    # Pequeña pausa entre mensajes
    await asyncio.sleep(2)
    
    # 2. Notificación de inicio de partido
    print("\n2. Enviando notificación de inicio de partido...")
    mensaje_inicio = formatter.format_match_start(match_details)
    await telegram_client.send_message(mensaje_inicio)
    
    # Pequeña pausa entre mensajes
    await asyncio.sleep(2)
    
    # 3. Notificaciones de eventos (goles, tarjetas, sustituciones)
    print("\n3. Enviando notificaciones de eventos del primer tiempo...")
    
    # Ordenar eventos por minuto
    sorted_events = sorted(events, key=lambda x: int(x.get("minute", "0").split("+")[0]) if x.get("minute") else 0)
    
    # Separar eventos del primer y segundo tiempo
    primer_tiempo_events = []
    segundo_tiempo_events = []
    
    for event in sorted_events:
        minute = event.get("minute", "")
        if not minute:
            continue
            
        # Convertir a entero para comparación
        try:
            minute_num = int(minute.split("+")[0])
            if minute_num <= 45:
                primer_tiempo_events.append(event)
            else:
                segundo_tiempo_events.append(event)
        except ValueError:
            # Si no podemos convertir a entero, asumimos primer tiempo
            primer_tiempo_events.append(event)
    
    # Procesar eventos del primer tiempo
    for event in primer_tiempo_events:
        event_type = event.get("type", "").lower()
        minute = event.get("minute", "")
        
        # Pequeña pausa entre mensajes
        await asyncio.sleep(2)
        
        if "goal" in event_type:
            print(f"  - Enviando notificación de gol en el minuto {minute}...")
            mensaje = formatter.format_goal_notification(match_details, event)
            await telegram_client.send_message(mensaje)
        elif "card" in event_type:
            print(f"  - Enviando notificación de tarjeta en el minuto {minute}...")
            mensaje = formatter.format_card_notification(match_details, event)
            await telegram_client.send_message(mensaje)
        elif "subst" in event_type:
            print(f"  - Enviando notificación de sustitución en el minuto {minute}...")
            mensaje = formatter.format_substitution_notification(match_details, event)
            await telegram_client.send_message(mensaje)
    
    # 4. Notificación de medio tiempo (después de los eventos del primer tiempo)
    print("\n4. Enviando notificación de medio tiempo...")
    mensaje_medio_tiempo = formatter.format_halftime_notification(match_details, statistics)
    await telegram_client.send_message(mensaje_medio_tiempo)
    
    # Pequeña pausa entre mensajes
    await asyncio.sleep(2)
    
    # 5. Notificaciones de eventos del segundo tiempo
    print("\n5. Enviando notificaciones de eventos del segundo tiempo...")
    
    # Procesar eventos del segundo tiempo
    for event in segundo_tiempo_events:
        event_type = event.get("type", "").lower()
        minute = event.get("minute", "")
        
        # Pequeña pausa entre mensajes
        await asyncio.sleep(2)
        
        if "goal" in event_type:
            print(f"  - Enviando notificación de gol en el minuto {minute}...")
            mensaje = formatter.format_goal_notification(match_details, event)
            await telegram_client.send_message(mensaje)
        elif "card" in event_type:
            print(f"  - Enviando notificación de tarjeta en el minuto {minute}...")
            mensaje = formatter.format_card_notification(match_details, event)
            await telegram_client.send_message(mensaje)
        elif "subst" in event_type:
            print(f"  - Enviando notificación de sustitución en el minuto {minute}...")
            mensaje = formatter.format_substitution_notification(match_details, event)
            await telegram_client.send_message(mensaje)
    
    # 6. Notificación de final del partido
    print("\n6. Enviando notificación de final del partido...")
    mensaje_final = formatter.format_fulltime_notification(match_details, events, statistics)
    await telegram_client.send_message(mensaje_final)
    
    print("\n" + "=" * 80)
    print("  SIMULACIÓN DE NOTIFICACIONES COMPLETADA")
    print("=" * 80)

async def main():
    """Función principal"""
    try:
        # Cargar datos locales
        logger.info("Cargando datos locales del partido...")
        match_details, events, statistics = cargar_datos_locales()
        
        # Simular notificaciones
        if match_details:
            await simular_notificaciones(match_details, events, statistics)
        else:
            logger.error("No se pudieron cargar los datos del partido para simular notificaciones")
        
    except Exception as e:
        logger.error(f"Error en la simulación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
