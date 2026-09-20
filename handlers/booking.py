from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database.db import (
    get_all_branches,
    get_branch_by_id,
    create_appointment,
    add_or_update_user
)
from states.booking_states import BookingState
from keyboards.default_kb import get_main_menu_kb, get_phone_request_kb, get_cancel_kb
from keyboards.inline_kb import (
    get_booking_branches_kb,
    get_dates_kb,
    get_times_kb,
    get_booking_confirmation_kb
)

router = Router()

@router.message(F.text.in_(["📝 Qabulga yozilish", "Qabulga yozilish", "📝 Ko'rikka yozilish", "Ko'rikka yozilish"]))
async def start_booking(message: Message, state: FSMContext):
    """Qabulga yozilishni boshlash: Filial tanlash"""
    await state.clear()
    await state.set_state(BookingState.selecting_branch)
    
    branches = await get_all_branches()
    text = (
        "📝 <b>Qabulga yozilish</b>\n\n"
        "1️⃣-qadam: O'zingizga qulay bo'lgan <b>filialni tanlang:</b>"
    )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_booking_branches_kb(branches)
    )

@router.callback_query(F.data.startswith("book_branch:"))
async def booking_select_branch(callback: CallbackQuery, state: FSMContext):
    """Filial tanlanganda"""
    await callback.answer()
    branch_id = int(callback.data.split(":")[1])
    branch = await get_branch_by_id(branch_id)
    
    if not branch:
        await callback.message.answer("Kechirasiz, filial topilmadi.")
        return
        
    manager_tg = branch.get("telegram_username") or "@Rixsiyeva81"
    await state.update_data(
        branch_id=branch["id"],
        branch_name=branch["name"],
        branch_address=branch["address"],
        branch_phone=branch["phone"],
        branch_landmark=branch["landmark"],
        branch_telegram_username=manager_tg
    )
    await state.set_state(BookingState.entering_parent_name)
    
    text = (
        f"🏥 Tanlangan filial: <b>{branch['name']}</b>\n"
        f"🏢 <b>Manzil:</b> {branch['address']}\n"
        f"☎️ <b>Filial telefoni:</b> <code>{branch['phone']}</code>\n"
        f"👩‍⚕️ <b>Mas'ul xodim:</b> {manager_tg}\n\n"
        "2️⃣-qadam: <b>Ism va familiyangizni kiriting:</b>\n"
        "<i>(Masalan: Madina Karimova)</i>"
    )
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_cancel_kb())

@router.message(BookingState.entering_parent_name)
async def booking_enter_parent_name(message: Message, state: FSMContext):
    """Ota-onaning ism-familiyasi kiritilganda"""
    parent_name = message.text.strip()
    if len(parent_name) < 2:
        await message.answer("Iltimos, ism va familiyangizni to'liqroq kiriting:")
        return
        
    await state.update_data(parent_name=parent_name)
    await state.set_state(BookingState.entering_child_name)
    
    await message.answer(
        "3️⃣-qadam: <b>Farzandingizning ismini kiriting:</b>\n"
        "<i>(Masalan: Amirbek)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )

@router.message(BookingState.entering_child_name)
async def booking_enter_child_name(message: Message, state: FSMContext):
    """Farzandning ismi kiritilganda"""
    child_name = message.text.strip()
    if len(child_name) < 2:
        await message.answer("Iltimos, farzandingizning ismini kiriting:")
        return
        
    await state.update_data(child_name=child_name)
    await state.set_state(BookingState.entering_phone)
    
    await message.answer(
        "4️⃣-qadam: Bog'lanish uchun <b>kontakt telefon raqamingizni</b> yuboring:\n\n"
        "Quyidagi <b>«📲 Telefon raqamimni yuborish»</b> tugmasini bosing yoki raqamingizni kiriting (+998901234567):",
        parse_mode="HTML",
        reply_markup=get_phone_request_kb()
    )

@router.message(BookingState.entering_phone, F.contact | F.text)
async def booking_enter_phone(message: Message, state: FSMContext):
    """Telefon raqam qabul qilinganda"""
    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
    else:
        phone = message.text.strip()
        if len(phone) < 7:
            await message.answer("Iltimos, to'g'ri telefon raqam kiriting:")
            return
            
    await state.update_data(phone=phone)
    await state.set_state(BookingState.selecting_date)
    
    await message.answer(
        "5️⃣-qadam: Qabul uchun <b>qulay kunni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_dates_kb()
    )

@router.callback_query(F.data.startswith("book_date:"), BookingState.selecting_date)
async def booking_select_date(callback: CallbackQuery, state: FSMContext):
    """Qabul kuni tanlanganda"""
    await callback.answer()
    selected_date = callback.data.split(":")[1]
    
    time_kb = get_times_kb(selected_date)
    has_slots = any(any(btn.callback_data.startswith("book_time:") for btn in row) for row in time_kb.inline_keyboard)
    
    if not has_slots:
        text = (
            f"📅 Tanlangan sana: <b>{selected_date}</b>\n\n"
            "⚠️ Ushbu kun uchun barcha qabul vaqtlari yakunlangan yoki bo'sh vaqt qolmagan.\n"
            "Iltimos, boshqa ish kunini tanlang:"
        )
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_dates_kb())
        return

    await state.update_data(preferred_date=selected_date)
    await state.set_state(BookingState.selecting_time)
    text = (
        f"📅 Tanlangan sana: <b>{selected_date}</b>\n\n"
        "6️⃣-qadam: Qabul uchun <b>qulay 1 soatlik vaqt oralig'ini tanlang:</b>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=time_kb)

@router.callback_query(F.data == "reselect_date", BookingState.selecting_time)
async def booking_reselect_date(callback: CallbackQuery, state: FSMContext):
    """Kunni qayta tanlashga qaytish"""
    await callback.answer()
    await state.set_state(BookingState.selecting_date)
    text = "5️⃣-qadam: Qabul uchun <b>qulay kunni tanlang:</b>"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_dates_kb())


@router.callback_query(F.data.startswith("book_time:"), BookingState.selecting_time)
async def booking_select_time(callback: CallbackQuery, state: FSMContext):
    """Qabul vaqti tanlanganda"""
    await callback.answer()
    selected_time = callback.data.split(":", 1)[1]
    await state.update_data(preferred_time=selected_time)
    
    data = await state.get_data()
    await state.set_state(BookingState.confirming)
    
    from utils.reminder import calculate_10_sessions
    session_dates = calculate_10_sessions(data['preferred_date'])
    await state.update_data(session_dates=session_dates)
    start_date = session_dates[0]
    end_date = session_dates[-1]

    manager_tg = data.get('branch_telegram_username') or "@Rixsiyeva81"
    summary_text = (
        "📋 <b>10 KUNLIK QABULGA YOZILISH MA'LUMOTLARI:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏥 <b>Filial:</b> {data['branch_name']}\n"
        f"🏢 <b>Manzil:</b> {data.get('branch_address', '')}\n"
        f"☎️ <b>Filial mas'uli telefoni:</b> {data.get('branch_phone', '')}\n"
        f"👩‍⚕️ <b>Mas'ul xodim:</b> {manager_tg}\n"
        "────────────────────\n"
        f"👤 <b>Mijoz (Ota-ona):</b> {data['parent_name']}\n"
        f"👶 <b>Farzandning ismi:</b> {data['child_name']}\n"
        f"📞 <b>Mijoz telefoni:</b> {data['phone']}\n"
        f"📚 <b>Muolaja:</b> 10 kunlik bolalar massaji kursi\n"
        f"📅 <b>Kurs muddati:</b> {start_date} dan {end_date} gacha (10 ish kuni)\n"
        f"⏰ <b>Har kungi qabul vaqti:</b> {data['preferred_time']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔔 <i>Har kuni qabuldan kamida 2 soat oldin bot orqali eslatma va holatni belgilash tugmalari yuboriladi.</i>\n\n"
        "Barcha ma'lumotlar to'g'rimi? Qabulga yozilishni tasdiqlaysizmi?"
    )
    
    await callback.message.edit_text(
        summary_text,
        parse_mode="HTML",
        reply_markup=get_booking_confirmation_kb()
    )

@router.callback_query(F.data == "confirm_booking_yes", BookingState.confirming)
async def booking_confirmed(callback: CallbackQuery, state: FSMContext):
    """Yozilishni tasdiqlash va bazaga saqlash hamda adminga yuborish"""
    await callback.answer("Ariza qabul qilinmoqda...")
    data = await state.get_data()
    user = callback.from_user
    
    # 1. Bazaga asosiy arizani kiritish
    app_id = await create_appointment(
        user_id=user.id,
        parent_name=data["parent_name"],
        child_name=data["child_name"],
        phone=data["phone"],
        branch_id=data["branch_id"],
        preferred_date=data["preferred_date"],
        preferred_time=data["preferred_time"]
    )
    
    # 2. 10 ta seansni bazaga kiritish
    from utils.reminder import calculate_10_sessions
    session_dates = data.get("session_dates") or calculate_10_sessions(data["preferred_date"])
    sessions_to_insert = [
        {
            "session_number": idx + 1,
            "session_date": s_date,
            "session_time": data["preferred_time"]
        }
        for idx, s_date in enumerate(session_dates)
    ]
    from database.db import create_appointment_sessions
    await create_appointment_sessions(app_id, sessions_to_insert)

    # Foydalanuvchi ma'lumotlarini yangilash
    await add_or_update_user(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username,
        phone=data["phone"]
    )
    
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    # Foydalanuvchiga muvaffaqiyat xabari
    manager_tg = data.get("branch_telegram_username") or "@Rixsiyeva81"
    start_date = session_dates[0]
    end_date = session_dates[-1]

    success_text = (
        f"🎉 <b>10 kunlik qabulga arizangiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"🆔 <b>Ariza raqami:</b> #{app_id}\n"
        f"🏥 <b>Filial:</b> {data['branch_name']}\n"
        f"🏢 <b>Filial manzili:</b> {data.get('branch_address', '')}\n"
        f"☎️ <b>Filial mas'ul telefoni:</b> <code>{data.get('branch_phone', '')}</code>\n"
        f"👩‍⚕️ <b>Filial mas'ul xodimi:</b> {manager_tg}\n"
        f"👤 <b>Mijoz:</b> {data['parent_name']}\n"
        f"👶 <b>Farzand:</b> {data['child_name']}\n"
        f"📚 <b>Muolaja kursi:</b> 10 kunlik bolalar massaji\n"
        f"📅 <b>Sanalar:</b> {start_date} dan {end_date} gacha (10 ish kuni)\n"
        f"⏰ <b>Har kungi qabul vaqti:</b> {data['preferred_time']}\n\n"
        f"🔔 <b>Avtomatik Eslatma:</b> Har kuni seans boshlanishidan kamida <b>2 soat oldin</b> bot orqali sizga eslatma xabari keladi. "
        f"Unda o'z vaqtida borishingiz yoki kechikishingiz haqida xabar bera olasiz.\n\n"
        f"Tez orada filialimiz ma'muri siz bilan bog'lanib, qabul vaqtini yana bir bor tasdiqlaydi.\n\n"
        f"Salomat bo'ling, farzandingizni kutib qolamiz! 🌸"
    )
    
    is_admin = user.id in ADMIN_IDS
    await callback.message.answer(
        success_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_kb(is_admin=is_admin)
    )
    
    # Guruhga va administratorlarga bildirishnoma yuborish
    from utils.notifier import notify_new_appointment
    data["session_dates"] = session_dates
    await notify_new_appointment(callback.message.bot, app_id, data, user)

@router.callback_query(F.data.startswith("session_resp:"))
async def handle_session_response_cb(callback: CallbackQuery):
    """Mijoz seans eslatmasiga javob berganda (o'z vaqtida boraman / kechikaman / kela olmayman)"""
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Noma'lum buyruq.")
        return
        
    session_id = int(parts[1])
    response_type = parts[2]
    
    from database.db import update_session_user_response, get_session_full_info
    await update_session_user_response(session_id, response_type)
    session_info = await get_session_full_info(session_id)
    
    status_text_map = {
        "on_time": "✅ <b>O'z vaqtida borishingiz tasdiqlandi!</b>\nKatta rahmat, mutaxassisimiz sizni kutmoqda! 🌸",
        "late_15": "⏳ <b>15 daqiqa kechikishingiz belgilandi!</b>\nFilial mas'uli ogohlantirildi. Yo'lda ehtiyot bo'ling! 🚗",
        "cannot_come": "❌ <b>Bugun kela olmasligingiz belgilandi!</b>\nFilial ma'muri seansni boshqa kunga ko'chirish bo'yicha siz bilan bog'lanadi."
    }
    
    confirm_text = status_text_map.get(response_type, "Javobingiz qabul qilindi.")
    await callback.answer("Javobingiz qabul qilindi!")
    
    # Eslatma xabarini yangilash
    try:
        updated_msg = (
            f"{callback.message.html_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Sizning javobingiz:</b>\n"
            f"{confirm_text}"
        )
        await callback.message.edit_text(updated_msg, parse_mode="HTML", reply_markup=None)
    except Exception:
        await callback.message.answer(confirm_text, parse_mode="HTML")
        
    # Guruhga va adminlarga bildirishnoma yuborish
    if session_info:
        from utils.notifier import notify_session_response
        await notify_session_response(callback.message.bot, session_info, response_type)

