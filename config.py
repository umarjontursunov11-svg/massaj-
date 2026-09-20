import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

def get_env_any_case(key: str, *aliases, default: str = "") -> str:
    """Katta-kichik harflardan qat'i nazar muhit o'zgaruvchisini olish"""
    candidates = [key] + list(aliases)
    # 1. To'g'ridan-to'g'ri tekshirish
    for c in candidates:
        v = os.getenv(c)
        if v:
            return v.strip()
    # 2. Case-insensitive qidirish
    candidate_lowers = [c.lower() for c in candidates]
    for env_k, env_v in os.environ.items():
        if env_k.lower() in candidate_lowers and env_v:
            return env_v.strip()
    return default

BOT_TOKEN = get_env_any_case("BOT_TOKEN", "bot_token", "token")

# Admin ID larini list ko'rinishida olish (ADMIN_IDS, Admin_id, admin_id)
admin_ids_raw = get_env_any_case("ADMIN_IDS", "ADMIN_ID", "admin_ids", "admin_id", "admins")
ADMIN_IDS = []
if admin_ids_raw:
    for item in admin_ids_raw.split(","):
        item = item.strip()
        if item.lstrip("-").isdigit():
            ADMIN_IDS.append(int(item))

# Arizalar kelib tushadigan guruh ID si (GROUP_ID, group_id)
group_id_raw = get_env_any_case("GROUP_ID", "group_id")
GROUP_ID = None
if group_id_raw and group_id_raw.lstrip("-").isdigit():
    GROUP_ID = int(group_id_raw)

DB_NAME = get_env_any_case("DB_NAME", "db_name", default="massage_bot.db")
DB_PATH = BASE_DIR / DB_NAME

# Google Calendar sozlamalari
GOOGLE_CALENDAR_ID = get_env_any_case("GOOGLE_CALENDAR_ID", "google_calendar_id")
GOOGLE_CREDENTIALS_FILE = BASE_DIR / "google_credentials.json"
GOOGLE_CREDENTIALS_JSON = get_env_any_case("GOOGLE_CREDENTIALS_JSON", "google_credentials_json")


