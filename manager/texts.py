"""Manager bot matnlari (uz). Premium (custom) emoji avtomatik qo'llanadi.

Premium egali bot HTML parse_mode'da <tg-emoji> orqali custom (animatsiyali)
emoji yubora oladi. premiumize() har matndagi tanish emojini custom emojiga aylantiradi.
custom_emoji_id lar getForumTopicIconStickers dan (tekin, animatsiyali)."""
from __future__ import annotations

import re

# Emoji belgisi → custom_emoji_id. Variatsiya selektorli (️) variantlar BIRINCHI
# turishi kerak (aks holda oddiy variant ularni buzadi).
EMOJI_IDS: dict[str, str] = {
    '\U0001f468\u200d\U0001f469\u200d\U0001f467\u200d\U0001f466': "5386435923204382258",
    '\U0001f3f4\u200d\u2620\ufe0f': "5386395194029515402",
    '\U0001f46e\u200d\u2642\ufe0f': "5377494501373780436",
    '\u26a1\ufe0f': "5312016608254762256",
    '\u2757\ufe0f': "5379748062124056162",
    '\u2764\ufe0f': "5312138559556164615",
    '\u2049\ufe0f': "5377438129928020693",
    '\u203c\ufe0f': "5377498341074542641",
    '\u26bd\ufe0f': "5375159220280762629",
    '\u2708\ufe0f': "5348436127038579546",
    '\u26c5\ufe0f': "5350424168615649565",
    '\u2615\ufe0f': "5350392020785437399",
    '\u270d\ufe0f': "5238156910363950406",
    '\u2b50\ufe0f': "5235579393115438657",
    '\U0001f4f0': "5434144690511290129",
    '\U0001f4a1': "5312536423851630001",
    '\U0001f399': "5377544228505134960",
    '\U0001f51d': "5418085807791545980",
    '\U0001f5e3': "5370870893004203704",
    '\U0001f192': "5420216386448270341",
    '\U0001f4dd': "5373251851074415873",
    '\U0001f4c6': "5433614043006903194",
    '\U0001f4c1': "5357315181649076022",
    '\U0001f50e': "5309965701241379366",
    '\U0001f4e3': "5309984423003823246",
    '\U0001f525': "5312241539987020022",
    '\u2753': "5377316857231450742",
    '\U0001f4c8': "5350305691942788490",
    '\U0001f4c9': "5350713563512052787",
    '\U0001f48e': "5309958691854754293",
    '\U0001f4b0': "5350452584119279096",
    '\U0001f4b8': "5309929258443874898",
    '\U0001fa99': "5377690785674175481",
    '\U0001f4b1': "5310107765874632305",
    '\U0001f3ae': "5309950797704865693",
    '\U0001f4bb': "5350554349074391003",
    '\U0001f4f1': "5409357944619802453",
    '\U0001f697': "5312322066328853156",
    '\U0001f3e0': "5312486108309757006",
    '\U0001f498': "5310029292527164639",
    '\U0001f389': "5310228579009699834",
    '\U0001f3c6': "5312315739842026755",
    '\U0001f3c1': "5408906741125490282",
    '\U0001f3ac': "5368653135101310687",
    '\U0001f3b5': "5310045076531978942",
    '\U0001f51e': "5420331611830886484",
    '\U0001f4da': "5350481781306958339",
    '\U0001f451': "5357107601584693888",
    '\U0001f3c0': "5384327463629233871",
    '\U0001f4fa': "5350513667144163474",
    '\U0001f440': "5357121491508928442",
    '\U0001fae6': "5357185426392096577",
    '\U0001f353': "5310157398516703416",
    '\U0001f484': "5310262535021142850",
    '\U0001f460': "5368741306484925109",
    '\U0001f9f3': "5357120306097956843",
    '\U0001f3d6': "5310303848311562896",
    '\U0001f984': "5413625003218313783",
    '\U0001f6cd': "5350699789551935589",
    '\U0001f45c': "5377478880577724584",
    '\U0001f6d2': "5431492767249342908",
    '\U0001f682': "5350497316203668441",
    '\U0001f6e5': "5350422527938141909",
    '\U0001f3d4': "5418196338774907917",
    '\U0001f3d5': "5350648297189023928",
    '\U0001f916': "5309832892262654231",
    '\U0001faa9': "5350751634102166060",
    '\U0001f39f': "5377624166436445368",
    '\U0001f5f3': "5350387571199319521",
    '\U0001f393': "5357419403325481346",
    '\U0001f52d': "5368585403467048206",
    '\U0001f52c': "5377580546748588396",
    '\U0001f3b6': "5377317729109811382",
    '\U0001f3a4': "5382003830487523366",
    '\U0001f57a': "5357298525765902091",
    '\U0001f483': "5357370526597653193",
    '\U0001fa96': "5357188789351490453",
    '\U0001f4bc': "5348227245599105972",
    '\U0001f9ea': "5411138633765757782",
    '\U0001f476': "5377675010259297233",
    '\U0001f930': "5386609083400856174",
    '\U0001f485': "5368808634392257474",
    '\U0001f3db': "5350548830041415279",
    '\U0001f9ee': "5355127101970194557",
    '\U0001f5a8': "5386379624773066504",
    '\U0001fa7a': "5350307998340226571",
    '\U0001f48a': "5310094636159607472",
    '\U0001f489': "5310139157790596888",
    '\U0001f9fc': "5377468357907849200",
    '\U0001faaa': "5418115271267197333",
    '\U0001f6c3': "5372819184658949787",
    '\U0001f37d': "5350344462612570293",
    '\U0001f41f': "5384574037701696503",
    '\U0001f3a8': "5310039132297242441",
    '\U0001f3ad': "5350658016700013471",
    '\U0001f3a9': "5357504778685392027",
    '\U0001f52e': "5350367161514732241",
    '\U0001f379': "5350520238444126134",
    '\U0001f382': "5310132165583840589",
    '\U0001f363': "5350406176997646350",
    '\U0001f354': "5350403544182694064",
    '\U0001f355': "5350444672789519765",
    '\U0001f9a0': "5312424913615723286",
    '\U0001f4ac': "5417915203100613993",
    '\U0001f384': "5312054580060625569",
    '\U0001f383': "5309744892677727325",
    '\u2705': "5237699328843200968",
    '\U0001f396': "5238027455754680851",
    '\U0001f921': "5238234236955148254",
    '\U0001f9e0': "5237889595894414384",
    '\U0001f9ae': "5237999392438371490",
    '\U0001f408': "5235912661102773458",
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
