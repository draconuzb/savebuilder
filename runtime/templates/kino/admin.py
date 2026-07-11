"""Kino shablon — admin (bot egasi) paneli."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import delete, func, select

from db.models import ChildUser, ForceChannel, KinoContent
from db.session import get_session
from runtime.templates.kino.keyboards import (
    admin_panel_kb,
    cancel_kb,
    confirm_broadcast_kb,
    force_sub_manage_kb,
)
from runtime.templates.kino.states import AddKino, Broadcast, DelKino, ForceSub

log = logging.getLogger(__name__)


def build_admin_router(child_bot_id: int, owner_tg_id: int) -> Router:
    router = Router(name=f"kino-admin-{child_bot_id}")
    # Butun router faqat egaga
    router.message.filter(F.from_user.id == owner_tg_id)
    router.callback_query.filter(F.from_user.id == owner_tg_id)

    async def panel_text() -> str:
        async with get_session() as s:
            films = await s.scalar(
                select(func.count(KinoContent.id)).where(
                    KinoContent.child_bot_id == child_bot_id
                )
            )
            users = await s.scalar(
                select(func.count(ChildUser.id)).where(
                    ChildUser.child_bot_id == child_bot_id
                )
            )
        return (
            f"⚙️ <b>Admin panel</b>\n\n"
            f"🎬 Kinolar: <b>{films or 0}</b>\n"
            f"👥 Foydalanuvchilar: <b>{users or 0}</b>"
        )

    @router.message(Command("admin"))
    async def admin(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(await panel_text(), reply_markup=admin_panel_kb())

    @router.callback_query(F.data == "k:panel")
    async def back_panel(cq: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await cq.message.edit_text(await panel_text(), reply_markup=admin_panel_kb())
        await cq.answer()

    @router.callback_query(F.data == "k:cancel")
    async def cancel(cq: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await cq.message.edit_text(await panel_text(), reply_markup=admin_panel_kb())
        await cq.answer("Bekor qilindi")

    # ---- Kino qo'shish ----
    @router.callback_query(F.data == "k:add")
    async def add_start(cq: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(AddKino.waiting_code)
        await cq.message.edit_text(
            "Yangi kino uchun <b>kod</b> yuboring (masalan: 123):", reply_markup=cancel_kb()
        )
        await cq.answer()

    @router.message(AddKino.waiting_code, F.text)
    async def add_code(message: Message, state: FSMContext) -> None:
        code = message.text.strip()
        async with get_session() as s:
            dup = await s.scalar(
                select(KinoContent.id).where(
                    KinoContent.child_bot_id == child_bot_id, KinoContent.code == code
                )
            )
        if dup:
            await message.answer("⚠️ Bu kod band. Boshqa kod yuboring.")
            return
        await state.update_data(code=code)
        await state.set_state(AddKino.waiting_video)
        await message.answer("Endi <b>video</b> faylini yuboring (sarlavha ixtiyoriy):")

    @router.message(AddKino.waiting_video, F.video)
    async def add_video(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        async with get_session() as s:
            s.add(
                KinoContent(
                    child_bot_id=child_bot_id,
                    code=data["code"],
                    title=message.caption,
                    file_id=message.video.file_id,
                )
            )
        await state.clear()
        await message.answer(
            f"✅ Kino saqlandi. Kod: <code>{data['code']}</code>",
            reply_markup=admin_panel_kb(),
        )

    @router.message(AddKino.waiting_video)
    async def add_video_invalid(message: Message) -> None:
        await message.answer("❌ Iltimos <b>video</b> yuboring.")

    # ---- Kino o'chirish ----
    @router.callback_query(F.data == "k:del")
    async def del_start(cq: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(DelKino.waiting_code)
        await cq.message.edit_text(
            "O'chiriladigan kino <b>kodini</b> yuboring:", reply_markup=cancel_kb()
        )
        await cq.answer()

    @router.message(DelKino.waiting_code, F.text)
    async def del_code(message: Message, state: FSMContext) -> None:
        code = message.text.strip()
        async with get_session() as s:
            res = await s.execute(
                delete(KinoContent).where(
                    KinoContent.child_bot_id == child_bot_id, KinoContent.code == code
                )
            )
        await state.clear()
        msg = "✅ O'chirildi." if res.rowcount else "❌ Bunday kod topilmadi."
        await message.answer(msg, reply_markup=admin_panel_kb())

    # ---- Statistika ----
    @router.callback_query(F.data == "k:stats")
    async def stats(cq: CallbackQuery) -> None:
        async with get_session() as s:
            films = await s.scalar(
                select(func.count(KinoContent.id)).where(
                    KinoContent.child_bot_id == child_bot_id
                )
            )
            users = await s.scalar(
                select(func.count(ChildUser.id)).where(
                    ChildUser.child_bot_id == child_bot_id
                )
            )
            total_views = await s.scalar(
                select(func.coalesce(func.sum(KinoContent.views), 0)).where(
                    KinoContent.child_bot_id == child_bot_id
                )
            )
            top = await s.execute(
                select(KinoContent.code, KinoContent.title, KinoContent.views)
                .where(KinoContent.child_bot_id == child_bot_id)
                .order_by(KinoContent.views.desc())
                .limit(5)
            )
        lines = [
            "📊 <b>Statistika</b>\n",
            f"🎬 Kinolar: <b>{films or 0}</b>",
            f"👥 Foydalanuvchilar: <b>{users or 0}</b>",
            f"👁 Jami ko'rishlar: <b>{total_views or 0}</b>\n",
            "🔝 <b>Top kinolar:</b>",
        ]
        for code, title, views in top.all():
            lines.append(f"• <code>{code}</code> {title or ''} — {views} ko'rish")
        await cq.message.edit_text("\n".join(lines), reply_markup=admin_panel_kb())
        await cq.answer()

    # ---- Majburiy obuna ----
    async def fsub_view(cq: CallbackQuery) -> None:
        async with get_session() as s:
            res = await s.execute(
                select(ForceChannel).where(ForceChannel.child_bot_id == child_bot_id)
            )
            channels = res.scalars().all()
        items = [(c.id, c.channel_username or str(c.channel_id)) for c in channels]
        text = "🔒 <b>Majburiy obuna</b>\n\n" + (
            "Kanallar:" if items else "Hozircha kanal yo'q."
        )
        await cq.message.edit_text(text, reply_markup=force_sub_manage_kb(items))

    @router.callback_query(F.data == "k:fsub")
    async def fsub(cq: CallbackQuery) -> None:
        await fsub_view(cq)
        await cq.answer()

    @router.callback_query(F.data == "k:fsubadd")
    async def fsub_add(cq: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(ForceSub.waiting_channel)
        await cq.message.edit_text(
            "Kanal @username yoki ID (-100...) yuboring.\n"
            "<i>Bot o'sha kanalda admin bo'lishi shart!</i>",
            reply_markup=cancel_kb(),
        )
        await cq.answer()

    @router.message(ForceSub.waiting_channel, F.text)
    async def fsub_save(message: Message, state: FSMContext) -> None:
        val = message.text.strip()
        channel_id = None
        username = None
        if val.startswith("-100"):
            channel_id = int(val)
        else:
            username = val.lstrip("@")
        async with get_session() as s:
            s.add(
                ForceChannel(
                    child_bot_id=child_bot_id,
                    channel_id=channel_id,
                    channel_username=username,
                )
            )
        await state.clear()
        await message.answer("✅ Kanal qo'shildi.", reply_markup=admin_panel_kb())

    @router.callback_query(F.data.startswith("k:fsubdel:"))
    async def fsub_del(cq: CallbackQuery) -> None:
        cid = int(cq.data.split(":")[2])
        async with get_session() as s:
            await s.execute(delete(ForceChannel).where(ForceChannel.id == cid))
        await fsub_view(cq)
        await cq.answer("O'chirildi")

    # ---- Broadcast ----
    @router.callback_query(F.data == "k:cast")
    async def cast_start(cq: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(Broadcast.waiting_message)
        await cq.message.edit_text(
            "📢 Tarqatiladigan xabarni yuboring (matn yoki media):",
            reply_markup=cancel_kb(),
        )
        await cq.answer()

    @router.message(Broadcast.waiting_message)
    async def cast_preview(message: Message, state: FSMContext) -> None:
        await state.update_data(from_chat_id=message.chat.id, message_id=message.message_id)
        await state.set_state(Broadcast.confirming)
        async with get_session() as s:
            users = await s.scalar(
                select(func.count(ChildUser.id)).where(
                    ChildUser.child_bot_id == child_bot_id
                )
            )
        await message.answer(
            f"👥 <b>{users or 0}</b> foydalanuvchiga yuboriladi. Tasdiqlaysizmi?",
            reply_markup=confirm_broadcast_kb(),
        )

    @router.callback_query(Broadcast.confirming, F.data == "k:castgo")
    async def cast_go(cq: CallbackQuery, state: FSMContext, bot: Bot) -> None:
        data = await state.get_data()
        await state.clear()
        await cq.message.edit_text("📤 Yuborilmoqda...")
        async with get_session() as s:
            res = await s.execute(
                select(ChildUser.tg_id).where(ChildUser.child_bot_id == child_bot_id)
            )
            user_ids = [r[0] for r in res.all()]

        sent = failed = 0
        for uid in user_ids:
            try:
                await bot.copy_message(
                    chat_id=uid,
                    from_chat_id=data["from_chat_id"],
                    message_id=data["message_id"],
                )
                sent += 1
            except Exception:  # noqa: BLE001
                failed += 1
            await asyncio.sleep(0.05)  # flood himoyasi (~20/s)

        await cq.message.answer(
            f"✅ Tarqatish tugadi.\n📤 Yuborildi: <b>{sent}</b>\n❌ Xato: <b>{failed}</b>",
            reply_markup=admin_panel_kb(),
        )
        await cq.answer()

    return router
