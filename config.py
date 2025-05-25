import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Google Sheets configuration
GOOGLE_CREDS_FILE = "data/service_account.json"
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Лист1")  # Default sheet name

# Calculation constants
DEFAULT_DIVISOR_FL = 150
DEFAULT_DIVISOR_UL = 300
UNIQUE_OBJECT_DIVISOR = 300
UNIQUE_OBJECT_MAX_PERCENTAGE = 0.05  # 5% max for unique objects 