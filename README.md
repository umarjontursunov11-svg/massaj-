# 👶 Bolalar Massaji Telegram Boti («Bolajon Shifo»)

Bolalar massaji markazi uchun ishlab chiqilgan, qulay, sodda va tez ishlovchi professional Telegram bot.

---

## 🌟 Asosiy Imkoniyatlar

### 1. 👥 Mijozlar (Ota-onalar) uchun:
- **Toshkent shahar tumanlari bo'yicha filiallar**:
  - Barcha 12 ta tuman (Yunusobod, Chilonzor, Mirzo Ulug'bek, Yakkasaroy, Mirobod, Shayxontohur, Olmazor, Uchtepa, Yashnobod, Sergeli, Bektemir, Yangihayot).
  - Har bir filialning aniq manzili, mo'ljali, telefon raqamlari va ish vaqti.
  - **Telegram geolokatsiyasi**: Bitta tugma orqali xaritadagi nuqtani va Yandex Maps havolasini yuborish.
- **Mutaxassis ko'rigiga online yozilish (Booking)**:
  - Tuman va Filialni tanlash
  - Xizmat turini tanlash (Diagnostika, Umumiy profilaktik, Gipertonus, Krivosheya, Displaziya, Gimnastika va boshqalar)
  - Filial mutaxassis shifokorini tanlash (yoki bo'sh mutaxassisni tanlash)
  - Qulay sana va vaqtni tanlash
  - Ota-ona va bolaning ma'lumotlarini kiritish
  - Telefon raqamni bitta tugma bilan yuborish
  - Ariza holati haqida tasdiqnoma olish
- **Xizmatlar va Narxlar**: Shaffof va aniq narxlar ro'yxati.
- **Bolalar massaji haqida qo'llanma**: Tibbiy ko'rsatmalar va ota-onalarga foydali tavsiyalar.
- **Yangiliklar va Chegirmalar**: Markazda e'lon qilingan aksiyalar va yangiliklarni ko'rish.

---

### 2. ⚙️ Soddalashtirilgan Admin Panel (`/admin`):
- **Har kungi yangiliklar va e'lonlarni tarqatish (Broadcast)**:
  - Barcha bot foydalanuvchilariga rasm va matn ko'rinishida yangiliklarni bir zumda tarqatish.
  - Yuborilgan e'lonlar avtomatik tarzda botning "Yangiliklar" bo'limiga ham saqlanadi.
- **Yangi arizalarni qabul qilish va boshqarish**:
  - Yangi ariza kelishi bilan administratorga to'liq tafsilotlar bilan xabarnoma boradi.
  - `[✅ Tasdiqlash]` yoki `[❌ Rad etish]` tugmalari orqali arizani boshqarish.
  - Natija mijozga avtomatik yetkaziladi.
- **Statistika**: Faol foydalanuvchilar va kelib tushgan arizalar soni.
- **Filiallar nazorati**: Filiallar ro'yxati va ma'lumotlari.

---

## 🚀 Ishga tushirish bo'yicha ko'rsatma

### 1-qadam: Bot Tokenini olish
1. Telegramda [@BotFather](https://t.me/BotFather) botiga kiring.
2. `/newbot` buyrug'ini yuboring va botingizga nom hamda username bering.
3. BotFather sizga bergan `API token`ni nusxalab oling.

### 2-qadam: O'zingizning Telegram ID raqamingizni bilish
1. Telegramda [@userinfobot](https://t.me/userinfobot) botiga kiring.
2. Sizga `Id: 123456789` ko'rinishida raqam beradi.

### 3-qadam: `.env` sozlamalari
Barcha sozlamalar avtomatik ravishda `.env` fayliga kiritildi:
```env
BOT_TOKEN=8912105475:AAHHXPS-BvXX7EnFnFiddN2OFpCscODDB34
GROUP_ID=5472693648
ADMIN_IDS=5472693648
DB_NAME=massage_bot.db
```

> [!TIP]
> **Guruhga ulanish:** Bot arizalarni guruhga yuborishi uchun:
> 1. `@bolalarmassaji_n79_bot` ni o'z guruhingizga a'zo qilib qo'shing.
> 2. Botga guruhda xabarlarni yozish (yoki Administrator) huquqini bering.
> 3. Guruhda `/id` buyrug'ini yozsangiz, bot guruhning aniq ID raqamini ko'rsatadi. Agar kerak bo'lsa uni `.env` ga yozib qo'yishingiz mumkin.

### 4-qadam: Botni ishga tushirish
Windows tizimida:
- **`run_bot.bat`** faylini sichqoncha bilan ikki marta bosing!
Yoki terminal orqali:
```powershell
python bot.py
```

---

## 📂 Loyiha Tuzilmasi

```
c:\Users\User\Desktop\массаж\
├── .env                       # Token va Admin ID
├── .env.example               # Namuna sozlamalar
├── config.py                  # Sozlamalar moduli
├── bot.py                     # Asosiy ishga tushirish fayli
├── run_bot.bat                # Bitta bosishda ishga tushirish
├── database/
│   ├── db.py                  # aiosqlite asinxron DB funksiyalari
│   └── seed_data.py           # Tumanlar, filiallar va mutaxassislar ma'lumotlari
├── handlers/
│   ├── user_start.py          # /start va asosiy menyu
│   ├── branches.py            # Tumanlar, filiallar va geolokatsiya
│   ├── booking.py             # Ko'rikka yozilish (FSM zanjiri)
│   ├── services.py            # Xizmatlar, narxlar va yangiliklar
│   └── admin.py               # Soddalashtirilgan admin paneli
├── keyboards/
│   ├── default_kb.py          # Asosiy menyu va telefon yuborish tugmalari
│   └── inline_kb.py           # Inline klaviaturalar
└── states/
    └── booking_states.py      # FSM holatlari
```

---

## 🛠 O'zgartirishlar kiritish
Filiallar manzillari, telefon raqamlari yoki mutaxassislarni o'zgartirmoqchi bo'lsangiz, `database/seed_data.py` faylini ochib, kerakli ma'lumotlarni tahrirlashingiz mumkin.
