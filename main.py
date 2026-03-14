import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)

from config import BOT_TOKEN, OWNER_ID
from bot_core import PatchedBot
from database import init_db, get_user_lang, set_user_lang

from handlers.workspace import (
    cmd_start, handle_ctx_switch,
    handle_my_account, handle_owner_panel,
    cmd_status, cmd_addadmin, cmd_removeadmin, cmd_listadmins,
    cmd_addchannel, cmd_removechannel, cmd_listchannels,
)
from handlers.owner import (
    cmd_activate, cmd_deactivate, cmd_extend, cmd_workspaces, cmd_lookup,
    build_owner_broadcast_handler,
)
from handlers.broadcast import (
    build_broadcast_handler, handle_approve, handle_reject
)
from handlers.named_templates import (
    handle_named_templates_menu, handle_delete_template, build_named_templates_handler
)
from handlers.settings import (
    handle_cooldown_menu, handle_cooldown_reset,
    handle_blackout_menu, handle_blackout_set, handle_blackout_clear,
    handle_template_menu, handle_set_header, handle_set_footer,
    handle_clear_header, handle_clear_footer, handle_toggle_sender, handle_template_preview,
    handle_pro_settings, handle_prosetting_toggle, handle_prosetting_inline,
    handle_prosetting_draft, handle_draft_toggle, receive_prosetting_inline,
    handle_stats, handle_log, handle_schedule_menu, handle_cancel_scheduled,
    WAITING_INLINE, WAITING_BLACKOUT, TPL_HEADER, TPL_FOOTER,
)
from handlers.payment import (
    handle_subscribe_menu, handle_sub_method, handle_sub_period,
    handle_pay_stars, handle_successful_payment, handle_pre_checkout,
    handle_addon_method, handle_addon_stars,
)
from handlers.expiry import check_expiry
from handlers.scheduler import start_scheduler, stop_scheduler
from handlers.backup import cmd_backup, handle_restore_file, register_auto_backup

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ── Language toggle ───────────────────────────────────────────────────────────

async def handle_language_menu(update: Update, context):
    q = update.callback_query; await q.answer()
    lang = await get_user_lang(q.from_user.id)
    from keyboards import language_keyboard
    from translations import t
    await q.edit_message_text(t("select_language", lang), parse_mode="HTML",
                               reply_markup=language_keyboard())


async def handle_set_lang(update: Update, context):
    q    = update.callback_query; await q.answer()
    lang = "ar" if "ar" in q.data else "en"
    await set_user_lang(q.from_user.id, lang)
    from translations import t
    await q.edit_message_text(t("language_set", lang), parse_mode="HTML")
    await cmd_start(update, context)


# ── Back / menu navigation ────────────────────────────────────────────────────

async def handle_back(update: Update, context):
    if update.callback_query:
        await update.callback_query.answer()
    await cmd_start(update, context)


async def handle_menu_status(update: Update, context):
    q = update.callback_query; await q.answer()
    from handlers.workspace import cmd_status
    await cmd_status(update, context)


async def handle_menu_admins(update: Update, context):
    q = update.callback_query; await q.answer()
    lang = await get_user_lang(q.from_user.id)
    from translations import t
    from keyboards import back_keyboard
    await q.edit_message_text(
        t("admins_help", lang), parse_mode="HTML", reply_markup=back_keyboard(lang))


async def handle_menu_channels(update: Update, context):
    q = update.callback_query; await q.answer()
    lang = await get_user_lang(q.from_user.id)
    from translations import t
    from keyboards import back_keyboard
    await q.edit_message_text(
        t("channels_help", lang), parse_mode="HTML", reply_markup=back_keyboard(lang))


async def handle_addon_admins_menu(update: Update, context):
    q = update.callback_query; await q.answer()
    lang = await get_user_lang(q.from_user.id)
    from translations import t
    from keyboards import addon_method_keyboard
    from config import ADDON_EXTRA_ADMINS, STARS_ADDON_ADMINS
    await q.edit_message_text(
        t("addon_admins_info", lang,
          count=ADDON_EXTRA_ADMINS["count"],
          usd=ADDON_EXTRA_ADMINS["price_usd"],
          stars=STARS_ADDON_ADMINS),
        parse_mode="HTML",
        reply_markup=addon_method_keyboard(lang))


# ── Post-init: DB + scheduler ─────────────────────────────────────────────────

async def post_init(app: Application):
    await init_db()
    start_scheduler(app)

    # APScheduler job: expiry checker every 30 min
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    # Already started by start_scheduler — add expiry job too
    from handlers.scheduler import _scheduler
    if _scheduler:
        _scheduler.add_job(
            check_expiry, "interval", minutes=30,
            args=[app.bot], id="expiry_check", replace_existing=True)
        register_auto_backup(_scheduler, app.bot)
    logger.info("Bot initialized")


async def post_shutdown(app: Application):
    stop_scheduler()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    app = (
        Application.builder()
        .bot(PatchedBot(token=BOT_TOKEN))
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # ── Owner broadcast ConversationHandler (group=-1, highest priority) ─────
    app.add_handler(build_owner_broadcast_handler(), group=-1)

    # ── Broadcast ConversationHandler (highest priority) ──────────────────────
    app.add_handler(build_broadcast_handler(), group=0)

    # ── Named templates ConversationHandler ───────────────────────────────────
    app.add_handler(build_named_templates_handler(), group=1)

    # ── Settings ConversationHandlers (inline + blackout + header/footer) ─────
    from telegram.ext import ConversationHandler
    settings_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_prosetting_inline, pattern="^prosetting_inline$"),
            CallbackQueryHandler(handle_blackout_set,      pattern="^blackout_set$"),
            CallbackQueryHandler(handle_set_header,        pattern="^tpl_set_header$"),
            CallbackQueryHandler(handle_set_footer,        pattern="^tpl_set_footer$"),
        ],
        states={
            WAITING_INLINE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_prosetting_inline)],
            WAITING_BLACKOUT:[MessageHandler(filters.TEXT & ~filters.COMMAND,
                                             __import__('handlers.settings', fromlist=['receive_blackout']).receive_blackout)],
            TPL_HEADER:      [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                             __import__('handlers.settings', fromlist=['receive_header']).receive_header)],
            TPL_FOOTER:      [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                             __import__('handlers.settings', fromlist=['receive_footer']).receive_footer)],
        },
        fallbacks=[CallbackQueryHandler(handle_back, pattern="^menu_back$")],
        per_message=False,
    )
    app.add_handler(settings_conv, group=2)

    # ── Commands ──────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",         cmd_start),         group=3)
    app.add_handler(CommandHandler("activate",      cmd_activate),      group=3)
    app.add_handler(CommandHandler("deactivate",    cmd_deactivate),    group=3)
    app.add_handler(CommandHandler("extend",        cmd_extend),        group=3)
    app.add_handler(CommandHandler("workspaces",    cmd_workspaces),    group=3)
    app.add_handler(CommandHandler("lookup",        cmd_lookup),        group=3)
    app.add_handler(CommandHandler("backup",        cmd_backup),        group=3)
    app.add_handler(CommandHandler("status",        cmd_status),        group=3)
    app.add_handler(CommandHandler("addadmin",      cmd_addadmin),      group=3)
    app.add_handler(CommandHandler("removeadmin",   cmd_removeadmin),   group=3)
    app.add_handler(CommandHandler("listadmins",    cmd_listadmins),    group=3)
    app.add_handler(CommandHandler("addchannel",    cmd_addchannel),    group=3)
    app.add_handler(CommandHandler("removechannel", cmd_removechannel), group=3)
    app.add_handler(CommandHandler("listchannels",  cmd_listchannels),  group=3)

    # ── Payments ──────────────────────────────────────────────────────────────
    from telegram.ext import PreCheckoutQueryHandler
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handle_successful_payment), group=3)
    app.add_handler(PreCheckoutQueryHandler(handle_pre_checkout), group=3)
    app.add_handler(MessageHandler(filters.Document.ALL, handle_restore_file), group=3)

    # ── Callback queries ──────────────────────────────────────────────────────
    cbs = [
        # Language
        ("^menu_language$",         handle_language_menu),
        ("^set_lang_",              handle_set_lang),

        # Navigation
        ("^menu_back$",             handle_back),
        ("^menu_status$",           handle_menu_status),
        ("^menu_admins$",           handle_menu_admins),
        ("^menu_channels$",         handle_menu_channels),
        ("^menu_addon_admins$",     handle_addon_admins_menu),

        # Workspace context switch
        ("^ctx_ws_",                handle_ctx_switch),

        # Account / Owner
        ("^menu_my_account$",       handle_my_account),
        ("^menu_owner_panel$",      handle_owner_panel),

        # Payment
        ("^menu_subscribe$",        handle_subscribe_menu),
        ("^sub_method_",            handle_sub_method),
        ("^pay_stars_",             handle_pay_stars),
        ("^pay_crypto_",            handle_sub_period),
        ("^addon_method_",          handle_addon_method),
        ("^addon_stars$",           handle_addon_stars),

        # Cooldown
        ("^menu_cooldown$",         handle_cooldown_menu),
        ("^cooldown_reset$",        handle_cooldown_reset),

        # Blackout
        ("^menu_blackout$",         handle_blackout_menu),
        ("^blackout_clear$",        handle_blackout_clear),

        # Template (header/footer)
        ("^menu_template$",         handle_template_menu),
        ("^tpl_clear_header$",      handle_clear_header),
        ("^tpl_clear_footer$",      handle_clear_footer),
        ("^tpl_toggle_sender$",     handle_toggle_sender),
        ("^tpl_preview$",           handle_template_preview),

        # Stats / Log / Schedule
        ("^menu_stats$",            handle_stats),
        ("^menu_log$",              handle_log),
        ("^menu_schedule$",         handle_schedule_menu),
        ("^sched_cancel_",          handle_cancel_scheduled),

        # Pro settings
        ("^menu_pro_settings$",     handle_pro_settings),
        ("^prosetting_approval$",   handle_prosetting_toggle),
        ("^prosetting_pin$",        handle_prosetting_toggle),
        ("^prosetting_log$",        handle_prosetting_toggle),
        ("^prosetting_draft$",      handle_prosetting_draft),
        ("^drafttoggle_",           handle_draft_toggle),

        # Named templates
        ("^menu_named_templates$",  handle_named_templates_menu),
        ("^tpl_del_",               handle_delete_template),

        # Approval
        ("^approve_",               handle_approve),
        ("^reject_",                handle_reject),
    ]

    for pattern, handler in cbs:
        app.add_handler(CallbackQueryHandler(handler, pattern=pattern), group=3)

    logger.info("Starting bot v3...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
