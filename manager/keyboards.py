"""Manager bot klaviaturalari (Bot API 9.4 rangli tugmalar bilan).

style qiymatlari: 'success' (yashil), 'danger' (qizil), 'primary' (ko'k).
Berilmasa — ilova standart rangi (neytral)."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.constants import CATEGORY_TITLES

# ---- Asosiy menyu (reply keyboard) — rangli ----
MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Bot yaratish", style="success"),
            KeyboardButton(text="🤖 Botlarim"),
        ],
        [
            KeyboardButton(text="💳 Pul kiritish", style="primary"),
            KeyboardButton(text="📇 Hisobim"),
        ],
        [KeyboardButton(text="💎 Referal"), KeyboardButton(text="📖 Qo'llanma")],
        [KeyboardButton(text="🧧 Qo'llab-quvvatlash")],
    ],
    resize_keyboard=True,
)


def security_check_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔐 Tekshiruvni boshlash", callback_data="sec:start", style="primary")]
        ]
    )


def force_sub_kb(channels: list[str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for ch in channels:
        username = ch.lstrip("@")
        b.row(InlineKeyboardButton(text="🔗 Kanalga o'tish", url=f"https://t.me/{username}"))
    b.row(InlineKeyboardButton(text="✅ Tekshirish", callback_data="sec:check", style="success"))
    return b.as_markup()


def categories_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for code, title in CATEGORY_TITLES.items():
        b.row(InlineKeyboardButton(text=title, callback_data=f"cat:{code}"))
    b.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="create:cancel", style="danger"))
    return b.as_markup()


def templates_kb(templates: list) -> InlineKeyboardMarkup:
    """templates: list of (code, title) tuples."""
    b = InlineKeyboardBuilder()
    for code, title in templates:
        b.row(InlineKeyboardButton(text=title, callback_data=f"tpl:{code}"))
    b.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="create:cancel", style="danger"))
    return b.as_markup()


def template_page_kb(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Bot yaratish", callback_data=f"tplcreate:{code}", style="success")],
            [InlineKeyboardButton(text="🎟 Tariflar ro'yxati", callback_data=f"tpltariffs:{code}", style="primary")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="create:cancel", style="danger")],
        ]
    )


def tariffs_kb(tariffs: list) -> InlineKeyboardMarkup:
    """tariffs: list of (id, name, price)."""
    b = InlineKeyboardBuilder()
    for tid, name, price in tariffs:
        b.row(InlineKeyboardButton(text=f"{name} — {price:,.0f} so'm".replace(",", " "), callback_data=f"tariff:{tid}", style="success"))
    b.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="create:cancel", style="danger"))
    return b.as_markup()
