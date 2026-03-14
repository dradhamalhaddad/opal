import html

DIVIDER = "─────────────────"


def build_message(text: str, sender_name: str, sender_username: str | None, settings: dict) -> str:
    """
    Builds the final broadcast message with header/footer/sender info.
    Returns an HTML-safe string intended for parse_mode=HTML.
    """
    header = settings.get("header_text") or ""
    footer = settings.get("footer_text") or ""
    show_sender = bool(settings.get("show_sender_info", 0))

    parts = []

    # Header
    if header.strip():
        parts.append(html.escape(header))
        parts.append(html.escape(DIVIDER))

    # Main message
    parts.append(html.escape(text))

    # Footer / sender info
    has_footer = bool(footer.strip())
    has_sender = show_sender

    if has_footer or has_sender:
        parts.append(html.escape(DIVIDER))
        if has_footer:
            parts.append(html.escape(footer))
        if has_sender:
            if sender_username:
                sender_line = f"📢 via @{sender_username}"
            else:
                sender_line = f"📢 via {sender_name}"
            parts.append(html.escape(sender_line))

    return "\n".join(parts)
