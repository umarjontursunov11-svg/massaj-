from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Asosiy menyu klaviaturasi"""
    keyboard = [
        [
            KeyboardButton(text="🏥 Filiallar va Manzillar"),
            KeyboardButton(text="📝 Qabulga yozilish")
        ],
        [
            KeyboardButton(text="👩‍⚕️ Nazokat opa ko'rik grafigi"),
            KeyboardButton(text="🌸 Bolalar massaj kursi")
        ],
        [
            KeyboardButton(text="🕒 Ish vaqti"),
            KeyboardButton(text="👶 Bolalar massaji haqida")
        ],
        [
            KeyboardButton(text="🦴 Ortoped ko'rigiga yozilish"),
            KeyboardButton(text="📞 Bog'lanish")
        ]
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="⚙️ Admin Paneli")])
        
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Quyidagi bo'limlardan birini tanlang 👇"
    )

def get_phone_request_kb() -> ReplyKeyboardMarkup:
    """Telefon raqamni bitta bosish bilan yuborish klaviaturasi"""
    keyboard = [
        [KeyboardButton(text="📲 Telefon raqamimni yuborish", request_contact=True)],
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Raqamni yuborish tugmasini bosing..."
    )

def get_cancel_kb() -> ReplyKeyboardMarkup:
    """Bekor qilish uchun oddiy klaviatura"""
    keyboard = [
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
