"""Balans / to'lov xizmati (test rejim — real provayder keyingi bosqichda)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import PaymentPurpose, PaymentStatus
from db.models import Payment, User


class InsufficientBalance(Exception):
    def __init__(self, need: Decimal, have: Decimal) -> None:
        self.need = need
        self.have = have
        super().__init__(f"Balans yetarli emas: kerak {need}, bor {have}")


async def charge(
    session: AsyncSession,
    user: User,
    amount: Decimal,
    purpose: str,
    child_bot_id: int | None = None,
) -> None:
    """Balansdan yechish + Payment yozuvi. Yetmasa InsufficientBalance."""
    if user.balance < amount:
        raise InsufficientBalance(amount, user.balance)
    user.balance -= amount
    session.add(
        Payment(
            user_id=user.id,
            amount=amount,
            provider="balance",
            purpose=purpose,
            child_bot_id=child_bot_id,
            status=PaymentStatus.PAID,
        )
    )


async def top_up(
    session: AsyncSession, user: User, amount: Decimal, provider: str = "manual"
) -> None:
    """Balansni to'ldirish (hozircha manual/test)."""
    user.balance += amount
    session.add(
        Payment(
            user_id=user.id,
            amount=amount,
            provider=provider,
            purpose=PaymentPurpose.TOPUP,
            status=PaymentStatus.PAID,
        )
    )


def tariff_expiry(duration_days: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=duration_days)
