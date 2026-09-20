import aiosqlite
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from config import DB_PATH
from database.seed_data import (
    INITIAL_DISTRICTS,
    INITIAL_BRANCHES,
    INITIAL_SERVICES,
    INITIAL_SPECIALISTS,
    INITIAL_NEWS
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def get_db():
    """Asinxron SQLite ulanishi va tranzaksiya boshqaruvi"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db

async def init_db():
    """Baza jadvallarini yaratish va boshlang'ich ma'lumotlar bilan to'ldirish"""
    async with get_db() as db:
        # Foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tumanlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS districts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # Filiallar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS branches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                district_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                landmark TEXT,
                phone TEXT NOT NULL,
                working_hours TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                yandex_url TEXT,
                telegram_username TEXT,
                FOREIGN KEY (district_id) REFERENCES districts (id) ON DELETE CASCADE
            )
        """)

        # Xizmatlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                price TEXT NOT NULL,
                duration TEXT NOT NULL
            )
        """)

        # Mutaxassislar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS specialists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                speciality TEXT NOT NULL,
                experience TEXT NOT NULL,
                FOREIGN KEY (branch_id) REFERENCES branches (id) ON DELETE CASCADE
            )
        """)

        # Ko'rikka yozilishlar (Arizalar)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                parent_name TEXT NOT NULL,
                child_name TEXT NOT NULL,
                child_age TEXT NOT NULL,
                phone TEXT NOT NULL,
                branch_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                specialist_id INTEGER,
                preferred_date TEXT NOT NULL,
                preferred_time TEXT NOT NULL,
                status TEXT DEFAULT 'Yangi',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (branch_id) REFERENCES branches (id),
                FOREIGN KEY (service_id) REFERENCES services (id),
                FOREIGN KEY (specialist_id) REFERENCES specialists (id)
            )
        """)

        # Yangiliklar va e'lonlar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                photo_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # O'quv kursi arizalari jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS course_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                course_name TEXT DEFAULT 'Bolalar massaji kursi (1 oylik)',
                status TEXT DEFAULT 'Yangi',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 10 kunlik seanslar va eslatmalar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS appointment_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id INTEGER NOT NULL,
                session_number INTEGER NOT NULL,
                session_date TEXT NOT NULL,
                session_time TEXT NOT NULL,
                reminder_sent INTEGER DEFAULT 0,
                user_response TEXT DEFAULT NULL,
                user_response_time TIMESTAMP DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appointment_id) REFERENCES appointments (id) ON DELETE CASCADE
            )
        """)

        # Mavjud bazalar uchun yangi ustunlarni tekshirish va qo'shish (migratsiya)
        cur_cols = await db.execute("PRAGMA table_info(branches)")
        existing_cols = [r["name"] for r in await cur_cols.fetchall()]
        if "yandex_url" not in existing_cols:
            await db.execute("ALTER TABLE branches ADD COLUMN yandex_url TEXT")
        if "telegram_username" not in existing_cols:
            await db.execute("ALTER TABLE branches ADD COLUMN telegram_username TEXT")

        # Ish vaqtini Dushanba - Shanba: 09:00 - 17:00 ga sinxronlash
        await db.execute("UPDATE branches SET working_hours = 'Dushanba - Shanba: 09:00 - 17:00'")

        await db.commit()

        # Dastlabki ma'lumotlarni tekshirish va to'ldirish
        cursor = await db.execute("SELECT COUNT(*) as count FROM districts")
        row = await cursor.fetchone()
        if row and row["count"] == 0:
            logger.info("Dastlabki ma'lumotlar bazaga kiritilmoqda...")
            
            # Tumanlarni kiritish
            district_map = {}
            for dist_name in INITIAL_DISTRICTS:
                cur = await db.execute("INSERT INTO districts (name) VALUES (?)", (dist_name,))
                district_map[dist_name] = cur.lastrowid

            # Filiallarni kiritish
            branch_map = {}
            for b in INITIAL_BRANCHES:
                dist_id = district_map.get(b["district"])
                if dist_id:
                    cur = await db.execute("""
                        INSERT INTO branches (district_id, name, address, landmark, phone, working_hours, latitude, longitude, yandex_url, telegram_username)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (dist_id, b["name"], b["address"], b["landmark"], b["phone"], b["working_hours"], b["latitude"], b["longitude"], b.get("yandex_url"), b.get("telegram_username")))
                    branch_map[b["name"]] = cur.lastrowid

            # Xizmatlarni kiritish
            for s in INITIAL_SERVICES:
                await db.execute("""
                    INSERT INTO services (title, description, price, duration)
                    VALUES (?, ?, ?, ?)
                """, (s["title"], s["description"], s["price"], s["duration"]))

            # Mutaxassislarni kiritish
            for sp in INITIAL_SPECIALISTS:
                b_id = branch_map.get(sp["branch_name"])
                if b_id:
                    await db.execute("""
                        INSERT INTO specialists (branch_id, full_name, speciality, experience)
                        VALUES (?, ?, ?, ?)
                    """, (b_id, sp["full_name"], sp["speciality"], sp["experience"]))

            # Dastlabki yangiliklarni kiritish
            for n in INITIAL_NEWS:
                await db.execute("""
                    INSERT INTO news (title, content)
                    VALUES (?, ?)
                """, (n["title"], n["content"]))

            await db.commit()
            logger.info("Dastlabki ma'lumotlar muvaffaqiyatli kiritildi.")

# --- Foydalanuvchi funksiyalari ---
async def add_or_update_user(user_id: int, full_name: str, username: Optional[str] = None, phone: Optional[str] = None):
    async with get_db() as db:
        await db.execute("""
            INSERT INTO users (user_id, full_name, username, phone)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                full_name = excluded.full_name,
                username = excluded.username,
                phone = COALESCE(excluded.phone, users.phone)
        """, (user_id, full_name, username, phone))
        await db.commit()

async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_all_user_ids() -> List[int]:
    async with get_db() as db:
        cursor = await db.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [row["user_id"] for row in rows]

async def get_users_count() -> int:
    async with get_db() as db:
        cursor = await db.execute("SELECT COUNT(*) as count FROM users")
        row = await cursor.fetchone()
        return row["count"] if row else 0

# --- Tumanlar va Filiallar ---
async def get_all_districts() -> List[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM districts ORDER BY name ASC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_district_by_id(district_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM districts WHERE id = ?", (district_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_branches_by_district(district_id: int) -> List[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM branches WHERE district_id = ? ORDER BY name ASC", (district_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_branch_by_id(branch_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT b.*, d.name as district_name 
            FROM branches b
            LEFT JOIN districts d ON b.district_id = d.id
            WHERE b.id = ?
        """, (branch_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_all_branches() -> List[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT b.*, d.name as district_name 
            FROM branches b
            LEFT JOIN districts d ON b.district_id = d.id
            ORDER BY d.name, b.name ASC
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def update_branch_phone(branch_id: int, phone: str) -> bool:
    async with get_db() as db:
        await db.execute("UPDATE branches SET phone = ? WHERE id = ?", (phone, branch_id))
        await db.commit()
        return True

async def update_branch_address(branch_id: int, address: str) -> bool:
    async with get_db() as db:
        await db.execute("UPDATE branches SET address = ? WHERE id = ?", (address, branch_id))
        await db.commit()
        return True

async def update_branch_landmark(branch_id: int, landmark: str) -> bool:
    async with get_db() as db:
        await db.execute("UPDATE branches SET landmark = ? WHERE id = ?", (landmark, branch_id))
        await db.commit()
        return True

async def update_branch_working_hours(branch_id: int, working_hours: str) -> bool:
    async with get_db() as db:
        await db.execute("UPDATE branches SET working_hours = ? WHERE id = ?", (working_hours, branch_id))
        await db.commit()
        return True

async def update_branch_location(branch_id: int, latitude: float, longitude: float) -> bool:
    async with get_db() as db:
        await db.execute("UPDATE branches SET latitude = ?, longitude = ? WHERE id = ?", (latitude, longitude, branch_id))
        await db.commit()
        return True

async def update_branch_telegram_username(branch_id: int, telegram_username: str) -> bool:
    async with get_db() as db:
        await db.execute("UPDATE branches SET telegram_username = ? WHERE id = ?", (telegram_username, branch_id))
        await db.commit()
        return True

async def update_branch_yandex_url(branch_id: int, yandex_url: str) -> bool:
    async with get_db() as db:
        await db.execute("UPDATE branches SET yandex_url = ? WHERE id = ?", (yandex_url, branch_id))
        await db.commit()
        return True


# --- Xizmatlar ---
async def get_all_services() -> List[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM services ORDER BY id ASC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_service_by_id(service_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM services WHERE id = ?", (service_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

# --- Mutaxassislar ---
async def get_specialists_by_branch(branch_id: int) -> List[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM specialists WHERE branch_id = ? ORDER BY id ASC", (branch_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_specialist_by_id(specialist_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM specialists WHERE id = ?", (specialist_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

# --- Ko'rikka yozilishlar (Appointments) ---
async def create_appointment(
    user_id: int,
    parent_name: str,
    child_name: str,
    phone: str,
    branch_id: int,
    preferred_date: str,
    preferred_time: str,
    child_age: str = "Ko'rsatilmagan",
    service_id: int = 1,
    specialist_id: Optional[int] = None
) -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO appointments (
                user_id, parent_name, child_name, child_age, phone,
                branch_id, service_id, specialist_id, preferred_date, preferred_time, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Yangi')
        """, (user_id, parent_name, child_name, child_age, phone, branch_id, service_id, specialist_id, preferred_date, preferred_time))
        await db.commit()
        return cursor.lastrowid

async def get_appointment_by_id(app_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT a.*, 
                   b.name as branch_name, b.phone as branch_phone, b.address as branch_address,
                   s.title as service_title, s.price as service_price,
                   sp.full_name as specialist_name, sp.speciality as specialist_role
            FROM appointments a
            LEFT JOIN branches b ON a.branch_id = b.id
            LEFT JOIN services s ON a.service_id = s.id
            LEFT JOIN specialists sp ON a.specialist_id = sp.id
            WHERE a.id = ?
        """, (app_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def update_appointment_status(app_id: int, status: str) -> bool:
    async with get_db() as db:
        await db.execute("UPDATE appointments SET status = ? WHERE id = ?", (status, app_id))
        await db.commit()
        return True

async def get_recent_appointments(limit: int = 10) -> List[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT a.*, 
                   b.name as branch_name,
                   s.title as service_title,
                   sp.full_name as specialist_name
            FROM appointments a
            LEFT JOIN branches b ON a.branch_id = b.id
            LEFT JOIN services s ON a.service_id = s.id
            LEFT JOIN specialists sp ON a.specialist_id = sp.id
            ORDER BY a.id DESC
            LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_appointments_count() -> int:
    async with get_db() as db:
        cursor = await db.execute("SELECT COUNT(*) as count FROM appointments")
        row = await cursor.fetchone()
        return row["count"] if row else 0

# --- Yangiliklar ---
async def add_news(title: str, content: str, photo_id: Optional[str] = None) -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO news (title, content, photo_id)
            VALUES (?, ?, ?)
        """, (title, content, photo_id))
        await db.commit()
        return cursor.lastrowid

async def get_latest_news(limit: int = 5) -> List[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT * FROM news ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def delete_news_by_id(news_id: int) -> bool:
    async with get_db() as db:
        await db.execute("DELETE FROM news WHERE id = ?", (news_id,))
        await db.commit()
        return True

# --- O'quv kursi arizalari ---
async def create_course_application(user_id: int, full_name: str, phone: str, course_name: str = "Bolalar massaji kursi (1 oylik)") -> int:
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO course_applications (user_id, full_name, phone, course_name)
            VALUES (?, ?, ?, ?)
        """, (user_id, full_name, phone, course_name))
        await db.commit()
        return cursor.lastrowid

async def get_all_course_applications(limit: int = 20) -> List[Dict[str, Any]]:
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT * FROM course_applications
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

# --- 10 kunlik seanslar va eslatmalar ---
async def create_appointment_sessions(appointment_id: int, sessions: List[Dict[str, Any]]) -> None:
    """Qabul uchun 10 ta seansni bazaga kiritish"""
    async with get_db() as db:
        for s in sessions:
            await db.execute("""
                INSERT INTO appointment_sessions (
                    appointment_id, session_number, session_date, session_time
                ) VALUES (?, ?, ?, ?)
            """, (appointment_id, s["session_number"], s["session_date"], s["session_time"]))
        await db.commit()

async def get_today_pending_sessions(today_date: str) -> List[Dict[str, Any]]:
    """Bugungi kunga belgilangan va hali eslatma yuborilmagan seanslar"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT 
                s.id as session_id,
                s.appointment_id,
                s.session_number,
                s.session_date,
                s.session_time,
                s.reminder_sent,
                s.user_response,
                a.user_id,
                a.parent_name,
                a.child_name,
                a.phone,
                b.name as branch_name,
                b.address as branch_address,
                b.phone as branch_phone,
                b.telegram_username as branch_telegram
            FROM appointment_sessions s
            JOIN appointments a ON s.appointment_id = a.id
            JOIN branches b ON a.branch_id = b.id
            WHERE s.session_date = ? AND s.reminder_sent = 0
            ORDER BY s.session_time ASC
        """, (today_date,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def mark_session_reminder_sent(session_id: int) -> None:
    """Seans uchun eslatma yuborilgan deb belgilash"""
    async with get_db() as db:
        await db.execute("""
            UPDATE appointment_sessions
            SET reminder_sent = 1
            WHERE id = ?
        """, (session_id,))
        await db.commit()

async def update_session_user_response(session_id: int, response_code: str) -> None:
    """Mijozning kelish/kechikish javobini saqlash"""
    async with get_db() as db:
        await db.execute("""
            UPDATE appointment_sessions
            SET user_response = ?, user_response_time = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (response_code, session_id))
        await db.commit()

async def get_session_full_info(session_id: int) -> Optional[Dict[str, Any]]:
    """Seans va ariza bo'yicha to'liq ma'lumot"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT 
                s.id as session_id,
                s.appointment_id,
                s.session_number,
                s.session_date,
                s.session_time,
                s.reminder_sent,
                s.user_response,
                s.user_response_time,
                a.user_id,
                a.parent_name,
                a.child_name,
                a.phone,
                b.name as branch_name,
                b.address as branch_address,
                b.phone as branch_phone,
                b.telegram_username as branch_telegram
            FROM appointment_sessions s
            JOIN appointments a ON s.appointment_id = a.id
            JOIN branches b ON a.branch_id = b.id
            WHERE s.id = ?
        """, (session_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_sessions_for_appointment(appointment_id: int) -> List[Dict[str, Any]]:
    """Muayyan ariza uchun barcha 10 ta seansni olish"""
    async with get_db() as db:
        cursor = await db.execute("""
            SELECT * FROM appointment_sessions
            WHERE appointment_id = ?
            ORDER BY session_number ASC
        """, (appointment_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]



