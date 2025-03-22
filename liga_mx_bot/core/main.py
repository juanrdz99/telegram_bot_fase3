"""
Main application for Liga MX Telegram Bot
"""
import asyncio
import logging
import time
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import UPDATE_INTERVAL
from livescore_client import LiveScoreClient
from telegram_client import TelegramClient
from formatter import MatchFormatter
from match_tracker import MatchTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LigaMXBot:
    """Main application for Liga MX Telegram Bot"""

    def __init__(self):
        """Initialize the Liga MX Bot"""
        self.livescore_client = LiveScoreClient()
        self.telegram_client = TelegramClient()
        self.match_tracker = MatchTracker()
        self.formatter = MatchFormatter()
        self.scheduler = AsyncIOScheduler()
        
        # Check if API keys are available
        if not self.livescore_client.api_key or not self.livescore_client.api_secret:
            logger.error("LiveScore API credentials not found. Please set the LIVESCORE_API_KEY and LIVESCORE_API_SECRET environment variables.")
        
        logger.info("Liga MX Bot initialized")

    async def check_for_updates(self) -> None:
        """Check for match updates and send notifications if needed"""
        logger.info("Checking for match updates...")
        
        try:
            # Get live Liga MX matches
            matches = self.livescore_client.get_liga_mx_matches(live_only=True)
            
            if not matches:
                logger.info("No live Liga MX matches found")
                return
                
            # Get active match IDs
            active_match_ids = [match.get("id") for match in matches if match.get("id")]
            
            # Clear finished matches from tracker
            self.match_tracker.clear_finished_matches(active_match_ids)
            
            # Process each match
            for match in matches:
                match_id = match.get("id")
                
                if not match_id:
                    continue
                    
                # Get match details, events, and statistics
                match_details = self.livescore_client.get_match_details(match_id)
                match_events = self.livescore_client.get_match_events(match_id)
                match_statistics = self.livescore_client.get_match_statistics(match_id)
                
                if not match_details:
                    logger.warning(f"Failed to get details for match {match_id}")
                    continue
                    
                # Update match state and check for changes
                has_changes = self.match_tracker.update_match_state(
                    match_id,
                    match_details,
                    match_events,
                    match_statistics
                )
                
                # If there are significant changes, send a notification
                if has_changes:
                    logger.info(f"Significant changes detected for match {match_id}")
                    
                    # Format the message
                    message = self.formatter.format_match_update(
                        match_details,
                        match_events,
                        match_statistics
                    )
                    
                    # Send the message to Telegram
                    await self.telegram_client.send_message(message)
        
        except Exception as e:
            logger.error(f"Error checking for match updates: {e}")

    async def start(self) -> None:
        """Start the Liga MX Bot"""
        logger.info("Starting Liga MX Bot...")
        
        # Schedule the update check
        self.scheduler.add_job(
            self.check_for_updates,
            'interval',
            seconds=UPDATE_INTERVAL,
            id='check_updates'
        )
        
        # Start the scheduler
        self.scheduler.start()
        
        try:
            # Keep the main thread alive
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Stopping Liga MX Bot...")
            self.scheduler.shutdown()


async def test_bot() -> None:
    """Test the bot by sending a sample message"""
    logger.info("Testing bot...")
    
    # Create clients
    livescore_client = LiveScoreClient()
    telegram_client = TelegramClient()
    formatter = MatchFormatter()
    
    # Create a sample match update
    sample_match = {
        "competition": {"name": "Liga MX"},
        "round": {"name": "Jornada 10"},
        "venue": {"name": "Estadio Azteca"},
        "home_name": "Club América",
        "away_name": "Guadalajara",
        "score": "2-1",
        "status": "IN_PLAY",
        "minute": "75"
    }
    
    sample_events = [
        {
            "id": "1",
            "type": "goal",
            "minute": "23",
            "player": "Henry Martín",
            "home_away": "h"
        },
        {
            "id": "2",
            "type": "goal",
            "minute": "45",
            "player": "Alexis Vega",
            "home_away": "a"
        },
        {
            "id": "3",
            "type": "goal",
            "minute": "67",
            "player": "Richard Sánchez",
            "home_away": "h"
        },
        {
            "id": "4",
            "type": "yellowcard",
            "minute": "34",
            "player": "Fernando Beltrán",
            "home_away": "a"
        },
        {
            "id": "5",
            "type": "substitution",
            "minute": "60",
            "player": "Álvaro Fidalgo",
            "player_in": "Jonathan dos Santos",
            "home_away": "h"
        }
    ]
    
    sample_statistics = {
        "possession": {"home": "58", "away": "42"},
        "shots_on_target": {"home": "7", "away": "3"},
        "corners": {"home": "5", "away": "2"}
    }
    
    # Format the message
    message = formatter.format_match_update(
        sample_match,
        sample_events,
        sample_statistics
    )
    
    # Send the message to Telegram
    success = await telegram_client.send_message(message)
    
    if success:
        logger.info("Test message sent successfully")
    else:
        logger.error("Failed to send test message")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Liga MX Telegram Bot")
    parser.add_argument("--test", action="store_true", help="Send a test message and exit")
    args = parser.parse_args()
    
    if args.test:
        # Run the test
        asyncio.run(test_bot())
    else:
        # Start the bot
        bot = LigaMXBot()
        asyncio.run(bot.start())
