"""
Script unificado para enviar notificaciones de partidos de Liga MX
Permite notificar partidos de:
- Toda la semana
- Solo fin de semana (viernes a domingo)
- Jornada específica

python src/notificar_partidos.py --tipo semana   # Notifica partidos de toda la semana
python src/notificar_partidos.py --tipo finde    # Notifica partidos del fin de semana
python src/notificar_partidos.py --tipo jornada  # Notifica partidos de la jornada actual
"""
import asyncio
import logging
import datetime
import pytz
import argparse
from typing import List, Dict, Any, Tuple, Optional
import requests

from config import (
    LIVESCORE_API_KEY,
    LIVESCORE_API_SECRET,
    LIGA_MX_COMPETITION_ID
)
from telegram_client import TelegramClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Zona horaria de México (Ciudad de México)
MEXICO_TZ = pytz.timezone('America/Mexico_City')

def calcular_rango_semana() -> Tuple[datetime.date, datetime.date]:
    """Calcular el rango de la semana actual (lunes a domingo)"""
    hoy = datetime.datetime.now(MEXICO_TZ).date()
    
    # Determinar el día de la semana (0 = lunes, 6 = domingo)
    dia_semana = hoy.weekday()
    
    # Calcular el lunes de esta semana
    lunes = hoy - datetime.timedelta(days=dia_semana)
    
    # Calcular el domingo de esta semana
    domingo = lunes + datetime.timedelta(days=6)
    
    return lunes, domingo

def calcular_rango_fin_de_semana() -> Tuple[datetime.date, datetime.date]:
    """Calcular el rango del fin de semana actual o próximo (viernes a domingo)"""
    hoy = datetime.datetime.now(MEXICO_TZ).date()
    
    # Determinar el día de la semana (0 = lunes, 6 = domingo)
    dia_semana = hoy.weekday()
    
    # Calcular días hasta el próximo viernes
    dias_hasta_viernes = (4 - dia_semana) % 7  # 4 = viernes
    if dias_hasta_viernes == 0 and datetime.datetime.now(MEXICO_TZ).hour >= 20:
        # Si es viernes pero ya es tarde, ir al próximo viernes
        dias_hasta_viernes = 7
    
    # Calcular fechas
    proximo_viernes = hoy + datetime.timedelta(days=dias_hasta_viernes)
    proximo_domingo = proximo_viernes + datetime.timedelta(days=2)
    
    return proximo_viernes, proximo_domingo

async def obtener_partidos(inicio: datetime.date, fin: datetime.date) -> List[Dict[str, Any]]:
    """Obtener los partidos de Liga MX en un rango de fechas"""
    # Formatear fechas para la API
    inicio_str = inicio.strftime("%Y-%m-%d")
    fin_str = fin.strftime("%Y-%m-%d")
    
    logger.info(f"Buscando partidos desde {inicio_str} hasta {fin_str}")
    
    # Construir URL para la consulta
    url = "https://livescore-api.com/api-client/fixtures/matches.json"
    params = {
        "key": LIVESCORE_API_KEY,
        "secret": LIVESCORE_API_SECRET,
        "competition_id": LIGA_MX_COMPETITION_ID,
        "from": inicio_str,
        "to": fin_str
    }
    
    try:
        # Hacer la petición a la API
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success") and "data" in data:
            partidos = data["data"].get("fixtures", [])
            logger.info(f"Se encontraron {len(partidos)} partidos en el rango de fechas")
            
            # Filtrar solo partidos de Liga MX (verificación adicional)
            partidos_liga_mx = []
            for partido in partidos:
                if partido.get("competition_id") == LIGA_MX_COMPETITION_ID or \
                   partido.get("competition", {}).get("id") == LIGA_MX_COMPETITION_ID or \
                   "Liga MX" in partido.get("competition_name", ""):
                    partidos_liga_mx.append(partido)
            
            if len(partidos_liga_mx) < len(partidos):
                logger.info(f"Filtrados {len(partidos_liga_mx)} partidos de Liga MX de un total de {len(partidos)}")
            
            return partidos_liga_mx
        else:
            logger.error(f"Error al obtener partidos: {data.get('error', 'Error desconocido')}")
            return []
    except Exception as e:
        logger.error(f"Error al hacer la petición a la API: {e}")
        return []

async def obtener_partidos_jornada() -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """Obtener los partidos de la jornada actual de Liga MX"""
    # Obtener fecha actual en formato México
    hoy = datetime.datetime.now(MEXICO_TZ)
    
    # Calcular un rango de 14 días (2 semanas) que probablemente incluya la jornada actual
    inicio = hoy - datetime.timedelta(days=3)  # Incluir partidos recientes
    fin = hoy + datetime.timedelta(days=10)    # Incluir próximos partidos
    
    partidos = await obtener_partidos(inicio.date(), fin.date())
    
    if not partidos:
        return None, []
    
    # Agrupar partidos por jornada
    partidos_por_jornada = {}
    for partido in partidos:
        # Intentar obtener el nombre de la jornada
        round_name = partido.get("round", {}).get("name", "")
        if not round_name and "round" in partido:
            round_name = str(partido.get("round"))
        
        if round_name:
            if round_name not in partidos_por_jornada:
                partidos_por_jornada[round_name] = []
            partidos_por_jornada[round_name].append(partido)
    
    # Si hay múltiples jornadas, seleccionar la que tenga más partidos
    # (probablemente la jornada actual)
    if partidos_por_jornada:
        jornada_actual = max(partidos_por_jornada.items(), key=lambda x: len(x[1]))
        logger.info(f"Jornada seleccionada: {jornada_actual[0]} con {len(jornada_actual[1])} partidos")
        return jornada_actual[0], jornada_actual[1]
    
    # Si no pudimos agrupar por jornada, devolver todos los partidos
    return "Próximos Partidos", partidos

def formatear_partidos(partidos: List[Dict[str, Any]], titulo: str) -> str:
    """Formatear la lista de partidos para enviar como notificación"""
    if not partidos:
        return f"No hay partidos programados para {titulo.lower()}."
    
    # Ordenar partidos por fecha y hora
    partidos_ordenados = sorted(partidos, key=lambda x: (x.get("date", ""), x.get("time", "")))
    
    # Agrupar partidos por fecha
    partidos_por_fecha = {}
    for partido in partidos_ordenados:
        fecha = partido.get("date", "")
        if fecha not in partidos_por_fecha:
            partidos_por_fecha[fecha] = []
        partidos_por_fecha[fecha].append(partido)
    
    # Formatear mensaje
    mensaje = f"🏆 <b>PARTIDOS DE LIGA MX - {titulo.upper()}</b> 🏆\n\n"
    
    for fecha, partidos_fecha in partidos_por_fecha.items():
        # Convertir formato de fecha
        try:
            fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
            # Asignar la zona horaria de México
            fecha_dt = MEXICO_TZ.localize(fecha_dt)
            fecha_str = fecha_dt.strftime("%d/%m/%Y")
            dia_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][fecha_dt.weekday()]
            mensaje += f"📅 <b>{dia_semana} {fecha_str}</b>\n"
        except:
            mensaje += f"📅 <b>{fecha}</b>\n"
        
        for partido in partidos_fecha:
            # Obtener datos del partido
            local = partido.get("home_name", "Equipo Local")
            visitante = partido.get("away_name", "Equipo Visitante")
            hora = partido.get("time", "")
            
            # Convertir hora a formato 12h si está en formato 24h
            try:
                if ":" in hora:
                    hora_dt = datetime.datetime.strptime(hora, "%H:%M")
                    hora = hora_dt.strftime("%I:%M %p")
            except:
                pass
            
            # Estadio (si está disponible)
            estadio = partido.get("location", "")
            if estadio:
                estadio = f"🏟️ {estadio}"
            
            # Agregar línea del partido
            mensaje += f"⚽ {hora} - {local} vs {visitante}"
            if estadio:
                mensaje += f" - {estadio}"
            mensaje += "\n"
        
        mensaje += "\n"
    
    return mensaje

async def notificar_partidos_semana():
    """Notificar los partidos de toda la semana"""
    inicio, fin = calcular_rango_semana()
    partidos = await obtener_partidos(inicio, fin)
    mensaje = formatear_partidos(partidos, "Esta Semana")
    
    # Enviar mensaje a Telegram
    telegram_client = TelegramClient()
    logger.info("Enviando notificación de partidos de la semana a Telegram...")
    success = await telegram_client.send_message(mensaje)
    
    if success:
        logger.info("Notificación enviada con éxito")
    else:
        logger.error("Error al enviar la notificación")

async def notificar_partidos_finde():
    """Notificar los partidos del fin de semana"""
    inicio, fin = calcular_rango_fin_de_semana()
    partidos = await obtener_partidos(inicio, fin)
    mensaje = formatear_partidos(partidos, "Fin de Semana")
    
    # Enviar mensaje a Telegram
    telegram_client = TelegramClient()
    logger.info("Enviando notificación de partidos del fin de semana a Telegram...")
    success = await telegram_client.send_message(mensaje)
    
    if success:
        logger.info("Notificación enviada con éxito")
    else:
        logger.error("Error al enviar la notificación")

async def notificar_partidos_jornada():
    """Notificar los partidos de la jornada actual"""
    nombre_jornada, partidos = await obtener_partidos_jornada()
    if nombre_jornada:
        mensaje = formatear_partidos(partidos, nombre_jornada)
        
        # Enviar mensaje a Telegram
        telegram_client = TelegramClient()
        logger.info(f"Enviando notificación de partidos de {nombre_jornada} a Telegram...")
        success = await telegram_client.send_message(mensaje)
        
        if success:
            logger.info("Notificación enviada con éxito")
        else:
            logger.error("Error al enviar la notificación")
    else:
        logger.error("No se pudo determinar la jornada actual")

async def main():
    """Función principal"""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Notificar partidos de Liga MX')
    parser.add_argument('--tipo', choices=['semana', 'finde', 'jornada'], default='semana',
                        help='Tipo de notificación: semana (toda la semana), finde (fin de semana) o jornada (jornada actual)')
    
    # Parsear argumentos
    args = parser.parse_args()
    
    # Ejecutar la función correspondiente según el tipo de notificación
    if args.tipo == 'semana':
        await notificar_partidos_semana()
    elif args.tipo == 'finde':
        await notificar_partidos_finde()
    elif args.tipo == 'jornada':
        await notificar_partidos_jornada()

if __name__ == "__main__":
    asyncio.run(main())
