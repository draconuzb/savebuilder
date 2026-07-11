"""Kino shablon klaviaturalari."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Kino qo'shish", callback_data="k:add"),
                InlineKeyboardButton(text="🗑 Kino o'chirish", callback_data="k:del"),
            ],
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="k:stats"),
                InlineKeyboardButton(text="📢 Broadcast", callback_data="k:cast"),
            ],
            [InlineKeyboardButton(text="🔒 Majburiy obuna", callback_data="k:fsub")],
        ]
    )


def force_sub_manage_kb(channels: list) -> InlineKeyboardMarkup:
    """channels: list of (id, label)."""
    rows = [
        [InlineKeyboardButton(text=f"❌ {label}", callback_data=f"k:fsubdel:{cid}")]
        for cid, label in channels
    ]
    rows.append([InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="k:fsubadd")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="k:panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor", callback_data="k:cancel")]]
    )


def confirm_broadcast_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data="k:castgo"),
                InlineKeyboardButton(text="❌ Bekor", callback_data="k:cancel"),
            ]
        ]
    )
