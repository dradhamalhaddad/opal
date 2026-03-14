import json
import logging
import re
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

from config import PLANS, OWNER_USERNAME
from database import (
    get_workspace_by_id, get_channels, get_settings, get_last_broadcast, update_cooldown,
    get_blackout_hours, log_broadcast, create_scheduled, create_approval,
    is_admin_draft_only, get_templates, get_template, get_workspace
)
from keyboards import (
    channel_select_keyboard, broadcast_options_keyboard, confirm_cancel_keyboard,
    approval_keyboard, templates_keyboard, back_keyboard
)
from message_builder import build_message
from middlewares import get_role
from translations import t

logger = logging.getLogger(__name__)

# ── ConversationHandler states ────────────────────────────────────────────────
WAITING_TEXT        = 1
SELECTING_CHANNELS  = 2
BROADCAST_OPTIONS   = 3
WAITING_SCHEDULE    = 4
WAITING_INLINE      = 5
CONFIRM_BROADCAST   = 6


def _ws_id(context) -> int:
    return context.user_data.get("ctx_ws_id") or context.user_data.get("_ws_id", 0)


def _is_pro(ws: dict) -> bool:
    return ws.get("plan") == "pro" and ws.get("is_active")


def _channel_label(ch: dict) -> str:
    return ch.get("channel_username") or str(ch["channel_id"])


def _is_in_blackout(start: int, end: int) -> bool:
    h = datetime.now().hour
    return (h >= start or h < end) if start > end else (start <= h < end)


async def _get_ws(context, user_id: int) -> dict | None:
    ws_id = _ws_id(context)
    if ws_id:
        return await get_workspace_by_id(ws_id)
    return await get_workspace(user_id)


async def _check_cooldown(ws: dict) -> tuple[bool, int, int]:
    """Returns (is_cooling, minutes_left, seconds_left)"""
    from config import PLANS
    plan_info = PLANS.get(ws["plan"], PLANS["basic"])
    cooldown_min = ws.get("custom_cooldown_minutes") or plan_info["cooldown_minutes"]
    last = await get_last_broadcast(ws["id"])
    if not last:
        return False, 0, 0
    elapsed = (datetime.now() - datetime.fromisoformat(last)).total_seconds()
    remaining = cooldown_min * 60 - elapsed
    if remaining > 0:
        return True, int(remaining // 60), int(remaining % 60)
    return False, 0, 0


# ── Entry points ──────────────────────────────────────────────────────────────

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry: callback do_broadcast or do_named_templates."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await __lang(user_id)

    ws = await _get_ws(context, user_id)
    if not ws or not ws["is_active"]:
        await query.edit_message_text(t("subscription_inactive", lang, owner=OWNER_USERNAME),
                                      parse_mode="HTML")
        return ConversationHandler.END

    # Check if using a named template
    if query.data == "do_named_templates":
        templates = await get_templates(ws["id"])
        if not templates:
            await query.edit_message_text(t("named_templates_empty", lang), parse_mode="HTML",
                                          reply_markup=back_keyboard(lang))
            return ConversationHandler.END
        context.user_data["broadcast_use_template"] = True
        await query.edit_message_text(t("named_templates_menu", lang), parse_mode="HTML",
                                      reply_markup=templates_keyboard(templates, lang, use_mode=True))
        return WAITING_TEXT

    context.user_data["broadcast_use_template"] = False
    await query.edit_message_text(t("send_broadcast_text", lang), parse_mode="HTML")
    return WAITING_TEXT


async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive broadcast text."""
    user_id = update.effective_user.id
    lang    = await __lang(user_id)
    ws      = await _get_ws(context, user_id)

    if not ws:
        await update.message.reply_text(t("error", lang), parse_mode="HTML")
        return ConversationHandler.END

    # Check blackout (Pro)
    if _is_pro(ws):
        bh = await get_blackout_hours(ws["id"])
        if bh and _is_in_blackout(bh["start_hour"], bh["end_hour"]):
            await update.message.reply_text(
                t("blackout_active", lang, start=bh["start_hour"], end=bh["end_hour"]),
                parse_mode="HTML")
            return ConversationHandler.END

    # Cooldown check
    cooling, mins, secs = await _check_cooldown(ws)
    if cooling:
        await update.message.reply_text(
            t("cooldown_active", lang, minutes=mins, seconds=secs), parse_mode="HTML")
        return ConversationHandler.END

    text = update.message.text.strip()
    context.user_data["bcast_text"] = text
    context.user_data["_ws_id"]     = ws["id"]

    is_pro  = _is_pro(ws)
    is_owner = (ws["owner_id"] == user_id)

    # Pro: channel selection
    if is_pro:
        channels = await get_channels(ws["id"])
        if not channels:
            await update.message.reply_text(t("no_channels_to_broadcast", lang), parse_mode="HTML")
            return ConversationHandler.END
        # pre-select all
        context.user_data["bcast_selected"] = {c["channel_id"] for c in channels}
        await update.message.reply_text(
            t("select_channels", lang), parse_mode="HTML",
            reply_markup=channel_select_keyboard(channels, context.user_data["bcast_selected"], lang))
        return SELECTING_CHANNELS

    # Basic: go straight to confirm
    settings = await get_settings(ws["id"])
    final = build_message(text, settings, update.effective_user.full_name,
                          update.effective_user.username)
    context.user_data["bcast_final"]    = final
    context.user_data["bcast_channels"] = None  # all
    await update.message.reply_text(
        t("broadcast_preview", lang, message=final), parse_mode="HTML",
        reply_markup=confirm_cancel_keyboard(lang))
    return CONFIRM_BROADCAST


async def receive_template_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User tapped a named template."""
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await __lang(user_id)
    ws      = await _get_ws(context, user_id)

    name = query.data.replace("tpl_use_", "")
    tpl  = await get_template(ws["id"], name)
    if not tpl:
        await query.edit_message_text(t("error", lang), parse_mode="HTML")
        return ConversationHandler.END

    context.user_data["bcast_text"] = tpl["content"]
    context.user_data["_ws_id"]     = ws["id"]

    channels = await get_channels(ws["id"])
    if not channels:
        await query.edit_message_text(t("no_channels_to_broadcast", lang), parse_mode="HTML")
        return ConversationHandler.END

    context.user_data["bcast_selected"] = {c["channel_id"] for c in channels}
    await query.edit_message_text(
        t("select_channels", lang), parse_mode="HTML",
        reply_markup=channel_select_keyboard(channels, context.user_data["bcast_selected"], lang))
    return SELECTING_CHANNELS


async def toggle_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle a channel in the selection."""
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await __lang(user_id)
    ws      = await _get_ws(context, user_id)
    channels = await get_channels(ws["id"])
    selected = context.user_data.get("bcast_selected", set())

    if query.data == "chsel_all":
        selected = {c["channel_id"] for c in channels}
    elif query.data == "chsel_clear":
        selected = set()
    elif query.data.startswith("chsel_"):
        cid = query.data[len("chsel_"):]
        selected ^= {cid}

    context.user_data["bcast_selected"] = selected
    await query.edit_message_reply_markup(
        reply_markup=channel_select_keyboard(channels, selected, lang))
    return SELECTING_CHANNELS


async def channel_select_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Proceed after channel selection."""
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await __lang(user_id)
    ws      = await _get_ws(context, user_id)

    selected = context.user_data.get("bcast_selected", set())
    if not selected:
        await query.answer(t("no_channels_selected", lang), show_alert=True)
        return SELECTING_CHANNELS

    context.user_data["bcast_channels"] = list(selected)
    is_owner = (ws["owner_id"] == user_id)

    await query.edit_message_text(
        t("broadcast_options", lang), parse_mode="HTML",
        reply_markup=broadcast_options_keyboard(lang, is_owner))
    return BROADCAST_OPTIONS


async def broadcast_option_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose 'Send Now'."""
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await __lang(user_id)
    ws      = await _get_ws(context, user_id)

    text     = context.user_data["bcast_text"]
    settings = await get_settings(ws["id"])
    final    = build_message(text, settings, query.from_user.full_name,
                             query.from_user.username)
    context.user_data["bcast_final"] = final

    await query.edit_message_text(
        t("broadcast_preview", lang, message=final), parse_mode="HTML",
        reply_markup=confirm_cancel_keyboard(lang))
    return CONFIRM_BROADCAST


async def broadcast_option_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose 'Schedule'."""
    query = update.callback_query
    await query.answer()
    lang  = await __lang(query.from_user.id)
    await query.edit_message_text(t("send_schedule_time", lang), parse_mode="HTML")
    return WAITING_SCHEDULE


async def broadcast_option_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose 'Add Button'."""
    query = update.callback_query
    await query.answer()
    lang  = await __lang(query.from_user.id)
    await query.edit_message_text(t("send_inline_btn", lang), parse_mode="HTML")
    return WAITING_INLINE


async def receive_schedule_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parse and store scheduled time."""
    user_id = update.effective_user.id
    lang    = await __lang(user_id)
    ws      = await _get_ws(context, user_id)
    raw     = update.message.text.strip()

    scheduled_at = _parse_time(raw)
    if not scheduled_at:
        await update.message.reply_text(t("schedule_invalid", lang), parse_mode="HTML")
        return WAITING_SCHEDULE
    if scheduled_at <= datetime.now():
        await update.message.reply_text(t("schedule_past", lang), parse_mode="HTML")
        return WAITING_SCHEDULE

    text     = context.user_data["bcast_text"]
    settings = await get_settings(ws["id"])
    final    = build_message(text, settings, update.effective_user.full_name,
                             update.effective_user.username)

    selected   = context.user_data.get("bcast_channels")
    inline_txt = context.user_data.get("bcast_inline_txt")
    inline_url = context.user_data.get("bcast_inline_url")
    should_pin = bool(settings.get("auto_pin"))

    await create_scheduled(ws["id"], user_id, text, final,
                           scheduled_at.isoformat(), selected,
                           inline_txt, inline_url, should_pin)

    await update.message.reply_text(
        t("scheduled_ok", lang, time=scheduled_at.strftime("%Y-%m-%d %H:%M")),
        parse_mode="HTML")
    context.user_data.clear()
    return ConversationHandler.END


async def receive_inline_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parse inline button text|url."""
    user_id = update.effective_user.id
    lang    = await __lang(user_id)
    ws      = await _get_ws(context, user_id)
    raw     = update.message.text.strip()

    if "|" not in raw:
        await update.message.reply_text(t("inline_btn_invalid", lang), parse_mode="HTML")
        return WAITING_INLINE

    parts = raw.split("|", 1)
    btn_text = parts[0].strip()
    btn_url  = parts[1].strip()

    if not btn_url.startswith("http"):
        await update.message.reply_text(t("inline_btn_invalid", lang), parse_mode="HTML")
        return WAITING_INLINE

    context.user_data["bcast_inline_txt"] = btn_text
    context.user_data["bcast_inline_url"] = btn_url

    text     = context.user_data["bcast_text"]
    settings = await get_settings(ws["id"])
    final    = build_message(text, settings, update.effective_user.full_name,
                             update.effective_user.username)
    context.user_data["bcast_final"] = final

    await update.message.reply_text(
        t("inline_btn_set", lang, text=btn_text) + "\n\n" +
        t("broadcast_preview", lang, message=final),
        parse_mode="HTML",
        reply_markup=confirm_cancel_keyboard(lang))
    return CONFIRM_BROADCAST


async def confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the broadcast."""
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await __lang(user_id)
    ws      = await _get_ws(context, user_id)

    if not ws:
        await query.edit_message_text(t("error", lang), parse_mode="HTML")
        return ConversationHandler.END

    is_owner   = (ws["owner_id"] == user_id)
    settings   = await get_settings(ws["id"])
    text       = context.user_data.get("bcast_text", "")
    final      = context.user_data.get("bcast_final", text)
    selected   = context.user_data.get("bcast_channels")  # None = all
    inline_txt = context.user_data.get("bcast_inline_txt") or settings.get("inline_btn_text")
    inline_url = context.user_data.get("bcast_inline_url") or settings.get("inline_btn_url")
    should_pin = bool(settings.get("auto_pin")) and is_owner

    # Draft-only check
    if not is_owner and await is_admin_draft_only(ws["id"], user_id):
        # Create approval request
        approval_id = await create_approval(
            ws["id"], user_id, text, final, selected, inline_txt, inline_url, should_pin)
        # Notify owner
        owner_ws = await get_workspace_by_id(ws["id"])
        sender_name = query.from_user.full_name or str(user_id)
        channels    = await get_channels(ws["id"])
        ch_names    = ", ".join(_channel_label(c) for c in channels
                                if not selected or c["channel_id"] in selected)
        try:
            await query.bot.send_message(
                chat_id=ws["owner_id"],
                text=t("approval_request", lang, sender=sender_name, channels=ch_names, text=final),
                parse_mode="HTML",
                reply_markup=approval_keyboard(approval_id, lang))
        except Exception:
            pass
        await query.edit_message_text(t("approval_pending_notice", lang), parse_mode="HTML")
        context.user_data.clear()
        return ConversationHandler.END

    # Approval mode (Pro, owner enabled it)
    if _is_pro(ws) and settings.get("approval_required") and not is_owner:
        approval_id = await create_approval(
            ws["id"], user_id, text, final, selected, inline_txt, inline_url, should_pin)
        sender_name = query.from_user.full_name or str(user_id)
        channels    = await get_channels(ws["id"])
        ch_names    = ", ".join(_channel_label(c) for c in channels
                                if not selected or c["channel_id"] in selected)
        try:
            await query.bot.send_message(
                chat_id=ws["owner_id"],
                text=t("approval_request", lang, sender=sender_name, channels=ch_names, text=final),
                parse_mode="HTML",
                reply_markup=approval_keyboard(approval_id, lang))
        except Exception:
            pass
        await query.edit_message_text(t("approval_pending_notice", lang), parse_mode="HTML")
        context.user_data.clear()
        return ConversationHandler.END

    # Send now
    await _do_send(query.bot, ws, final, selected, inline_txt, inline_url,
                   should_pin, user_id, text, lang, query)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang  = await __lang(query.from_user.id)
    context.user_data.clear()
    await query.edit_message_text(t("cancelled", lang), parse_mode="HTML")
    return ConversationHandler.END


# ── Approval callbacks ────────────────────────────────────────────────────────

async def handle_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database import get_approval, resolve_approval
    query       = update.callback_query
    await query.answer()
    approval_id = int(query.data.split("_")[1])
    lang        = await __lang(query.from_user.id)

    ap = await get_approval(approval_id)
    if not ap or ap["status"] != "pending":
        await query.edit_message_text("⚠️ Already resolved.", parse_mode="HTML")
        return

    ws       = await get_workspace_by_id(ap["workspace_id"])
    selected = json.loads(ap["selected_channels"]) if ap.get("selected_channels") else None

    await _do_send(query.bot, ws, ap["final_message"], selected,
                   ap.get("inline_btn_text"), ap.get("inline_btn_url"),
                   bool(ap["should_pin"]), ap["admin_id"], ap["message_text"], lang, query,
                   owner_lang=lang)
    await resolve_approval(approval_id, "approved")

    # Notify admin
    try:
        await query.bot.send_message(ap["admin_id"], t("approval_approved", lang), parse_mode="HTML")
    except Exception:
        pass

    await query.edit_message_text(t("approval_notif_approved", lang), parse_mode="HTML")


async def handle_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database import get_approval, resolve_approval
    query       = update.callback_query
    await query.answer()
    approval_id = int(query.data.split("_")[1])
    lang        = await __lang(query.from_user.id)

    ap = await get_approval(approval_id)
    if not ap or ap["status"] != "pending":
        await query.edit_message_text("⚠️ Already resolved.", parse_mode="HTML")
        return

    await resolve_approval(approval_id, "rejected")
    try:
        await query.bot.send_message(ap["admin_id"], t("approval_rejected", lang), parse_mode="HTML")
    except Exception:
        pass
    await query.edit_message_text(t("approval_notif_rejected", lang), parse_mode="HTML")


# ── Core send logic ───────────────────────────────────────────────────────────

async def _do_send(bot, ws: dict, final: str, selected: list | None,
                   inline_txt: str | None, inline_url: str | None,
                   should_pin: bool, admin_id: int, raw_text: str,
                   lang: str, query=None, owner_lang: str = None):
    from database import get_channels as _gc
    channels = await _gc(ws["id"])
    targets  = [c for c in channels if not selected or c["channel_id"] in selected]

    # Build inline markup if needed
    markup = None
    if inline_txt and inline_url:
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(inline_txt, url=inline_url)]])

    ok, fail = 0, 0
    sent_channels = []
    for ch in targets:
        try:
            msg = await bot.send_message(
                chat_id=ch["channel_id"], text=final,
                parse_mode="HTML", reply_markup=markup)
            if should_pin:
                try:
                    await bot.pin_chat_message(ch["channel_id"], msg.message_id)
                except Exception:
                    pass
            ok += 1
            sent_channels.append(_channel_label(ch))
        except Exception as e:
            logger.error(f"Failed to send to {ch['channel_id']}: {e}")
            fail += 1

    await update_cooldown(ws["id"])
    broadcast_id = await log_broadcast(
        ws["id"], admin_id, raw_text, final, ok,
        selected, inline_txt, inline_url, should_pin)

    # Notify sender
    msg_out = t("broadcast_sent", lang, count=ok)
    if query:
        await query.edit_message_text(msg_out, parse_mode="HTML")
    else:
        try:
            await bot.send_message(admin_id, msg_out, parse_mode="HTML")
        except Exception:
            pass

    # Send log to owner
    settings = await get_settings(ws["id"])
    if settings.get("log_enabled", 1) and ws["owner_id"] != admin_id:
        ol = owner_lang or "en"
        pin_line = t("log_pinned_line", ol) if should_pin else ""
        try:
            sender_info = f"<a href='tg://user?id={admin_id}'>{admin_id}</a>"
            ch_str      = ", ".join(sent_channels)
            await bot.send_message(
                chat_id=ws["owner_id"],
                text=t("broadcast_log_entry", ol,
                       sender=sender_info,
                       channels=ch_str,
                       time=datetime.now().strftime("%H:%M"),
                       pin_line=pin_line,
                       ok=ok, fail=fail,
                       text=raw_text),
                parse_mode="HTML")
        except Exception as e:
            logger.error(f"Log to owner failed: {e}")


# ── Time parser ───────────────────────────────────────────────────────────────

def _parse_time(raw: str) -> datetime | None:
    # Relative: +2h, +30m
    m = re.match(r'^\+(\d+)(h|m)$', raw.strip(), re.IGNORECASE)
    if m:
        val, unit = int(m.group(1)), m.group(2).lower()
        return datetime.now() + (timedelta(hours=val) if unit == "h" else timedelta(minutes=val))
    # Absolute
    for fmt in ("%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            pass
    return None


# ── Lang helper ───────────────────────────────────────────────────────────────

async def __lang(user_id: int) -> str:
    from database import get_user_lang
    return await get_user_lang(user_id)


# ── ConversationHandler builder ───────────────────────────────────────────────

def build_broadcast_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_broadcast,          pattern="^do_broadcast$"),
            CallbackQueryHandler(start_broadcast,          pattern="^do_named_templates$"),
        ],
        states={
            WAITING_TEXT: [
                CallbackQueryHandler(receive_template_choice, pattern="^tpl_use_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text),
            ],
            SELECTING_CHANNELS: [
                CallbackQueryHandler(toggle_channel,       pattern="^chsel_(?!done)"),
                CallbackQueryHandler(channel_select_done,  pattern="^chsel_done$"),
            ],
            BROADCAST_OPTIONS: [
                CallbackQueryHandler(broadcast_option_now,      pattern="^bopt_now$"),
                CallbackQueryHandler(broadcast_option_schedule, pattern="^bopt_schedule$"),
                CallbackQueryHandler(broadcast_option_inline,   pattern="^bopt_inline$"),
                CallbackQueryHandler(cancel_broadcast,          pattern="^cancel_broadcast$"),
            ],
            WAITING_SCHEDULE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_schedule_time),
            ],
            WAITING_INLINE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_inline_btn),
            ],
            CONFIRM_BROADCAST: [
                CallbackQueryHandler(confirm_broadcast, pattern="^confirm_broadcast$"),
                CallbackQueryHandler(cancel_broadcast,  pattern="^cancel_broadcast$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_broadcast, pattern="^cancel_broadcast$"),
            CommandHandler("cancel", lambda u, c: (c.user_data.clear(),
                                                    ConversationHandler.END)),
        ],
        per_message=False,
    )
