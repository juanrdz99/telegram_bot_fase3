"""
Configuration settings for the Liga MX Telegram Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys and Tokens
LIVESCORE_API_KEY = os.getenv("LIVESCORE_API_KEY", "uVOrxTq8GBEsqYkw")
LIVESCORE_API_SECRET = os.getenv("LIVESCORE_API_SECRET", "mA8oe2jV0lolZ1DuXsVulmD2XhuogPUC")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7400623821:AAGKTnJtwsB8S_pKp2zgaOOqLxtxxqQeNCU")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1002322753499")

# API Endpoints
LIVESCORE_BASE_URL = "https://livescore-api.com/api-client"
LIVESCORE_MATCHES_ENDPOINT = f"{LIVESCORE_BASE_URL}/scores/live.json"
LIVESCORE_FIXTURES_ENDPOINT = f"{LIVESCORE_BASE_URL}/fixtures/matches.json"
LIVESCORE_MATCH_DETAILS_ENDPOINT = f"{LIVESCORE_BASE_URL}/scores/match.json"
LIVESCORE_EVENTS_ENDPOINT = f"{LIVESCORE_BASE_URL}/scores/events.json"
LIVESCORE_STATISTICS_ENDPOINT = f"{LIVESCORE_BASE_URL}/scores/statistics.json"
LIVESCORE_LEAGUE_TABLE_ENDPOINT = f"{LIVESCORE_BASE_URL}/leagues/table.json"
LIVESCORE_HISTORY_ENDPOINT = f"{LIVESCORE_BASE_URL}/scores/history.json"
LIVESCORE_TOPSCORERS_ENDPOINT = f"{LIVESCORE_BASE_URL}/competitions/topscorers.json"

# Liga MX Competition ID
LIGA_MX_COMPETITION_ID = "45"  # Found using find_competition_id.py
LIGA_MX_GROUP_ID = "3420"  # Group ID for Liga MX standings

# Update frequency in seconds
UPDATE_INTERVAL = 30

# Match status codes
MATCH_STATUS = {
    "NOT_STARTED": "NS",
    "IN_PLAY": "IN_PLAY",
    "HALF_TIME": "HT",
    "FINISHED": "FT",
    "POSTPONED": "POSTP",
    "CANCELED": "CANC"
}

# Event types
EVENT_TYPES = {
    "GOAL": "goal",
    "YELLOW_CARD": "yellowcard",
    "RED_CARD": "redcard",
    "SUBSTITUTION": "substitution"
}
