import html
from datetime import datetime, timezone, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database.db import add_or_update_user, get_user_by_id, get_all_services
from keyboards.default_kb import get_main_menu_kb
from keyboards.inline_kb import get_welcome_quick_actions_kb, get_working_hours_kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Bot boshlanishi /start: Nazokat Mirsobitovna rasmiy salomlashuv xabari"""
    await state.clear()
    
    user = message.from_user
    is_admin = user.id in ADMIN_IDS
    
    # Bazaga foydalanuvchini qo'shish yoki yangilash
    await add_or_update_user(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username
    )
    
    user_name = html.escape(user.full_name or user.first_name or "Foydalanuvchi")
    
    welcome_text = (
        f"Assalomu aleykum <b>{user_name}</b>\n"
        f"Nazokat Mirsobitovnaning bolalar massaji rasmiy telegram botiga xush kelibsiz\n\n"
        f"“Bolalar Massaji Nazokat79” — bolalar salomatligi va rivojlanishiga e’tibor qaratadigan, "
        f"Toshkent shahri bo‘ylab faoliyat yurituvchi bolalar massaji markazlari tarmog‘i.\n\n"
        f"Bugungi kunda filiallarimiz shahar bo‘ylab 13 ta qulay va yaxshi joylashgan lokatsiyada faoliyat yuritadi. "
        f"Sizga eng yaqin filialimizni tanlab, farzandingiz uchun qulay sharoitda xizmat olishingiz mumkin.\n\n"
        f"Markazimiz rahbari — Nazokat Mirsobitovna, vrach-osteopat va Yumeiho terapevt.\n\n"
        f"Ular A. Andreanov nomidagi Osteopatiya institutini tamomlagan bo‘lib, bolalar bilan ishlash sohasida 27 yillik tajribaga ega.\n\n"
        f"Shuningdek, Nazokat Mirsobitovna taniqli “Bübchen” brendining O‘zbekistondagi ambassadori hisoblanadi.\n\n"
        f"27 yillik tajriba, professional yondashuv va bolalarga bo‘lgan mehr — “Bolalar Massaji Nazokat79”ning asosiy qadriyatlaridir."
    )
    
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_welcome_quick_actions_kb()
    )
    
    # Asosiy doimiy menyuni ham o'rnatish
    await message.answer(
        "💡 <i>Quyidagi menyu orqali kerakli bo'limni tanlashingiz mumkin:</i>",
        parse_mode="HTML",
        reply_markup=get_main_menu_kb(is_admin=is_admin)
    )

# --- Tezkor inline tugmalar uchun callback handlerlar ---
@router.callback_query(F.data == "start_booking_from_welcome")
async def start_booking_from_welcome_cb(callback: CallbackQuery, state: FSMContext):
    """Salomlashuvdan to'g'ridan-to'g'ri yozilishga o'tish"""
    await callback.answer()
    from handlers.booking import start_booking
    await start_booking(callback.message, state)

@router.callback_query(F.data.in_(["view_services_quick", "view_course_info"]))
async def view_course_quick_cb(callback: CallbackQuery):
    """Tezkor kurs ma'lumotlarini ko'rsatish"""
    await callback.answer()
    from handlers.services import show_massage_course_info
    await show_massage_course_info(callback.message)

@router.callback_query(F.data == "view_about_quick")
async def view_about_quick_cb(callback: CallbackQuery):
    """Tezkor massaj ma'lumotlarini ko'rsatish"""
    await callback.answer()
    from handlers.services import about_baby_massage
    await about_baby_massage(callback.message)

@router.callback_query(F.data == "view_contact_quick")
async def view_contact_quick_cb(callback: CallbackQuery):
    """Tezkor aloqa ma'lumotlarini ko'rsatish"""
    await callback.answer()
    await contact_us(callback.message)

@router.callback_query(F.data == "view_working_hours_quick")
async def view_working_hours_quick_cb(callback: CallbackQuery):
    """Tezkor ish vaqtini ko'rsatish"""
    await callback.answer()
    await show_working_hours(callback.message)

@router.callback_query(F.data == "view_doctor_schedule")
async def view_doctor_schedule_quick_cb(callback: CallbackQuery):
    """Tezkor Nazokat opa grafigini ko'rsatish"""
    await callback.answer()
    from handlers.doctor_schedule import show_doctor_schedule
    await show_doctor_schedule(callback.message)


# --- Standart buyruqlar va menyu handlerlari ---
@router.message(F.text == "❌ Bekor qilish")
async def cancel_action(message: Message, state: FSMContext):
    """Amalni bekor qilish"""
    await state.clear()
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(
        "❌ Amaliyot bekor qilindi. Bosh menyudasiz.",
        reply_markup=get_main_menu_kb(is_admin=is_admin)
    )

@router.callback_query(F.data == "cancel_booking")
async def cancel_booking_cb(callback: CallbackQuery, state: FSMContext):
    """Inline orqali bekor qilish"""
    await state.clear()
    await callback.answer("Amal bekor qilindi")
    is_admin = callback.from_user.id in ADMIN_IDS
    await callback.message.delete()
    await callback.message.answer(
        "❌ Qabulga yozilish bekor qilindi. Bosh menyudasiz.",
        reply_markup=get_main_menu_kb(is_admin=is_admin)
    )

@router.message(F.text.in_(["🕒 Ish vaqti", "Ish vaqti"]))
async def show_working_hours(message: Message):
    """Markaz va filiallar ish vaqti ma'lumotlarini ko'rsatish"""
    text = (
        "🕒 <b>«Bolalar Massaji Nazokat79» Markazi Ish Tartibi</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🗓 <b>Qabul va ish vaqtlari:</b>\n"
        "• <b>Dushanbadan – Jumagacha:</b> 09:00 dan 17:00 gacha\n"
        "• <b>Shanba kuni:</b> 10:00 dan 15:00 gacha\n"
        "• <b>Yakshanba:</b> Dam olish kuni 🏖\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏥 <b>Barcha 12 ta filiallarimiz ushbu jadval asosida faoliyat yuritadi.</b>\n\n"
        "<i>Farzandingizni o'zingizga qulay vaqt va filialga yozdirish uchun quyidagi tugmalardan foydalanishingiz mumkin:</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_working_hours_kb())

@router.message(F.text == "📞 Bog'lanish")
async def contact_us(message: Message):
    """Bog'lanish va aloqa ma'lumotlari"""
    text = (
        "📞 <b>«Bolalar Massaji Nazokat79» Markazi Aloqa Ma'lumotlari:</b>\n\n"
        "🏢 <b>Yagona Call-Markaz:</b>\n"
        "☎️ +998 71 200 11 00\n"
        "📱 +998 90 123 45 67\n\n"
        "🕒 <b>Ish tartibi:</b>\n"
        "• Dushanbadan Jumagacha: 09:00 dan 17:00 gacha\n"
        "• Shanba kuni: 10:00 dan 15:00 gacha\n"
        "<i>(Yakshanba — dam olish kuni)</i>\n\n"
        "💬 <b>Telegram Administrator:</b>\n"
        "👉 @Nazokat79_Admin\n\n"
        "📍 Toshkent shahri bo‘ylab 12 ta qulay filiallarimiz faoliyat yuritmoqda. "
        "Eng yaqin filialni bilish uchun <b>«🏥 Filiallar va Manzillar»</b> tugmasini bosing."
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Yordam buyrug'i"""
    text = (
        "ℹ️ <b>Botdan foydalanish bo'yicha qo'llanma:</b>\n\n"
        "🔹 <b>🏥 Filiallar va Manzillar</b> — Toshkent tumanlari bo'yicha filiallar ro'yxati, manzili, telefonlari va xaritadagi lokatsiyasi.\n"
        "🔹 <b>📝 Qabulga yozilish</b> — Filial tanlab, farzandingizni 10 kunlik massaj kursiga yozdirish.\n"
        "🔹 <b>👩‍⚕️ Nazokat opa ko'rik grafigi</b> — Nazokat opaning haftalik ko'rik grafigi (Google Calendar).\n"
        "🔹 <b>🌸 Bolalar massaj kursi</b> — Bolalar massaji kursi dasturi va narxi haqida ma'lumot.\n"
        "🔹 <b>🕒 Ish vaqti</b> — Markaz va filiallar ish kunlari hamda soatlarini ko'rish.\n"
        "🔹 <b>📰 Yangiliklar va Chegirmalar</b> — Markazimiz aksiyalari va yangiliklari.\n"
        "🔹 <b>👶 Bolalar massaji haqida</b> — Ota-onalar uchun foydali maslahatlar va tibbiy ko'rsatmalar.\n"
        "🔹 <b>📞 Bog'lanish</b> — Yagona Call-markaz va admin kontaktlari."
    )

    await message.answer(text, parse_mode="HTML")
