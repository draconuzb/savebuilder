# SaveBuilder Clone 🤖

No-code Telegram bot **shablon-fabrikasi**. Foydalanuvchi tayyor bot turini (Kino, Serial, Audio...) tanlaydi, o'z BotFather tokenini ulaydi va ishlaydigan bot oladi — barchasi bitta server ustida **webhook multiplekser** orqali.

> @SaveBuilderBot (88k oylik user) tahlili asosida qurilmoqda. To'liq reja: [ROADMAP.md](ROADMAP.md)

## Stack
- **Python 3.11+ · aiogram 3** — bot logikasi
- **FastAPI** — webhook multiplekser (bitta endpoint, token bo'yicha marshrutlash)
- **PostgreSQL** (SQLAlchemy async) · **Redis** (FSM, kesh)
- **AWS EC2** — deploy

## Arxitektura
```
Telegram → FastAPI (/wh/manager, /wh/child/{secret}) → tegishli Dispatcher
                          │
                   PostgreSQL + Redis
```
- **Manager bot** — mijozlar kiradi, bot yaratadi, tarif to'laydi.
- **Bola botlar** — mijoz yaratgan botlar, shablon Dispatcheri orqali ishlaydi.

## Katalog
| Papka | Vazifa |
|-------|--------|
| `manager/` | asosiy bot: menyu, bot yaratish, billing, referal |
| `runtime/` | webhook mux, registry, loader, shablonlar |
| `runtime/templates/kino/` | 1-shablon: Kino bot |
| `db/` | SQLAlchemy modellar, sessiya |
| `security/` | token shifrlash, anti-bot, majburiy obuna |
| `payments/` | Click / Payme (keyingi bosqich) |
| `webapp/` | Mini App captcha (keyingi bosqich) |

## Ishga tushirish (lokal)
```bash
python -m venv .venv && source .venv/bin/activate   # win: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # qiymatlarni to'ldiring
# Fernet kalit: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

python -m scripts.seed_templates      # jadvallar + shablon/tariflar
uvicorn runtime.app:app --host 0.0.0.0 --port 8080
```
> Webhook uchun HTTPS domen shart (Telegram talabi). Lokal test uchun `ngrok`/`cloudflared` bilan tunnel oching va `DOMAIN` ni o'sha URL ga qo'ying.

## Holat (2026-07-11)
- ✅ Bosqich 0: skelet — config, DB modellar, manager /start+menyu, webhook mux, Kino shablon skeleti, seed
- ⏳ Bosqich 1: bot yaratish FSM to'liq test
- ⏳ Bosqich 2: real bola bot jonli test (token bilan)
- ⏳ Bosqich 3: to'lov (Click/Payme), referal
- ⏳ Bosqich 4: anti-bot WebApp, boshqa shablonlar

Batafsil: [ROADMAP.md](ROADMAP.md)
