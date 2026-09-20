import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from aiogram import Bot

from database.db import (
    get_today_pending_sessions,
    mark_session_reminder_sent
)
from keyboards.inline_kb import get_reminder_action_kb

logger = logging.getLogger(__name__)

# Toshkent vaqt mintaqasi (UTC+5)
TASHKENT_TZ = timezone(timedelta(hours=5))

def calculate_10_sessions(start_date_str: str) -> List[str]:
    """
    Boshlanish sanasidan boshlab ketma-ket 10 ta ish kunini hisoblash.
    Yakshanba (dam olish kuni) avtomatik o'tkazib yuboriladi.
    """
    dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    sessions = []
    curr = dt
    while len(sessions) < 10:
        # 6 = Yakshanba (dam olish kuni)
        if curr.weekday() != 6:
            sessions.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)
    return sessions

async def reminder_worker(bot: Bot):
    """
    Fondagi rejalashtiruvchi (Background Worker):
    Har daqiqada bugungi seanslarni tekshiradi va seans boshlanishidan
    kamida 2 soat oldin (120 daqiqa) mijozga eslatma xabarini yuboradi.
    """
    logger.info("Avtomatik eslatma (Reminder worker) ishga tushdi.")
    
    while True:
        try:
            now = datetime.now(TASHKENT_TZ)
            today_str = now.strftime("%Y-%m-%d")
            
            pending_sessions = await get_today_pending_sessions(today_str)
            
            for session in pending_sessions:
                session_id = session["session_id"]
                session_time = session.get("session_time", "")
                
                # Seans boshlanish soatini ajratib olish (masalan: "10:00 - 11:00" -> "10:00")
                try:
                    start_time_part = session_time.split("-")[0].strip()
                    hour, minute = map(int, start_time_part.split(":"))
                    session_dt = datetime(now.year, now.month, now.day, hour, minute, tzinfo=TASHKENT_TZ)
                    diff_minutes = (session_dt - now).total_seconds() / 60
                except Exception as parse_err:
                    logger.warning(f"Seans #{session_id} vaqtini tahlil qilishda xatolik: {parse_err}")
                    diff_minutes = 0

                # Kamida 2 soat oldin (<= 120 daqiqa) va seans hali tugamagan bo'lsa (>-60 daqiqa)
                if diff_minutes <= 120 and diff_minutes > -60:
                    user_id = session["user_id"]
                    manager_tg = session.get("branch_telegram") or "@Nazokat79_Admin"
                    
                    reminder_text = (
                        f"🔔 <b>BUGUNGI QABUL ESLATMASI! (Kun #{session['session_number']}/10)</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👶 <b>Farzandingiz:</b> {session['child_name']}\n"
                        f"🏥 <b>Filial:</b> {session['branch_name']}\n"
                        f"🏢 <b>Manzil:</b> {session['branch_address']}\n"
                        f"⏰ <b>Bugungi qabul vaqti:</b> {session['session_time']}\n"
                        f"☎️ <b>Filial telefoni:</b> <code>{session['branch_phone']}</code>\n"
                        f"👩‍⚕️ <b>Mas'ul xodim:</b> {manager_tg}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"<i>Bugun belgilangan vaqtda kela olasizmi? Iltimos, holatingizni tanlang:</i>"
                    )
                    
                    try:
                        await bot.send_message(
                            chat_id=user_id,
                            text=reminder_text,
                            parse_mode="HTML",
                            reply_markup=get_reminder_action_kb(session_id)
                        )
                        logger.info(f"Mijoz {user_id} ga seans #{session_id} eslatmasi yuborildi.")
                    except Exception as send_err:
                        logger.error(f"Mijoz {user_id} ga eslatma yuborishda xatolik: {send_err}")
                        
                    # Yuborilgan deb belgilash (qayta-qayta yuborilmasligi uchun)
                    await mark_session_reminder_sent(session_id)
                    
        except Exception as e:
            logger.error(f"Reminder worker xatoligi: {e}", exc_info=True)
            
        # Keyingi tekshiruvgacha 60 soniya kutish
        await asyncio.sleep(60)
