"""Loyiha bo'ylab ishlatiladigan konstantalar."""
from enum import Enum


class StrEnum(str, Enum):
    """Python 3.10 uchun StrEnum polifili (3.11 da stdlib da bor)."""

    def __str__(self) -> str:  # noqa: D105
        return str(self.value)


class TemplateCategory(StrEnum):
    MEDIA = "media"
    FINANCE = "finance"
    EDU = "edu"
    GROUP = "group"
    SERVICE = "service"


CATEGORY_TITLES: dict[str, str] = {
    TemplateCategory.MEDIA: "🎬 Media botlar",
    TemplateCategory.FINANCE: "💰 Moliyaviy botlar",
    TemplateCategory.EDU: "📚 Ta'lim va tarjimon botlar",
    TemplateCategory.GROUP: "👥 Guruh uchun botlar",
    TemplateCategory.SERVICE: "⭐ Foydali servis botlar",
}


class ChildBotStatus(StrEnum):
    PENDING_TOKEN = "pending_token"
    ACTIVE = "active"
    EXPIRED = "expired"
    STOPPED = "stopped"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class PaymentPurpose(StrEnum):
    TOPUP = "topup"
    CREATE_BOT = "create_bot"
    TARIFF = "tariff"
