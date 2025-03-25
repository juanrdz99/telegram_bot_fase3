"""
LiveScore API client
"""
import logging
import requests
from typing import Dict, List, Any, Optional

from core.config import (
    LIVESCORE_API_KEY, 
    LIVESCORE_API_SECRET, 
    LIGA_MX_COMPETITION_ID,
    LIGA_MX_GROUP_ID,
    LIVESCORE_MATCHES_ENDPOINT,
    LIVESCORE_FIXTURES_ENDPOINT,
    LIVESCORE_MATCH_DETAILS_ENDPOINT,
    LIVESCORE_EVENTS_ENDPOINT,
    LIVESCORE_STATISTICS_ENDPOINT,
    LIVESCORE_LEAGUE_TABLE_ENDPOINT,
    LIVESCORE_HISTORY_ENDPOINT,
    LIVESCORE_TOPSCORERS_ENDPOINT
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LiveScoreClient:
    """Client for the LiveScore API"""

    def __init__(self, api_key=None, api_secret=None):
        """Initialize the LiveScore API client"""
        self.api_key = api_key or LIVESCORE_API_KEY
        self.api_secret = api_secret or LIVESCORE_API_SECRET
        self.base_url = "https://livescore-api.com/api-client"
        
        logger.info("LiveScore API client initialized")

    def get_liga_mx_matches(self, live_only: bool = True) -> List[Dict[str, Any]]:
        """Get Liga MX matches

        Args:
            live_only: If True, only return live matches

        Returns:
            List of matches
        """
        # Build URL for the request
        if live_only:
            url = LIVESCORE_MATCHES_ENDPOINT
        else:
            url = LIVESCORE_FIXTURES_ENDPOINT
        
        # Build parameters
        params = {
            "key": self.api_key,
            "secret": self.api_secret,
            "competition_id": LIGA_MX_COMPETITION_ID
        }
        
        try:
            # Make the request
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "data" in data:
                if live_only:
                    matches = data["data"].get("match", [])
                else:
                    matches = data["data"].get("fixtures", [])
                logger.info(f"Found {len(matches)} Liga MX matches")
                return matches
            else:
                logger.error(f"Error getting Liga MX matches: {data.get('error', 'Unknown error')}")
                return []
        except Exception as e:
            logger.error(f"Error making request to LiveScore API: {e}")
            return []

    def get_fixtures(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get fixtures with custom parameters

        Args:
            params: Custom parameters for the request

        Returns:
            List of fixtures
        """
        # Build URL for the request
        url = LIVESCORE_FIXTURES_ENDPOINT
        
        # Add API credentials to parameters
        request_params = {
            "key": self.api_key,
            "secret": self.api_secret,
            **params
        }
        
        try:
            # Make the request
            response = requests.get(url, params=request_params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "data" in data:
                fixtures = data["data"].get("fixtures", [])
                logger.info(f"Found {len(fixtures)} fixtures")
                return fixtures
            else:
                logger.error(f"Error getting fixtures: {data.get('error', 'Unknown error')}")
                return []
        except Exception as e:
            logger.error(f"Error making request to LiveScore API: {e}")
            return []

    def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Get match details

        Args:
            match_id: ID of the match

        Returns:
            Match details
        """
        # Build URL for the request
        url = LIVESCORE_MATCH_DETAILS_ENDPOINT
        
        # Build parameters
        params = {
            "key": self.api_key,
            "secret": self.api_secret,
            "id": match_id
        }
        
        try:
            # Make the request
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "data" in data:
                match = data["data"]
                logger.info(f"Got details for match {match_id}")
                return match
            else:
                logger.error(f"Error getting match details: {data.get('error', 'Unknown error')}")
                return {}
        except Exception as e:
            logger.error(f"Error making request to LiveScore API: {e}")
            return {}

    def get_match_events(self, match_id: str) -> List[Dict[str, Any]]:
        """Get match events

        Args:
            match_id: ID of the match

        Returns:
            List of match events
        """
        # Build URL for the request
        url = LIVESCORE_EVENTS_ENDPOINT
        
        # Build parameters
        params = {
            "key": self.api_key,
            "secret": self.api_secret,
            "id": match_id
        }
        
        try:
            # Make the request
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "data" in data:
                events = data["data"].get("event", [])
                logger.info(f"Found {len(events)} events for match {match_id}")
                return events
            else:
                logger.error(f"Error getting match events: {data.get('error', 'Unknown error')}")
                return []
        except Exception as e:
            logger.error(f"Error making request to LiveScore API: {e}")
            return []

    def get_match_statistics(self, match_id: str) -> Dict[str, Any]:
        """Get match statistics

        Args:
            match_id: ID of the match

        Returns:
            Match statistics
        """
        # Build URL for the request
        url = LIVESCORE_STATISTICS_ENDPOINT
        
        # Build parameters
        params = {
            "key": self.api_key,
            "secret": self.api_secret,
            "id": match_id
        }
        
        try:
            # Make the request
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "data" in data:
                statistics = data["data"]
                logger.info(f"Got statistics for match {match_id}")
                return statistics
            else:
                logger.error(f"Error getting match statistics: {data.get('error', 'Unknown error')}")
                return {}
        except Exception as e:
            logger.error(f"Error making request to LiveScore API: {e}")
            return {}

    def get_league_table(self, competition_id: str = LIGA_MX_COMPETITION_ID) -> List[Dict[str, Any]]:
        """Get the league table for a competition

        Args:
            competition_id: Competition ID

        Returns:
            League table
        """
        # Build URL for the request
        url = LIVESCORE_LEAGUE_TABLE_ENDPOINT
        
        # Build parameters
        params = {
            "key": self.api_key,
            "secret": self.api_secret,
            "competition_id": competition_id,
            "group_id": LIGA_MX_GROUP_ID  # Use the group ID for Liga MX standings
        }
        
        try:
            # Make the request
            logger.info(f"Requesting league table for competition {competition_id}, group {LIGA_MX_GROUP_ID}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "data" in data:
                table = data["data"].get("table", [])
                logger.info(f"Successfully retrieved league table with {len(table)} teams")
                
                # Log the structure of the first team for debugging
                if table and len(table) > 0:
                    logger.info(f"Sample team data structure: {table[0].keys()}")
                
                # Process and format the table data to match the expected format
                formatted_table = []
                for team in table:
                    # Extract team data and ensure all required fields are present
                    team_data = {
                        "name": team.get("name", ""),
                        "logo": self._get_team_logo(team.get("name", "")),
                        "played": team.get("matches_total", team.get("played", 0)),
                        "won": team.get("matches_won", team.get("won", 0)),
                        "drawn": team.get("matches_drawn", team.get("drawn", 0)),
                        "lost": team.get("matches_lost", team.get("lost", 0)),
                        "goalsFor": team.get("goals_scored", team.get("goalsFor", 0)),
                        "goalsAgainst": team.get("goals_conceded", team.get("goalsAgainst", 0)),
                        "goalDifference": team.get("goal_diff", team.get("goalDifference", 0)),
                        "points": team.get("points", 0)
                    }
                    formatted_table.append(team_data)
                
                return formatted_table
            else:
                error_msg = data.get("error", "Unknown error")
                logger.error(f"Error getting league table: {error_msg}")
                logger.error(f"Full response: {data}")
                return []
        except Exception as e:
            logger.error(f"Error making request to LiveScore API: {e}")
            return []
    
    def get_match_history(self, competition_id: str = LIGA_MX_COMPETITION_ID, page: int = 1) -> List[Dict[str, Any]]:
        """Get match history for a competition

        Args:
            competition_id: Competition ID
            page: Page number for pagination

        Returns:
            List of historical matches
        """
        # Build URL for the request
        url = LIVESCORE_HISTORY_ENDPOINT
        
        # Build parameters
        params = {
            "key": self.api_key,
            "secret": self.api_secret,
            "competition_id": competition_id,
            "page": page
        }
        
        try:
            # Make the request
            logger.info(f"Requesting match history for competition {competition_id}, page {page}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "data" in data:
                matches = data["data"].get("match", [])
                logger.info(f"Successfully retrieved {len(matches)} historical matches")
                return matches
            else:
                error_msg = data.get("error", "Unknown error")
                logger.error(f"Error getting match history: {error_msg}")
                return []
        except Exception as e:
            logger.error(f"Error making request to LiveScore API: {e}")
            return []
    
    def get_top_scorers(self, competition_id: str = LIGA_MX_COMPETITION_ID) -> List[Dict[str, Any]]:
        """Get top scorers for a competition

        Args:
            competition_id: Competition ID

        Returns:
            List of top scorers
        """
        # Build URL for the request
        url = LIVESCORE_TOPSCORERS_ENDPOINT
        
        # Build parameters
        params = {
            "key": self.api_key,
            "secret": self.api_secret,
            "competition_id": competition_id
        }
        
        try:
            # Make the request
            logger.info(f"Requesting top scorers for competition {competition_id}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "data" in data:
                scorers = data["data"].get("topscorers", [])
                logger.info(f"Successfully retrieved {len(scorers)} top scorers")
                return scorers
            else:
                error_msg = data.get("error", "Unknown error")
                logger.error(f"Error getting top scorers: {error_msg}")
                return []
        except Exception as e:
            logger.error(f"Error making request to LiveScore API: {e}")
            return []
    
    def _get_team_logo(self, team_name: str) -> str:
        """Get the logo URL for a team

        Args:
            team_name: Name of the team

        Returns:
            URL of the team logo
        """
        # Normalize team name (lowercase, remove accents, etc.)
        normalized_name = self._normalize_team_name(team_name)
        
        # Map of normalized team names to logo filenames
        team_logos = {
            "america": "america.png",
            "cruz azul": "cruzazul.png",
            "guadalajara": "guadalajara.png",
            "chivas": "guadalajara.png",
            "pumas unam": "pumas.png",
            "pumas": "pumas.png",
            "tigres uanl": "tigres.png",
            "tigres": "tigres.png",
            "monterrey": "monterrey.png",
            "atlas": "atlas.png",
            "toluca": "toluca.png",
            "leon": "leon.png",
            "santos laguna": "santos.png",
            "santos": "santos.png",
            "pachuca": "pachuca.png",
            "tijuana": "tijuana.png",
            "xolos": "tijuana.png",
            "puebla": "puebla.png",
            "necaxa": "necaxa.png",
            "queretaro": "queretaro.png",
            "queretaro fc": "queretaro.png",
            "gallos blancos": "queretaro.png",
            "mazatlan": "mazatlan.png",
            "mazatlan fc": "mazatlan.png",
            "atletico san luis": "atleticosl.png",
            "san luis": "atleticosl.png",
            "juarez": "juarez.png",
            "fc juarez": "juarez.png"
        }
        
        # Get the logo filename or use a default
        logo_filename = team_logos.get(normalized_name, "america.png")
        
        logger.info(f"Logo para '{team_name}' (normalizado: '{normalized_name}'): {logo_filename}")
        
        # Return the full URL
        return f"/static/img/ligamx/{logo_filename}"
    
    def _normalize_team_name(self, team_name: str) -> str:
        """Normalize a team name for consistent matching

        Args:
            team_name: Name of the team

        Returns:
            Normalized team name
        """
        import unicodedata
        import re
        
        # Convert to lowercase
        name = team_name.lower()
        
        # Remove accents
        name = ''.join(c for c in unicodedata.normalize('NFD', name)
                      if unicodedata.category(c) != 'Mn')
        
        # Remove common prefixes/suffixes
        name = re.sub(r'^cd\s+|^club\s+|^cf\s+|^fc\s+', '', name)
        
        # Remove "de" and "del" words
        name = re.sub(r'\s+de\s+|\s+del\s+', ' ', name)
        
        # Clean up extra spaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        logger.debug(f"Normalized team name: '{team_name}' -> '{name}'")
        return name
