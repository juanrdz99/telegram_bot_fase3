"""
Format match data into Telegram messages
"""
from typing import Dict, List, Any
import logging
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Zona horaria de México
MEXICO_TZ = pytz.timezone('America/Mexico_City')

class MatchFormatter:
    """Format match data into Telegram messages"""

    @staticmethod
    def format_match_update(
        match_details: Dict[str, Any],
        events: List[Dict[str, Any]],
        statistics: Dict[str, Any]
    ) -> str:
        """Format match data into a Telegram message

        Args:
            match_details: Match details from LiveScore API
            events: Match events from LiveScore API
            statistics: Match statistics from LiveScore API

        Returns:
            Formatted message for Telegram
        """
        # Extract basic match information
        competition = match_details.get("competition", {}).get("name", "Liga MX")
        round_info = match_details.get("round", {}).get("name", "")
        stadium = match_details.get("venue", {}).get("name", "")
        
        home_team = match_details.get("home_name", "")
        away_team = match_details.get("away_name", "")
        home_score = match_details.get("score", "0-0").split("-")[0].strip()
        away_score = match_details.get("score", "0-0").split("-")[1].strip()
        
        # Format header
        header = (
            f"🏆 {competition} - {round_info}\n"
            f"🏟️ {stadium}\n\n"
            f"{home_team} {home_score} - {away_score} {away_team}\n"
        )
        
        # Format goals
        goals = MatchFormatter._format_goals(events, home_team, away_team)
        
        # Format substitutions
        substitutions = MatchFormatter._format_substitutions(events, home_team, away_team)
        
        # Format cards
        cards = MatchFormatter._format_cards(events, home_team, away_team)
        
        # Format statistics
        stats = MatchFormatter._format_statistics(statistics, home_team, away_team)
        
        # Combine all sections
        message_parts = [header]
        
        if goals:
            message_parts.append(f"\n⚽️ Goles:\n{goals}")
            
        if substitutions:
            message_parts.append(f"\n🔄 Cambios:\n{substitutions}")
            
        if cards:
            message_parts.append(f"\n🟨 Tarjetas:\n{cards}")
            
        if stats:
            message_parts.append(f"\n📊 Estadísticas:\n{stats}")
            
        return "".join(message_parts)

    @staticmethod
    def _format_goals(
        events: List[Dict[str, Any]],
        home_team: str,
        away_team: str
    ) -> str:
        """Format goal events

        Args:
            events: Match events
            home_team: Home team name
            away_team: Away team name

        Returns:
            Formatted goals section
        """
        goal_events = [e for e in events if e.get("type") == "goal"]
        
        if not goal_events:
            return ""
            
        goals_text = ""
        for goal in goal_events:
            minute = goal.get("minute", "")
            player = goal.get("player", "")
            team = home_team if goal.get("home_away") == "h" else away_team
            goals_text += f"⚽️ {minute}' {player} ({team})\n"
            
        return goals_text

    @staticmethod
    def _format_substitutions(
        events: List[Dict[str, Any]],
        home_team: str,
        away_team: str
    ) -> str:
        """Format substitution events

        Args:
            events: Match events
            home_team: Home team name
            away_team: Away team name

        Returns:
            Formatted substitutions section
        """
        sub_events = [e for e in events if e.get("type") == "substitution"]
        
        if not sub_events:
            return ""
            
        subs_text = ""
        for sub in sub_events:
            minute = sub.get("minute", "")
            player_in = sub.get("player_in", "")
            player_out = sub.get("player", "")
            team = home_team if sub.get("home_away") == "h" else away_team
            subs_text += f"🔄 {minute}' Sale: {player_out}, Entra: {player_in} ({team})\n"
            
        return subs_text

    @staticmethod
    def _format_cards(
        events: List[Dict[str, Any]],
        home_team: str,
        away_team: str
    ) -> str:
        """Format card events

        Args:
            events: Match events
            home_team: Home team name
            away_team: Away team name

        Returns:
            Formatted cards section
        """
        yellow_cards = [e for e in events if e.get("type") == "yellowcard"]
        red_cards = [e for e in events if e.get("type") == "redcard"]
        
        if not yellow_cards and not red_cards:
            return ""
            
        cards_text = ""
        
        # Yellow cards
        for card in yellow_cards:
            minute = card.get("minute", "")
            player = card.get("player", "")
            team = home_team if card.get("home_away") == "h" else away_team
            cards_text += f"🟨 {minute}' {player} ({team})\n"
            
        # Red cards
        for card in red_cards:
            minute = card.get("minute", "")
            player = card.get("player", "")
            team = home_team if card.get("home_away") == "h" else away_team
            cards_text += f"🟥 {minute}' {player} ({team})\n"
            
        return cards_text

    @staticmethod
    def _format_statistics(
        statistics: Dict[str, Any],
        home_team: str,
        away_team: str
    ) -> str:
        """Format match statistics

        Args:
            statistics: Match statistics
            home_team: Home team name
            away_team: Away team name

        Returns:
            Formatted statistics section
        """
        if not statistics:
            return ""
            
        # Extract statistics
        possession_home = statistics.get("possession", {}).get("home", "0")
        possession_away = statistics.get("possession", {}).get("away", "0")
        
        shots_on_target_home = statistics.get("shots_on_target", {}).get("home", "0")
        shots_on_target_away = statistics.get("shots_on_target", {}).get("away", "0")
        
        corners_home = statistics.get("corners", {}).get("home", "0")
        corners_away = statistics.get("corners", {}).get("away", "0")
        
        # Format statistics text
        stats_text = (
            f"👟 Posesión: {possession_home}% - {possession_away}%\n"
            f"🎯 Tiros a gol: {shots_on_target_home} - {shots_on_target_away}\n"
            f"🚩 Tiros de esquina: {corners_home} - {corners_away}"
        )
        
        return stats_text

    @staticmethod
    def format_match_notification(match: Dict[str, Any]) -> str:
        """Format a match notification

        Args:
            match: Match data

        Returns:
            Formatted message
        """
        # Extraer datos del partido
        home_team = match.get("home_name", "Equipo Local")
        away_team = match.get("away_name", "Equipo Visitante")
        date_str = match.get("date", "")
        time_str = match.get("time", "")
        location = match.get("location", "Estadio no disponible")
        competition = match.get("competition", {}).get("name", "Liga MX")
        round_info = match.get("round", "")
        
        # Formatear fecha y hora para México
        try:
            date_time_str = f"{date_str} {time_str}"
            date_time = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
            date_time_mexico = pytz.utc.localize(date_time).astimezone(MEXICO_TZ)
            formatted_date = date_time_mexico.strftime("%d/%m/%Y")
            formatted_time = date_time_mexico.strftime("%H:%M")
        except Exception as e:
            logging.error(f"Error formatting date and time: {e}")
            formatted_date = date_str
            formatted_time = time_str
        
        # Construir mensaje
        message = f"""
🔜 *PRÓXIMO PARTIDO* 🔜

🏆 {competition} - Jornada {round_info}
🏟️ {location}

{home_team} vs {away_team}

📅 {formatted_date}
⏰ {formatted_time} hrs (Ciudad de México)
        """
        
        return message

    @staticmethod
    def format_match_start(match_details: Dict[str, Any]) -> str:
        """Format a message for when a match starts

        Args:
            match_details: Match details

        Returns:
            Formatted message
        """
        # Extraer datos del partido
        home_team = match_details.get("home_name", "Equipo Local")
        away_team = match_details.get("away_name", "Equipo Visitante")
        venue = match_details.get("venue", {}).get("name", "Estadio no disponible")
        competition = match_details.get("competition", {}).get("name", "Liga MX")
        round_info = match_details.get("round", "")
        
        # Construir mensaje
        message = f"""
🎮 *PARTIDO INICIADO* 🎮

🏆 {competition} - Jornada {round_info}
🏟️ {venue}

{home_team} vs {away_team}

⏰ ¡El partido ha comenzado!
        """
        
        return message

    @staticmethod
    def format_goal_notification(match_details: Dict[str, Any], event: Dict[str, Any]) -> str:
        """Format a goal notification

        Args:
            match_details: Match details
            event: Goal event data

        Returns:
            Formatted message
        """
        # Extraer datos del partido
        home_team = match_details.get("home_name", "Equipo Local")
        away_team = match_details.get("away_name", "Equipo Visitante")
        home_score = match_details.get("score", {}).get("home", 0)
        away_score = match_details.get("score", {}).get("away", 0)
        venue = match_details.get("venue", {}).get("name", "Estadio no disponible")
        competition = match_details.get("competition", {}).get("name", "Liga MX")
        round_info = match_details.get("round", "")
        
        # Extraer datos del evento
        player = event.get("player", "Jugador")
        minute = event.get("minute", "?")
        team_side = event.get("home_away", "home")
        team_name = home_team if team_side == "home" else away_team
        
        # Construir mensaje
        message = f"""
⚽️ *¡GOL!* ⚽️

🏆 {competition} - Jornada {round_info}
🏟️ {venue}

{home_team} {home_score} - {away_score} {away_team}

⚽️ {minute}' {player} ({team_name})
        """
        
        return message

    @staticmethod
    def format_card_notification(match_details: Dict[str, Any], event: Dict[str, Any]) -> str:
        """Format a card notification

        Args:
            match_details: Match details
            event: Card event data

        Returns:
            Formatted message
        """
        # Extraer datos del partido
        home_team = match_details.get("home_name", "Equipo Local")
        away_team = match_details.get("away_name", "Equipo Visitante")
        home_score = match_details.get("score", {}).get("home", 0)
        away_score = match_details.get("score", {}).get("away", 0)
        venue = match_details.get("venue", {}).get("name", "Estadio no disponible")
        competition = match_details.get("competition", {}).get("name", "Liga MX")
        round_info = match_details.get("round", "")
        
        # Extraer datos del evento
        player = event.get("player", "Jugador")
        minute = event.get("minute", "?")
        team_side = event.get("home_away", "home")
        team_name = home_team if team_side == "home" else away_team
        card_type = event.get("type", "").lower()
        
        # Determinar tipo de tarjeta
        if "yellow" in card_type:
            emoji = "🟨"
            card_text = "TARJETA AMARILLA"
        elif "red" in card_type:
            emoji = "🟥"
            card_text = "TARJETA ROJA"
        else:
            emoji = "🃏"
            card_text = "TARJETA"
        
        # Construir mensaje
        message = f"""
{emoji} *{card_text}* {emoji}

🏆 {competition} - Jornada {round_info}
🏟️ {venue}

{home_team} {home_score} - {away_score} {away_team}

{emoji} {minute}' {player} ({team_name})
        """
        
        return message

    @staticmethod
    def format_substitution_notification(match_details: Dict[str, Any], event: Dict[str, Any]) -> str:
        """Format a substitution notification

        Args:
            match_details: Match details
            event: Substitution event data

        Returns:
            Formatted message
        """
        # Extraer datos del partido
        home_team = match_details.get("home_name", "Equipo Local")
        away_team = match_details.get("away_name", "Equipo Visitante")
        home_score = match_details.get("score", {}).get("home", 0)
        away_score = match_details.get("score", {}).get("away", 0)
        venue = match_details.get("venue", {}).get("name", "Estadio no disponible")
        competition = match_details.get("competition", {}).get("name", "Liga MX")
        round_info = match_details.get("round", "")
        
        # Extraer datos del evento
        player_out = event.get("player", "Jugador")
        player_in = event.get("player_in", "Jugador")
        minute = event.get("minute", "?")
        team_side = event.get("home_away", "home")
        team_name = home_team if team_side == "home" else away_team
        
        # Construir mensaje
        message = f"""
🔄 *SUSTITUCIÓN* 🔄

🏆 {competition} - Jornada {round_info}
🏟️ {venue}

{home_team} {home_score} - {away_score} {away_team}

🔄 {minute}' Sale: {player_out}, Entra: {player_in} ({team_name})
        """
        
        return message

    @staticmethod
    def format_halftime_notification(match_details: Dict[str, Any], statistics: Dict[str, Any]) -> str:
        """Format a halftime notification

        Args:
            match_details: Match details
            statistics: Match statistics

        Returns:
            Formatted message
        """
        # Extraer datos del partido
        home_team = match_details.get("home_name", "Equipo Local")
        away_team = match_details.get("away_name", "Equipo Visitante")
        home_score = match_details.get("score", {}).get("home", 0)
        away_score = match_details.get("score", {}).get("away", 0)
        venue = match_details.get("venue", {}).get("name", "Estadio no disponible")
        competition = match_details.get("competition", {}).get("name", "Liga MX")
        round_info = match_details.get("round", "")
        
        # Extraer estadísticas del primer tiempo
        possession_home = statistics.get("possession_ht", {}).get("home", "?")
        possession_away = statistics.get("possession_ht", {}).get("away", "?")
        shots_on_target_home = statistics.get("shots_on_target_ht", {}).get("home", "?")
        shots_on_target_away = statistics.get("shots_on_target_ht", {}).get("away", "?")
        corners_home = statistics.get("corners_ht", {}).get("home", "?")
        corners_away = statistics.get("corners_ht", {}).get("away", "?")
        
        # Construir mensaje
        message = f"""
⏱️ *MEDIO TIEMPO* ⏱️

🏆 {competition} - Jornada {round_info}
🏟️ {venue}

{home_team} {home_score} - {away_score} {away_team}

📊 Estadísticas:
👟 Posesión: {possession_home}% - {possession_away}%
🎯 Tiros a gol: {shots_on_target_home} - {shots_on_target_away}
🚩 Tiros de esquina: {corners_home} - {corners_away}
        """
        
        return message

    @staticmethod
    def format_fulltime_notification(match_details: Dict[str, Any], events: List[Dict[str, Any]], statistics: Dict[str, Any]) -> str:
        """Format a fulltime notification

        Args:
            match_details: Match details
            events: Match events
            statistics: Match statistics

        Returns:
            Formatted message
        """
        # Extraer datos del partido
        home_team = match_details.get("home_name", "Equipo Local")
        away_team = match_details.get("away_name", "Equipo Visitante")
        home_score = match_details.get("score", {}).get("home", 0)
        away_score = match_details.get("score", {}).get("away", 0)
        venue = match_details.get("venue", {}).get("name", "Estadio no disponible")
        competition = match_details.get("competition", {}).get("name", "Liga MX")
        round_info = match_details.get("round", "")
        
        # Extraer estadísticas finales
        possession_home = statistics.get("possession_ft", {}).get("home", "?")
        possession_away = statistics.get("possession_ft", {}).get("away", "?")
        shots_on_target_home = statistics.get("shots_on_target_ft", {}).get("home", "?")
        shots_on_target_away = statistics.get("shots_on_target_ft", {}).get("away", "?")
        corners_home = statistics.get("corners_ft", {}).get("home", "?")
        corners_away = statistics.get("corners_ft", {}).get("away", "?")
        
        # Procesar eventos para obtener goles, tarjetas y sustituciones
        goals = []
        cards = []
        substitutions = []
        
        for event in events:
            event_type = event.get("type", "").lower()
            player = event.get("player", "Jugador")
            minute = event.get("minute", "?")
            team_side = event.get("home_away", "home")
            team_name = home_team if team_side == "home" else away_team
            
            if "goal" in event_type:
                goals.append(f"⚽️ {minute}' {player} ({team_name})")
            elif "card" in event_type:
                card_emoji = "🟨" if "yellow" in event_type else "🟥"
                cards.append(f"{card_emoji} {minute}' {player} ({team_name})")
            elif "subst" in event_type:
                player_in = event.get("player_in", "Jugador")
                substitutions.append(f"🔄 {minute}' Sale: {player}, Entra: {player_in} ({team_name})")
        
        # Construir secciones del mensaje
        goals_section = "\n⚽️ Goles:\n" + "\n".join(goals) if goals else ""
        cards_section = "\n🟨 Tarjetas:\n" + "\n".join(cards) if cards else ""
        subs_section = "\n🔄 Cambios:\n" + "\n".join(substitutions) if substitutions else ""
        
        # Construir mensaje
        message = f"""
🏁 *FINAL DEL PARTIDO* 🏁

🏆 {competition} - Jornada {round_info}
🏟️ {venue}

{home_team} {home_score} - {away_score} {away_team}
{goals_section}
{subs_section}
{cards_section}

📊 Estadísticas:
👟 Posesión: {possession_home}% - {possession_away}%
🎯 Tiros a gol: {shots_on_target_home} - {shots_on_target_away}
🚩 Tiros de esquina: {corners_home} - {corners_away}
        """
        
        return message
