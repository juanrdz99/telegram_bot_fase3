"""
Track match states and detect changes
"""
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MatchTracker:
    """Track match states and detect changes"""

    def __init__(self):
        """Initialize the match tracker"""
        # Dictionary to store the last known state of each match
        # Key: match_id, Value: match state (score, events, etc.)
        self.match_states: Dict[str, Dict[str, Any]] = {}

    def update_match_state(
        self,
        match_id: str,
        match_details: Dict[str, Any],
        events: List[Dict[str, Any]],
        statistics: Dict[str, Any]
    ) -> bool:
        """Update the state of a match and check if there are significant changes

        Args:
            match_id: Match ID
            match_details: Match details from LiveScore API
            events: Match events from LiveScore API
            statistics: Match statistics from LiveScore API

        Returns:
            True if there are significant changes, False otherwise
        """
        # Create a new state for the match
        new_state = {
            "score": match_details.get("score", "0-0"),
            "status": match_details.get("status", ""),
            "minute": match_details.get("minute", ""),
            "events": self._extract_event_ids(events),
            "statistics": self._extract_key_statistics(statistics)
        }

        # Check if this is a new match or if there are significant changes
        if match_id not in self.match_states:
            logger.info(f"New match detected: {match_id}")
            self.match_states[match_id] = new_state
            return True
        
        # Get the previous state
        prev_state = self.match_states[match_id]
        
        # Check for significant changes
        has_changes = self._detect_significant_changes(prev_state, new_state)
        
        # Update the state if there are changes
        if has_changes:
            self.match_states[match_id] = new_state
            
        return has_changes

    def _extract_event_ids(self, events: List[Dict[str, Any]]) -> List[str]:
        """Extract event IDs from a list of events

        Args:
            events: List of match events

        Returns:
            List of event IDs
        """
        return [str(event.get("id", "")) for event in events]

    def _extract_key_statistics(self, statistics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key statistics from match statistics

        Args:
            statistics: Match statistics

        Returns:
            Dictionary of key statistics
        """
        key_stats = {}
        
        # Extract possession
        if "possession" in statistics:
            key_stats["possession"] = statistics["possession"]
            
        # Extract shots on target
        if "shots_on_target" in statistics:
            key_stats["shots_on_target"] = statistics["shots_on_target"]
            
        # Extract corners
        if "corners" in statistics:
            key_stats["corners"] = statistics["corners"]
            
        return key_stats

    def _detect_significant_changes(
        self,
        prev_state: Dict[str, Any],
        new_state: Dict[str, Any]
    ) -> bool:
        """Detect if there are significant changes between two match states

        Args:
            prev_state: Previous match state
            new_state: New match state

        Returns:
            True if there are significant changes, False otherwise
        """
        # Check if the score has changed
        if prev_state["score"] != new_state["score"]:
            logger.info("Score change detected")
            return True
            
        # Check if the status has changed
        if prev_state["status"] != new_state["status"]:
            logger.info("Status change detected")
            return True
            
        # Check if there are new events
        prev_events = set(prev_state["events"])
        new_events = set(new_state["events"])
        
        if len(new_events - prev_events) > 0:
            logger.info("New events detected")
            return True
            
        # Check if key statistics have changed significantly
        # For simplicity, we're just checking if the statistics objects are different
        if prev_state["statistics"] != new_state["statistics"]:
            logger.info("Statistics change detected")
            return True
            
        return False

    def get_tracked_match_ids(self) -> List[str]:
        """Get the IDs of all tracked matches

        Returns:
            List of match IDs
        """
        return list(self.match_states.keys())

    def clear_finished_matches(self, active_match_ids: List[str]) -> None:
        """Clear finished matches from the tracker

        Args:
            active_match_ids: List of active match IDs
        """
        # Convert to set for faster lookups
        active_ids = set(active_match_ids)
        
        # Find matches to remove
        to_remove = [match_id for match_id in self.match_states if match_id not in active_ids]
        
        # Remove finished matches
        for match_id in to_remove:
            logger.info(f"Removing finished match from tracker: {match_id}")
            self.match_states.pop(match_id, None)
