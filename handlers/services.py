from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database.db import (
    get_all_services,
    get_latest_news,
    create_course_application,
    add_or_update_user
)
from states.booking_states import CourseApplicationState
from keyboards.default_kb import get_main_menu_kb, get_phone_request_kb, get_cancel_kb
from keyboards.inline_kb import get_course_action_kb, get_course_confirm_kb

router = Router()

@router.message(F.text.in_([
    "🌸 Bolalar massaj kursi",
    "🌸 Bolalar massaji kursi",
    "Bolalar massaj kursi",
    "Bolalar massaji kursi",
    "💆‍♂️ Xizmatlar va Narxlar"
]))
async def show_massage_course_info(message: Message):
    """Bolalar massaji kursi haqida to'liq ma'lumot"""
    text = (
        "🌸 <b>Bolalar Massaji Kursi</b> 🌸\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📚 <b>Kurs davomiyligi:</b> 1 oy\n"
        "📅 <b>Dars kunlari:</b> Seshanba – Shanba\n"
        "⏰ <b>Vaqt:</b> 10:00 – 13:00\n"
        "📍 <b>Manzil:</b> Qushbegi 10A filiali\n\n"
        "✨ <b>Kurs dasturiga quyidagilar kiradi:</b>\n\n"
        "• 👩 Ayollar va bolalar massaji\n"
        "• 👶 Bolalar ortopedik va nevrologik massaji\n"
        "• 🦴 Ortoped darslari\n"
        "• 🩹 Hijoma va ignaterapiya\n"
        "• 🗣️ Logodeziatriya\n"
        "• 🤝 Imkoniyati cheklangan bolalar bilan ishlash\n"
        "• 💆‍♀️ Face fitness darslari\n\n"
        "📖 <b>10 kun nazariya + 20 kun amaliyot</b>\n\n"
        "🎓 <b>Kurs yakunida sertifikat taqdim etiladi.</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📩 <i>Batafsil ma’lumot va ro‘yxatdan o‘tish uchun quyidagi tugma orqali ariza qoldiring:</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_course_action_kb())

@router.callback_query(F.data == "view_course_info")
async def view_course_info_cb(callback: CallbackQuery):
    """Inline tugma orqali kurs ma'lumotini ko'rsatish"""
    await callback.answer()
    await show_massage_course_info(callback.message)

@router.callback_query(F.data == "apply_course_start")
async def apply_course_start_cb(callback: CallbackQuery, state: FSMContext):
    """Kursga ariza to'ldirishni boshlash"""
    await callback.answer()
    await state.clear()
    await state.set_state(CourseApplicationState.entering_name)
    
    text = (
        "📝 <b>«Bolalar Massaji Kursi»ga Ro'yxatdan O'tish</b>\n\n"
        "1️⃣-qadam: <b>Ism va familiyangizni kiriting:</b>\n"
        "<i>(Masalan: Madina Karimova)</i>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_cancel_kb())

@router.message(CourseApplicationState.entering_name, F.text)
async def course_enter_name(message: Message, state: FSMContext):
    """Ism-familiya kiritilganda"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = message.from_user.id in ADMIN_IDS
        await message.answer("❌ Bekor qilindi. Bosh menyudasiz.", reply_markup=get_main_menu_kb(is_admin=is_admin))
        return

    name = message.text.strip()
    if len(name) < 3:
        await message.answer("Iltimos, ism va familiyangizni to'liqroq kiriting:")
        return

    await state.update_data(applicant_name=name)
    await state.set_state(CourseApplicationState.entering_phone)

    text = (
        f"👤 Qabul qilindi: <b>{name}</b>\n\n"
        "2️⃣-qadam: <b>Bog'lanish uchun telefon raqamingizni yuboring:</b>\n"
        "<i>Quyidagi tugmani bosing yoki raqamingizni yozib yuboring:</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_phone_request_kb())

@router.message(CourseApplicationState.entering_phone)
async def course_enter_phone(message: Message, state: FSMContext):
    """Telefon raqami yuborilganda"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        is_admin = message.from_user.id in ADMIN_IDS
        await message.answer("❌ Bekor qilindi. Bosh menyudasiz.", reply_markup=get_main_menu_kb(is_admin=is_admin))
        return

    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = f"+{phone}"
    else:
        phone = message.text.strip()
        if len(phone) < 7:
            await message.answer("Iltimos, to'g'ri telefon raqamini kiriting:")
            return

    await state.update_data(applicant_phone=phone)
    await state.set_state(CourseApplicationState.confirming)

    data = await state.get_data()
    summary_text = (
        "📋 <b>KURSNING NARXINI BILISH VA RO'YXATDAN O'TISH ARIZASI:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎓 <b>Kurs:</b> Bolalar massaji kursi (1 oylik)\n"
        "📍 <b>Manzil:</b> Qushbegi 10A filiali (Seshanba – Shanba 10:00 – 13:00)\n"
        "────────────────────\n"
        f"👤 <b>F.I.Sh:</b> {data['applicant_name']}\n"
        f"📞 <b>Telefon:</b> <code>{phone}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Arizani yuborishni tasdiqlaysizmi?"
    )

    await message.answer(summary_text, parse_mode="HTML", reply_markup=get_course_confirm_kb())

@router.callback_query(F.data == "confirm_course_app_yes", CourseApplicationState.confirming)
async def course_app_confirmed(callback: CallbackQuery, state: FSMContext):
    """Arizani tasdiqlash va saqlash"""
    await callback.answer("Ariza qabul qilinmoqda...")
    data = await state.get_data()
    user = callback.from_user

    app_id = await create_course_application(
        user_id=user.id,
        full_name=data["applicant_name"],
        phone=data["applicant_phone"]
    )

    await add_or_update_user(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username,
        phone=data["applicant_phone"]
    )

    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass

    success_text = (
        f"🎉 <b>Arizangiz muvaffaqiyatli qabul qilindi! #{app_id}</b>\n\n"
        f"🎓 <b>Yo'nalish:</b> Bolalar massaji kursi (1 oylik)\n"
        f"📍 <b>Manzil:</b> Qushbegi 10A filiali\n"
        f"👤 <b>Mijoz:</b> {data['applicant_name']}\n"
        f"📞 <b>Telefon:</b> <code>{data['applicant_phone']}</code>\n\n"
        "Tez orada kurs koordinatori siz bilan bog'lanib, kurs narxi, to'lov usullari va darslar jadvali bo'yicha to'liq ma'lumot beradi.\n\n"
        "🌸 <i>«Bolalar Massaji Nazokat79» markazini tanlaganingiz uchun rahmat!</i>"
    )

    is_admin = user.id in ADMIN_IDS
    await callback.message.answer(success_text, parse_mode="HTML", reply_markup=get_main_menu_kb(is_admin=is_admin))

    # Guruhga va administratorlarga bildirishnoma yuborish
    from utils.notifier import notify_course_application
    await notify_course_application(
        callback.message.bot,
        app_id,
        data["applicant_name"],
        data["applicant_phone"],
        user
    )


@router.message(F.text == "👶 Bolalar massaji haqida")
async def about_baby_massage(message: Message):
    """Bolalar massaji haqida foydali ma'lumotlar va ko'rsatmalar"""
    text = (
        "👶 <b>Bolalar massaji haqida nimalarni bilish kerak?</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Massaj — bu chaqaloqlar va yosh bolalarning jismoniy hamda asab tizimi to'g'ri rivojlanishi uchun eng samarali va xavfsiz tabiiy muolajadir.\n\n"
        "<b>📌 Massaj qachon tavsiya etiladi?</b>\n"
        "• <b>Mushaklar tonusi buzilganda:</b> Gipertonus (mushaklar qotishi) yoki Gipotonus (bo'shashishi);\n"
        "• <b>Ortopedik muammolarda:</b> Chanoq-son bo'g'imlari displaziyasi, maymoqlik (kosolapie), yassioyoqlik;\n"
        "• <b>Bo'yin qiyshiqligi:</b> Tug'ruq asoratlari natijasida bo'yin mushaklarining tortilishi (krivosheya);\n"
        "• <b>Kech rivojlanish:</b> Bola o'z vaqtida boshini ushlamasa, ag'darilyolmasa, o'tirmasa yoki yurmasa;\n"
        "• <b>Umumiy chiniqtirish:</b> Sog'lom bolalarni immunitetini oshirish, uyqusini yaxshilash va ishtahasini ochish uchun.\n\n"
        "<b>💡 Ota-onalar uchun muhim maslahatlar:</b>\n"
        "1. Massaj seansiga bolani to'yib ovqatlanganidan so'ng kamida 40-45 daqiqa o'tgach olib kelish tavsiya etiladi.\n"
        "2. Bola uxlayotgan yoki injiqlik qilayotgan paytda majburlamaslik kerak.\n"
        "3. Birinchi seansdan oldin mutaxassisimiz bolani diqqat bilan ko'rikdan o'tkazadi."
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📰 Yangiliklar va Chegirmalar")
async def show_news(message: Message):
    """Eng so'nggi yangiliklar va aksiyalarni ko'rish"""
    news_list = await get_latest_news(limit=5)
    
    if not news_list:
        await message.answer("📰 Hozircha yangiliklar va e'lonlar mavjud emas.")
        return
        
    for item in news_list:
        date_str = item.get("created_at", "")[:10] if item.get("created_at") else ""
        header = f"📰 <b>{item['title']}</b>"
        if date_str:
            header += f" <i>({date_str})</i>"
            
        content = f"{header}\n\n{item['content']}"
        
        photo_id = item.get("photo_id")
        if photo_id:
            try:
                await message.answer_photo(photo=photo_id, caption=content, parse_mode="HTML")
                continue
            except Exception:
                pass
                
        await message.answer(content, parse_mode="HTML")
