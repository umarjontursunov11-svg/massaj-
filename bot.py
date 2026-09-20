import sys
import asyncio
import logging

# Windows konsolida emoji va UTF-8 belgilarni to'g'ri chiqarish
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN, ADMIN_IDS
from database.db import init_db
from handlers import user_start, branches, booking, services, admin, doctor_schedule

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def set_main_commands(bot: Bot):
    """Telegram menyu buyruqlarini o'rnatish"""
    commands = [
        BotCommand(command="start", description="Botni qayta ishga tushirish"),
        BotCommand(command="help", description="Yordam va qo'llanma"),
        BotCommand(command="admin", description="Boshqaruv paneli (Adminlar uchun)")
    ]
    await bot.set_my_commands(commands)

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error(
            "\n" + "="*60 + "\n"
            "XATOLIK: Bot tokeni topilmadi yoki o'rnatilmagan!\n"
            "Iltimos, '.env' faylini oching va Telegram @BotFather dan olgan\n"
            "BOT_TOKEN ingizni kiriting:\n"
            "BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz\n" + "="*60
        )
        sys.exit(1)

    logger.info("Ma'lumotlar bazasi ishga tushirilmoqda...")
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Routerlarni ro'yxatdan o'tkazish
    dp.include_router(user_start.router)
    dp.include_router(doctor_schedule.router)
    dp.include_router(branches.router)
    dp.include_router(booking.router)
    dp.include_router(services.router)
    dp.include_router(admin.router)

    # Buyruqlar menyusini o'rnatish
    try:
        await set_main_commands(bot)
    except Exception as e:
        logger.warning(f"Buyruqlar menyusini o'rnatishda tarmoq xatoligi: {e}")

    # Adminlarga bot ishga tushganligi haqida xabar berish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text="🤖 <b>«Bolalar Massaji Nazokat79» boti muvaffaqiyatli ishga tushdi!</b>\n\nBoshqaruv panelini ochish uchun /admin buyrug'ini yuboring.",
                parse_mode="HTML"
            )
        except Exception:
            pass

    logger.info("Bot polling rejimida ishga tushdi...")
    from utils.reminder import reminder_worker
    reminder_task = asyncio.create_task(reminder_worker(bot))

    try:
        try:
            await bot.delete_webhook(drop_pending_updates=True)
        except Exception as e:
            logger.warning(f"Webhook tozalashda xatolik: {e}")
        await dp.start_polling(bot)
    finally:
        reminder_task.cancel()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
