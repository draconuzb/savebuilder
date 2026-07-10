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
]

TARIFFS = [
    {"name": "Start", "speed_x": 2, "duration_days": 30, "price": Decimal("0")},
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
