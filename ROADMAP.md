# SaveBuilder Clone — Texnik Reja (ROADMAP)

> No-code Telegram bot **shablon-fabrikasi**. @SaveBuilderBot (88k oylik user) tahlili asosida.
> Stack: **Python 3.11 · aiogram 3 · FastAPI (webhook mux) · PostgreSQL · Redis · AWS EC2**
> Yaratildi: 2026-07-11

---

## 1. Mahsulot mohiyati

Foydalanuvchi (mijoz) → tayyor bot **shablonini** tanlaydi → o'z `@BotFather` tokenini ulaydi → to'lov qiladi → uning "bola boti" bizning serverda ishlaydi. Har bola botning o'z admin paneli, kontenti va majburiy obunasi bor.

**Biznes model:** bir martalik ochish narxi (masalan Kino bot = 65 000 so'm) + oylik tarif obunasi (20k–45k so'm, "tezlik" bo'yicha) × har bola bot.

**3 rol:**
| Rol | Kim | Nima qiladi |
|-----|-----|-------------|
| **Super-admin** | biz | shablonlar, narxlar, userlar, moliya |
| **Mijoz** | manager botga kirgan odam | bot yaratadi, tarif to'laydi, o'z botini boshqaradi |
| **Oxirgi user** | mijoz botiga kirgan odam | kontent oladi (masalan kino kodi) |

---

## 2. Arxitektura (yuqori daraja)

```
                    ┌──────────────────────────────┐
   Telegram  ─────▶ │  FastAPI  (bitta HTTPS server) │
   (barcha            │   POST /wh/manager            │──▶ Manager Dispatcher
    updatelar)        │   POST /wh/{bot_secret}       │──▶ Child Router ──▶ kerakli
                    └──────────────────────────────┘          shablon Dispatcher
                              │            │
                    ┌─────────▼──┐   ┌─────▼─────┐
                    │ PostgreSQL │   │   Redis    │  (FSM state, registry cache,
                    └────────────┘   └───────────┘   rate-limit, majburiy-obuna cache)
```

**Nega webhook mux (polling emas):** 88k potensial bola bot uchun har biriga alohida polling protsess imkonsiz. Bitta HTTPS endpoint barcha updatelarni oladi, URL'dagi `bot_secret` bo'yicha kerakli bot/ dispatcher'ga marshrutlaydi. aiogram 3 buni `Bot` obyektlarini keshda saqlab qo'llab-quvvatlaydi.

---

## 3. Katalog tuzilishi

```
savebuilder/
├── manager/                 # asosiy bot (mijozlar kiradigan)
│   ├── __init__.py
│   ├── handlers/
│   │   ├── start.py         # /start, xavfsizlik, majburiy obuna
│   │   ├── menu.py          # reply keyboard menyu
│   │   ├── create.py        # kategoriya → shablon → token → tarif → to'lov
│   │   ├── my_bots.py       # "Botlarim" — ro'yxat, boshqaruv, o'chirish
│   │   ├── billing.py       # "Pul kiritish", "Hisobim", tariflar
│   │   ├── referral.py      # referal havola, bonus
│   │   └── support.py       # qo'llab-quvvatlash, qo'llanma
│   ├── keyboards.py
│   ├── texts.py             # barcha matnlar (uz) — premium emoji shu yerda
│   └── states.py            # FSM (token kutish, kontent kutish...)
│
├── runtime/                 # bola botlar dvigateli
│   ├── app.py               # FastAPI: /wh/manager, /wh/{secret}
│   ├── registry.py          # token→(bot_id, template, config) — Redis+DB kesh
│   ├── router.py            # update → to'g'ri shablon dispatcheriga
│   ├── loader.py            # bola botni ishga tushirish/to'xtatish, setWebhook
│   └── templates/
│       ├── base.py          # umumiy: majburiy obuna, admin tekshiruvi, broadcast
│       └── kino/            # 1-SHABLON
│           ├── router.py    # user oqimi: kod yuborish → kino olish
│           ├── admin.py     # admin: kino yuklash (kod, fayl, kanal), stat
│           └── texts.py
│
├── db/
│   ├── models.py            # SQLAlchemy (async) modellar
│   ├── session.py
│   └── migrations/          # Alembic
│
├── payments/
│   ├── click.py             # Click.uz integratsiya
│   ├── payme.py             # Payme integratsiya
│   └── webhook.py           # to'lov callback endpointlari
│
├── security/
│   ├── antibot.py           # WebApp captcha tekshiruvi (initData validatsiya)
│   └── force_sub.py         # majburiy obuna: kanal a'zoligini tekshirish
│
├── webapp/                  # Mini App captcha (statik + FastAPI route)
│   └── index.html
│
├── core/
│   ├── config.py            # .env: BOT_TOKEN, DB_URL, REDIS_URL, DOMAIN, secretlar
│   ├── logging.py
│   └── constants.py
│
├── scripts/
│   ├── seed_templates.py    # shablonlar va tariflarni DB ga yozish
│   └── set_webhooks.py
│
├── deploy/
│   ├── savebuilder.service  # systemd unit
│   ├── nginx.conf
│   └── README.md
│
├── requirements.txt
├── .env.example
└── ROADMAP.md               # (shu fayl)
```

---

## 4. Ma'lumotlar bazasi sxemasi (PostgreSQL)

```sql
-- Mijozlar (manager botga kirganlar)
users(
  id BIGSERIAL PK,
  tg_id BIGINT UNIQUE,
  username TEXT, full_name TEXT,
  balance NUMERIC(12,2) DEFAULT 0,        -- so'm
  referred_by BIGINT NULL REFERENCES users(id),
  is_verified BOOL DEFAULT FALSE,          -- anti-bot o'tganmi
  created_at TIMESTAMPTZ DEFAULT now()
)

-- Shablon katalogi (biz boshqaramiz)
templates(
  id SERIAL PK,
  code TEXT UNIQUE,           -- 'kino', 'serial', 'audio_pechat'...
  category TEXT,              -- 'media','finance','edu','group','service'
  title TEXT, description TEXT, example_username TEXT,
  create_price NUMERIC(12,2), -- bir martalik ochish (65000)
  version TEXT, is_active BOOL DEFAULT TRUE
)

-- Tarif rejalari (shablonga bog'liq bo'lishi mumkin)
tariffs(
  id SERIAL PK,
  name TEXT,                  -- Start/Standart/Pro/Turbo/Ultra
  speed_x INT,                -- 4,6,8,10
  duration_days INT DEFAULT 30,
  price NUMERIC(12,2)         -- 20000...45000
)

-- Bola botlar (mijoz yaratgan)
child_bots(
  id BIGSERIAL PK,
  owner_id BIGINT REFERENCES users(id),
  template_id INT REFERENCES templates(id),
  bot_token TEXT,             -- SHIFRLANGAN saqlanadi (Fernet)
  bot_username TEXT, bot_tg_id BIGINT,
  webhook_secret TEXT UNIQUE, -- /wh/{secret}
  tariff_id INT REFERENCES tariffs(id),
  status TEXT,                -- 'active','expired','stopped','pending_token'
  expires_at TIMESTAMPTZ,
  config JSONB,               -- shablonga xos sozlamalar
  created_at TIMESTAMPTZ DEFAULT now()
)

-- Majburiy obuna kanallari (har bola bot uchun)
force_channels(
  id SERIAL PK, child_bot_id BIGINT REFERENCES child_bots(id),
  channel_id BIGINT, channel_username TEXT, invite_link TEXT
)

-- Kino kontenti (Kino shablon uchun)
kino_content(
  id BIGSERIAL PK, child_bot_id BIGINT REFERENCES child_bots(id),
  code TEXT,                  -- user kiritadigan maxsus kod
  title TEXT,
  file_id TEXT,               -- Telegram file_id (yoki kanal msg ref)
  source_channel_id BIGINT, source_msg_id BIGINT,
  views INT DEFAULT 0,
  UNIQUE(child_bot_id, code)
)

-- Bola botning oxirgi userlari (statistika + broadcast uchun)
child_users(
  id BIGSERIAL PK, child_bot_id BIGINT REFERENCES child_bots(id),
  tg_id BIGINT, joined_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(child_bot_id, tg_id)
)

-- To'lovlar
payments(
  id BIGSERIAL PK, user_id BIGINT REFERENCES users(id),
  amount NUMERIC(12,2), provider TEXT,   -- 'click','payme','manual','balance'
  purpose TEXT,                          -- 'topup','create_bot','tariff'
  child_bot_id BIGINT NULL, status TEXT, -- 'pending','paid','failed'
  external_id TEXT, created_at TIMESTAMPTZ DEFAULT now()
)

-- Referal bonuslari
referral_rewards(
  id BIGSERIAL PK, referrer_id BIGINT, referred_id BIGINT,
  amount NUMERIC(12,2), created_at TIMESTAMPTZ DEFAULT now()
)
```

---

## 5. Manager bot oqimlari

**/start:**
1. Anti-bot tekshiruvi (agar `is_verified=false`) → WebApp captcha → tasdiq
2. Majburiy obuna gate (bizning kanal) → "Tekshirish"
3. Welcome + asosiy menyu (reply keyboard)

**Asosiy menyu:** `➕ Bot yaratish` · `🤖 Botlarim` · `💳 Pul kiritish` · `📇 Hisobim` · `💎 Referal` · `📖 Qo'llanma` · `🧧 Qo'llab-quvvatlash`

**Bot yaratish oqimi (FSM):**
```
Kategoriya tanlash (inline)
  → Shablon tanlash (inline, narx bilan)
    → Shablon sahifasi (narx, namuna, tavsif, "Tariflar")
      → "Bot yaratish" bosildi
        → balans yetarlimi? (create_price)  [yo'q → Pul kiritish]
        → BotFather token so'rash (FSM: waiting_token)
          → token validatsiya (getMe) → username saqlash
            → tarif tanlash → balansdan yechish
              → setWebhook + registry ga qo'shish → BOLA BOT JONLI ✅
```

---

## 6. Bola bot — Kino shablon (1-MVP)

**Oxirgi user oqimi:**
- `/start` → majburiy obuna tekshiruvi → "Kino kodini yuboring"
- User kod yuboradi → `kino_content` dan topib, `file_id` ni yuboradi (views++)
- Kod topilmasa → xato xabari

**Admin (bola bot egasi) oqimi:**
- `/admin` → panel: `➕ Kino qo'shish` · `📊 Statistika` · `📢 Broadcast` · `🔒 Majburiy obuna` · `⚙️ Sozlamalar`
- Kino qo'shish: kod kirit → video yubor (yoki kanal post havolasi) → saqlanadi
- Broadcast: matn/media → barcha `child_users` ga yuboriladi (rate-limit bilan)
- Majburiy obuna: kanal qo'shish/o'chirish

---

## 7. To'lov (O'zbekiston)

- **Click.uz** va **Payme** — asosiy provayderlar (Merchant API).
- Oqim: balans to'ldirish → provider invoice → callback → `payments.status='paid'` → `users.balance += amount`.
- MVP bosqichida: **manual to'lov** (admin tasdiqlaydi) yoki test balans, keyin real integratsiya.

---

## 8. Xavfsizlik

- **Anti-bot WebApp:** Mini App `initData` ni `HMAC-SHA256(bot_token)` bilan tekshirish (Telegram standarti). Qurilma fingerprint + rate-limit.
- **Majburiy obuna:** `getChatMember` orqali kanal a'zoligini tekshirish, Redis'da qisqa keshlash.
- **Token shifrlash:** `bot_token` DB da Fernet bilan shifrlanadi.
- **Rate-limit:** manager + har bola bot uchun (flood himoyasi).

---

## 9. Deploy (AWS EC2 + Postgres)

- EC2 (Amazon Linux 2023) — taxi botlar turgan 54.160.255.7 yoki yangi instance.
- **Nginx** (HTTPS, Let's Encrypt) → **FastAPI** (uvicorn/gunicorn).
- **PostgreSQL** (lokal yoki RDS), **Redis** (lokal).
- **systemd** unit: `savebuilder.service` (Restart=always). Loglar `/var/log/`.
- Domen kerak (webhook uchun HTTPS majburiy). Cloudflare + LE.
- CI: hozircha qo'lda `git pull && systemctl restart`.

---

## 10. Bosqichli reja (milestones)

### Bosqich 0 — Skelet (1-2 kun)
- [ ] Repo, venv, `requirements.txt`, `.env.example`
- [ ] `core/config.py`, DB ulanish, Alembic, modellar
- [ ] FastAPI `/wh/manager` + manager `/start`+menyu (bo'sh)
- [ ] Seed: shablonlar + tariflar

### Bosqich 1 — Manager MVP (2-4 kun)
- [ ] Bot yaratish FSM: kategoriya→shablon→token→tarif
- [ ] `child_bots` yozish, token validatsiya, balans (test)
- [ ] "Botlarim", "Hisobim", "Pul kiritish" (manual)

### Bosqich 2 — Webhook mux + Kino shablon (3-5 kun)
- [ ] `runtime/router.py` + `registry.py` + `loader.py` (setWebhook)
- [ ] Kino shablon: user kod oqimi + admin panel + majburiy obuna
- [ ] Bitta real bola bot jonli test (token seniki)

### Bosqich 3 — Monetizatsiya (3-5 kun)
- [ ] Click/Payme integratsiya, obuna muddati, expired holati
- [ ] Referal tizim + bonus

### Bosqich 4 — Kengaytirish
- [ ] Anti-bot WebApp captcha
- [ ] Boshqa shablonlar: Serial, Audio Pechat, Downloader...
- [ ] Super-admin panel (moliya, userlar, shablon narxlari)

---

## 11. Ochiq savollar / qarorlar

- [ ] Domen nomi? (webhook HTTPS uchun kerak)
- [ ] Premium emoji: token bergach botning premium emoji yubora olishini tekshirish (odatda bot custom emojini faqat premium bo'lsa yoki ma'lum joyda yuboradi — aniqlaymiz)
- [ ] Birinchi real shablon: Kino bot (tasdiqlangan)
- [ ] To'lov: MVP da manual, keyin Click/Payme (qaysi biri birinchi?)
- [ ] Bola bot fayllari: `file_id` qayta ishlatish yoki maxsus "saqlash kanali"?

---

*Keyingi qadam: bu reja tasdiqlangach → Bosqich 0 (skelet) ni yozishni boshlaymiz. Token tayyor bo'lsa Bosqich 2 da jonli test qilamiz.*
