import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database.db import (
    get_users_count,
    get_appointments_count,
    get_all_user_ids,
    get_recent_appointments,
    get_appointment_by_id,
    update_appointment_status,
    add_news,
    get_latest_news,
    delete_news_by_id,
    get_all_branches,
    get_branch_by_id,
    update_branch_phone,
    update_branch_address,
    update_branch_landmark,
    update_branch_working_hours,
    update_branch_location
)
from states.booking_states import AdminBroadcastState, AdminBranchEditState
from keyboards.inline_kb import (
    get_admin_main_kb,
    get_admin_broadcast_confirm_kb,
    get_admin_branches_list_kb,
    get_admin_branch_detail_kb,
    get_admin_news_delete_kb
)
from keyboards.default_kb import get_cancel_kb, get_main_menu_kb

logger = logging.getLogger(__name__)
router = Router()

from config import ADMIN_IDS, GROUP_ID

def is_admin(user_id_or_event, chat_id: int = None) -> bool:
    """Faqat ma'mur (admin) yoki rasmiy guruh ichida qilingan murojaatga ruxsat berish"""
    if hasattr(user_id_or_event, 'from_user'):
        u_id = user_id_or_event.from_user.id
        msg = getattr(user_id_or_event, 'message', user_id_or_event)
        c_id_val = msg.chat.id if hasattr(msg, 'chat') and msg.chat else None
    else:
        u_id = user_id_or_event
        c_id_val = chat_id

    if u_id in ADMIN_IDS:
        return True
    if GROUP_ID and c_id_val:
        raw_group = str(abs(GROUP_ID))
        raw_chat = str(abs(c_id_val))
        if raw_chat == raw_group or raw_chat.endswith(raw_group):
            return True
    return False

def can_manage_appointment(callback: CallbackQuery) -> bool:
    """Arizani tasdiqlash/rad etish huquqini tekshirish (admin yoki guruh a'zosi)"""
    if is_admin(callback.from_user.id):
        return True
    if callback.message and callback.message.chat.type in ("group", "supergroup"):
        return True
    return False

@router.message(Command("id"))
@router.message(Command("chat_id"))
async def cmd_chat_id(message: Message):
    """Chat ID raqamini aniqlash uchun yordamchi buyruq"""
    await message.reply(
        f"📌 <b>Chat Ma'lumotlari:</b>\n\n"
        f"• Chat turi: <b>{message.chat.type}</b>\n"
        f"• Chat ID: <code>{message.chat.id}</code>\n"
        f"• Foydalanuvchi ID: <code>{message.from_user.id}</code>\n\n"
        f"<i>Arizalar shu yerga kelishi uchun .env faylidagi GROUP_ID ga ushbu raqamni yozing:</i>\n"
        f"<code>GROUP_ID={message.chat.id}</code>",
        parse_mode="HTML"
    )

@router.message(F.new_chat_members)
async def on_bot_added_to_group(message: Message):
    """Bot guruhga qo'shilganda kutib olish va guruh ID sini ko'rsatish"""
    bot_info = await message.bot.get_me()
    for member in message.new_chat_members:
        if member.id == bot_info.id:
            await message.answer(
                f"👋 <b>Assalomu alaykum!</b>\n\n"
                f"<b>«Bolajon Shifo»</b> boti guruhga muvaffaqiyatli qo'shildi.\n"
                f"🆔 <b>Ushbu guruh ID raqami:</b> <code>{message.chat.id}</code>\n\n"
                f"✅ Endi mijozlar qoldirgan barcha arizalar shu yerga to'g'ridan-to'g'ri kelib tushadi!",
                parse_mode="HTML"
            )

@router.message(Command("admin"))
@router.message(F.text == "⚙️ Admin Paneli")
async def cmd_admin_panel(message: Message, state: FSMContext):
    """Admin boshqaruv panelini ochish"""
    await state.clear()
    
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Kechirasiz, ushbu bo'lim faqat bot administratorlari uchun ochiq.")
        return
        
    users_cnt = await get_users_count()
    app_cnt = await get_appointments_count()
    
    panel_text = (
        "⚙️ <b>«Bolajon Shifo» Boshqaruv Paneli (Admin)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Foydalanuvchilar:</b> {users_cnt} nafar\n"
        f"📋 <b>Jami arizalar:</b> {app_cnt} ta\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Ushbu bo me'yorda filiallar lokatsiyasi, telefon raqamlari, "
        "yangiliklar va arizalarni tahrirlashingiz mumkin:\n"
        "👇 Kerakli bo'limni tanlang:"
    )
    
    await message.answer(panel_text, parse_mode="HTML", reply_markup=get_admin_main_kb())

@router.callback_query(F.data == "admin_back_main")
async def back_to_admin_main(callback: CallbackQuery, state: FSMContext):
    """Admin bosh menyusiga qaytish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
        
    await state.clear()
    await callback.answer()
    users_cnt = await get_users_count()
    app_cnt = await get_appointments_count()
    
    panel_text = (
        "⚙️ <b>«Bolajon Shifo» Boshqaruv Paneli (Admin)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Foydalanuvchilar:</b> {users_cnt} nafar\n"
        f"📋 <b>Jami arizalar:</b> {app_cnt} ta\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 Kerakli bo'limni tanlang:"
    )
    await callback.message.edit_text(panel_text, parse_mode="HTML", reply_markup=get_admin_main_kb())

@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery):
    """Statistika ko'rsatish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
        
    await callback.answer()
    users_cnt = await get_users_count()
    app_cnt = await get_appointments_count()
    
    text = (
        "📊 <b>Bot Statistikasi:</b>\n\n"
        f"• Faol foydalanuvchilar: <b>{users_cnt}</b>\n"
        f"• Qabulga yozilganlar: <b>{app_cnt}</b>\n"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_main_kb())

# --- FILIALLARNI VA LOKATSIYALARNI TAHRIRLASH ---
@router.callback_query(F.data == "admin_branches_edit")
async def show_admin_branches_list(callback: CallbackQuery, state: FSMContext):
    """Filiallarni tahrirlash uchun ro'yxatni chiqarish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
        
    await state.clear()
    await callback.answer()
    branches = await get_all_branches()
    
    text = (
        "🏥 <b>Filiallar va Lokatsiyalarni Boshqarish</b>\n\n"
        "Tahrirlamoqchi bo'lgan filialingizni tanlang:\n"
        "<i>(Har bir filialning telefon raqami, manzili, mo'ljali va xaritadagi geolokatsiyasini o'zgartirishingiz mumkin)</i>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_branches_list_kb(branches))

@router.callback_query(F.data.startswith("adm_br_edit:"))
async def select_branch_for_edit(callback: CallbackQuery, state: FSMContext):
    """Tanlangan filial tafsilotlari va tahrirlash menyusi"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
        
    await state.clear()
    await callback.answer()
    branch_id = int(callback.data.split(":")[1])
    branch = await get_branch_by_id(branch_id)
    
    if not branch:
        await callback.message.answer("Filial topilmadi.")
        return
        
    await state.update_data(editing_branch_id=branch_id)
    
    text = (
        f"⚙️ <b>Filialni Tahrirlash:</b> {branch['name']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Tuman:</b> {branch.get('district_name', '')}\n"
        f"🏢 <b>Manzil:</b> {branch['address']}\n"
        f"🎯 <b>Mo'ljal:</b> {branch['landmark']}\n"
        f"☎️ <b>Telefon:</b> <code>{branch['phone']}</code>\n"
        f"👩‍⚕️ <b>Mas'ul xodim (Telegram):</b> {branch.get('telegram_username', 'Mavjud emas')}\n"
        f"🕒 <b>Ish vaqti:</b> {branch['working_hours']}\n"
        f"🗺 <b>Koordinatalar:</b> Lat {branch['latitude']}, Lon {branch['longitude']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Nimani o'zgartirmoqchisiz? Quyidagi tugmalardan birini bosing:"
    )

    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_branch_detail_kb(branch))

# --- TELEFONNI TAHRIRLASH ---
@router.callback_query(F.data.startswith("adm_ed_ph:"))
async def edit_branch_phone_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    branch_id = int(callback.data.split(":")[1])
    await state.update_data(editing_branch_id=branch_id)
    await state.set_state(AdminBranchEditState.editing_phone)
    await callback.message.answer(
        "✏️ <b>Filial uchun yangi telefon raqamini kiriting:</b>\n<i>(Masalan: +998 71 200 11 99)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )

@router.message(AdminBranchEditState.editing_phone, F.text)
async def edit_branch_phone_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    branch_id = data.get("editing_branch_id")
    new_phone = message.text.strip()
    
    await update_branch_phone(branch_id, new_phone)
    await state.clear()
    
    branch = await get_branch_by_id(branch_id)
    await message.answer(
        f"✅ <b>{branch['name']}</b> telefon raqami muvaffaqiyatli yangilandi!\nYangilangan raqam: <code>{new_phone}</code>",
        parse_mode="HTML",
        reply_markup=get_main_menu_kb(is_admin=True)
    )

# --- MANZILNI TAHRIRLASH ---
@router.callback_query(F.data.startswith("adm_ed_ad:"))
async def edit_branch_address_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    branch_id = int(callback.data.split(":")[1])
    await state.update_data(editing_branch_id=branch_id)
    await state.set_state(AdminBranchEditState.editing_address)
    await callback.message.answer(
        "✏️ <b>Filial uchun yangi manzilni kiriting:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )

@router.message(AdminBranchEditState.editing_address, F.text)
async def edit_branch_address_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    branch_id = data.get("editing_branch_id")
    new_address = message.text.strip()
    
    await update_branch_address(branch_id, new_address)
    await state.clear()
    
    branch = await get_branch_by_id(branch_id)
    await message.answer(
        f"✅ <b>{branch['name']}</b> manzili yangilandi!\nYangi manzil: <b>{new_address}</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_kb(is_admin=True)
    )

# --- MO'LJALNI TAHRIRLASH ---
@router.callback_query(F.data.startswith("adm_ed_lm:"))
async def edit_branch_landmark_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    branch_id = int(callback.data.split(":")[1])
    await state.update_data(editing_branch_id=branch_id)
    await state.set_state(AdminBranchEditState.editing_landmark)
    await callback.message.answer(
        "✏️ <b>Filial mo'ljalini kiriting:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )

@router.message(AdminBranchEditState.editing_landmark, F.text)
async def edit_branch_landmark_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    branch_id = data.get("editing_branch_id")
    new_landmark = message.text.strip()
    
    await update_branch_landmark(branch_id, new_landmark)
    await state.clear()
    
    branch = await get_branch_by_id(branch_id)
    await message.answer(
        f"✅ <b>{branch['name']}</b> mo'ljali yangilandi!\nYangi mo'ljal: <b>{new_landmark}</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_kb(is_admin=True)
    )

# --- ISH VAQTINI TAHRIRLASH ---
@router.callback_query(F.data.startswith("adm_ed_wh:"))
async def edit_branch_hours_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    branch_id = int(callback.data.split(":")[1])
    await state.update_data(editing_branch_id=branch_id)
    await state.set_state(AdminBranchEditState.editing_working_hours)
    await callback.message.answer(
        "✏️ <b>Yangi ish vaqtini kiriting:</b>\n<i>(Masalan: 08:00 - 21:00)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )

@router.message(AdminBranchEditState.editing_working_hours, F.text)
async def edit_branch_hours_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    branch_id = data.get("editing_branch_id")
    new_hours = message.text.strip()
    
    await update_branch_working_hours(branch_id, new_hours)
    await state.clear()
    
    branch = await get_branch_by_id(branch_id)
    await message.answer(
        f"✅ <b>{branch['name']}</b> ish vaqti yangilandi!\nYangi ish vaqti: <b>{new_hours}</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_kb(is_admin=True)
    )

# --- GEOLOKATSIYANI TAHRIRLASH ---
@router.callback_query(F.data.startswith("adm_ed_lc:"))
async def edit_branch_loc_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    branch_id = int(callback.data.split(":")[1])
    await state.update_data(editing_branch_id=branch_id)
    await state.set_state(AdminBranchEditState.editing_location)
    await callback.message.answer(
        "📍 <b>Filialning yangi geolokatsiyasini yuboring:</b>\n\n"
        "Telegram xaritasi (Location pin) orqali geolokatsiya yuboring yoki koordinatalarni matn ko'rinishida kiriting:\n"
        "<i>(Masalan: 41.3111, 69.2401)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )

@router.message(AdminBranchEditState.editing_location, F.location | F.text)
async def edit_branch_loc_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    branch_id = data.get("editing_branch_id")
    
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
    else:
        try:
            parts = message.text.split(",")
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
        except Exception:
            await message.answer("Iltimos, to'g'ri geolokatsiya yuboring yoki koordinatalarni '41.3111, 69.2401' formatida kiriting:")
            return
            
    await update_branch_location(branch_id, lat, lon)
    await state.clear()
    
    branch = await get_branch_by_id(branch_id)
    await message.answer(
        f"✅ <b>{branch['name']}</b> geolokatsiyasi xaritada muvaffaqiyatli yangilandi!\n"
        f"📍 Latitude: {lat}, Longitude: {lon}",
        parse_mode="HTML",
        reply_markup=get_main_menu_kb(is_admin=True)
    )

# --- YANGILIKLARNI O'CHIRISH VA BOSHQARISH ---
@router.callback_query(F.data == "admin_news_manage")
async def show_admin_news_manage(callback: CallbackQuery):
    """Yangiliklarni o'chirish menyusini ko'rsatish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
        
    await callback.answer()
    news_list = await get_latest_news(limit=10)
    
    if not news_list:
        await callback.message.edit_text("📰 Hozircha bazada yangiliklar mavjud emas.", reply_markup=get_admin_main_kb())
        return
        
    text = (
        "🗑 <b>Yangiliklarni O'chirish Boshqaruvi</b>\n\n"
        "O'chirmoqchi bo'lgan yangiligingizni tanlang:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_news_delete_kb(news_list))

@router.callback_query(F.data.startswith("adm_news_del:"))
async def delete_news_item_cb(callback: CallbackQuery):
    """Tanlangan yangilikni bazadan o'chirish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
        
    news_id = int(callback.data.split(":")[1])
    await delete_news_by_id(news_id)
    await callback.answer("Yangilik o'chirildi!", show_alert=True)
    
    # Ro'yxatni qayta yangilash
    news_list = await get_latest_news(limit=10)
    if not news_list:
        await callback.message.edit_text("✅ Barcha yangiliklar o'chirildi.", reply_markup=get_admin_main_kb())
    else:
        await callback.message.edit_text("🗑 Tanlangan yangilik o'chirildi. Yana o'chirmoqchi bo'lsangiz tanlang:", reply_markup=get_admin_news_delete_kb(news_list))

# --- OXIRGI ARIZALAR ---
@router.callback_query(F.data == "admin_appointments")
async def show_admin_appointments(callback: CallbackQuery):
    """Oxirgi arizalarni ko'rsatish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
        
    await callback.answer()
    appointments = await get_recent_appointments(limit=10)
    
    if not appointments:
        await callback.message.edit_text("📋 Hozircha arizalar kelib tushmagan.", reply_markup=get_admin_main_kb())
        return
        
    text = "📋 <b>Oxirgi 10 ta ariza:</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for app in appointments:
        status_icon = "🟡" if app["status"] == "Yangi" else ("🟢" if app["status"] == "Tasdiqlandi" else "🔴")
        text += (
            f"{status_icon} <b>#{app['id']} | {app['child_name']}</b> ({app['child_age']})\n"
            f"👤 Ota-ona: {app['parent_name']} | 📞 {app['phone']}\n"
            f"🏥 {app['branch_name']} | {app['preferred_date']} {app['preferred_time']}\n"
            f"💆‍♂️ {app['service_title']} ({app['status']})\n"
            f"────────────────────\n"
        )
        
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_main_kb())

# --- Ariza tasdiqlash / rad etish handlerlari ---
@router.callback_query(F.data.startswith("adm_app_ok:"))
async def confirm_appointment_cb(callback: CallbackQuery):
    """Admin yoki guruh a'zosi arizani tasdiqlaganda"""
    if not can_manage_appointment(callback):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
        
    app_id = int(callback.data.split(":")[1])
    await update_appointment_status(app_id, "Tasdiqlandi")
    await callback.answer("Ariza tasdiqlandi!")
    
    manager_name = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
    
    await callback.message.edit_text(
        callback.message.text + f"\n\n🟢 <b>HOLAT: TASDIQLANDI (Mas'ul: {manager_name})</b>",
        parse_mode="HTML"
    )
    
    app = await get_appointment_by_id(app_id)
    if app:
        try:
            user_msg = (
                f"✅ <b>Xushxabar!</b>\n\n"
                f"Sizning <b>#{app_id}</b> raqamli ko'rikka yozilish arizangiz <b>tasdiqlandi!</b>\n"
                f"🏥 <b>Filial:</b> {app['branch_name']}\n"
                f"🏢 <b>Manzil:</b> {app['branch_address']}\n"
                f"📅 <b>Sana va vaqt:</b> {app['preferred_date']} | {app['preferred_time']}\n"
                f"☎️ <b>Filial telefoni:</b> {app['branch_phone']}\n\n"
                f"Belgilangan vaqtda farzandingiz bilan kutamiz!"
            )
            await callback.message.bot.send_message(chat_id=app["user_id"], text=user_msg, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Foydalanuvchiga xabar yuborishda xato: {e}")

@router.callback_query(F.data.startswith("adm_app_no:"))
async def reject_appointment_cb(callback: CallbackQuery):
    """Admin yoki guruh a'zosi arizani rad etganda"""
    if not can_manage_appointment(callback):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
        
    app_id = int(callback.data.split(":")[1])
    await update_appointment_status(app_id, "Rad etildi")
    await callback.answer("Ariza rad etildi.")
    
    manager_name = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
    
    await callback.message.edit_text(
        callback.message.text + f"\n\n🔴 <b>HOLAT: RAD ETILDI (Mas'ul: {manager_name})</b>",
        parse_mode="HTML"
    )
    
    app = await get_appointment_by_id(app_id)
    if app:
        try:
            user_msg = (
                f"ℹ️ <b>Hurmatli {app['parent_name']}!</b>\n\n"
                f"Sizning <b>#{app_id}</b> raqamli arizangiz bo'yicha ko'rsatilgan vaqtda filialda bo'sh joy bo'lmaganligi sababli "
                f"ariza qabul qilinmadi.\n\n"
                f"Iltimos, boshqa vaqtni tanlab qayta ariza qoldiring yoki aloqa markazimiz bilan bog'laning: {app['branch_phone']}"
            )
            await callback.message.bot.send_message(chat_id=app["user_id"], text=user_msg, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Foydalanuvchiga xabar yuborishda xato: {e}")

# --- Yangilik va E'lon tarqatish (Broadcast) ---
@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """E'lon tarqatishni boshlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
        
    await callback.answer()
    await state.set_state(AdminBroadcastState.waiting_for_content)
    
    text = (
        "📢 <b>Yangi Yangilik yoki E'lon Tarqatish</b>\n\n"
        "Foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing.\n"
        "<i>(Siz oddiy matn yoki rasmli xabar (caption bilan) yuborishingiz mumkin):</i>\n\n"
        "Bekor qilish uchun pastdagi <b>«❌ Bekor qilish»</b> tugmasini bosing."
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_cancel_kb())

@router.message(AdminBroadcastState.waiting_for_content, F.text | F.photo)
async def receive_broadcast_content(message: Message, state: FSMContext):
    """E'lon mazmunini qabul qilish va tasdiqlashga chiqarish"""
    if not is_admin(message.from_user.id):
        return
        
    photo_id = None
    caption = ""
    
    if message.photo:
        photo_id = message.photo[-1].file_id
        caption = message.caption or ""
    else:
        caption = message.text or ""
        
    if not caption and not photo_id:
        await message.answer("Iltimos, matn yoki rasm yuboring:")
        return
        
    await state.update_data(photo_id=photo_id, content=caption)
    await state.set_state(AdminBroadcastState.confirming_broadcast)
    
    await message.answer("👀 <b>E'lon ko'rinishi (Prevyu):</b>", parse_mode="HTML")
    
    if photo_id:
        await message.answer_photo(photo=photo_id, caption=caption, parse_mode="HTML")
    else:
        await message.answer(caption, parse_mode="HTML")
        
    users_cnt = await get_users_count()
    await message.answer(
        f"Ushbu e'lon jami <b>{users_cnt}</b> nafar bot foydalanuvchisiga yuboriladi va yangiliklar lentasiga saqlanadi.\n\n"
        f"Tarqatishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=get_admin_broadcast_confirm_kb()
    )

@router.callback_query(F.data == "admin_cancel_broadcast", AdminBroadcastState.confirming_broadcast)
async def cancel_broadcast_cb(callback: CallbackQuery, state: FSMContext):
    """E'lonni bekor qilish"""
    await state.clear()
    await callback.answer("E'lon bekor qilindi.")
    await callback.message.edit_text("❌ E'lon tarqatish bekor qilindi.", reply_markup=get_admin_main_kb())
    await callback.message.answer("Bosh menyudasiz:", reply_markup=get_main_menu_kb(is_admin=True))

@router.callback_query(F.data == "admin_send_broadcast", AdminBroadcastState.confirming_broadcast)
async def send_broadcast_now(callback: CallbackQuery, state: FSMContext):
    """Barcha foydalanuvchilarga e'lonni tarqatish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
        
    await callback.answer("Tarqatish boshlandi...")
    data = await state.get_data()
    photo_id = data.get("photo_id")
    content = data.get("content", "")
    
    lines = content.split("\n")
    title = lines[0][:50] if lines else "Markaz Yangiligi"
    await add_news(title=title, content=content, photo_id=photo_id)
    
    user_ids = await get_all_user_ids()
    await callback.message.edit_text("⏳ Xabar tarqatilmoqda, iltimos kuting...")
    
    sent_count = 0
    blocked_count = 0
    
    for uid in user_ids:
        try:
            if photo_id:
                await callback.message.bot.send_photo(chat_id=uid, photo=photo_id, caption=content, parse_mode="HTML")
            else:
                await callback.message.bot.send_message(chat_id=uid, text=content, parse_mode="HTML")
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            blocked_count += 1
            
    await state.clear()
    result_text = (
        f"✅ <b>E'lon muvaffaqiyatli tarqatildi!</b>\n\n"
        f"📨 Yetkazildi: <b>{sent_count}</b> ta\n"
        f"🚫 Bloklagan/Xato: <b>{blocked_count}</b> ta\n"
        f"💾 Yangiliklar bo'limiga ham saqlandi."
    )
    await callback.message.edit_text(result_text, parse_mode="HTML", reply_markup=get_admin_main_kb())
    await callback.message.answer("Bosh menyudasiz:", reply_markup=get_main_menu_kb(is_admin=True))
