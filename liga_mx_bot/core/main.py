"""
Main application for Liga MX Telegram Bot
"""
import asyncio
import logging
import time
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.config import UPDATE_INTERVAL
from core.livescore_client import LiveScoreClient
from core.telegram_client import TelegramClient
from core.formatter import MatchFormatter
from core.match_tracker import MatchTracker

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

    async def send_standings(self) -> None:
        """Send current Liga MX standings to Telegram"""
        logger.info("Sending Liga MX standings...")
        
        try:
            # Get the league table
            standings = self.livescore_client.get_league_table()
            
            if not standings:
                logger.warning("Failed to get Liga MX standings")
                return
            
            # Format the standings message
            message = self.formatter.format_standings(standings)
            
            # Send the message to Telegram
            await self.telegram_client.send_message(message)
            logger.info("Standings message sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending standings: {e}")
    
    async def send_top_scorers(self) -> None:
        """Send Liga MX top scorers to Telegram"""
        logger.info("Sending Liga MX top scorers...")
        
        try:
            # Get the top scorers
            scorers = self.livescore_client.get_top_scorers()
            
            if not scorers:
                logger.warning("Failed to get Liga MX top scorers")
                return
            
            # Format the top scorers message
            message = self.formatter.format_top_scorers(scorers)
            
            # Send the message to Telegram
            await self.telegram_client.send_message(message)
            logger.info("Top scorers message sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending top scorers: {e}")

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


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Liga MX Telegram Bot")
    parser.add_argument("--standings", action="store_true", help="Send current standings and exit")
    parser.add_argument("--scorers", action="store_true", help="Send top scorers and exit")
    args = parser.parse_args()
    
    bot = LigaMXBot()
    
    if args.standings:
        # Send standings and exit
        asyncio.run(bot.send_standings())
    elif args.scorers:
        # Send top scorers and exit
        asyncio.run(bot.send_top_scorers())
    else:
        # Start the bot
        asyncio.run(bot.start())
