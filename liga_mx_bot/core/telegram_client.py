"""
Telegram client for sending match notifications
"""
import logging
from typing import Optional
from telegram import Bot
from telegram.constants import ParseMode

from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramClient:
    """Client for sending notifications to Telegram"""

    def __init__(self, token: str = TELEGRAM_BOT_TOKEN, chat_id: str = TELEGRAM_CHAT_ID):
        """Initialize the Telegram client

        Args:
            token: Telegram bot token
            chat_id: Telegram chat ID to send messages to
        """
        self.token = token
        self.chat_id = chat_id
        
        if not token:
            logger.error("Telegram bot token not found. Please set the TELEGRAM_BOT_TOKEN environment variable.")
            self.bot = None
        elif not chat_id:
            logger.error("Telegram chat ID not found. Please set the TELEGRAM_CHAT_ID environment variable.")
            self.bot = None
        else:
            self.bot = Bot(token=token)
            logger.info("Telegram bot initialized successfully")

    async def send_message(self, message: str) -> bool:
        """Send a message to the Telegram chat

        Args:
            message: Message to send

        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.bot or not self.chat_id:
            logger.error("Cannot send message: Telegram bot not properly initialized")
            return False

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            logger.info("Message sent to Telegram successfully")
            return True
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return False
