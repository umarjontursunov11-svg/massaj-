import logging
from typing import Dict, Any
from aiogram import Bot
from aiogram.types import User
from config import GROUP_ID, ADMIN_IDS
from keyboards.inline_kb import get_admin_app_action_kb

logger = logging.getLogger(__name__)

async def notify_new_appointment(bot: Bot, app_id: int, data: Dict[str, Any], user: User):
    """Yangi ariza kelganda guruhga va adminlarga xabarnoma yuborish"""
    service_title = data.get('service_title')
    service_line = f"💆‍♂️ <b>Xizmat:</b> {service_title}\n" if service_title else ""
    specialist_name = data.get('specialist_name')
    spec_line = f"👩‍⚕️ <b>Mutaxassis:</b> {specialist_name}\n" if specialist_name else ""
    child_age = data.get('child_age')
    child_info = f"{data['child_name']} ({child_age})" if child_age and child_age != "Ko'rsatilmagan" else data['child_name']

    branch_addr = data.get('branch_address')
    addr_line = f"🏢 <b>Filial manzili:</b> {branch_addr}\n" if branch_addr else ""
    branch_phone = data.get('branch_phone')
    branch_phone_line = f"☎️ <b>Filial mas'ul telefoni:</b> {branch_phone}\n" if branch_phone else ""
    branch_manager = data.get('branch_telegram_username')
    manager_line = f"👩‍⚕️ <b>Filial mas'uli:</b> {branch_manager}\n" if branch_manager else ""

    is_ortho = data.get("booking_type") == "orthopedic"
    session_dates = data.get("session_dates")

    if is_ortho:
        header_text = f"🔔 <b>YANGI ARIZA: BOLALAR ORTOPEDI KO'RIGI! #{app_id}</b>"
        dates_line = (
            f"🦴 <b>Xizmat:</b> Bolalar ortopedi ko'rigi va diagnostikasi\n"
            f"📅 <b>Ko'rik sanasi:</b> {data.get('preferred_date', '')}\n"
        )
        time_label = "Qabul vaqti"
    elif session_dates and len(session_dates) > 1:
        header_text = f"🔔 <b>YANGI QABULGA YOZILISH ARIZASI! #{app_id}</b>"
        dates_line = (
            f"📚 <b>Muolaja:</b> 10 kunlik massaj kursi\n"
            f"📅 <b>Kurs davri (10 ish kuni):</b> {session_dates[0]} — {session_dates[-1]}\n"
        )
        time_label = "Har kungi vaqti"
    else:
        header_text = f"🔔 <b>YANGI QABULGA YOZILISH ARIZASI! #{app_id}</b>"
        dates_line = f"📅 <b>Qabul kuni:</b> {data.get('preferred_date', '')}\n"
        time_label = "Qabul vaqti"

    admin_notification = (
        f"{header_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏥 <b>Filial:</b> {data['branch_name']}\n"
        f"{addr_line}"
        f"{branch_phone_line}"
        f"{manager_line}"
        f"────────────────────\n"
        f"👤 <b>Mijoz (Ota-ona):</b> {data['parent_name']}\n"
        f"👶 <b>Farzandning ismi:</b> {child_info}\n"
        f"📞 <b>Mijoz telefoni:</b> {data['phone']}\n"
        f"{dates_line}"
        f"🕒 <b>{time_label}:</b> {data['preferred_time']}\n"
        f"{service_line}"
        f"{spec_line}"
        f"────────────────────\n"
        f"💬 <b>Telegram:</b> @{user.username or 'mavjud emas'} (ID: <code>{user.id}</code>)\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    reply_markup = get_admin_app_action_kb(app_id)

    # 1. Guruhga yuborish
    if GROUP_ID:
        candidate_ids = [GROUP_ID]
        raw_str = str(GROUP_ID).lstrip("-")
        
        # Agar -100 prefiksi bo'lmasa, uni ham sinab ko'ramiz
        if not str(GROUP_ID).startswith("-100"):
            candidate_ids.append(int(f"-100{raw_str}"))
        if not str(GROUP_ID).startswith("-"):
            candidate_ids.append(int(f"-{raw_str}"))

        group_sent = False
        for cid in candidate_ids:
            try:
                await bot.send_message(
                    chat_id=cid,
                    text=admin_notification,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
                logger.info(f"Ariza #{app_id} guruhga (ID: {cid}) muvaffaqiyatli yuborildi.")
                group_sent = True
                break
            except Exception as e:
                logger.debug(f"Guruh {cid} ga yuborish sinovi: {e}")

        if not group_sent:
            logger.warning(
                f"Ariza #{app_id} guruhga ({GROUP_ID}) yuborilmadi. "
                f"Iltimos, botni guruhga a'zo qiling va xabar yozish ruxsatini bering!"
            )

    # 2. Shaxsiy adminlarga yuborish
    for admin_id in ADMIN_IDS:
        if admin_id == GROUP_ID:
            continue
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_notification,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        except Exception:
            pass

async def notify_course_application(bot: Bot, app_id: int, full_name: str, phone: str, user: User):
    """O'quv kursi arizasi kelganda guruhga va adminlarga xabar berish"""
    notification = (
        f"🎓 <b>YANGI O'QUV KURSI ARIZASI! #{app_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📚 <b>Kurs:</b> Bolalar massaji kursi (1 oylik)\n"
        f"📍 <b>Manzil:</b> Qushbegi 10A filiali\n"
        f"⏰ <b>Dars vaqti:</b> Seshanba – Shanba, 10:00 – 13:00\n"
        f"────────────────────\n"
        f"👤 <b>Mijoz:</b> {full_name}\n"
        f"📞 <b>Telefon:</b> <code>{phone}</code>\n"
        f"💬 <b>Telegram:</b> @{user.username or 'mavjud emas'} (ID: <code>{user.id}</code>)\n"
        f"❓ <b>Murojaat maqsadi:</b> Kurs narxini bilish va ro'yxatdan o'tish\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    # 1. Guruhga yuborish
    if GROUP_ID:
        candidate_ids = [GROUP_ID]
        raw_str = str(GROUP_ID).lstrip("-")
        if not str(GROUP_ID).startswith("-100"):
            candidate_ids.append(int(f"-100{raw_str}"))
        if not str(GROUP_ID).startswith("-"):
            candidate_ids.append(int(f"-{raw_str}"))

        for cid in candidate_ids:
            try:
                await bot.send_message(
                    chat_id=cid,
                    text=notification,
                    parse_mode="HTML"
                )
                logger.info(f"Kurs arizasi #{app_id} guruhga muvaffaqiyatli yuborildi.")
                break
            except Exception as e:
                logger.debug(f"Guruh {cid} ga kurs arizasini yuborish sinovi: {e}")

    # 2. Shaxsiy adminlarga yuborish
    for admin_id in ADMIN_IDS:
        if admin_id == GROUP_ID:
            continue
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=notification,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Admin {admin_id} ga kurs arizasini yuborishda xatolik: {e}")

async def notify_session_response(bot: Bot, session: Dict[str, Any], response_type: str):
    """Mijoz seans eslatmasiga javob berganda guruhga va adminlarga xabar berish"""
    status_map = {
        "on_time": ("✅ O'z vaqtida boradi", "Mijoz belgilangan vaqtda yetib kelishini tasdiqladi."),
        "late_15": ("⏳ 15 daqiqa kechikadi", "Mijoz 15 daqiqa kechikishi haqida xabar qoldirdi."),
        "cannot_come": ("❌ Bugun kela olmaydi", "Mijoz bugungi seansga kela olmasligini bildirdi. Aloqaga chiqish tavsiya etiladi.")
    }
    status_title, status_desc = status_map.get(response_type, ("ℹ️ Noma'lum", ""))

    manager_tg = session.get("branch_telegram") or "@Rixsiyeva81"

    notification = (
        f"⚡️ <b>MIJOZDAN QABUL BO'YICHA XABAR!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Ariza raqami:</b> #{session.get('appointment_id')} (Seans: {session.get('session_number')}/10)\n"
        f"🏥 <b>Filial:</b> {session.get('branch_name')}\n"
        f"👩‍⚕️ <b>Filial mas'uli:</b> {manager_tg}\n"
        f"────────────────────\n"
        f"👤 <b>Mijoz:</b> {session.get('parent_name')}\n"
        f"👶 <b>Farzand:</b> {session.get('child_name')}\n"
        f"📞 <b>Telefon:</b> <code>{session.get('phone')}</code>\n"
        f"⏰ <b>Bugungi qabul vaqti:</b> {session.get('session_time')}\n"
        f"📅 <b>Sana:</b> {session.get('session_date')}\n"
        f"────────────────────\n"
        f"📊 <b>Mijoz javobi:</b> <b>{status_title}</b>\n"
        f"📝 <i>{status_desc}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    # 1. Guruhga yuborish
    if GROUP_ID:
        candidate_ids = [GROUP_ID]
        raw_str = str(GROUP_ID).lstrip("-")
        if not str(GROUP_ID).startswith("-100"):
            candidate_ids.append(int(f"-100{raw_str}"))
        if not str(GROUP_ID).startswith("-"):
            candidate_ids.append(int(f"-{raw_str}"))

        for cid in candidate_ids:
            try:
                await bot.send_message(
                    chat_id=cid,
                    text=notification,
                    parse_mode="HTML"
                )
                logger.info(f"Seans #{session.get('session_id')} javob bildirishnomasi guruhga yuborildi.")
                break
            except Exception as e:
                logger.debug(f"Guruh {cid} ga bildirishnoma yuborish sinovi: {e}")

    # 2. Shaxsiy adminlarga yuborish
    for admin_id in ADMIN_IDS:
        if admin_id == GROUP_ID:
            continue
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=notification,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Admin {admin_id} ga bildirishnoma yuborishda xatolik: {e}")


