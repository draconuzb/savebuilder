# Deploy — bot.wecreate.uz (AWS EC2)

Nishon server: onson-gym EC2 (`54.82.28.27`, wecreate.uz). ⚠️ Bu production box —
onson gym real userlar bilan ishlaydi. Ehtiyot bo'ling, alohida DB/port ishlating.

## 0. DNS
Cloudflare'da `bot.wecreate.uz` A-record → EC2 IP (`54.82.28.27`).

## 1. Postgres + Redis (bola botlar uchun alohida DB)
```bash
# Postgres (onson bilan bir instansiyada, alohida db/user)
sudo -u postgres psql -c "CREATE USER savebuilder WITH PASSWORD 'savebuilder_pass';"
sudo -u postgres psql -c "CREATE DATABASE savebuilder OWNER savebuilder;"

# Redis (ixtiyoriy — .env da REDIS_URL bo'sh bo'lsa MemoryStorage ishlatadi)
sudo apt-get install -y redis-server && sudo systemctl enable --now redis
```

## 2. Kod + venv
```bash
cd /home/ubuntu
git clone git@github.com:draconuzb/savebuilder.git
cd savebuilder
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp .env.example .env    # qiymatlarni to'ldiring (DOMAIN=https://bot.wecreate.uz, REDIS_URL=redis://localhost:6379/0)
./.venv/bin/python -m scripts.seed_templates
```

## 3. Nginx + SSL
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/bot.wecreate.uz
sudo ln -s /etc/nginx/sites-available/bot.wecreate.uz /etc/nginx/sites-enabled/
sudo certbot --nginx -d bot.wecreate.uz   # yoki Cloudflare DNS-01
sudo nginx -t && sudo systemctl reload nginx
```

## 4. systemd
```bash
sudo cp deploy/savebuilder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now savebuilder
sudo systemctl status savebuilder
tail -f /var/log/savebuilder.log
```

## 5. Tekshirish
```bash
curl https://bot.wecreate.uz/health     # {"status":"ok","child_bots":N}
```
Manager webhook startupda avtomatik o'rnatiladi (`runtime/app.py` lifespan).

## Lokal test (domensiz — POLLING)
Server/deploy shart emas:
```bash
python -m scripts.run_polling
```
Manager + aktiv bola botlarni long-polling orqali ishga tushiradi.
