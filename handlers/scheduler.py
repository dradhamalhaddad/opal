import json
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application

from database import (
    get_pending_scheduled, mark_scheduled_sent, log_broadcast,
    update_cooldown, get_channels, get_workspace_by_id, get_settings
)

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


def _channel_label(ch): return ch.get("channel_username") or str(ch["channel_id"])


async def run_due_broadcasts(app: Application):
    """Called every minute — send any pending scheduled broadcasts that are due."""
    due = await get_pending_scheduled()
    for s in due:
        ws = await get_workspace_by_id(s["workspace_id"])
        if not ws or not ws["is_active"]:
            await mark_scheduled_sent(s["id"])
            continue

        channels  = await get_channels(ws["id"])
        selected  = json.loads(s["selected_channels"]) if s.get("selected_channels") else None
        targets   = [c for c in channels if not selected or c["channel_id"] in selected]
        settings  = await get_settings(ws["id"])

        markup = None
        if s.get("inline_btn_text") and s.get("inline_btn_url"):
            markup = InlineKeyboardMarkup([[
                InlineKeyboardButton(s["inline_btn_text"], url=s["inline_btn_url"])]])

        ok, fail = 0, 0
        sent_channels = []
        for ch in targets:
            try:
                msg = await app.bot.send_message(
                    chat_id=ch["channel_id"], text=s["final_message"],
                    parse_mode="HTML", reply_markup=markup)
                if s.get("should_pin"):
                    try:
                        await app.bot.pin_chat_message(ch["channel_id"], msg.message_id)
                    except Exception:
                        pass
                ok += 1
                sent_channels.append(_channel_label(ch))
            except Exception as e:
                logger.error(f"Scheduled send failed to {ch['channel_id']}: {e}")
                fail += 1

        await update_cooldown(ws["id"])
        await log_broadcast(
            ws["id"], s["admin_id"], s["message_text"], s["final_message"],
            ok, selected, s.get("inline_btn_text"), s.get("inline_btn_url"),
            bool(s.get("should_pin")), was_scheduled=True)
        await mark_scheduled_sent(s["id"])

        # Notify admin
        try:
            await app.bot.send_message(
                s["admin_id"],
                f"✅ تم نشر الإعلان المجدول → {ok} قناة\n✅ Scheduled broadcast sent → {ok} ch",
                parse_mode="HTML")
        except Exception:
            pass

        # Log to owner
        if settings.get("log_enabled", 1) and ws["owner_id"] != s["admin_id"]:
            try:
                adm_id   = s['admin_id']
                ch_str   = ', '.join(sent_channels)
                time_str = datetime.now().strftime('%H:%M')
                msg_text = s['message_text']
                log_msg  = (
                    f"📋 <b>إعلان مجدول نُشر</b>\n"
                    f"👤 المرسل: <a href='tg://user?id={adm_id}'>{adm_id}</a>\n"
                    f"📡 القنوات: {ch_str}\n"
                    f"🕐 {time_str}\n"
                    f"✅ {ok} | ❌ {fail}\n\n{msg_text}"
                )
                await app.bot.send_message(
                    ws["owner_id"], log_msg, parse_mode="HTML")
            except Exception:
                pass

        logger.info(f"Scheduled broadcast {s['id']} sent: {ok} ok, {fail} fail")


def start_scheduler(app: Application):
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        run_due_broadcasts,
        trigger="interval",
        minutes=1,
        args=[app],
        id="scheduled_broadcasts",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
