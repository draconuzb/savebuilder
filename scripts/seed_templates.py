"""Jadvallarni yaratish va boshlang'ich shablon/tariflarni yozish.

Ishlatish:  python -m scripts.seed_templates
"""
from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select

from core.constants import TemplateCategory
from db.models import Base, Tariff, Template
from db.session import async_session_factory, engine

TEMPLATES = [
    {
        "code": "kino",
        "category": TemplateCategory.MEDIA,
        "title": "🎬 Kino bot",
        "description": "🎬 Kinolarni yuklash va maxsus kod orqali yuklab olish imkoniyati mavjud.",
        "example_username": "@Kinoni_sevib_koramizbot",
        "create_price": Decimal("65000"),
        "version": "1.0.1",
    },
    {
        "code": "serial",
        "category": TemplateCategory.MEDIA,
        "title": "🎞 Serial Bot Pro",
        "description": "Seriallarni qism-qism kod orqali tarqatish.",
        "example_username": None,
        "create_price": Decimal("70000"),
        "version": "1.0.0",
    },
    {
        "code": "audio_pechat",
        "category": TemplateCategory.MEDIA,
        "title": "🎵 Audio Pechat Bot",
        "description": "Audio kitob / audio kontent tarqatish.",
        "example_username": None,
        "create_price": Decimal("50000"),
        "version": "1.0.0",
    },
    {
        "code": "kino_pro",
        "category": TemplateCategory.MEDIA,
        "title": "🎬 Kino Bot Pro",
        "description": "Kino botning kengaytirilgan versiyasi — tezroq va ko'proq imkoniyat.",
        "example_username": None,
        "create_price": Decimal("75000"),
        "version": "2.0.0",
    },
    {
        "code": "video_bot",
        "category": TemplateCategory.MEDIA,
        "title": "📹 Pro Video Bot",
        "description": "Har qanday videolarni kod orqali tarqatish.",
        "example_username": None,
        "create_price": Decimal("60000"),
        "version": "1.0.0",
    },
    {
        "code": "drama",
        "category": TemplateCategory.MEDIA,
        "title": "🎭 DramaBot",
        "description": "Drama va qisqa metrajli videolar uchun.",
        "example_username": None,
        "create_price": Decimal("65000"),
        "version": "1.0.0",
    },
    {
        "code": "anon",
        "category": TemplateCategory.SERVICE,
        "title": "🕵️ Anonim xabar bot",
        "description": "Foydalanuvchilar sizga anonim xabar yozadi, siz anonim javob berasiz.",
        "example_username": None,
        "create_price": Decimal("40000"),
        "version": "1.0.0",
    },
    {
        "code": "group_welcome",
        "category": TemplateCategory.GROUP,
        "title": "👥 Guruh salomlashuvchi",
        "description": "Guruhga qo'shilgan yangi a'zolarni avtomatik chiroyli kutib oladi.",
        "example_username": None,
        "create_price": Decimal("35000"),
        "version": "1.0.0",
    },
    {
        "code": "poll",
        "category": TemplateCategory.SERVICE,
        "title": "📊 So'rovnoma bot",
        "description": "So'rovnoma yaratib, barcha obunachilaringizga tarqating.",
        "example_username": None,
        "create_price": Decimal("35000"),
        "version": "1.0.0",
    },
    {
        "code": "quiz",
        "category": TemplateCategory.EDU,
        "title": "🧠 Viktorina bot",
        "description": "To'g'ri javobli test-viktorina yaratib, bilimlarni sinang.",
        "example_username": None,
        "create_price": Decimal("45000"),
        "version": "1.0.0",
    },
    {
        "code": "currency",
        "category": TemplateCategory.FINANCE,
        "title": "💱 Valyuta kursi bot",
        "description": "Markaziy bank rasmiy valyuta kurslarini ko'rsatadi (USD, EUR, RUB...).",
        "example_username": None,
        "create_price": Decimal("40000"),
        "version": "1.0.0",
    },
]

TARIFFS = [
    {"name": "Start", "speed_x": 2, "duration_days": 30, "price": Decimal("15000")},
    {"name": "Standart", "speed_x": 4, "duration_days": 30, "price": Decimal("20000")},
    {"name": "Pro", "speed_x": 6, "duration_days": 30, "price": Decimal("25000")},
    {"name": "Turbo", "speed_x": 8, "duration_days": 30, "price": Decimal("35000")},
    {"name": "Ultra", "speed_x": 10, "duration_days": 30, "price": Decimal("45000")},
]


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Jadvallar yaratildi.")

    async with async_session_factory() as s:
        for t in TEMPLATES:
            exists = await s.scalar(select(Template).where(Template.code == t["code"]))
            if not exists:
                s.add(Template(**t))
                print(f"  + shablon: {t['code']}")
        for tf in TARIFFS:
            exists = await s.scalar(select(Tariff).where(Tariff.name == tf["name"]))
            if not exists:
                s.add(Tariff(**tf))
                print(f"  + tarif: {tf['name']}")
        await s.commit()
    print("✅ Seed tugadi.")


if __name__ == "__main__":
    asyncio.run(main())
