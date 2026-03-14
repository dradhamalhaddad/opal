import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN             = os.getenv("BOT_TOKEN")
OWNER_ID              = int(os.getenv("OWNER_ID"))
OWNER_USERNAME        = os.getenv("OWNER_USERNAME")

# ── Telegram Stars prices (after 30% TG commission, ~$0.013/star net) ─────────
STARS_PRO_MONTHLY  = 600   # ~$5 net
STARS_PRO_WEEKLY   = 250   # ~$2 net
STARS_ADDON_ADMINS = 150   # ~$1 net

# ── Plans ──────────────────────────────────────────────────────────────────────
PLANS = {
    "basic": {
        "max_admins":       3,
        "max_channels":     1,
        "cooldown_minutes": 60,
        "custom_cooldown":  False,
        "header_footer":    False,
        "blackout_hours":   False,
        "stats":            False,
        "channel_select":   False,
        "schedule":         False,
        "approval":         False,
        "named_templates":  False,
        "inline_button":    False,
        "auto_pin":         False,
        "draft_only":       False,
        "auto_repeat":      False,
        "price_monthly":    0,
        "price_weekly":     0,
    },
    "pro": {
        "max_admins":       10,
        "max_channels":     10,
        "cooldown_minutes": 10,
        "custom_cooldown":  True,
        "header_footer":    True,
        "blackout_hours":   True,
        "stats":            True,
        "channel_select":   True,
        "schedule":         True,
        "approval":         True,
        "named_templates":  True,
        "inline_button":    True,
        "auto_pin":         True,
        "draft_only":       True,
        "auto_repeat":      True,
        "price_monthly":    5,
        "price_weekly":     2,
    },
}

ADDON_EXTRA_ADMINS = {"count": 5, "price_usd": 1}
COOLDOWN_MIN_MINUTES = 5
