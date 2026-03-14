import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import OWNER_ID, OWNER_USERNAME, PLANS, ADDON_EXTRA_ADMINS
from database import (
    get_workspace, get_workspace_by_id, create_workspace, get_user_lang, set_user_lang,
    get_workspaces_as_admin, add_admin, remove_admin, get_admins, count_admins,
    add_channel, remove_channel, get_channels, count_channels, get_settings,
    get_user_lang
)
from keyboards import (
    main_menu_keyboard, admin_menu_keyboard, new_user_keyboard,
    language_keyboard, template_keyboard, back_keyboard,
    workspace_picker_keyboard
)
from middlewares import get_role
from translations import t

logger = logging.getLogger(__name__)


def _is_pro(ws): return ws and ws.get("plan") == "pro" and ws.get("is_active")

def _max_admins(ws):
    plan_info = PLANS.get(ws["plan"], PLANS["basic"])
    return plan_info["max_admins"] + ws.get("addon_extra_admins", 0)

def _ws_id(ctx): return ctx.user_data.get("ctx_ws_id") or ctx.user_data.get("_ws_id", 0)

async def _get_ws(context, user_id):
    ws_id = _ws_id(context)
    return await get_workspace_by_id(ws_id) if ws_id else await get_workspace(user_id)


# ── /start ────────────────────────────────────────────────────────────────────

async def _reply(update: Update, text: str, reply_markup=None):
    """Works for both command messages and callback queries."""
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode="HTML")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    user_id = user.id

    # Language detection
    stored_lang = await get_user_lang(user_id)
    if stored_lang != "en":
        lang = stored_lang
    else:
        tg_lang = user.language_code or "en"
        lang    = "ar" if tg_lang.startswith("ar") else "en"
        await set_user_lang(user_id, lang)

    if user_id == OWNER_ID:
        from keyboards import owner_keyboard
        own_ws = await get_workspace(user_id)
        if own_ws and own_ws.get("is_active"):
            context.user_data["ctx_ws_id"] = own_ws["id"]
            await _reply(update,
                t("owner_panel", lang),
                reply_markup=main_menu_keyboard(lang, is_pro=_is_pro(own_ws)))
        else:
            await _reply(update,
                t("owner_panel", lang),
                reply_markup=owner_keyboard(lang))
        return

    own_ws  = await get_workspace(user_id)
    admin_ws= await get_workspaces_as_admin(user_id)

    # New user
    if not own_ws and not admin_ws:
        await create_workspace(user_id)
        own_ws = await get_workspace(user_id)
        await update.message.reply_text(
            t("welcome_new", lang, owner=OWNER_USERNAME),
            reply_markup=new_user_keyboard(lang),
            parse_mode="HTML")
        return

    # Multi-workspace: owns one + is admin in others
    active_admin_ws = [w for w in admin_ws if w.get("is_active")]
    if own_ws and own_ws.get("is_active") and active_admin_ws:
        await _reply(update,
            t("pick_workspace", lang),
            reply_markup=workspace_picker_keyboard(own_ws, active_admin_ws, lang))
        return

    # Single workspace owner
    if own_ws:
        if not own_ws.get("is_active"):
            await _reply(update,
                t("subscription_inactive", lang, owner=OWNER_USERNAME),
                reply_markup=new_user_keyboard(lang))
            return
        context.user_data["ctx_ws_id"] = own_ws["id"]
        await _reply(update,
            t("welcome_back", lang),
            reply_markup=main_menu_keyboard(lang, is_pro=_is_pro(own_ws)))
        return

    # Only admin (no owned workspace)
    if admin_ws:
        if len(admin_ws) == 1:
            context.user_data["ctx_ws_id"] = admin_ws[0]["id"]
        await _reply(update,
            t("welcome_back", lang),
            reply_markup=admin_menu_keyboard(lang))


# ── Workspace context switch ───────────────────────────────────────────────────

async def handle_ctx_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle workspace_picker button tap."""
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await get_user_lang(user_id)
    ws_id   = int(query.data.split("_")[2])

    ws = await get_workspace_by_id(ws_id)
    if not ws:
        await query.edit_message_text(t("error", lang), parse_mode="HTML")
        return

    # Verify access
    is_owner = (ws["owner_id"] == user_id)
    admins   = await get_admins(ws_id)
    is_admin = any(a["user_id"] == user_id for a in admins)

    if not is_owner and not is_admin:
        await query.edit_message_text(t("not_authorized", lang), parse_mode="HTML")
        return

    context.user_data["ctx_ws_id"] = ws_id

    if is_owner:
        await query.edit_message_text(
            t("welcome_back", lang),
            reply_markup=main_menu_keyboard(lang, is_pro=_is_pro(ws)),
            parse_mode="HTML")
    else:
        await query.edit_message_text(
            t("welcome_back", lang),
            reply_markup=admin_menu_keyboard(lang),
            parse_mode="HTML")


# ── /status ───────────────────────────────────────────────────────────────────

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = await get_user_lang(uid)
    ws   = await _get_ws(context, uid) or await get_workspace(uid)
    if not ws:
        await update.message.reply_text(t("subscription_inactive", lang, owner=OWNER_USERNAME),
                                        parse_mode="HTML"); return
    plan_info = PLANS.get(ws["plan"], PLANS["basic"])
    cooldown  = ws.get("custom_cooldown_minutes") or plan_info["cooldown_minutes"]
    await update.message.reply_text(
        t("status_body", lang,
          plan=ws["plan"].upper(),
          expiry=ws.get("expires_at", "N/A"),
          admins=await count_admins(ws["id"]),
          max_admins=_max_admins(ws),
          channels=await count_channels(ws["id"]),
          max_channels=plan_info["max_channels"],
          cooldown=cooldown,
          addon_admins=ws.get("addon_extra_admins", 0)),
        reply_markup=back_keyboard(lang),
        parse_mode="HTML")


# ── Admin management ──────────────────────────────────────────────────────────

async def cmd_addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = await get_user_lang(uid)
    ws   = await get_workspace(uid)
    if not ws or not ws["is_active"]:
        await update.message.reply_text(t("subscription_inactive", lang, owner=OWNER_USERNAME),
                                        parse_mode="HTML"); return
    if not context.args:
        await update.message.reply_text("Usage: /addadmin <user_id> [name]", parse_mode="HTML"); return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(t("error", lang), parse_mode="HTML"); return

    display_name = " ".join(context.args[1:]) if len(context.args) > 1 else None

    if await count_admins(ws["id"]) >= _max_admins(ws):
        await update.message.reply_text(t("admin_limit_reached", lang, max=_max_admins(ws)),
                                        parse_mode="HTML"); return
    ok = await add_admin(ws["id"], target_id, display_name)
    if ok:
        await update.message.reply_text(t("admin_added", lang, user_id=target_id), parse_mode="HTML")
        # Welcome message (Pro)
        if _is_pro(ws):
            try:
                ul = await get_user_lang(target_id)
                await context.bot.send_message(
                    target_id,
                    f"👋 {'تمت إضافتك أدمناً في مساحة عمل جديدة!' if ul=='ar' else 'You have been added as an admin to a workspace!'}\n"
                    f"{'اضغط /start للبدء' if ul=='ar' else 'Type /start to begin'}",
                    parse_mode="HTML")
            except Exception:
                pass
    else:
        await update.message.reply_text(t("admin_already_exists", lang), parse_mode="HTML")


async def cmd_removeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = await get_user_lang(uid)
    ws   = await get_workspace(uid)
    if not ws or not context.args:
        await update.message.reply_text("Usage: /removeadmin <user_id>", parse_mode="HTML"); return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(t("error", lang), parse_mode="HTML"); return
    ok = await remove_admin(ws["id"], target_id)
    msg = t("admin_removed", lang, user_id=target_id) if ok else t("admin_not_found", lang)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_listadmins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = await get_user_lang(uid)
    ws   = await get_workspace(uid)
    if not ws:
        await update.message.reply_text(t("error", lang), parse_mode="HTML"); return
    admins = await get_admins(ws["id"])
    if not admins:
        await update.message.reply_text(t("no_admins", lang), parse_mode="HTML"); return
    lines = []
    for a in admins:
        draft = " ✏️" if a.get("draft_only") else ""
        name  = a.get("display_name") or str(a["user_id"])
        lines.append(f"• {name} ({a['user_id']}){draft}")
    await update.message.reply_text(
        t("admins_list", lang, list="\n".join(lines)), parse_mode="HTML")


# ── Channel management ────────────────────────────────────────────────────────

async def cmd_addchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = await get_user_lang(uid)
    ws   = await get_workspace(uid)
    if not ws or not ws["is_active"]:
        await update.message.reply_text(t("subscription_inactive", lang, owner=OWNER_USERNAME),
                                        parse_mode="HTML"); return
    plan_info = PLANS.get(ws["plan"], PLANS["basic"])
    if not context.args:
        await update.message.reply_text("Usage: /addchannel <channel_id or @username>",
                                        parse_mode="HTML"); return
    if await count_channels(ws["id"]) >= plan_info["max_channels"]:
        await update.message.reply_text(
            t("channel_limit_reached", lang, max=plan_info["max_channels"]),
            parse_mode="HTML"); return

    raw = context.args[0]
    try:
        chat = await context.bot.get_chat(raw)
    except Exception:
        await update.message.reply_text(t("bot_not_admin_in_channel", lang), parse_mode="HTML"); return

    # Verify bot is admin
    try:
        member = await context.bot.get_chat_member(chat.id, context.bot.id)
        if member.status not in ("administrator", "creator"):
            raise ValueError
    except Exception:
        await update.message.reply_text(t("bot_not_admin_in_channel", lang), parse_mode="HTML"); return

    username = f"@{chat.username}" if chat.username else None
    ok = await add_channel(ws["id"], str(chat.id), username)
    if ok:
        await update.message.reply_text(
            t("channel_added", lang, channel=username or str(chat.id)), parse_mode="HTML")
    else:
        await update.message.reply_text(t("channel_already_exists", lang), parse_mode="HTML")


async def cmd_removechannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = await get_user_lang(uid)
    ws   = await get_workspace(uid)
    if not ws or not context.args:
        await update.message.reply_text("Usage: /removechannel <channel_id>", parse_mode="HTML"); return
    ok = await remove_channel(ws["id"], context.args[0])
    msg = t("channel_removed", lang, channel=context.args[0]) if ok else t("channel_not_found", lang)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_listchannels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = await get_user_lang(uid)
    ws   = await get_workspace(uid)
    if not ws:
        await update.message.reply_text(t("error", lang), parse_mode="HTML"); return
    channels = await get_channels(ws["id"])
    if not channels:
        await update.message.reply_text(t("no_channels", lang), parse_mode="HTML"); return
    lines = [f"• {c.get('channel_username') or c['channel_id']}" for c in channels]
    await update.message.reply_text(
        t("channels_list", lang, list="\n".join(lines)), parse_mode="HTML")


# ── My Account ────────────────────────────────────────────────────────────────

async def handle_my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await get_user_lang(user_id)

    # Check if owner
    own_ws = await get_workspace(user_id)
    if own_ws:
        plan_info = PLANS.get(own_ws["plan"], PLANS["basic"])
        cooldown  = own_ws.get("custom_cooldown_minutes") or plan_info["cooldown_minutes"]
        from translations import t
        await query.edit_message_text(
            t("account_info", lang,
              plan=own_ws["plan"].upper(),
              expiry=own_ws.get("expires_at", "N/A"),
              admins=await count_admins(own_ws["id"]),
              max_admins=_max_admins(own_ws),
              channels=await count_channels(own_ws["id"]),
              max_channels=plan_info["max_channels"],
              cooldown=cooldown,
              addon_admins=own_ws.get("addon_extra_admins", 0),
              user_id=user_id),
            parse_mode="HTML",
            reply_markup=back_keyboard(lang))
        return

    # Admin in someone else's workspace
    ws = await _get_ws(context, user_id) or await get_workspace_by_admin(user_id)
    if ws:
        plan_info = PLANS.get(ws["plan"], PLANS["basic"])
        cooldown  = ws.get("custom_cooldown_minutes") or plan_info["cooldown_minutes"]
        from translations import t
        await query.edit_message_text(
            t("account_admin_info", lang,
              ws_id=ws["id"],
              plan=ws["plan"].upper(),
              expiry=ws.get("expires_at", "N/A"),
              cooldown=cooldown,
              user_id=user_id),
            parse_mode="HTML",
            reply_markup=back_keyboard(lang))
        return

    from translations import t
    await query.edit_message_text(t("error", lang), parse_mode="HTML",
                                   reply_markup=back_keyboard(lang))


# ── Owner Panel ───────────────────────────────────────────────────────────────

async def handle_owner_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await get_user_lang(user_id)
    from translations import t
    from keyboards import back_keyboard
    await query.edit_message_text(
        t("owner_panel", lang),
        parse_mode="HTML",
        reply_markup=back_keyboard(lang))
