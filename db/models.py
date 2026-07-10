"""SQLAlchemy (async) modellar. ROADMAP.md §4 sxemasiga mos."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """Manager botga kirgan mijozlar."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    full_name: Mapped[str | None] = mapped_column(String(256))
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    referred_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bots: Mapped[list["ChildBot"]] = relationship(back_populates="owner")


class Template(Base):
    """Shablon katalogi (biz boshqaramiz)."""

    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    example_username: Mapped[str | None] = mapped_column(String(64))
    create_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    version: Mapped[str] = mapped_column(String(16), default="1.0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Tariff(Base):
    """Oylik tarif rejalari (tezlik bo'yicha)."""

    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32))
    speed_x: Mapped[int] = mapped_column(Integer, default=1)
    duration_days: Mapped[int] = mapped_column(Integer, default=30)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ChildBot(Base):
    """Mijoz yaratgan bola botlar."""

    __tablename__ = "child_bots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"))
    token_enc: Mapped[str | None] = mapped_column(Text)  # Fernet bilan shifrlangan
    bot_username: Mapped[str | None] = mapped_column(String(64))
    bot_tg_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    webhook_secret: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    tariff_id: Mapped[int | None] = mapped_column(ForeignKey("tariffs.id"))
    status: Mapped[str] = mapped_column(String(24), default="pending_token", index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="bots")
    template: Mapped["Template"] = relationship()


class ForceChannel(Base):
    """Bola bot uchun majburiy obuna kanallari."""

    __tablename__ = "force_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    child_bot_id: Mapped[int] = mapped_column(ForeignKey("child_bots.id"), index=True)
    channel_id: Mapped[int | None] = mapped_column(BigInteger)
    channel_username: Mapped[str | None] = mapped_column(String(64))
    invite_link: Mapped[str | None] = mapped_column(Text)


class KinoContent(Base):
    """Kino shablon kontenti (kod → fayl)."""

    __tablename__ = "kino_content"
    __table_args__ = (UniqueConstraint("child_bot_id", "code", name="uq_kino_code"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    child_bot_id: Mapped[int] = mapped_column(ForeignKey("child_bots.id"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    title: Mapped[str | None] = mapped_column(String(256))
    file_id: Mapped[str | None] = mapped_column(Text)
    source_channel_id: Mapped[int | None] = mapped_column(BigInteger)
    source_msg_id: Mapped[int | None] = mapped_column(BigInteger)
    views: Mapped[int] = mapped_column(Integer, default=0)


class ChildUser(Base):
    """Bola botning oxirgi userlari (stat + broadcast)."""

    __tablename__ = "child_users"
    __table_args__ = (UniqueConstraint("child_bot_id", "tg_id", name="uq_child_user"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    child_bot_id: Mapped[int] = mapped_column(ForeignKey("child_bots.id"), index=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    provider: Mapped[str] = mapped_column(String(24))
    purpose: Mapped[str] = mapped_column(String(24))
    child_bot_id: Mapped[int | None] = mapped_column(ForeignKey("child_bots.id"))
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    external_id: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReferralReward(Base):
    __tablename__ = "referral_rewards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    referred_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
