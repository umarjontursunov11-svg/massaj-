from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_welcome_quick_actions_kb() -> InlineKeyboardMarkup:
    """/start salomlashuv xabari ostidagi tezkor inline tugmalar"""
    buttons = [
        [
            InlineKeyboardButton(text="📝 Qabulga yozilish", callback_data="start_booking_from_welcome"),
            InlineKeyboardButton(text="🏥 Filiallar & Lokatsiya", callback_data="back_to_districts")
        ],
        [
            InlineKeyboardButton(text="👩‍⚕️ Nazokat opa grafigi", callback_data="view_doctor_schedule"),
            InlineKeyboardButton(text="🌸 Bolalar massaj kursi", callback_data="view_course_info")
        ],
        [
            InlineKeyboardButton(text="🕒 Ish vaqti", callback_data="view_working_hours_quick"),
            InlineKeyboardButton(text="👶 Massaj haqida", callback_data="view_about_quick")
        ],
        [
            InlineKeyboardButton(text="📞 Call-Markaz & Bog'lanish", callback_data="view_contact_quick")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_doctor_schedule_kb() -> InlineKeyboardMarkup:
    """Nazokat opa ko'rik grafigi xabari ostidagi tugmalar"""
    buttons = [
        [
            InlineKeyboardButton(text="📝 Qabulga yozilish", callback_data="start_booking_from_welcome"),
            InlineKeyboardButton(text="🏥 Filiallar ro'yxati", callback_data="back_to_districts")
        ],
        [
            InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_doctor_schedule"),
            InlineKeyboardButton(text="💬 Administrator", url="https://t.me/Rixsiyeva81")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_course_action_kb() -> InlineKeyboardMarkup:
    """O'quv kursi ma'lumoti ostidagi tugmalar"""
    buttons = [
        [
            InlineKeyboardButton(text="💰 Kurs narxi va ro'yxatdan o'tish", callback_data="apply_course_start")
        ],
        [
            InlineKeyboardButton(text="📍 Qushbegi filiali manzili", callback_data="info_branch:3"),
            InlineKeyboardButton(text="💬 Administratorga yozish", url="https://t.me/Nazokat79_Admin")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_course_confirm_kb() -> InlineKeyboardMarkup:
    """Kurs arizasini tasdiqlash tugmalari"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash va Yuborish", callback_data="confirm_course_app_yes"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_booking")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_working_hours_kb() -> InlineKeyboardMarkup:
    """Ish vaqti xabari ostidagi tugmalar"""
    buttons = [
        [
            InlineKeyboardButton(text="📝 Qabulga yozilish", callback_data="start_booking_from_welcome"),
            InlineKeyboardButton(text="🏥 Filiallar va Manzillar", callback_data="back_to_districts")
        ],
        [
            InlineKeyboardButton(text="💬 Administrator", url="https://t.me/Nazokat79_Admin")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reminder_action_kb(session_id: int) -> InlineKeyboardMarkup:
    """Eslatma xabari ostidagi javob tugmalari"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ O'z vaqtida boraman", callback_data=f"session_resp:{session_id}:on_time")
        ],
        [
            InlineKeyboardButton(text="⏳ 15 daqiqa kechikaman", callback_data=f"session_resp:{session_id}:late_15"),
            InlineKeyboardButton(text="❌ Bugun kela olmayman", callback_data=f"session_resp:{session_id}:cannot_come")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)




def get_branch_short_name(name: str) -> str:
    """Filial nomini tugma uchun qisqartirish"""
    short = name.replace(" filiali", "")
    short = short.replace("Mirzo Ulug'bek", "M.Ulug'bek")
    return short

def get_booking_branches_kb(branches: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Qabulga yozilish uchun filiallar ro'yxati (2 ustun)"""
    buttons = []
    row = []
    for b in branches:
        btn_text = f"🏥 {get_branch_short_name(b['name'])}"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"book_branch:{b['id']}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_booking")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_all_branches_info_kb(branches: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Filiallar ma'lumotlarini ko'rish uchun ro'yxat (2 ustun)"""
    buttons = []
    row = []
    for b in branches:
        btn_text = f"🏥 {get_branch_short_name(b['name'])}"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"info_branch:{b['id']}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_branch_action_kb(branch: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Filial tafsilotlari ostidagi tugmalar"""
    yandex_url = branch.get('yandex_url') or f"https://yandex.uz/maps/?pt={branch['longitude']},{branch['latitude']}&z=17&l=map"
    manager_tg = (branch.get('telegram_username') or "@Nazokat79_Admin").lstrip("@")
    buttons = [
        [
            InlineKeyboardButton(text="📍 Geolokatsiyani olish", callback_data=f"send_loc:{branch['id']}"),
            InlineKeyboardButton(text="📝 Shu filialga yozilish", callback_data=f"book_branch:{branch['id']}")
        ],
        [
            InlineKeyboardButton(text="🗺 Yandex Xaritada ochish", url=yandex_url),
            InlineKeyboardButton(text="💬 Mas'ul xodimga yozish", url=f"https://t.me/{manager_tg}")
        ],
        [
            InlineKeyboardButton(text="🔙 Barcha filiallar", callback_data="back_to_districts")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_services_kb(services: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Xizmatlar / Ko'rik turlari"""
    buttons = []
    for s in services:
        buttons.append([InlineKeyboardButton(text=f"🔹 {s['title']} ({s['price']})", callback_data=f"book_service:{s['id']}")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_booking")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_specialists_kb(specialists: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Mutaxassislar ro'yxati"""
    buttons = []
    buttons.append([InlineKeyboardButton(text="✨ Ixtiyoriy bo'sh mutaxassis", callback_data="book_spec:0")])
    for sp in specialists:
        buttons.append([InlineKeyboardButton(text=f"👩‍⚕️ {sp['full_name']} ({sp['experience']})", callback_data=f"book_spec:{sp['id']}")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_booking")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_dates_kb() -> InlineKeyboardMarkup:
    """Qulay kunni tanlash tugmalari (Dushanbadan Shanbagacha, real vaqt bo'yicha bo'sh kunlar)"""
    buttons = []
    months = {
        1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel", 5: "May", 6: "Iyun",
        7: "Iyul", 8: "Avgust", 9: "Sentyabr", 10: "Oktyabr", 11: "Noyabr", 12: "Dekabr"
    }
    weekdays_uz = {
        0: "Dushanba", 1: "Seshanba", 2: "Chorshanba", 3: "Payshanba", 4: "Juma",
        5: "Shanba", 6: "Yakshanba"
    }
    # Toshkent vaqti (UTC+5)
    now = datetime.now(timezone(timedelta(hours=5)))
    
    offset = 0
    workdays_count = 0
    while workdays_count < 6 and offset < 14:
        day = now + timedelta(days=offset)
        # Yakshanba doim dam olish kuni
        if day.weekday() == 6:
            offset += 1
            continue
            
        date_str = day.strftime("%Y-%m-%d")
        day_name = weekdays_uz[day.weekday()]
        
        # Agar bugungi kun bo'lsa, bugun uchun qolgan bo'sh vaqt slotlari borligini tekshiramiz
        if offset == 0:
            is_saturday = (day.weekday() == 5)
            # Shanba kuni oxirgi slot 14:00-15:00, ish kunlarida esa 16:00-17:00
            last_start_hour = 14 if is_saturday else 16
            if now.hour >= last_start_hour:
                # Bugun uchun barcha qabul vaqtlari o'tib ketgan, shuning uchun bugunni chiqarmaymiz
                offset += 1
                continue
            label = f"Bugun ({day_name}, {day.day}-{months[day.month]})"
        else:
            diff_days = (day.date() - now.date()).days
            if diff_days == 1:
                label = f"Ertaga ({day_name}, {day.day}-{months[day.month]})"
            else:
                label = f"{day_name} ({day.day}-{months[day.month]})"
                
        buttons.append([InlineKeyboardButton(text=f"📅 {label}", callback_data=f"book_date:{date_str}")])
        workdays_count += 1
        offset += 1
        
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_booking")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_times_kb(selected_date: Optional[str] = None) -> InlineKeyboardMarkup:
    """Qulay vaqt oralig'i (1 soatlik oraliqda, real vaqtdan kelib chiqqan holda)"""
    # Toshkent vaqti (UTC+5)
    now = datetime.now(timezone(timedelta(hours=5)))
    
    is_today = False
    is_saturday = False
    
    if selected_date:
        try:
            dt = datetime.strptime(selected_date, "%Y-%m-%d")
            is_today = (dt.date() == now.date())
            is_saturday = (dt.weekday() == 5)
        except Exception:
            pass
            
    if is_saturday:
        # Shanba: 10:00 dan 15:00 gacha, 1 soatlik oraliq
        start_hours = [10, 11, 12, 13, 14]
    else:
        # Dushanba - Juma: 09:00 dan 17:00 gacha, 1 soatlik oraliq
        start_hours = [9, 10, 11, 12, 13, 14, 15, 16]
        
    buttons = []
    row = []
    
    for h in start_hours:
        # Agar bugungi kun tanlangan bo'lsa, real vaqt bo'yicha o'tib ketgan yoki joriy soatni chiqarmaymiz
        if is_today and h <= now.hour:
            continue
            
        slot_text = f"🕒 {h:02d}:00 - {h+1:02d}:00"
        row.append(InlineKeyboardButton(text=slot_text, callback_data=f"book_time:{h:02d}:00 - {h+1:02d}:00"))
        
        # 2 ta ustun ko'rinishida joylashtirish
        if len(row) == 2:
            buttons.append(row)
            row = []
            
    if row:
        buttons.append(row)
        
    buttons.append([InlineKeyboardButton(text="🔙 Boshqa kunni tanlash", callback_data="reselect_date")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_booking")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)




def get_booking_confirmation_kb() -> InlineKeyboardMarkup:
    """Tasdiqlash tugmalari"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash va Yuborish", callback_data="confirm_booking_yes"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_booking")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_main_kb() -> InlineKeyboardMarkup:
    """Admin bosh menyu paneli"""
    buttons = [
        [
            InlineKeyboardButton(text="📢 Yangilik joylash & tarqatish", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="🗑 Yangilikni o'chirish", callback_data="admin_news_manage")
        ],
        [
            InlineKeyboardButton(text="🏥 Filiallarni boshqarish & Tahrirlash", callback_data="admin_branches_edit")
        ],
        [
            InlineKeyboardButton(text="📋 Oxirgi arizalar", callback_data="admin_appointments"),
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_branches_list_kb(branches: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Admin uchun filiallar ro'yxati"""
    buttons = []
    for b in branches:
        buttons.append([InlineKeyboardButton(text=f"🏥 {b['name']}", callback_data=f"adm_br_edit:{b['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Admin menyusiga qaytish", callback_data="admin_back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_branch_detail_kb(branch: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Filial ma'lumotlarini tahrirlash tugmalari"""
    buttons = [
        [
            InlineKeyboardButton(text="📞 Telefon raqamni o'zgartirish", callback_data=f"adm_ed_ph:{branch['id']}"),
            InlineKeyboardButton(text="🏢 Manzilni o'zgartirish", callback_data=f"adm_ed_ad:{branch['id']}")
        ],
        [
            InlineKeyboardButton(text="🎯 Mo'ljalni o'zgartirish", callback_data=f"adm_ed_lm:{branch['id']}"),
            InlineKeyboardButton(text="🕒 Ish vaqtini o'zgartirish", callback_data=f"adm_ed_wh:{branch['id']}")
        ],
        [
            InlineKeyboardButton(text="📍 Geolokatsiyani (Xaritada) yangilash", callback_data=f"adm_ed_lc:{branch['id']}")
        ],
        [
            InlineKeyboardButton(text="🔙 Filiallar ro'yxatiga qaytish", callback_data="admin_branches_edit")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_news_delete_kb(news_list: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Yangiliklarni o'chirish tugmalari"""
    buttons = []
    for n in news_list:
        buttons.append([InlineKeyboardButton(text=f"🗑 {n['title'][:35]}", callback_data=f"adm_news_del:{n['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Admin menyusiga qaytish", callback_data="admin_back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_app_action_kb(app_id: int) -> InlineKeyboardMarkup:
    """Admin uchun ariza tasdiqlash yoki rad etish tugmalari"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_app_ok:{app_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_app_no:{app_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_broadcast_confirm_kb() -> InlineKeyboardMarkup:
    """E'lonni tarqatishni tasdiqlash"""
    buttons = [
        [
            InlineKeyboardButton(text="🚀 Ha, barchaga yuborilsin!", callback_data="admin_send_broadcast"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel_broadcast")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
