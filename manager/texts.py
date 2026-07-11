"""Manager bot matnlari (uz). Premium (custom) emoji avtomatik qo'llanadi.

Premium egali bot HTML parse_mode'da <tg-emoji> orqali custom (animatsiyali)
emoji yubora oladi. premiumize() har matndagi tanish emojini custom emojiga aylantiradi.
custom_emoji_id lar getForumTopicIconStickers dan (tekin, animatsiyali)."""
from __future__ import annotations

import re

# Emoji belgisi → custom_emoji_id. Variatsiya selektorli (️) variantlar BIRINCHI
# turishi kerak (aks holda oddiy variant ularni buzadi).
EMOJI_IDS: dict[str, str] = {
    "⚡️": "5312016608254762256",
    "⭐️": "5235579393115438657",
    "🔥": "5312241539987020022",
    "💡": "5312536423851630001",
    "🎬": "5368653135101310687",
    "💰": "5350452584119279096",
    "✅": "5237699328843200968",
    "🤖": "5309832892262654231",
    "💎": "5309958691854754293",
    "🎉": "5310228579009699834",
    "🎵": "5310045076531978942",
    "📱": "5409357944619802453",
    "👑": "5357107601584693888",
    "🎟": "5377624166436445368",
    "📣": "5309984423003823246",
}


_TAG_RE = re.compile(r'<tg-emoji emoji-id="\d+">(.*?)</tg-emoji>')


def premiumize(text: str) -> str:
    """Matndagi tanish emojilarni premium (custom) emojiga aylantiradi.

    Idempotent: avval mavjud <tg-emoji> teglarni yechadi, so'ng qayta o'raydi
    (ikki marta qo'llansa ichma-ich tag bo'lib qolmaydi)."""
    if not text:
        return text
    text = _TAG_RE.sub(r"\1", text)  # mavjud teglarni yechish
    for ch, cid in EMOJI_IDS.items():
        if ch in text:
            text = text.replace(ch, f'<tg-emoji emoji-id="{cid}">{ch}</tg-emoji>')
    return text


WELCOME = premiumize(
    "⚡️ <b>SaveBuilder</b> — botlar yaratish platformasi\n"
    "━━━━━━━━━━━━━━━\n"
    "Kod yozmasdan o'z Telegram botingizni <b>tez</b> va <b>oson</b> "
    "yarating, tahrirlang va boshqaring.\n\n"
    "🔥 <b>Imkoniyatlar</b>\n"
    "├ 🎬 Tayyor shablonlar (Kino, Serial, Audio)\n"
    "├ 📣 Ommaviy xabar va statistika\n"
    "├ 🔒 Majburiy obuna\n"
    "└ 💎 Stars to'lov va referal bonus\n\n"
    "💡 Boshlash uchun pastdagi menyudan foydalaning"
)

SECURITY_CHECK = premiumize(
    "🔐 <b>Xavfsizlik tekshiruvi</b>\n"
    "━━━━━━━━━━━━━━━\n"
    "Botdan foydalanish uchun bir martalik tekshiruvdan o'ting.\n"
    "🛡 Bu hisobingizni himoya qiladi va bir necha soniya oladi.\n\n"
    "👇 <i>Quyidagi tugmani bosing</i>"
)

FORCE_SUB = premiumize(
    "📢 <b>Majburiy obuna</b>\n"
    "━━━━━━━━━━━━━━━\n"
    "Botdan foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling,\n"
    "so'ng ✅ <b>Tekshirish</b> tugmasini bosing 👇"
)

NOT_SUBSCRIBED = "❌ Siz hali barcha kanallarga obuna bo'lmadingiz. Obuna bo'lib, qayta tekshiring."

CHOOSE_CATEGORY = premiumize(
    "🤖 <b>Bot yaratish</b>\n"
    "━━━━━━━━━━━━━━━\n"
    "Qaysi turdagi bot yaratmoqchisiz?\nKategoriyani tanlang 👇"
)

CHOOSE_TEMPLATE = premiumize("📋 <b>Shablonlar</b>\n━━━━━━━━━━━━━━━\nBirini tanlang 👇")

ACCOUNT = premiumize(
    "📇 <b>Hisobim</b>\n"
    "━━━━━━━━━━━━━━━\n"
    "👤 <b>{name}</b>\n"
    "🆔 <code>{tg_id}</code>\n\n"
    "💰 Balans: <b>{balance:,.0f}</b> so'm\n"
    "🤖 Botlar: <b>{bots}</b> ta"
)

MY_BOTS_EMPTY = premiumize(
    "🤖 <b>Botlarim</b>\n\nSizda hali yaratilgan bot yo'q. «➕ Bot yaratish» tugmasidan foydalaning."
)

REFERRAL = premiumize(
    "💎 <b>Referal dasturi</b>\n\n"
    "Do'stlaringizni taklif qiling va bonus oling!\n\n"
    "🔗 Sizning havolangiz:\n<code>{link}</code>\n\n"
    "👥 Takliflar: <b>{count}</b>"
)

GUIDE = premiumize(
    "📖 <b>Qo'llanma</b>\n"
    "━━━━━━━━━━━━━━━\n"
    "<b>1.</b> ➕ Bot yaratish → kategoriya va shablon tanlang\n"
    "<b>2.</b> 🔑 @BotFather'dan olingan tokenni yuboring\n"
    "<b>3.</b> 🎟 Tarifni tanlab, balansdan to'lang\n"
    "<b>4.</b> 🎉 Botingiz tayyor!\n\n"
    "💡 <i>Balansni «💳 Pul kiritish» → Stars orqali to'ldiring.\n"
    "Do'st taklif qilib «💎 Referal» orqali bonus oling.</i>"
)

SUPPORT = premiumize(
    "🧧 <b>Qo'llab-quvvatlash</b>\n"
    "━━━━━━━━━━━━━━━\n"
    "Savol yoki muammo bo'lsa, biz yordam beramiz!\n\n"
    "📨 Adminga yozing: @wecreate_admin\n"
    "🕒 Ish vaqti: 09:00 — 21:00"
)

ASK_TOKEN = premiumize(
    "🔑 <b>{template}</b> — token ulash\n"
    "━━━━━━━━━━━━━━━\n"
    "<b>1.</b> @BotFather'ga o'ting → /newbot → yangi bot yarating\n"
    "<b>2.</b> Berilgan <b>tokenni</b> shu yerga yuboring 👇\n\n"
    "<i>Masalan:</i> <code>123456789:AAE...xyz</code>"
)

TOKEN_INVALID = "❌ Token noto'g'ri yoki ishlamayapti. Qayta yuboring."
TOKEN_OK = premiumize(
    "✅ <b>Token qabul qilindi!</b>\n"
    "🤖 @{username}\n"
    "━━━━━━━━━━━━━━━\n"
    "Endi <b>tarif</b>ni tanlang 👇"
)
