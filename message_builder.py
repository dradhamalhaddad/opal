from telegram.helpers import escape_markdown

DIVIDER = "─────────────────"


def build_message(text: str, sender_name: str, sender_username: str | None, settings: dict) -> str:
    """
    Builds the final broadcast message with header/footer/sender info.
    Returns a MarkdownV2-escaped string.
    """
    header = settings.get("header_text") or ""
    footer = settings.get("footer_text") or ""
    show_sender = bool(settings.get("show_sender_info", 0))

    parts = []

    # Header
    if header.strip():
        parts.append(escape_markdown(header, version=2))
        parts.append(escape_markdown(DIVIDER, version=2))

    # Main message
    parts.append(escape_markdown(text, version=2))

    # Footer / sender info
    has_footer = bool(footer.strip())
    has_sender = show_sender

    if has_footer or has_sender:
        parts.append(escape_markdown(DIVIDER, version=2))
        if has_footer:
            parts.append(escape_markdown(footer, version=2))
        if has_sender:
            if sender_username:
                sender_line = f"📢 via @{sender_username}"
            else:
                sender_line = f"📢 via {sender_name}"
            parts.append(escape_markdown(sender_line, version=2))

    return "\n".join(parts)
