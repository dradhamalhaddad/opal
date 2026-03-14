import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CallbackQueryHandler, filters
)

from config import OWNER_USERNAME, PLANS
from database import (
    get_workspace_by_id, get_workspace, get_settings, upsert_settings,
    set_custom_cooldown, set_blackout_hours, clear_blackout_hours,
    get_admins, set_admin_draft_only, get_user_lang
)
from keyboards import (
    cooldown_keyboard, blackout_keyboard, back_keyboard,
    pro_settings_keyboard, template_keyboard
)
from translations import t

logger = logging.getLogger(__name__)

WAITING_COOLDOWN = 200
WAITING_BLACKOUT = 201
WAITING_INLINE   = 202
TPL_HEADER       = 10
TPL_FOOTER       = 11


def _ws_id(ctx): return ctx.user_data.get("ctx_ws_id") or ctx.user_data.get("_ws_id", 0)


async def _get_ws(context, user_id):
    ws_id = _ws_id(context)
    return await get_workspace_by_id(ws_id) if ws_id else await get_workspace(user_id)


async def _lang(uid): return await get_user_lang(uid)


def _is_pro(ws): return ws and ws.get("plan") == "pro" and ws.get("is_active")


# ── Cooldown ──────────────────────────────────────────────────────────────────

async def handle_cooldown_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query; await q.answer()
    uid  = q.from_user.id; lang = await _lang(uid)
    ws   = await _get_ws(context, uid)
    if not ws or not _is_pro(ws):
        await q.edit_message_text(t("cooldown_pro_only", lang, parse_mode="HTML"), parse_mode="HTML",
                                  reply_markup=back_keyboard(lang)); return
    plan_info = PLANS[ws["plan"]]
    current   = ws.get("custom_cooldown_minutes") or plan_info["cooldown_minutes"]
    await q.edit_message_text(
        t("cooldown_settings_title", lang, current=current, parse_mode="HTML"), parse_mode="HTML",
        reply_markup=cooldown_keyboard(lang))
    context.user_data["setting_ws_id"] = ws["id"]


async def handle_cooldown_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    await set_custom_cooldown(ws["id"], None)
    await q.edit_message_text(t("cooldown_reset", lang, parse_mode="HTML"), parse_mode="HTML",
                               reply_markup=back_keyboard(lang))


# ── Blackout ──────────────────────────────────────────────────────────────────

async def handle_blackout_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    if not ws or not _is_pro(ws):
        await q.edit_message_text(t("blackout_pro_only", lang, parse_mode="HTML"), parse_mode="HTML",
                                  reply_markup=back_keyboard(lang)); return
    from database import get_blackout_hours
    bh  = await get_blackout_hours(ws["id"])
    cur = t("blackout_current", lang, start=bh["start_hour"], end=bh["end_hour"]) if bh \
          else t("blackout_none", lang)
    await q.edit_message_text(
        t("blackout_menu_title", lang, current=cur, parse_mode="HTML"), parse_mode="HTML",
        reply_markup=blackout_keyboard(lang, bool(bh)))
    context.user_data["setting_ws_id"] = ws["id"]


async def handle_blackout_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = await _lang(q.from_user.id)
    await q.edit_message_text(t("send_blackout_range", lang, parse_mode="HTML"), parse_mode="HTML")
    return WAITING_BLACKOUT


async def receive_blackout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id; lang = await _lang(uid)
    ws   = await _get_ws(context, uid)
    raw  = update.message.text.strip()
    try:
        parts = raw.split("-")
        s, e  = int(parts[0].strip()), int(parts[1].strip())
        assert 0 <= s <= 23 and 0 <= e <= 23
    except Exception:
        await update.message.reply_text(t("blackout_invalid", lang, parse_mode="HTML"), parse_mode="HTML")
        return WAITING_BLACKOUT
    await set_blackout_hours(ws["id"], s, e)
    await update.message.reply_text(t("blackout_set", lang, start=s, end=e, parse_mode="HTML"), parse_mode="HTML",
                                    reply_markup=back_keyboard(lang))
    return ConversationHandler.END


async def handle_blackout_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    await clear_blackout_hours(ws["id"])
    await q.edit_message_text(t("blackout_cleared", lang, parse_mode="HTML"), parse_mode="HTML",
                               reply_markup=back_keyboard(lang))


# ── Template (header/footer) ──────────────────────────────────────────────────

async def handle_template_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    if not ws or not _is_pro(ws):
        await q.edit_message_text(t("template_pro_only", lang, parse_mode="HTML"), parse_mode="HTML",
                                  reply_markup=back_keyboard(lang)); return
    s   = await get_settings(ws["id"])
    hdr = s.get("header_text") or t("none_set", lang)
    ftr = s.get("footer_text") or t("none_set", lang)
    sen = t("enabled", lang) if s.get("show_sender_info") else t("disabled", lang)
    await q.edit_message_text(
        t("template_current", lang, header=hdr, footer=ftr, sender_info=sen, parse_mode="HTML"),
        parse_mode="HTML",
        reply_markup=template_keyboard(lang, bool(s.get("show_sender_info"))))
    context.user_data["setting_ws_id"] = ws["id"]


async def handle_set_header(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = await _lang(q.from_user.id)
    await q.edit_message_text(t("send_header_text", lang, parse_mode="HTML"), parse_mode="HTML")
    return TPL_HEADER


async def handle_set_footer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = await _lang(q.from_user.id)
    await q.edit_message_text(t("send_footer_text", lang, parse_mode="HTML"), parse_mode="HTML")
    return TPL_FOOTER


async def receive_header(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    await upsert_settings(ws["id"], header_text=update.message.text.strip())
    await update.message.reply_text(t("header_set", lang, parse_mode="HTML"), parse_mode="HTML",
                                    reply_markup=back_keyboard(lang))
    return ConversationHandler.END


async def receive_footer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    await upsert_settings(ws["id"], footer_text=update.message.text.strip())
    await update.message.reply_text(t("footer_set", lang, parse_mode="HTML"), parse_mode="HTML",
                                    reply_markup=back_keyboard(lang))
    return ConversationHandler.END


async def handle_clear_header(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    await upsert_settings(ws["id"], header_text=None)
    await q.edit_message_text(t("header_cleared", lang, parse_mode="HTML"), parse_mode="HTML",
                               reply_markup=back_keyboard(lang))


async def handle_clear_footer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    await upsert_settings(ws["id"], footer_text=None)
    await q.edit_message_text(t("footer_cleared", lang, parse_mode="HTML"), parse_mode="HTML",
                               reply_markup=back_keyboard(lang))


async def handle_toggle_sender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    s   = await get_settings(ws["id"])
    new = 0 if s.get("show_sender_info") else 1
    await upsert_settings(ws["id"], show_sender_info=new)
    msg = t("sender_info_on", lang) if new else t("sender_info_off", lang)
    await q.edit_message_text(msg, parse_mode="HTML", reply_markup=back_keyboard(lang))


async def handle_template_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    from message_builder import build_message
    s    = await get_settings(ws["id"])
    prev = build_message(t("sample_broadcast_text", lang), s, q.from_user.full_name,
                         q.from_user.username)
    await q.edit_message_text(
        t("template_preview_title", lang, parse_mode="HTML") + "\n\n" + prev,
        parse_mode="HTML", reply_markup=back_keyboard(lang))


# ── Pro owner settings ────────────────────────────────────────────────────────

async def handle_pro_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    if not ws or not _is_pro(ws) or ws["owner_id"] != uid:
        await q.edit_message_text(t("not_authorized", lang, parse_mode="HTML"), parse_mode="HTML"); return
    s = await get_settings(ws["id"])
    await q.edit_message_text(
        t("pro_settings_title", lang, parse_mode="HTML"), parse_mode="HTML",
        reply_markup=pro_settings_keyboard(lang,
            bool(s.get("approval_required")),
            bool(s.get("auto_pin")),
            bool(s.get("log_enabled", 1))))


async def handle_prosetting_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    if not ws or ws["owner_id"] != uid:
        await q.answer(t("not_authorized", lang), show_alert=True); return

    s   = await get_settings(ws["id"])
    key = {"prosetting_approval": "approval_required",
           "prosetting_pin":      "auto_pin",
           "prosetting_log":      "log_enabled"}.get(q.data)
    if key:
        await upsert_settings(ws["id"], **{key: 0 if s.get(key, 0 if key != "log_enabled" else 1) else 1})

    s2 = await get_settings(ws["id"])
    await q.edit_message_text(
        t("pro_settings_title", lang, parse_mode="HTML"), parse_mode="HTML",
        reply_markup=pro_settings_keyboard(lang,
            bool(s2.get("approval_required")),
            bool(s2.get("auto_pin")),
            bool(s2.get("log_enabled", 1))))


async def handle_prosetting_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = await _lang(q.from_user.id)
    ws   = await _get_ws(context, q.from_user.id)
    s    = await get_settings(ws["id"])
    cur  = f"\n\nالحالي: <b>{s['inline_btn_text']}</b> → {s['inline_btn_url']}" \
           if s.get("inline_btn_text") else ""
    await q.edit_message_text(t("send_inline_btn", lang, parse_mode="HTML") + cur, parse_mode="HTML")
    return WAITING_INLINE


async def receive_prosetting_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id; lang = await _lang(uid)
    ws   = await _get_ws(context, uid)
    raw  = update.message.text.strip()
    if raw.lower() in ("clear", "حذف", "مسح"):
        await upsert_settings(ws["id"], inline_btn_text=None, inline_btn_url=None)
        await update.message.reply_text(t("inline_btn_cleared", lang, parse_mode="HTML"), parse_mode="HTML",
                                        reply_markup=back_keyboard(lang))
        return ConversationHandler.END
    if "|" not in raw:
        await update.message.reply_text(t("inline_btn_invalid", lang, parse_mode="HTML"), parse_mode="HTML")
        return WAITING_INLINE
    parts    = raw.split("|", 1)
    btn_text = parts[0].strip()
    btn_url  = parts[1].strip()
    if not btn_url.startswith("http"):
        await update.message.reply_text(t("inline_btn_invalid", lang, parse_mode="HTML"), parse_mode="HTML")
        return WAITING_INLINE
    await upsert_settings(ws["id"], inline_btn_text=btn_text, inline_btn_url=btn_url)
    await update.message.reply_text(t("inline_btn_set", lang, text=btn_text, parse_mode="HTML"), parse_mode="HTML",
                                    reply_markup=back_keyboard(lang))
    return ConversationHandler.END


async def handle_prosetting_draft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin list to toggle draft-only."""
    q   = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    if not ws or ws["owner_id"] != uid:
        await q.answer(t("not_authorized", lang), show_alert=True); return

    admins = await get_admins(ws["id"])
    if not admins:
        await q.edit_message_text(t("no_admins", lang, parse_mode="HTML"), parse_mode="HTML",
                                  reply_markup=back_keyboard(lang)); return

    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    rows = []
    for adm in admins:
        icon  = "✏️" if adm.get("draft_only") else "🚀"
        label = f"{icon} {adm.get('display_name') or adm['user_id']}"
        rows.append([InlineKeyboardButton(label, callback_data=f"drafttoggle_{adm['user_id']}")])
    rows.append([InlineKeyboardButton(t("btn_back", lang), callback_data="menu_back")])
    await q.edit_message_text(t("draft_only_menu", lang, parse_mode="HTML"), parse_mode="HTML",
                               reply_markup=InlineKeyboardMarkup(rows))


async def handle_draft_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q       = update.callback_query; await q.answer()
    uid     = q.from_user.id; lang = await _lang(uid)
    ws      = await _get_ws(context, uid)
    adm_id  = int(q.data.split("_")[1])
    admins  = await get_admins(ws["id"])
    adm     = next((a for a in admins if a["user_id"] == adm_id), None)
    if not adm:
        return
    new_val = not bool(adm.get("draft_only"))
    await set_admin_draft_only(ws["id"], adm_id, new_val)
    status  = t("enabled", lang) if new_val else t("disabled", lang)
    name    = adm.get("display_name") or str(adm_id)
    await q.answer(t("draft_only_set", lang, user=name, status=status), show_alert=True)
    # Re-render
    await handle_prosetting_draft(update, context)


# ── Stats ─────────────────────────────────────────────────────────────────────

async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    if not ws or not _is_pro(ws):
        await q.edit_message_text(t("stats_pro_only", lang, parse_mode="HTML"), parse_mode="HTML",
                                  reply_markup=back_keyboard(lang)); return
    from database import get_broadcast_stats
    s = await get_broadcast_stats(ws["id"])
    await q.edit_message_text(
        t("stats_title", lang,
          total=s["total"], month=s["month"],
          reaches=s["reaches"], last=s["last"] or "—", parse_mode="HTML"),
        parse_mode="HTML", reply_markup=back_keyboard(lang))


# ── Log viewer ────────────────────────────────────────────────────────────────

async def handle_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    if not ws or ws["owner_id"] != uid:
        await q.edit_message_text(t("not_authorized", lang, parse_mode="HTML"), parse_mode="HTML"); return
    from database import get_broadcast_log
    entries = await get_broadcast_log(ws["id"], limit=10)
    if not entries:
        await q.edit_message_text(t("log_empty", lang, parse_mode="HTML"), parse_mode="HTML",
                                  reply_markup=back_keyboard(lang)); return
    lines = [t("log_title", lang)]
    for e in entries:
        sender = e.get("display_name") or str(e.get("sender_id") or e.get("admin_id","?"))
        text   = (e.get("message_text") or "")[:40]
        lines.append(t("log_entry", lang,
                       time=str(e["sent_at"])[:16],
                       sender=sender,
                       channels=e["channels_count"],
                       text=text))
    await q.edit_message_text("\n".join(lines, parse_mode="HTML"), parse_mode="HTML",
                               reply_markup=back_keyboard(lang))


# ── Schedule viewer ───────────────────────────────────────────────────────────

async def handle_schedule_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    from database import get_pending_scheduled
    from keyboards import scheduled_list_keyboard
    scheds = await get_pending_scheduled(ws["id"])
    if not scheds:
        await q.edit_message_text(t("schedule_menu_empty", lang, parse_mode="HTML"), parse_mode="HTML",
                                  reply_markup=back_keyboard(lang)); return
    await q.edit_message_text("⏰", reply_markup=scheduled_list_keyboard(scheds, lang, parse_mode="HTML"))


async def handle_cancel_scheduled(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q       = update.callback_query; await q.answer()
    uid     = q.from_user.id; lang = await _lang(uid)
    ws      = await _get_ws(context, uid)
    sched_id= int(q.data.split("_")[2])
    from database import cancel_scheduled
    await cancel_scheduled(sched_id, ws["id"])
    await q.answer(t("scheduled_cancelled", lang), show_alert=True)
    await handle_schedule_menu(update, context)


# Needed for ConversationHandler import
from telegram.ext import ConversationHandler
