import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from utils.calendar_service import get_weekly_events, format_weekly_schedule_text
from keyboards.inline_kb import get_doctor_schedule_kb

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.in_([
    "👩‍⚕️ Nazokat opa ko'rik grafigi",
    "Nazokat opa ko'rik grafigi",
    "📅 Nazokat opa ko'rik grafigi",
    "📅 Nazokat opa qabul grafigi",
    "Nazokat opa qabul grafigi"
]))
async def show_doctor_schedule(message: Message):
    """Nazokat opaning haftalik ko'rik jadvalini ko'rsatish"""
    data = get_weekly_events()
    text = format_weekly_schedule_text(data)
    await message.answer(text, parse_mode="HTML", reply_markup=get_doctor_schedule_kb())

@router.callback_query(F.data == "view_doctor_schedule")
async def view_doctor_schedule_cb(callback: CallbackQuery):
    """Inline tugma orqali grafikni ko'rish"""
    await callback.answer()
    data = get_weekly_events()
    text = format_weekly_schedule_text(data)
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_doctor_schedule_kb())

@router.callback_query(F.data == "refresh_doctor_schedule")
async def refresh_doctor_schedule_cb(callback: CallbackQuery):
    """Grafikni qayta yangilash"""
    await callback.answer("Jadval yangilanmoqda...")
    data = get_weekly_events()
    text = format_weekly_schedule_text(data)
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_doctor_schedule_kb())
    except Exception:
        pass
