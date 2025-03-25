"""
Sistema mejorado de seguimiento de partidos con notificaciones detalladas
"""
import asyncio
import logging
import datetime
import pytz
from typing import Dict, List, Any, Set, Optional
import time

from core.config import (
    LIVESCORE_API_KEY,
    LIVESCORE_API_SECRET,
    LIGA_MX_COMPETITION_ID
)
from core.livescore_client import LiveScoreClient
from core.telegram_client import TelegramClient
from core.formatter import MatchFormatter

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Zona horaria de México (Ciudad de México)
MEXICO_TZ = pytz.timezone('America/Mexico_City')

class EnhancedMatchTracker:
    """Sistema mejorado de seguimiento de partidos con notificaciones detalladas"""

    def __init__(self):
        """Inicializar el rastreador de partidos mejorado"""
        self.livescore_client = LiveScoreClient()
        self.telegram_client = TelegramClient()
        self.formatter = MatchFormatter()
        
        # Diccionario para almacenar el estado de cada partido
        # Clave: match_id, Valor: estado del partido (puntuación, eventos, etc.)
        self.match_states: Dict[str, Dict[str, Any]] = {}
        
        # Conjunto para almacenar los IDs de los partidos que ya han sido notificados
        # para eventos específicos (pre-partido, inicio, medio tiempo, etc.)
        self.notified_matches: Dict[str, Set[str]] = {
            "pre_match": set(),       # Notificación 1 hora antes
            "match_start": set(),     # Inicio del partido
            "half_time": set(),       # Medio tiempo
            "match_end": set(),       # Final del partido
            "events": set()           # IDs de eventos ya notificados
        }
        
        logger.info("Rastreador de partidos mejorado inicializado")

    async def check_upcoming_matches(self) -> None:
        """Verificar próximos partidos y enviar notificaciones si es necesario"""
        logger.info("Verificando próximos partidos...")
        
        try:
            # Obtener fecha actual en México
            now = datetime.datetime.now(MEXICO_TZ)
            
            # Obtener partidos de hoy y mañana
            today = now.strftime("%Y-%m-%d")
            tomorrow = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Construir parámetros para la API
            params = {
                "competition_id": LIGA_MX_COMPETITION_ID,
                "from": today,
                "to": tomorrow
            }
            
            # Obtener partidos
            matches = self.livescore_client.get_fixtures(params)
            
            if not matches:
                logger.info("No se encontraron próximos partidos")
                return
                
            logger.info(f"Se encontraron {len(matches)} próximos partidos")
            
            # Procesar cada partido
            for match in matches:
                match_id = match.get("id")
                
                if not match_id:
                    continue
                
                # Obtener detalles del partido
                match_date_str = match.get("date", "")
                match_time_str = match.get("time", "")
                
                if not match_date_str or not match_time_str:
                    continue
                
                # Limpiar la hora si tiene segundos (formato HH:MM:SS)
                if match_time_str and ":" in match_time_str:
                    parts = match_time_str.split(":")
                    if len(parts) > 2:
                        match_time_str = f"{parts[0]}:{parts[1]}"
                
                # Combinar fecha y hora
                match_datetime_str = f"{match_date_str} {match_time_str}"
                
                try:
                    # Parsear fecha y hora
                    match_datetime = datetime.datetime.strptime(match_datetime_str, "%Y-%m-%d %H:%M")
                    # Asignar zona horaria de México
                    match_datetime = MEXICO_TZ.localize(match_datetime)
                    
                    # Calcular tiempo hasta el partido
                    time_until_match = match_datetime - now
                    
                    # Si el partido es en menos de 1 hora y 5 minutos pero más de 55 minutos
                    # (ventana de 10 minutos para evitar notificaciones duplicadas)
                    if time_until_match.total_seconds() <= 3900 and time_until_match.total_seconds() >= 3300:
                        # Verificar si ya se envió la notificación pre-partido
                        if match_id not in self.notified_matches["pre_match"]:
                            await self._send_pre_match_notification(match)
                            self.notified_matches["pre_match"].add(match_id)
                            
                except Exception as e:
                    logger.error(f"Error al procesar fecha/hora del partido {match_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error al verificar próximos partidos: {e}")

    async def check_live_matches(self) -> None:
        """Verificar partidos en vivo y enviar notificaciones si es necesario"""
        logger.info("Verificando partidos en vivo...")
        
        try:
            # Obtener partidos en vivo de Liga MX
            matches = self.livescore_client.get_liga_mx_matches(live_only=True)
            
            if not matches:
                logger.info("No se encontraron partidos en vivo")
                return
                
            logger.info(f"Se encontraron {len(matches)} partidos en vivo")
            
            # Obtener IDs de partidos activos
            active_match_ids = [match.get("id") for match in matches if match.get("id")]
            
            # Limpiar partidos terminados del rastreador
            self._clear_finished_matches(active_match_ids)
            
            # Procesar cada partido
            for match in matches:
                match_id = match.get("id")
                
                if not match_id:
                    logger.warning("Partido sin ID detectado, omitiendo...")
                    continue
                    
                try:
                    # Obtener detalles, eventos y estadísticas del partido
                    match_details = self.livescore_client.get_match_details(match_id)
                    if not match_details:
                        logger.warning(f"No se pudieron obtener detalles para el partido {match_id}, omitiendo...")
                        continue
                    
                    match_events = self.livescore_client.get_match_events(match_id)
                    match_statistics = self.livescore_client.get_match_statistics(match_id)
                    
                    # Verificar el estado del partido
                    status = match_details.get("status", "")
                    minute = match_details.get("minute", "")
                    
                    # Verificar si es el inicio del partido
                    if status == "IN_PLAY" and (minute == "1" or minute == "1'"):
                        if match_id not in self.notified_matches["match_start"]:
                            await self._send_match_start_notification(match_details)
                            self.notified_matches["match_start"].add(match_id)
                    
                    # Verificar si es medio tiempo
                    if status == "HALF_TIME" or (status == "BREAK" and minute in ["45", "45'"]):
                        if match_id not in self.notified_matches["half_time"]:
                            await self._send_half_time_notification(match_details, match_statistics)
                            self.notified_matches["half_time"].add(match_id)
                    
                    # Verificar si el partido ha terminado
                    if status in ["FINISHED", "FULL_TIME", "ENDED"]:
                        if match_id not in self.notified_matches["match_end"]:
                            await self._send_match_end_notification(match_details, match_events, match_statistics)
                            self.notified_matches["match_end"].add(match_id)
                    
                    # Actualizar estado del partido y verificar cambios
                    await self._update_match_state(match_id, match_details, match_events, match_statistics)
                except Exception as e:
                    logger.error(f"Error al procesar el partido {match_id}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error al verificar partidos en vivo: {e}")

    async def _update_match_state(
        self,
        match_id: str,
        match_details: Dict[str, Any],
        events: List[Dict[str, Any]],
        statistics: Dict[str, Any]
    ) -> None:
        """Actualizar el estado de un partido y verificar si hay cambios significativos

        Args:
            match_id: ID del partido
            match_details: Detalles del partido de la API de LiveScore
            events: Eventos del partido de la API de LiveScore
            statistics: Estadísticas del partido de la API de LiveScore
        """
        # Crear un nuevo estado para el partido
        new_state = {
            "score": match_details.get("score", "0-0"),
            "status": match_details.get("status", ""),
            "minute": match_details.get("minute", ""),
            "events": events,
            "statistics": statistics
        }
        
        # Verificar si es un partido nuevo
        if match_id not in self.match_states:
            logger.info(f"Nuevo partido detectado: {match_id}")
            self.match_states[match_id] = new_state
            return
        
        # Obtener el estado anterior
        prev_state = self.match_states[match_id]
        
        # Verificar cambios en la puntuación
        if prev_state["score"] != new_state["score"]:
            logger.info(f"Cambio de puntuación detectado en partido {match_id}")
            await self._send_score_change_notification(match_details, new_state["score"], prev_state["score"])
        
        # Verificar nuevos eventos
        await self._check_new_events(match_id, match_details, prev_state["events"], new_state["events"])
        
        # Actualizar el estado
        self.match_states[match_id] = new_state

    async def _check_new_events(
        self,
        match_id: str,
        match_details: Dict[str, Any],
        prev_events: List[Dict[str, Any]],
        new_events: List[Dict[str, Any]]
    ) -> None:
        """Verificar si hay nuevos eventos y enviar notificaciones

        Args:
            match_id: ID del partido
            match_details: Detalles del partido
            prev_events: Eventos anteriores
            new_events: Eventos nuevos
        """
        # Obtener IDs de eventos anteriores
        prev_event_ids = {str(event.get("id", "")) for event in prev_events if event.get("id")}
        
        # Verificar cada nuevo evento
        for event in new_events:
            event_id = str(event.get("id", "")) if event.get("id") else ""
            
            # Si es un evento nuevo y no ha sido notificado
            if event_id and event_id not in prev_event_ids and event_id not in self.notified_matches["events"]:
                event_type = event.get("type", "")
                
                # Enviar notificación según el tipo de evento
                if event_type == "goal":
                    await self._send_goal_notification(match_details, event)
                elif event_type in ["yellowcard", "redcard"]:
                    await self._send_card_notification(match_details, event)
                elif event_type == "substitution":
                    await self._send_substitution_notification(match_details, event)
                
                # Marcar evento como notificado
                self.notified_matches["events"].add(event_id)

    async def _send_pre_match_notification(self, match: Dict[str, Any]) -> None:
        """Enviar notificación 1 hora antes del partido

        Args:
            match: Información del partido
        """
        home_team = match.get("home_name", "")
        away_team = match.get("away_name", "")
        match_time = match.get("time", "")
        stadium = match.get("location", "")
        
        message = (
            f"🚨 <b>PARTIDO EN 1 HORA</b> 🚨\n\n"
            f"⚽️ {home_team} vs {away_team}\n"
            f"🕒 {match_time}\n"
        )
        
        if stadium:
            message += f"🏟️ {stadium}\n"
        
        await self.telegram_client.send_message(message)
        logger.info(f"Notificación pre-partido enviada: {home_team} vs {away_team}")

    async def _send_match_start_notification(self, match_details: Dict[str, Any]) -> None:
        """Enviar notificación al inicio del partido

        Args:
            match_details: Detalles del partido
        """
        home_team = match_details.get("home_name", "")
        away_team = match_details.get("away_name", "")
        stadium = match_details.get("venue", {}).get("name", "")
        competition = match_details.get("competition", {}).get("name", "Liga MX")
        round_info = match_details.get("round", {}).get("name", "")
        
        message = (
            f"🏆 <b>INICIA EL PARTIDO</b> 🏆\n\n"
            f"🏆 {competition} - {round_info}\n"
            f"⚽️ {home_team} vs {away_team}\n"
        )
        
        if stadium:
            message += f"🏟️ {stadium}\n"
        
        await self.telegram_client.send_message(message)
        logger.info(f"Notificación inicio de partido enviada: {home_team} vs {away_team}")

    async def _send_half_time_notification(
        self,
        match_details: Dict[str, Any],
        statistics: Dict[str, Any]
    ) -> None:
        """Enviar notificación al medio tiempo

        Args:
            match_details: Detalles del partido
            statistics: Estadísticas del partido
        """
        home_team = match_details.get("home_name", "")
        away_team = match_details.get("away_name", "")
        score = match_details.get("score", "0-0")
        
        message = (
            f"⏱️ <b>MEDIO TIEMPO</b> ⏱️\n\n"
            f"⚽️ {home_team} {score} {away_team}\n\n"
        )
        
        # Agregar estadísticas
        if statistics:
            # Extraer estadísticas
            possession_home = statistics.get("possession", {}).get("home", "0")
            possession_away = statistics.get("possession", {}).get("away", "0")
            
            shots_on_target_home = statistics.get("shots_on_target", {}).get("home", "0")
            shots_on_target_away = statistics.get("shots_on_target", {}).get("away", "0")
            
            corners_home = statistics.get("corners", {}).get("home", "0")
            corners_away = statistics.get("corners", {}).get("away", "0")
            
            message += (
                f"📊 <b>Estadísticas:</b>\n"
                f"Posesión: {home_team} {possession_home}% - {possession_away}% {away_team}\n"
                f"Tiros a puerta: {home_team} {shots_on_target_home} - {shots_on_target_away} {away_team}\n"
                f"Corners: {home_team} {corners_home} - {corners_away} {away_team}\n"
            )
        
        await self.telegram_client.send_message(message)
        logger.info(f"Notificación medio tiempo enviada: {home_team} vs {away_team}")

    async def _send_match_end_notification(
        self,
        match_details: Dict[str, Any],
        events: List[Dict[str, Any]],
        statistics: Dict[str, Any]
    ) -> None:
        """Enviar notificación al final del partido

        Args:
            match_details: Detalles del partido
            events: Eventos del partido
            statistics: Estadísticas del partido
        """
        # Usar el formateador para crear un resumen completo del partido
        message = self.formatter.format_match_update(match_details, events, statistics)
        
        # Agregar encabezado de final del partido
        home_team = match_details.get("home_name", "")
        away_team = match_details.get("away_name", "")
        score = match_details.get("score", "0-0")
        
        header = f"🏁 <b>FINAL DEL PARTIDO</b> 🏁\n\n"
        
        await self.telegram_client.send_message(header + message)
        logger.info(f"Notificación final de partido enviada: {home_team} vs {away_team}")

    async def _send_score_change_notification(
        self,
        match_details: Dict[str, Any],
        new_score: str,
        prev_score: str
    ) -> None:
        """Enviar notificación de cambio de puntuación

        Args:
            match_details: Detalles del partido
            new_score: Nueva puntuación
            prev_score: Puntuación anterior
        """
        home_team = match_details.get("home_name", "")
        away_team = match_details.get("away_name", "")
        minute = match_details.get("minute", "")
        
        # Obtener puntuaciones individuales
        try:
            new_home, new_away = new_score.split("-")
            prev_home, prev_away = prev_score.split("-")
            
            # Determinar qué equipo anotó
            team_scored = home_team if int(new_home) > int(prev_home) else away_team
            
            message = (
                f"⚽️ <b>¡GOOOOL!</b> ⚽️\n\n"
                f"⏱️ Minuto: {minute}\n"
                f"⚽️ {team_scored} anota\n"
                f"🏆 {home_team} {new_score} {away_team}\n"
            )
            
            await self.telegram_client.send_message(message)
            logger.info(f"Notificación de gol enviada: {team_scored} en {home_team} vs {away_team}")
        except:
            # Si hay un error al parsear la puntuación, enviar una notificación genérica
            message = (
                f"⚽️ <b>¡CAMBIO EN EL MARCADOR!</b> ⚽️\n\n"
                f"⏱️ Minuto: {minute}\n"
                f"🏆 {home_team} {new_score} {away_team}\n"
            )
            
            await self.telegram_client.send_message(message)
            logger.info(f"Notificación de cambio de marcador enviada: {home_team} vs {away_team}")

    async def _send_goal_notification(
        self,
        match_details: Dict[str, Any],
        event: Dict[str, Any]
    ) -> None:
        """Enviar notificación de gol

        Args:
            match_details: Detalles del partido
            event: Evento de gol
        """
        home_team = match_details.get("home_name", "")
        away_team = match_details.get("away_name", "")
        score = match_details.get("score", "0-0")
        minute = event.get("minute", "")
        player = event.get("player", "Jugador desconocido")
        team = home_team if event.get("home_away") == "h" else away_team
        
        message = (
            f"⚽️ <b>¡GOOOOL!</b> ⚽️\n\n"
            f"⏱️ Minuto: {minute}\n"
            f"👤 {player} ({team})\n"
            f"🏆 {home_team} {score} {away_team}\n"
        )
        
        await self.telegram_client.send_message(message)
        logger.info(f"Notificación de gol enviada: {player} ({team})")

    async def _send_card_notification(
        self,
        match_details: Dict[str, Any],
        event: Dict[str, Any]
    ) -> None:
        """Enviar notificación de tarjeta

        Args:
            match_details: Detalles del partido
            event: Evento de tarjeta
        """
        home_team = match_details.get("home_name", "")
        away_team = match_details.get("away_name", "")
        minute = event.get("minute", "")
        player = event.get("player", "Jugador desconocido")
        team = home_team if event.get("home_away") == "h" else away_team
        card_type = event.get("type", "")
        
        card_emoji = "🟨" if card_type == "yellowcard" else "🟥"
        card_text = "TARJETA AMARILLA" if card_type == "yellowcard" else "TARJETA ROJA"
        
        message = (
            f"{card_emoji} <b>{card_text}</b> {card_emoji}\n\n"
            f"⏱️ Minuto: {minute}\n"
            f"👤 {player} ({team})\n"
            f"🏆 {home_team} vs {away_team}\n"
        )
        
        await self.telegram_client.send_message(message)
        logger.info(f"Notificación de tarjeta enviada: {player} ({team})")

    async def _send_substitution_notification(
        self,
        match_details: Dict[str, Any],
        event: Dict[str, Any]
    ) -> None:
        """Enviar notificación de sustitución

        Args:
            match_details: Detalles del partido
            event: Evento de sustitución
        """
        home_team = match_details.get("home_name", "")
        away_team = match_details.get("away_name", "")
        minute = event.get("minute", "")
        player_out = event.get("player", "Jugador desconocido")
        player_in = event.get("player_in", "Jugador desconocido")
        team = home_team if event.get("home_away") == "h" else away_team
        
        message = (
            f"🔄 <b>CAMBIO</b> 🔄\n\n"
            f"⏱️ Minuto: {minute}\n"
            f"👤 Sale: {player_out}\n"
            f"👤 Entra: {player_in}\n"
            f"🏆 Equipo: {team}\n"
        )
        
        await self.telegram_client.send_message(message)
        logger.info(f"Notificación de cambio enviada: {player_out} por {player_in} ({team})")

    def _clear_finished_matches(self, active_match_ids: List[str]) -> None:
        """Limpiar partidos terminados del rastreador

        Args:
            active_match_ids: Lista de IDs de partidos activos
        """
        # Convertir a conjunto para búsquedas más rápidas
        active_ids = set(active_match_ids)
        
        # Encontrar partidos a eliminar
        to_remove = [match_id for match_id in self.match_states if match_id not in active_ids]
        
        # Eliminar partidos terminados
        for match_id in to_remove:
            logger.info(f"Eliminando partido terminado del rastreador: {match_id}")
            self.match_states.pop(match_id, None)
            
            # También limpiar las notificaciones para este partido
            # excepto las de final de partido
            if match_id in self.notified_matches["pre_match"]:
                self.notified_matches["pre_match"].remove(match_id)
            if match_id in self.notified_matches["match_start"]:
                self.notified_matches["match_start"].remove(match_id)
            if match_id in self.notified_matches["half_time"]:
                self.notified_matches["half_time"].remove(match_id)


async def main():
    """Función principal"""
    logger.info("Iniciando el rastreador de partidos mejorado...")
    
    tracker = EnhancedMatchTracker()
    
    # Intervalo de verificación en segundos
    check_interval = 30
    
    try:
        while True:
            # Verificar próximos partidos
            await tracker.check_upcoming_matches()
            
            # Verificar partidos en vivo
            await tracker.check_live_matches()
            
            # Esperar antes de la próxima verificación
            await asyncio.sleep(check_interval)
    except KeyboardInterrupt:
        logger.info("Deteniendo el rastreador de partidos...")
    except Exception as e:
        logger.error(f"Error en el bucle principal: {e}")


if __name__ == "__main__":
    asyncio.run(main())
