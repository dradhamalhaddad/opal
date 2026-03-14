"""
emoji_sender.py
Alternative to <tg-emoji> HTML — uses MessageEntity objects directly.
Works WITHOUT Premium Bot subscription.
"""
from telegram import MessageEntity
from typing import Optional


def _utf16_len(s: str) -> int:
    return len(s.encode('utf-16-le')) // 2


def _utf16_offset(s: str, py_index: int) -> int:
    return _utf16_len(s[:py_index])


# Same IDs from translations.py
EMOJI_IDS = {
    "✅": "5215492745900077682",
    "❌": "5852477713482255786",
    "🛡": "5895483165182529286",
    "💎": "5348318749877351830",
    "⭐": "5978878257406152193",
    "🥇": "5978741411158167019",
    "👀": "5267338666224660069",
    "👨‍💻": "5971889748615105853",
    "⏳": "5971837680726576448",
    "📱": "5852830669599674051",
}


def build_emoji_entities(text: str) -> list[MessageEntity]:
    """Build MessageEntity list for custom emojis in plain text."""
    entities = []
    for emoji, eid in EMOJI_IDS.items():
        start = 0
        while True:
            i = text.find(emoji, start)
            if i == -1:
                break
            off = _utf16_offset(text, i)
            ln  = _utf16_len(emoji)
            try:
                entities.append(MessageEntity(
                    type="custom_emoji",
                    offset=off,
                    length=ln,
                    custom_emoji_id=str(eid)
                ))
            except Exception:
                pass
            start = i + len(emoji)
    entities.sort(key=lambda e: e.offset)
    return entities


async def send_with_emoji(bot, chat_id: int, text: str, **kwargs) -> None:
    """
    Send a message using entities for custom emoji instead of HTML tags.
    Strip HTML bold/italic for simplicity, or keep text plain.
    """
    # Strip HTML tags from text for entity-based sending
    import re
    plain = re.sub(r'<[^>]+>', '', text)
    entities = build_emoji_entities(plain)
    if entities:
        await bot.send_message(chat_id=chat_id, text=plain, entities=entities, **kwargs)
    else:
        await bot.send_message(chat_id=chat_id, text=plain, **kwargs)
