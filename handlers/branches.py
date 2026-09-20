from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database.db import (
    get_all_branches,
    get_branch_by_id
)
from keyboards.inline_kb import (
    get_all_branches_info_kb,
    get_branch_action_kb
)

router = Router()

@router.message(F.text == "🏥 Filiallar va Manzillar")
async def show_branches(message: Message):
    """Barcha 12 ta filiallar ro'yxatini ko'rsatish"""
    branches = await get_all_branches()
    text = (
        "🏥 <b>«Bolalar Massaji Nazokat79» Markazi Filiallari va Manzillari</b>\n\n"
        "O'zingizga qulay va yaqin filialni tanlang. "
        "Har bir filialning aniq manzili, mo'ljali, mas'ul telefon raqami va geolokatsiyasini ko'rishingiz mumkin:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_all_branches_info_kb(branches))

@router.callback_query(F.data == "back_to_districts")
async def back_to_branches_cb(callback: CallbackQuery):
    """Filiallar ro'yxatiga qaytish"""
    await callback.answer()
    branches = await get_all_branches()
    text = (
        "🏥 <b>«Bolalar Massaji Nazokat79» Markazi Filiallari:</b>\n\n"
        "Kerakli filialni tanlang:"
    )
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_all_branches_info_kb(branches))
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_all_branches_info_kb(branches))

@router.callback_query(F.data.startswith("info_branch:"))
async def select_branch_info(callback: CallbackQuery):
    """Aynan bir filial tafsilotlarini ko'rsatish"""
    await callback.answer()
    branch_id = int(callback.data.split(":")[1])
    branch = await get_branch_by_id(branch_id)
    
    if not branch:
        await callback.message.answer("Kechirasiz, filial topilmadi.")
        return
        
    manager_tg = branch.get('telegram_username') or '@Rixsiyeva81'
    branch_info = (
        f"🏥 <b>{branch['name']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Hudud:</b> {branch.get('district_name', '')}\n"
        f"🏢 <b>Aniq manzil:</b> {branch['address']}\n"
        f"🎯 <b>Mo'ljal:</b> {branch['landmark']}\n"
        f"☎️ <b>Filial mas'ul telefoni:</b> <code>{branch['phone']}</code>\n"
        f"👩‍⚕️ <b>Mas'ul xodim (Telegram):</b> {manager_tg}\n"
        f"🕒 <b>Ish vaqti:</b> {branch['working_hours']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<i>Xaritada lokatsiyani olish, mas'ul xodimga yozish yoki ushbu filialga yozilish uchun quyidagi tugmalardan foydalaning:</i>"
    )
    
    await callback.message.edit_text(
        branch_info,
        parse_mode="HTML",
        reply_markup=get_branch_action_kb(branch)
    )

@router.callback_query(F.data.startswith("send_loc:"))
async def send_branch_location(callback: CallbackQuery):
    """Filialning Telegram geolokatsiyasini xarita qilib yuborish"""
    await callback.answer("Lokatsiya yuborilmoqda...")
    branch_id = int(callback.data.split(":")[1])
    branch = await get_branch_by_id(branch_id)
    
    if not branch:
        await callback.message.answer("Filial topilmadi.")
        return
        
    # Telegram xaritasidagi interaktiv venue / lokatsiyani jo'natish
    try:
        await callback.message.bot.send_venue(
            chat_id=callback.message.chat.id,
            latitude=branch["latitude"],
            longitude=branch["longitude"],
            title=f"Nazokat79 - {branch['name']}",
            address=branch["address"]
        )
    except Exception:
        await callback.message.bot.send_location(
            chat_id=callback.message.chat.id,
            latitude=branch["latitude"],
            longitude=branch["longitude"]
        )
    
    yandex_link = branch.get("yandex_url") or f"https://yandex.uz/maps/?pt={branch['longitude']},{branch['latitude']}&z=17&l=map"
    manager_tg = branch.get("telegram_username") or "@Rixsiyeva81"
    manager_clean = manager_tg.lstrip("@")
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    loc_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗺 Yandex Xaritada ochish", url=yandex_link),
            InlineKeyboardButton(text="💬 Mas'ul xodimga yozish", url=f"https://t.me/{manager_clean}")
        ],
        [
            InlineKeyboardButton(text="📝 Shu filialga yozilish", callback_data=f"book_branch:{branch['id']}")
        ],
        [
            InlineKeyboardButton(text="🔙 Barcha filiallar", callback_data="back_to_districts")
        ]
    ])
    
    await callback.message.answer(
        f"📍 <b>{branch['name']}</b> geolokatsiyasi yuqorida yuborildi!\n\n"
        f"🏢 <b>Manzil:</b> {branch['address']}\n"
        f"🎯 <b>Mo'ljal:</b> {branch['landmark']}\n"
        f"☎️ <b>Filial mas'uli:</b> <code>{branch['phone']}</code>\n"
        f"👩‍⚕️ <b>Mas'ul xodim (Telegram):</b> {manager_tg}\n\n"
        f"🗺 <a href=\"{yandex_link}\">Yandex Xaritada tashkilot sahifasi va marshrut</a>",
        parse_mode="HTML",
        reply_markup=loc_kb,
        disable_web_page_preview=False
    )

