import re
import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from database import (
    get_workspace, get_workspace_by_id, get_templates,
    save_template, delete_template, get_user_lang
)
from keyboards import templates_keyboard, back_keyboard
from translations import t

logger = logging.getLogger(__name__)

WAITING_NAME    = 300
WAITING_CONTENT = 301

def _ws_id(ctx): return ctx.user_data.get("ctx_ws_id") or ctx.user_data.get("_ws_id", 0)

async def _get_ws(context, user_id):
    ws_id = _ws_id(context)
    return await get_workspace_by_id(ws_id) if ws_id else await get_workspace(user_id)

async def _lang(uid): return await get_user_lang(uid)


async def handle_named_templates_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query; await q.answer()
    uid = q.from_user.id; lang = await _lang(uid)
    ws  = await _get_ws(context, uid)
    if not ws or ws.get("plan") != "pro":
        await q.edit_message_text(t("not_authorized", lang, parse_mode="HTML"), parse_mode="HTML"); return
    templates = await get_templates(ws["id"])
    if not templates:
        await q.edit_message_text(
            t("named_templates_empty", lang, parse_mode="HTML"), parse_mode="HTML",
            reply_markup=templates_keyboard([], lang, use_mode=False))
        return
    await q.edit_message_text(
        t("named_templates_menu", lang, parse_mode="HTML"), parse_mode="HTML",
        reply_markup=templates_keyboard(templates, lang, use_mode=False))


async def handle_new_template(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query; await q.answer()
    lang = await _lang(q.from_user.id)
    await q.edit_message_text(t("send_template_name", lang, parse_mode="HTML"), parse_mode="HTML")
    return WAITING_NAME


async def receive_template_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id; lang = await _lang(uid)
    name = update.message.text.strip()
    if not re.match(r'^\w+$', name):
        await update.message.reply_text(t("template_name_invalid", lang, parse_mode="HTML"), parse_mode="HTML")
        return WAITING_NAME
    context.user_data["new_tpl_name"] = name
    await update.message.reply_text(t("send_template_content", lang, parse_mode="HTML"), parse_mode="HTML")
    return WAITING_CONTENT


async def receive_template_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid     = update.effective_user.id; lang = await _lang(uid)
    ws      = await _get_ws(context, uid)
    name    = context.user_data.pop("new_tpl_name", "template")
    content = update.message.text.strip()
    await save_template(ws["id"], name, content)
    await update.message.reply_text(
        t("template_saved", lang, name=name, parse_mode="HTML"), parse_mode="HTML",
        reply_markup=back_keyboard(lang))
    return ConversationHandler.END


async def handle_delete_template(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query; await q.answer()
    uid  = q.from_user.id; lang = await _lang(uid)
    ws   = await _get_ws(context, uid)
    name = q.data.replace("tpl_del_", "")
    await delete_template(ws["id"], name)
    await q.answer(t("template_deleted", lang, name=name), show_alert=True)
    # Re-render
    templates = await get_templates(ws["id"])
    await q.edit_message_text(
        t("named_templates_menu", lang, parse_mode="HTML"), parse_mode="HTML",
        reply_markup=templates_keyboard(templates, lang, use_mode=False))


def build_named_templates_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_new_template, pattern="^tpl_new$")],
        states={
            WAITING_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_template_name)],
            WAITING_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_template_content)],
        },
        fallbacks=[CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^menu_back$")],
        per_message=False,
    )
