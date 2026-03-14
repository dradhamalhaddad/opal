"""
bot_core.py
Interceptor pattern: plain emoji in text → auto-wrapped as <tg-emoji> HTML before sending.
Guaranteed correct HTML — built programmatically, not manually.
"""
import re
from telegram import MessageEntity
from telegram.ext import ExtBot
from telegram import InlineKeyboardButton, KeyboardButton
from telegram.constants import ParseMode

# ── Emoji → custom_emoji_id mapping ──────────────────────────────────────────
# Plain emoji as written in translations.py → their animated ID
CUSTOM_EMOJI_ID = {
    # Original repo keys (preserved)
    "✅": "5215492745900077682",
    "❌": "5852812849780362931",
    "🛡": "5895483165182529286",
    "🟢": "5978741411158167019",
    "🟠": "5978878257406152193",
    "🤬": "5267338666224660069",
    "💎": "5348318749877351830",
    "💻": "5971889748615105853",
    "🔸": "5971837680726576448",
    "✈️": "5852830669599674051",
    "🔎": "5895476993314524652",
    # Extended mapping (from rol.py reference)
    "⚠️": "5938686976689020141",
    "💐": "5266636354860859799",
    "🎰": "5314107660240585993",
    "🔝": "5271697294989661096",
    "🎟️": "5272054512005716016",
    "🛠️": "5288527892922101303",
    "❓": "5271608930498614783",
    "✨": "5288455771842558503",
    "⭐️": "5266800750602648148",
    "💰": "5271587889584695690",
    "🏅": "5271597736544638235",
    "🎮": "5271624540558393119",
    "📣": "5271677047154437612",
    "🎁": "5272041695319810172",
    "💸": "5271661039890415629",
    "🏆": "5271607964965380292",
    "🎉": "5271624338060636495",
    "🎯": "5272058626989371617",
    "1️⃣": "5271655700448448476",
    "2️⃣": "5271699007244793019",
    "3️⃣": "5271758997890219516",
    "4️⃣": "5271662896573063175",
    "🔥": "5271652713870463622",
    "👇": "5271624606562304000",
    "⬇️": "5271736843439734388",
    "🧩": "5271624423392624640",
}


def _to_custom_emoji_html(text: str) -> str:
    """
    Replace plain emojis in text with <tg-emoji> HTML tags.
    Skips emojis already inside a tg-emoji tag.
    """
    if not text:
        return text

    result = []
    last = 0

    # Find all emoji occurrences in order
    pattern = re.compile("|".join(re.escape(e) for e in sorted(CUSTOM_EMOJI_ID, key=len, reverse=True)))

    for m in pattern.finditer(text):
        s, e = m.start(), m.end()

        # Check if already wrapped
        prefix = text[max(0, s - 60):s]
        if "<tg-emoji" in prefix and "</tg-emoji>" not in prefix:
            result.append(text[last:e])
            last = e
            continue

        result.append(text[last:s])
        emoji = m.group(0)
        eid   = CUSTOM_EMOJI_ID[emoji]
        result.append(f'<tg-emoji emoji-id="{eid}">{emoji}</tg-emoji>')
        last = e

    result.append(text[last:])
    return "".join(result)


# ── PatchedBot ────────────────────────────────────────────────────────────────

class PatchedBot(ExtBot):
    """
    Intercepts every outgoing message:
    1. Forces parse_mode=HTML if not set
    2. Wraps plain emojis with <tg-emoji> tags programmatically
    """

    def _patch(self, kwargs: dict) -> dict:
        pm = kwargs.get("parse_mode")
        if pm is None:
            kwargs["parse_mode"] = ParseMode.HTML

        if kwargs.get("parse_mode") == ParseMode.HTML:
            for field in ("text", "caption"):
                if isinstance(kwargs.get(field), str):
                    kwargs[field] = _to_custom_emoji_html(kwargs[field])

        return kwargs

    async def send_message(self, *args, **kwargs):
        return await super().send_message(*args, **self._patch(kwargs))

    async def edit_message_text(self, *args, **kwargs):
        return await super().edit_message_text(*args, **self._patch(kwargs))

    async def send_photo(self, *args, **kwargs):
        return await super().send_photo(*args, **self._patch(kwargs))

    async def send_document(self, *args, **kwargs):
        return await super().send_document(*args, **self._patch(kwargs))

    async def send_invoice(self, *args, **kwargs):
        return await super().send_invoice(*args, **kwargs)


# ── Button styles (Bot API 9.4) ───────────────────────────────────────────────

_SUCCESS = ("✅","نشر","تأكيد","confirm","publish","approve","موافقة",
            "تفعيل","activate","🚀","نعم","yes","إضافة","add",
            "⭐️ إذاعة للمشتركين Pro")
_DANGER  = ("❌","حذف","إلغاء","cancel","delete","remove","رفض",
            "reject","أوقف","deactivate","تعطيل","حظر","🗑",
            "رجوع","إغلاق")
_PRIMARY = ("💎","pro","اشترك","subscribe","upgrade","ترقية",
            "⭐","Stars","Crypto","💳")

def _style(text: str) -> str:
    t = (text or "").strip()
    if any(k in t for k in _SUCCESS): return "success"
    if any(k in t for k in _DANGER):  return "danger"
    return "primary"

def mk_ikb(text: str = "", **kwargs) -> InlineKeyboardButton:
    api_kwargs = dict(kwargs.pop("api_kwargs", None) or {})
    api_kwargs.setdefault("style", _style(text))
    return InlineKeyboardButton(text, api_kwargs=api_kwargs, **kwargs)

def mk_kb(text: str = "", **kwargs) -> KeyboardButton:
    api_kwargs = dict(kwargs.pop("api_kwargs", None) or {})
    api_kwargs.setdefault("style", _style(text))
    return KeyboardButton(text, api_kwargs=api_kwargs, **kwargs)
