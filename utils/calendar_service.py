import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_CALENDAR_ID, GOOGLE_CREDENTIALS_JSON

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TASHKENT_TZ = timezone(timedelta(hours=5))

UZBEK_WEEKDAYS = {
    0: "Dushanba",
    1: "Seshanba",
    2: "Chorshanba",
    3: "Payshanba",
    4: "Juma",
    5: "Shanba",
    6: "Yakshanba"
}

def get_calendar_service():
    """Google Calendar API servisini qaytarish (fayl yoki muhit o'zgaruvchisi orqali)"""
    import json
    creds_json_env = GOOGLE_CREDENTIALS_JSON
    try:
        if creds_json_env:
            info = json.loads(creds_json_env)
            creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            return build('calendar', 'v3', credentials=creds, cache_discovery=False)
        elif os.path.exists(GOOGLE_CREDENTIALS_FILE):
            creds = service_account.Credentials.from_service_account_file(
                str(GOOGLE_CREDENTIALS_FILE), scopes=SCOPES
            )
            return build('calendar', 'v3', credentials=creds, cache_discovery=False)
        else:
            logger.error(f"Google credentials topilmadi: {GOOGLE_CREDENTIALS_FILE}")
            return None
    except Exception as e:
        logger.error(f"Google Calendar servisini yaratishda xatolik: {e}")
        return None

def get_weekly_events(calendar_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Joriy haftaning (Dushanbadan Yakshanbagacha) barcha voqealarini Google Kalendardan olish.
    """
    cal_id = calendar_id or GOOGLE_CALENDAR_ID
    if not cal_id:
        return {
            "success": False,
            "error": "CALENDAR_NOT_CONFIGURED",
            "message": "Google Calendar ID hali sozlanmagan."
        }

    service = get_calendar_service()
    if not service:
        return {
            "success": False,
            "error": "SERVICE_ERROR",
            "message": "Google Calendar servisi bilan bog'lanib bo'lmadi."
        }

    try:
        now = datetime.now(TASHKENT_TZ)
        # Agar bugun yakshanba bo'lsa, ertangi kundan boshlab kelasi haftani ham qamrab olamiz
        if now.weekday() == 6: # Yakshanba
            target_monday = now + timedelta(days=1)
            monday_start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=TASHKENT_TZ)
            sunday_end = target_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
            week_display_start = target_monday.strftime("%d.%m")
            week_display_end = (target_monday + timedelta(days=6)).strftime("%d.%m.%Y")
        else:
            target_monday = now - timedelta(days=now.weekday())
            monday_start = datetime(target_monday.year, target_monday.month, target_monday.day, 0, 0, 0, tzinfo=TASHKENT_TZ)
            sunday_end = monday_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
            week_display_start = target_monday.strftime("%d.%m")
            week_display_end = (target_monday + timedelta(days=6)).strftime("%d.%m.%Y")

        time_min = monday_start.isoformat()
        time_max = sunday_end.isoformat()

        events_result = service.events().list(
            calendarId=cal_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        items = events_result.get('items', [])
        parsed_events = []

        for item in items:
            start = item.get('start', {})
            end = item.get('end', {})

            start_raw = start.get('dateTime') or start.get('date')
            end_raw = end.get('dateTime') or end.get('date')

            # Vaqtni formatlash
            if 'T' in start_raw:
                try:
                    dt_start = datetime.fromisoformat(start_raw)
                    # Toshkent vaqtiga o'girish
                    if dt_start.tzinfo:
                        dt_start = dt_start.astimezone(TASHKENT_TZ)
                    date_str = dt_start.strftime("%Y-%m-%d")
                    day_name = UZBEK_WEEKDAYS.get(dt_start.weekday(), "")
                    time_str = dt_start.strftime("%H:%M")
                    
                    if end_raw and 'T' in end_raw:
                        dt_end = datetime.fromisoformat(end_raw).astimezone(TASHKENT_TZ)
                        time_str += f" – {dt_end.strftime('%H:%M')}"
                except Exception:
                    date_str = start_raw[:10]
                    day_name = ""
                    time_str = "Kun davomida"
            else:
                date_str = start_raw
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    day_name = UZBEK_WEEKDAYS.get(dt.weekday(), "")
                except Exception:
                    day_name = ""
                time_str = "Kun davomida"

            parsed_events.append({
                "id": item.get('id'),
                "summary": item.get('summary', "Ko'rik qabuli"),
                "description": item.get('description', ""),
                "location": item.get('location', ""),
                "date": date_str,
                "day_name": day_name,
                "time": time_str
            })

        return {
            "success": True,
            "events": parsed_events,
            "week_start": week_display_start,
            "week_end": week_display_end
        }

    except Exception as e:
        logger.error(f"Google Calendar voqealarini olishda xatolik: {e}")
        error_str = str(e)
        if "Not Found" in error_str:
            return {
                "success": False,
                "error": "CALENDAR_NOT_FOUND",
                "message": "Kiritilgan Calendar ID topilmadi yoki botga ulashilmagan."
            }
        return {
            "success": False,
            "error": "API_ERROR",
            "message": f"Kalendarni o'qishda xatolik yuz berdi: {e}"
        }

def format_weekly_schedule_text(data: Dict[str, Any]) -> str:
    """Olingan voqealarni Telegram xabari ko'rinishida formatlash"""
    if not data.get("success"):
        error = data.get("error")
        if error == "CALENDAR_NOT_CONFIGURED":
            return (
                "👩‍⚕️ <b>Nazokat Mirsobitovnaning Ko'rik Grafigi</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "ℹ️ <i>Hozirda Google Calendar to'liq sozlanish jarayonida.</i>\n\n"
                "Nazokat opaning eng yaqin qabul vaqtini bilish yoki qabulga yozilish uchun "
                "Call-markazimiz bilan bog'lanishingiz yoki to'g'ridan-to'g'ri filialga yozilishingiz mumkin:\n\n"
                "☎️ +998 90 174 82 84\n"
                "💬 @Rixsiyeva81"
            )
        elif error == "CALENDAR_NOT_FOUND":
            return (
                "👩‍⚕️ <b>Nazokat Mirsobitovnaning Ko'rik Grafigi</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ <i>Kalendar topilmadi yoki botga ruxsat berilmagan.</i>\n\n"
                "Administrator kalendarni bot emailiga ulashi lozim:\n"
                "<code>bolalar-massaji@bolalar-massaji-bot.iam.gserviceaccount.com</code>"
            )
        else:
            return (
                "👩‍⚕️ <b>Nazokat Mirsobitovnaning Ko'rik Grafigi</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ <i>Kalendar ma'lumotlarini yuklashda vaqtinchalik uzilish yuz berdi.</i>\n"
                "Iltimos, birozdan so'ng qayta urinib ko'ring yoki Call-markazga murojaat qiling."
            )

    events = data.get("events", [])
    week_start = data.get("week_start")
    week_end = data.get("week_end")

    if not events:
        return (
            f"👩‍⚕️ <b>Nazokat Mirsobitovnaning Haftalik Ko'rik Grafigi</b>\n"
            f"🗓 <i>Hafta: {week_start} — {week_end}</i>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 <b>Ushbu hafta uchun ko'rik kunlari hali kiritilmagan.</b>\n\n"
            "Nazokat opaning qabul kunlari tez orada yangilanadi. Aniq ma'lumot olish yoki navbatga yozilish uchun administratorga murojaat qilishingiz mumkin:\n\n"
            "💬 Administrator: @Rixsiyeva81\n"
            "☎️ Call-markaz: +998 90 174 82 84"
        )

    text = (
        f"👩‍⚕️ <b>Nazokat Mirsobitovnaning Haftalik Ko'rik Grafigi</b>\n"
        f"🗓 <i>Hafta: {week_start} — {week_end}</i>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for ev in events:
        day_str = f"🗓 <b>{ev['day_name']}</b> ({ev['date'][8:10]}.{ev['date'][5:7]}):"
        summary_str = f"🏥 <b>{ev['summary']}</b>"
        time_str = f"⏰ <b>Vaqt:</b> {ev['time']}"
        loc_str = f"📍 <i>{ev['location']}</i>" if ev.get('location') else ""
        desc_str = f"📝 <i>{ev['description']}</i>" if ev.get('description') else ""

        entry_parts = [day_str, summary_str, time_str]
        if loc_str:
            entry_parts.append(loc_str)
        if desc_str:
            entry_parts.append(desc_str)

        text += "\n".join(entry_parts) + "\n\n"

    text += (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Ko'rikka yozilish yoki filial bilan bog'lanish uchun quyidagi tugmalardan foydalaning:</i>"
    )

    return text
