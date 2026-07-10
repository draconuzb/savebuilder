"""Manager bot matnlari (uz). Premium emoji shu yerda qo'shiladi."""

WELCOME = (
    "🤖 <b>SaveBuilder — Telegram botlar yaratish uchun qulay platforma.</b>\n\n"
    "Bu platforma orqali siz hech qanday kod yozmasdan o'z Telegram "
    "botlaringizni tez va oson yaratishingiz, ularni tahrirlashingiz "
    "hamda boshqarishingiz mumkin.\n\n"
    "⚡️ <b>Nega aynan SaveBuilder?</b>\n"
    "• <b>Tez va oson</b> — Hech qanday kod yozmasdan o'z botingizni yaratishingiz mumkin.\n"
    "• <b>Qulay interfeys</b> — Foydalanish oson va qulay interfeys.\n"
    "• <b>Yaxshi qo'llab-quvvatlash</b> — Doimiy va tezkor qo'llab-quvvatlash xizmati!"
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
    "📇 <b>Hisobim</b>\n\n"
    "👤 Ism: {name}\n"
    "🆔 ID: <code>{tg_id}</code>\n"
    "💰 Balans: <b>{balance:,.0f}</b> so'm\n"
    "🤖 Botlar soni: <b>{bots}</b>"
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
    "📖 <b>Qo'llanma</b>\n\n"
    "1. «➕ Bot yaratish» → kategoriya va shablon tanlang.\n"
    "2. @BotFather'dan olingan tokenni yuboring.\n"
    "3. Tarifni tanlab, balansdan to'lang.\n"
    "4. Botingiz tayyor! «🤖 Botlarim» orqali boshqaring."
)

SUPPORT = "🧧 <b>Qo'llab-quvvatlash</b>\n\nSavollar bo'lsa: @your_support_username"

ASK_TOKEN = (
    "🔑 <b>{template} yaratish</b>\n\n"
    "@BotFather'dan olingan bot <b>tokenini</b> yuboring.\n"
    "Masalan: <code>123456789:AAE...xyz</code>"
)

TOKEN_INVALID = "❌ Token noto'g'ri yoki ishlamayapti. Qayta yuboring yoki /bekor bosing."
TOKEN_OK = "✅ Token qabul qilindi: @{username}\n\nEndi tarifni tanlang:"
