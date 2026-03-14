from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from translations import t
from bot_core import mk_ikb


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _btn(label, data): return mk_ikb(label, callback_data=data)
def _url_btn(label, url): return mk_ikb(label, url=url)


# ─── Language ─────────────────────────────────────────────────────────────────

def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
        InlineKeyboardButton("🇬🇧 English",  callback_data="set_lang_en"),
    ]])


# ─── New user / inactive ──────────────────────────────────────────────────────

def new_user_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_btn(t("btn_subscribe",  lang), "menu_subscribe")],
        [_btn(t("btn_my_account", lang), "menu_my_account")],
        [_btn(t("btn_language",   lang), "menu_language")],
    ])


# ─── Workspace picker (multi-workspace) ───────────────────────────────────────

def workspace_picker_keyboard(owned_ws: dict, member_ws: list, lang: str) -> InlineKeyboardMarkup:
    rows = []
    if owned_ws and owned_ws.get("is_active"):
        label = "🏠 " + ("مساحتي" if lang == "ar" else "My Workspace")
        rows.append([_btn(label, f"ctx_ws_{owned_ws['id']}")])
    for ws in member_ws:
        label = f"🫂 workspace #{ws['id']}"
        rows.append([_btn(label, f"ctx_ws_{ws['id']}")])
    rows.append([_btn(t("btn_language", lang), "menu_language")])
    return InlineKeyboardMarkup(rows)


# ─── Main menus ───────────────────────────────────────────────────────────────

def main_menu_keyboard(lang: str, is_pro: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [_btn(t("btn_status",   lang), "menu_status"),
         _btn(t("btn_admins",   lang), "menu_admins")],
        [_btn(t("btn_channels", lang), "menu_channels"),
         _btn(t("btn_template", lang), "menu_template")],
    ]
    if is_pro:
        rows += [
            [_btn(t("btn_stats",   lang), "menu_stats"),
             _btn(t("btn_cooldown",lang), "menu_cooldown")],
            [_btn(t("btn_blackout",lang), "menu_blackout"),
             _btn(t("btn_schedule",lang), "menu_schedule")],
            [_btn(t("btn_templates_named", lang), "menu_named_templates"),
             _btn(t("btn_pro_settings", lang), "menu_pro_settings")],
            [_btn(t("btn_log",    lang), "menu_log"),
             _btn(t("btn_addon_admins", lang), "menu_addon_admins")],
        ]
        rows.append([_btn(t("btn_my_account", lang), "menu_my_account"),
                     _btn(t("btn_language",   lang), "menu_language")])
        return InlineKeyboardMarkup(rows)
    else:
        rows.append([_btn(t("btn_subscribe",  lang), "menu_subscribe")])
    rows.append([_btn(t("btn_my_account", lang), "menu_my_account"),
                 _btn(t("btn_language",   lang), "menu_language")])
    return InlineKeyboardMarkup(rows)


def admin_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_btn(t("btn_broadcast",      lang), "do_broadcast")],
        [_btn(t("btn_named_templates",lang), "do_named_templates")],
        [_btn(t("btn_my_account",     lang), "menu_my_account"),
         _btn(t("btn_language",       lang), "menu_language")],
    ])


# ─── Pro owner settings ───────────────────────────────────────────────────────

def pro_settings_keyboard(lang: str, approval: bool, auto_pin: bool, log: bool) -> InlineKeyboardMarkup:
    a_lbl = ("✅ " if approval else "❌ ") + t("btn_approval", lang)
    p_lbl = ("✅ " if auto_pin  else "❌ ") + t("btn_auto_pin", lang)
    l_lbl = ("✅ " if log       else "❌ ") + t("btn_log_toggle", lang)
    return InlineKeyboardMarkup([
        [_btn(a_lbl, "prosetting_approval")],
        [_btn(p_lbl, "prosetting_pin")],
        [_btn(l_lbl, "prosetting_log")],
        [_btn(t("btn_inline_btn_setup", lang), "prosetting_inline")],
        [_btn(t("btn_draft_only_setup", lang), "prosetting_draft")],
        [_btn(t("btn_back", lang), "menu_back")],
    ])


# ─── Broadcast flow ───────────────────────────────────────────────────────────

def channel_select_keyboard(channels: list, selected: set, lang: str) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        cid   = ch["channel_id"]
        label = ("✅ " if cid in selected else "☐ ") + (ch.get("channel_username") or cid)
        rows.append([_btn(label, f"chsel_{cid}")])
    rows.append([
        _btn(t("btn_select_all",  lang), "chsel_all"),
        _btn(t("btn_clear_sel",   lang), "chsel_clear"),
    ])
    rows.append([_btn(t("btn_next", lang), "chsel_done")])
    return InlineKeyboardMarkup(rows)


def broadcast_options_keyboard(lang: str, is_owner: bool) -> InlineKeyboardMarkup:
    rows = [
        [_btn(t("btn_send_now",  lang), "bopt_now"),
         _btn(t("btn_schedule",  lang), "bopt_schedule")],
    ]
    if is_owner:
        rows.append([_btn(t("btn_add_inline_btn", lang), "bopt_inline")])
    rows.append([_btn(t("btn_cancel", lang), "cancel_broadcast")])
    return InlineKeyboardMarkup(rows)


def confirm_cancel_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        _btn(t("btn_confirm", lang), "confirm_broadcast"),
        _btn(t("btn_cancel",  lang), "cancel_broadcast"),
    ]])


def approval_keyboard(approval_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        _btn("✅ " + t("btn_approve", lang), f"approve_{approval_id}"),
        _btn("❌ " + t("btn_reject",  lang), f"reject_{approval_id}"),
    ]])


# ─── Schedule ─────────────────────────────────────────────────────────────────

def scheduled_list_keyboard(schedules: list, lang: str) -> InlineKeyboardMarkup:
    rows = []
    for s in schedules:
        label = f"⏰ {s['scheduled_at'][:16]} — {s['message_text'][:20]}…"
        rows.append([_btn(label, f"sched_view_{s['id']}"),
                     _btn("🗑️", f"sched_cancel_{s['id']}")])
    rows.append([_btn(t("btn_back", lang), "menu_back")])
    return InlineKeyboardMarkup(rows)


# ─── Named Templates ──────────────────────────────────────────────────────────

def templates_keyboard(templates: list, lang: str, use_mode: bool = False) -> InlineKeyboardMarkup:
    rows = []
    for tpl in templates:
        cb = f"tpl_use_{tpl['name']}" if use_mode else f"tpl_del_{tpl['name']}"
        icon = "📋 " if use_mode else "🗑️ "
        rows.append([_btn(icon + tpl["name"], cb)])
    if not use_mode:
        rows.append([_btn(t("btn_new_template", lang), "tpl_new")])
    rows.append([_btn(t("btn_back", lang), "menu_back")])
    return InlineKeyboardMarkup(rows)


# ─── Template (header/footer) ─────────────────────────────────────────────────

def template_keyboard(lang: str, show_sender: bool) -> InlineKeyboardMarkup:
    sender_lbl = t("btn_sender_on", lang) if show_sender else t("btn_sender_off", lang)
    return InlineKeyboardMarkup([
        [_btn(t("btn_set_header",   lang), "tpl_set_header"),
         _btn(t("btn_set_footer",   lang), "tpl_set_footer")],
        [_btn(t("btn_clear_header", lang), "tpl_clear_header"),
         _btn(t("btn_clear_footer", lang), "tpl_clear_footer")],
        [_btn(sender_lbl,                  "tpl_toggle_sender")],
        [_btn(t("btn_preview",      lang), "tpl_preview")],
        [_btn(t("btn_back",         lang), "menu_back")],
    ])


# ─── Cooldown / Blackout ──────────────────────────────────────────────────────

def cooldown_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_btn(t("btn_reset_cooldown", lang), "cooldown_reset")],
        [_btn(t("btn_back", lang), "menu_back")],
    ])


def blackout_keyboard(lang: str, has_blackout: bool) -> InlineKeyboardMarkup:
    rows = [[_btn(t("btn_set_blackout", lang), "blackout_set")]]
    if has_blackout:
        rows.append([_btn(t("btn_clear_blackout", lang), "blackout_clear")])
    rows.append([_btn(t("btn_back", lang), "menu_back")])
    return InlineKeyboardMarkup(rows)


# ─── Payment ──────────────────────────────────────────────────────────────────

def subscribe_method_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_btn(t("btn_pay_stars",  lang), "sub_method_stars")],
        [_btn(t("btn_pay_crypto", lang), "sub_method_crypto")],
        [_btn(t("btn_back",       lang), "menu_back")],
    ])


def subscribe_period_keyboard(lang: str, method: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_btn(t("btn_monthly", lang), f"pay_{method}_pro_monthly")],
        [_btn(t("btn_weekly",  lang), f"pay_{method}_pro_weekly")],
        [_btn(t("btn_back",    lang), "menu_subscribe")],
    ])


def addon_method_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_btn(t("btn_pay_stars",  lang), "addon_method_stars")],
        [_btn(t("btn_pay_crypto", lang), "addon_method_crypto")],
        [_btn(t("btn_back",       lang), "menu_back")],
    ])


# ─── Generic ──────────────────────────────────────────────────────────────────

def back_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[_btn(t("btn_back", lang), "menu_back")]])


def owner_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Keyboard for owner/dev panel."""
    from translations import t as _t
    return InlineKeyboardMarkup([
        [_btn(_t("btn_owner_panel", lang), "menu_owner_panel")],
        [_btn(_t("btn_my_account",  lang), "menu_my_account"),
         _btn(_t("btn_language",    lang), "menu_language")],
    ])
