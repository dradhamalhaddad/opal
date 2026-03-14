from config import OWNER_ID
from database import get_workspace, get_workspace_by_admin, get_user_lang
from translations import t


async def get_role(user_id: int):
    """Returns: 'owner', 'workspace_owner', 'admin', or None"""
    if user_id == OWNER_ID:
        return "owner"
    ws = await get_workspace(user_id)
    if ws:
        return "workspace_owner"
    ws = await get_workspace_by_admin(user_id)
    if ws:
        return "admin"
    return None


async def check_workspace_active(user_id: int) -> tuple[dict | None, str]:
    """Returns (workspace, error_message) — error_message is empty string if OK"""
    from config import OWNER_USERNAME
    lang = await get_user_lang(user_id)
    ws = await get_workspace(user_id)
    if not ws:
        ws = await get_workspace_by_admin(user_id)
    if not ws:
        return None, t("subscription_inactive", lang, owner=OWNER_USERNAME)
    if not ws["is_active"]:
        return None, t("subscription_inactive", lang, owner=OWNER_USERNAME)
    return ws, ""
