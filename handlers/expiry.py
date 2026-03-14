import logging

from database import get_expired_workspaces, deactivate_workspace, get_user_lang
from translations import t
from config import OWNER_USERNAME

logger = logging.getLogger(__name__)


async def check_expiry(context):
    """APScheduler job: deactivate expired workspaces and notify owners"""
    try:
        expired = await get_expired_workspaces()
        for ws in expired:
            owner_id = ws["owner_id"]
            await deactivate_workspace(owner_id)
            logger.info(f"Deactivated expired workspace for owner {owner_id}")

            try:
                lang = await get_user_lang(owner_id)
                await context.bot.send_message(
                    chat_id=owner_id,
                    text=t("subscription_expired", lang, owner=OWNER_USERNAME, parse_mode="HTML")
                )
            except Exception as e:
                logger.warning(f"Could not notify owner {owner_id}: {e}")
    except Exception as e:
        logger.error(f"Expiry check error: {e}")
