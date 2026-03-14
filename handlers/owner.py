import html
import logging
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters,
)

from config import OWNER_ID, PLANS
from bot_core import mk_ikb
from database import (
    get_all_workspaces, get_workspace, activate_workspace, deactivate_workspace,
    extend_workspace, get_user_lang, lookup_user, lookup_workspace_by_channel,
    get_active_workspace_owner_ids, get_active_pro_workspace_owner_ids,
    get_admins, get_channels, count_admins, count_channels
)
from translations import t

logger = logging.getLogger(__name__)


def _is_owner(user_id): return user_id == OWNER_ID


async def cmd_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update.effective_user.id):
        return
    lang = await get_user_lang(update.effective_user.id)
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(t("usage_activate", lang), parse_mode="HTML")
        return
    try:
        user_id = int(args[0])
        plan    = args[1].lower()
        days    = int(args[2])
    except ValueError:
        await update.message.reply_text(t("usage_activate", lang), parse_mode="HTML")
        return

    if plan not in ("basic", "pro"):
        await update.message.reply_text("Plan must be basic or pro", parse_mode="HTML")
        return

    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
    await activate_workspace(user_id, plan, expiry)
    await update.message.reply_text(
        t("workspace_activated", lang, user_id=user_id, plan=plan, expiry=expiry),
        parse_mode="HTML")
    try:
        ul = await get_user_lang(user_id)
        await context.bot.send_message(
            user_id,
            t("notify_activated", ul, plan=plan.upper(), expiry=expiry),
            parse_mode="HTML")
    except Exception:
        pass


async def cmd_deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update.effective_user.id):
        return
    lang = await get_user_lang(update.effective_user.id)
    if not context.args:
        await update.message.reply_text(t("usage_deactivate", lang), parse_mode="HTML")
        return
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(t("usage_deactivate", lang), parse_mode="HTML")
        return
    await deactivate_workspace(user_id)
    await update.message.reply_text(
        t("workspace_deactivated", lang, user_id=user_id), parse_mode="HTML")


async def cmd_extend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update.effective_user.id):
        return
    lang = await get_user_lang(update.effective_user.id)
    if len(context.args) < 2:
        await update.message.reply_text(t("usage_extend", lang), parse_mode="HTML")
        return
    try:
        user_id = int(context.args[0])
        days    = int(context.args[1])
    except ValueError:
        await update.message.reply_text(t("usage_extend", lang), parse_mode="HTML")
        return
    ws = await get_workspace(user_id)
    if not ws:
        await update.message.reply_text(t("workspace_not_found", lang), parse_mode="HTML")
        return
    base = datetime.fromisoformat(ws["expires_at"]) if ws.get("expires_at") else datetime.now()
    if base < datetime.now():
        base = datetime.now()
    new_expiry = (base + timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
    await extend_workspace(user_id, new_expiry)
    await update.message.reply_text(
        t("workspace_extended", lang, days=days, user_id=user_id), parse_mode="HTML")


async def cmd_workspaces(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update.effective_user.id):
        return
    lang = await get_user_lang(update.effective_user.id)
    all_ws = await get_all_workspaces()
    if not all_ws:
        await update.message.reply_text(t("no_workspaces", lang), parse_mode="HTML")
        return
    lines = []
    for ws in all_ws:
        status = "✅" if ws["is_active"] else "❌"
        lines.append(
            f"{status} ID:{ws['id']} owner:{ws['owner_id']} "
            f"plan:{ws['plan']} exp:{ws.get('expires_at','—')}"
        )
    await update.message.reply_text(
        t("workspaces_list", lang, list="\n".join(lines)), parse_mode="HTML")


async def cmd_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dev-only: /lookup <user_id|@username|channel_id>"""
    if not _is_owner(update.effective_user.id):
        return
    lang = await get_user_lang(update.effective_user.id)

    if not context.args:
        await update.message.reply_text(t("lookup_usage", lang), parse_mode="HTML")
        return

    raw = context.args[0].lstrip("@")

    # Try as user_id first
    user_id = None
    try:
        user_id = int(raw)
    except ValueError:
        # Try resolving username via telegram
        try:
            chat = await context.bot.get_chat(f"@{raw}")
            user_id = chat.id
        except Exception:
            pass

    if not user_id:
        await update.message.reply_text(t("lookup_not_found", lang), parse_mode="HTML")
        return

    # Check if it's a channel
    ws_by_ch = await lookup_workspace_by_channel(str(user_id))
    if ws_by_ch:
        admins_list = await get_admins(ws_by_ch["id"])
        ch_count    = await count_channels(ws_by_ch["id"])
        text = (
            f"📡 <b>Channel/Chat:</b> {user_id}\n\n"
            f"🏠 Owner ID: <code>{ws_by_ch['owner_id']}</code>\n"
            f"📦 Plan: {ws_by_ch['plan'].upper()} {'✅' if ws_by_ch['is_active'] else '❌'}\n"
            f"🫂 Admins: {len(admins_list)}\n"
            f"📡 Total channels: {ch_count}\n"
            f"📅 Expires: {ws_by_ch.get('expires_at','—')}"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    # Lookup as user
    result = await lookup_user(user_id)
    owned  = result["owned"]
    member = result["member"]

    if not owned and not member:
        await update.message.reply_text(t("lookup_not_found", lang), parse_mode="HTML")
        return

    owned_lines = "—"
    if owned:
        plan    = owned.get("plan", "?").upper()
        status  = "✅" if owned.get("is_active") else "❌"
        exp     = owned.get("expires_at", "—")
        admins  = await count_admins(owned["id"])
        channels= await count_channels(owned["id"])
        owned_lines = f"  • Workspace #{owned['id']} {plan} {status}\n    exp:{exp} | {admins} admins | {channels} ch"

    member_lines = "—"
    if member:
        lines = []
        for ws in member:
            plan   = ws.get("plan","?").upper()
            status = "✅" if ws.get("is_active") else "❌"
            lines.append(f"  • Workspace #{ws['id']} (owner:{ws['owner_id']}) {plan} {status}")
        member_lines = "\n".join(lines)

    await update.message.reply_text(
        t("lookup_user_result", lang,
          user=f"<code>{user_id}</code>",
          owned=owned_lines,
          member=member_lines),
        parse_mode="HTML")


# ── Owner broadcast ConversationHandler ──────────────────────────────────────

_OWNER_BCAST_CHOOSING = "OWNER_BCAST_CHOOSING"
_OWNER_BCAST_WAITING  = "OWNER_BCAST_WAITING"
_CB_BCAST_ALL         = "owner_bcast_all"
_CB_BCAST_PRO         = "owner_bcast_pro"
_CB_BCAST_CANCEL      = "owner_bcast_cancel"


async def cmd_ownerpanel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update.effective_user.id):
        return
    keyboard = InlineKeyboardMarkup([
        [mk_ikb("📣 إذاعة للجميع",           callback_data=_CB_BCAST_ALL)],
        [mk_ikb("⭐️ إذاعة للمشتركين Pro",    callback_data=_CB_BCAST_PRO)],
        [mk_ikb("إلغاء",                      callback_data=_CB_BCAST_CANCEL)],
    ])
    await update.message.reply_text(
        "🔧 <b>لوحة المالك</b>\n\nاختر نوع الإذاعة:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return _OWNER_BCAST_CHOOSING


async def _handle_bcast_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == _CB_BCAST_CANCEL:
        await q.edit_message_text("❌ تم الإلغاء.", parse_mode="HTML")
        return ConversationHandler.END

    context.user_data["owner_bcast_mode"] = q.data
    label = "الجميع" if q.data == _CB_BCAST_ALL else "مشتركي Pro"
    await q.edit_message_text(
        f"📝 أرسل نص الإذاعة الآن.\n"
        f"سيتم إرسالها إلى: <b>{html.escape(label)}</b>\n\n"
        f"أرسل /cancel للإلغاء.",
        parse_mode="HTML",
    )
    return _OWNER_BCAST_WAITING


async def _handle_bcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update.effective_user.id):
        return ConversationHandler.END

    raw_text = update.message.text or ""
    safe_text = html.escape(raw_text, quote=False)
    mode = context.user_data.get("owner_bcast_mode", _CB_BCAST_ALL)

    if mode == _CB_BCAST_PRO:
        recipients = await get_active_pro_workspace_owner_ids()
    else:
        recipients = await get_active_workspace_owner_ids()

    ok = fail = 0
    for uid in recipients:
        try:
            await context.bot.send_message(uid, safe_text, parse_mode="HTML")
            ok += 1
        except Exception as e:
            logger.warning("Owner broadcast: failed to send to %s: %s", uid, e)
            fail += 1

    total = ok + fail
    await update.message.reply_text(
        f"✅ <b>اكتملت الإذاعة</b>\n\n"
        f"• الإجمالي: <b>{total}</b>\n"
        f"• نجح: <b>{ok}</b>\n"
        f"• فشل: <b>{fail}</b>",
        parse_mode="HTML",
    )
    return ConversationHandler.END


async def _handle_bcast_cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء الإذاعة.", parse_mode="HTML")
    return ConversationHandler.END


def build_owner_broadcast_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("ownerpanel", cmd_ownerpanel)],
        states={
            _OWNER_BCAST_CHOOSING: [
                CallbackQueryHandler(_handle_bcast_choice,
                                     pattern=f"^({_CB_BCAST_ALL}|{_CB_BCAST_PRO}|{_CB_BCAST_CANCEL})$"),
            ],
            _OWNER_BCAST_WAITING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_bcast_text),
                CommandHandler("cancel", _handle_bcast_cancel_cmd),
            ],
        },
        fallbacks=[CommandHandler("cancel", _handle_bcast_cancel_cmd)],
        per_message=False,
    )
