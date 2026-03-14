import logging
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from config import OWNER_ID, PLANS
from database import (
    get_all_workspaces, get_workspace, activate_workspace, deactivate_workspace,
    extend_workspace, get_user_lang, lookup_user, lookup_workspace_by_channel,
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
