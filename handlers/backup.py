import logging
import os
import shutil
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters

from config import OWNER_ID
from database import DB_PATH, get_user_lang

logger = logging.getLogger(__name__)

BACKUP_CHANNEL_ID = -1003133487338


def _is_owner(uid): return uid == OWNER_ID


def _backup_filename():
    now = datetime.now().strftime("%Y%m%d_%H%M")
    return f"bot_backup_{now}.db"


# ─── Manual backup ────────────────────────────────────────────────────────────

async def cmd_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update.effective_user.id):
        return
    await _send_backup(context.bot, notify_user=update.effective_user.id)
    await update.message.reply_text("✅ Backup sent to channel!", parse_mode="HTML")


async def _send_backup(bot, notify_user: int = None):
    if not os.path.exists(DB_PATH):
        logger.warning("Backup: DB file not found")
        return False
    try:
        filename = _backup_filename()
        caption  = (
            f"🗄 <b>Bot Backup</b>\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"📦 <code>{filename}</code>\n\n"
            f"لاستعادة النسخة: ابعت الملف للبوت بأمر /restore"
        )
        with open(DB_PATH, "rb") as f:
            await bot.send_document(
                chat_id=BACKUP_CHANNEL_ID,
                document=f,
                filename=filename,
                caption=caption,
                parse_mode="HTML",
            )
        logger.info(f"Backup sent: {filename}")
        return True
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        if notify_user:
            try:
                await bot.send_message(notify_user, f"❌ Backup failed: {e}", parse_mode="HTML")
            except Exception:
                pass
        return False


# ─── Restore ──────────────────────────────────────────────────────────────────

async def handle_restore_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner sends a .db file → restore it."""
    if not _is_owner(update.effective_user.id):
        return

    doc = update.message.document
    if not doc or not doc.file_name.endswith(".db"):
        return

    await update.message.reply_text("⏳ Restoring backup...", parse_mode="HTML")

    try:
        # Download the file
        tg_file  = await context.bot.get_file(doc.file_id)
        tmp_path = f"{DB_PATH}.restore_tmp"
        await tg_file.download_to_drive(tmp_path)

        # Backup current DB before overwriting
        bak_path = f"{DB_PATH}.before_restore"
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, bak_path)

        # Replace
        shutil.move(tmp_path, DB_PATH)

        await update.message.reply_text(
            "✅ <b>Restore complete!</b>\n\n"
            "⚠️ أعد تشغيل البوت عشان التغييرات تاخد أثر:\n"
            "<code>systemctl restart ad0bot</code>",
            parse_mode="HTML")
        logger.info(f"DB restored from {doc.file_name}")

    except Exception as e:
        await update.message.reply_text(f"❌ Restore failed: {e}", parse_mode="HTML")
        logger.error(f"Restore error: {e}")


# ─── Auto backup job (APScheduler) ───────────────────────────────────────────

async def auto_backup_job(bot):
    """Called every hour by APScheduler."""
    await _send_backup(bot)


def register_auto_backup(scheduler, bot):
    scheduler.add_job(
        auto_backup_job,
        trigger="interval",
        hours=1,
        args=[bot],
        id="auto_backup",
        replace_existing=True,
    )
    logger.info("Auto backup registered — every 1 hour → channel")
