import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Admin ID larini list ko'rinishida olish
admin_ids_raw = os.getenv("ADMIN_IDS", "").strip()
ADMIN_IDS = []
if admin_ids_raw:
    for item in admin_ids_raw.split(","):
        item = item.strip()
        if item.lstrip("-").isdigit():
            ADMIN_IDS.append(int(item))

# Arizalar kelib tushadigan guruh ID si
group_id_raw = os.getenv("GROUP_ID", "").strip()
GROUP_ID = None
if group_id_raw and group_id_raw.lstrip("-").isdigit():
    GROUP_ID = int(group_id_raw)

DB_NAME = os.getenv("DB_NAME", "massage_bot.db")
DB_PATH = BASE_DIR / DB_NAME

# Google Calendar sozlamalari
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "").strip()
GOOGLE_CREDENTIALS_FILE = BASE_DIR / "google_credentials.json"

