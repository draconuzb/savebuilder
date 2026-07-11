"""/start, xavfsizlik tekshiruvi va majburiy obuna."""
from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from core.config import get_settings
from db.models import User
from db.session import get_session
from manager import texts
from manager.keyboards import MAIN_MENU, force_sub_kb, security_check_kb

router = Router(name="manager-start")
log = logging.getLogger(__name__)


def _parse_referrer_tg_id(args: str | None) -> int | None:
    """/start ref<tg_id> dan taklif qilgan tg_id ni ajratadi."""
    if args and args.startswith("ref"):
        try:
            return int(args[3:])
        except ValueError:
            return None
    return None


async def get_or_create_user(message: Message, referrer_tg_id: int | None = None) -> User:
    async with get_session() as s:
        res = await s.execute(select(User).where(User.tg_id == message.from_user.id))
        user = res.scalar_one_or_none()
        if user is None:
            referred_by = None
            if referrer_tg_id and referrer_tg_id != message.from_user.id:
                ref = (
                    await s.execute(select(User).where(User.tg_id == referrer_tg_id))
                ).scalar_one_or_none()
                if ref:
                    referred_by = ref.id
            user = User(
                tg_id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name,
                referred_by=referred_by,
            )
            s.add(user)
            await s.flush()
        return user


async def is_subscribed(bot: Bot, tg_id: int) -> bool:
    """Majburiy obuna kanallariga a'zolikni tekshirish."""
    channels = get_settings().force_sub_list
    if not channels:
        return True
    for ch in channels:
        chat = ch if ch.startswith("-100") else f"@{ch.lstrip('@')}"
        try:
            member = await bot.get_chat_member(chat, tg_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception as e:  # noqa: BLE001
            log.warning("get_chat_member xato (%s): %s", ch, e)
    return True


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, command: CommandObject) -> None:
    user = await get_or_create_user(message, _parse_referrer_tg_id(command.args))

    if not user.is_verified:
        await message.answer(texts.SECURITY_CHECK, reply_markup=security_check_kb())
        return

    if not await is_subscribed(bot, message.from_user.id):
        await message.answer(
            texts.FORCE_SUB, reply_markup=force_sub_kb(get_settings().force_sub_list)
        )
        return

    await message.answer(texts.WELCOME, reply_markup=MAIN_MENU)


@router.callback_query(F.data == "sec:start")
async def sec_start(cq: CallbackQuery) -> None:
    """MVP: WebApp captcha o'rniga to'g'ridan-to'g'ri tasdiqlash.
    Keyingi bosqichda haqiqiy Mini App initData tekshiruvi qo'shiladi."""
    async with get_session() as s:
        res = await s.execute(select(User).where(User.tg_id == cq.from_user.id))
        user = res.scalar_one_or_none()
        if user:
            user.is_verified = True
    await cq.message.edit_text("✅ Tekshiruv muvaffaqiyatli o'tdi!")
    await cq.message.answer(texts.WELCOME, reply_markup=MAIN_MENU)
    await cq.answer()


@router.callback_query(F.data == "sec:check")
async def sec_check(cq: CallbackQuery, bot: Bot) -> None:
    if await is_subscribed(bot, cq.from_user.id):
        await cq.message.edit_text("✅ Obuna tasdiqlandi!")
        await cq.message.answer(texts.WELCOME, reply_markup=MAIN_MENU)
    else:
        await cq.answer(texts.NOT_SUBSCRIBED, show_alert=True)
