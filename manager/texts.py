"""Manager bot matnlari (uz). Premium emoji shu yerda qo'shiladi."""

WELCOME = (
    "🤖 <b>SaveBuilder</b> — botlar yaratish platformasi\n"
    "━━━━━━━━━━━━━━━\n"
    "Kod yozmasdan o'z Telegram botingizni <b>tez</b> va <b>oson</b> "
    "yarating, tahrirlang va boshqaring.\n\n"
    "⚡️ <b>Imkoniyatlar</b>\n"
    "├ 🎬 Tayyor shablonlar (Kino, Serial, Audio)\n"
    "├ 📢 Ommaviy xabar va statistika\n"
    "├ 🔒 Majburiy obuna\n"
    "└ 💫 Stars to'lov va referal bonus\n\n"
    "👇 Boshlash uchun pastdagi menyudan foydalaning"
)

SECURITY_CHECK = (
    "🔐 <b>Xavfsizlik tekshiruvi</b>\n\n"
    "Botdan foydalanish uchun bir martalik xavfsizlik tekshiruvidan o'ting. "
    "Bu hisobingizni himoya qiladi va bir necha soniya oladi.\n\n"
    "<i>Quyidagi tugmani bosing 👇</i>"
)

FORCE_SUB = (
    "‼️ <i>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling🙂</i>\n\n"
    "<i>Keyin ✅ Tasdiqlashingiz kerak</i>"
)

NOT_SUBSCRIBED = "❌ Siz hali barcha kanallarga obuna bo'lmadingiz. Obuna bo'lib, qayta tekshiring."

CHOOSE_CATEGORY = "🤖 <b>Bot yaratish</b>\n\nQuyidagi kategoriyalardan birini tanlang: 👇"

CHOOSE_TEMPLATE = "📋 <b>Quyidagi botlardan birini tanlang:</b>"

ACCOUNT = (
    "📇 <b>Hisobim</b>\n"
    "━━━━━━━━━━━━━━━\n"
    "👤 <b>{name}</b>\n"
    "🆔 <code>{tg_id}</code>\n\n"
    "💰 Balans: <b>{balance:,.0f}</b> so'm\n"
    "🤖 Botlar: <b>{bots}</b> ta"
)

MY_BOTS_EMPTY = "🤖 <b>Botlarim</b>\n\nSizda hali yaratilgan bot yo'q. «➕ Bot yaratish» tugmasidan foydalaning."

TOPUP = (
    "💳 <b>Pul kiritish</b>\n\n"
    "Balansni to'ldirish uchun to'lov usulini tanlang.\n"
    "<i>(To'lov integratsiyasi keyingi bosqichda ulanadi.)</i>"
)

REFERRAL = (
    "💎 <b>Referal dasturi</b>\n\n"
    "Do'stlaringizni taklif qiling va bonus oling!\n\n"
    "🔗 Sizning havolangiz:\n<code>{link}</code>\n\n"
    "👥 Takliflar: <b>{count}</b>"
)

GUIDE = (
    "📖 <b>Qo'llanma</b>\n"
    "━━━━━━━━━━━━━━━\n"
    "<b>1.</b> ➕ Bot yaratish → kategoriya va shablon tanlang\n"
    "<b>2.</b> 🔑 @BotFather'dan olingan tokenni yuboring\n"
    "<b>3.</b> 🎟 Tarifni tanlab, balansdan to'lang\n"
    "<b>4.</b> 🎉 Botingiz tayyor!\n\n"
    "💡 <i>Balansni «💳 Pul kiritish» → Stars orqali to'ldiring.\n"
    "Do'st taklif qilib «💎 Referal» orqali bonus oling.</i>"
)

SUPPORT = "🧧 <b>Qo'llab-quvvatlash</b>\n\nSavollar bo'lsa: @your_support_username"

ASK_TOKEN = (
    "🔑 <b>{template} yaratish</b>\n\n"
    "@BotFather'dan olingan bot <b>tokenini</b> yuboring.\n"
    "Masalan: <code>123456789:AAE...xyz</code>"
)

TOKEN_INVALID = "❌ Token noto'g'ri yoki ishlamayapti. Qayta yuboring yoki /bekor bosing."
TOKEN_OK = "✅ Token qabul qilindi: @{username}\n\nEndi tarifni tanlang:"
