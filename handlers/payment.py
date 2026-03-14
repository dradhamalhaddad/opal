import logging
import uuid
from datetime import datetime, timedelta

import httpx
from telegram import Update, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import (
    STARS_PRO_MONTHLY, STARS_PRO_WEEKLY, STARS_ADDON_ADMINS,
    ADDON_EXTRA_ADMINS, OWNER_USERNAME
)
from database import (
    get_workspace, create_workspace, activate_workspace,
    add_addon_admins, get_user_lang, create_payment, mark_payment_paid
)
from translations import t
from keyboards import subscribe_method_keyboard, subscribe_period_keyboard, addon_method_keyboard, back_keyboard

logger = logging.getLogger(__name__)

OXAPAY_MERCHANT_KEY = "OKIS2P-VYNXFU-EPIS7I-WD7NBT"
OXAPAY_BASE         = "https://api.oxapay.com"


# ─── Oxapay ───────────────────────────────────────────────────────────────────

async def create_oxapay_invoice(amount_usd: float, order_id: str, description: str = "") -> str | None:
    data = {
        "merchant":    OXAPAY_MERCHANT_KEY,
        "amount":      amount_usd,
        "currency":    "USDT",
        "lifeTime":    30,
        "orderId":     order_id,
        "description": description or "ad0bot subscription",
        "feePaidByPayer": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp   = await client.post(f"{OXAPAY_BASE}/merchants/request", json=data)
            result = resp.json()
            if result.get("result") == 100:
                return result.get("payLink")
            logger.error(f"Oxapay invoice error: {result}")
    except Exception as e:
        logger.error(f"Oxapay request failed: {e}")
    return None


# ─── Subscribe menu ───────────────────────────────────────────────────────────

async def handle_subscribe_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    await query.edit_message_text(
        t("subscribe_title", lang, parse_mode="HTML"), parse_mode="HTML",
        reply_markup=subscribe_method_keyboard(lang))


async def handle_sub_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    lang   = await get_user_lang(query.from_user.id)
    method = query.data.split("_")[2]
    await query.edit_message_text(
        t("subscribe_period", lang, parse_mode="HTML"), parse_mode="HTML",
        reply_markup=subscribe_period_keyboard(lang, method))


async def handle_pay_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await get_user_lang(user_id)

    parts  = query.data.split("_")
    period = parts[3]
    stars  = STARS_PRO_MONTHLY if period == "monthly" else STARS_PRO_WEEKLY
    period_label = "Monthly" if period == "monthly" else "Weekly"

    ws = await get_workspace(user_id)
    if not ws:
        await create_workspace(user_id)
        ws = await get_workspace(user_id)

    order_id = str(uuid.uuid4())
    await create_payment(ws["id"], user_id, "stars", "pro", period, order_id, stars_amount=stars)
    await query.edit_message_text(t("payment_pending", lang, parse_mode="HTML"), parse_mode="HTML")
    await context.bot.send_invoice(
        chat_id=user_id,
        title=t("pay_stars_invoice_title", lang, period=period_label),
        description=t("pay_stars_invoice_desc", lang),
        payload=f"pro_{period}_{order_id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Pro", amount=stars)],
    )


async def handle_sub_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """pay_crypto_pro_monthly / pay_crypto_pro_weekly"""
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await get_user_lang(user_id)

    parts  = query.data.split("_")
    period = parts[3]
    amount = 5.0 if period == "monthly" else 2.0

    ws = await get_workspace(user_id)
    if not ws:
        await create_workspace(user_id)
        ws = await get_workspace(user_id)

    order_id = str(uuid.uuid4())
    await create_payment(ws["id"], user_id, "oxapay", "pro", period, order_id, amount_usd=amount)

    desc = f"ad0bot Pro {'Monthly' if period == 'monthly' else 'Weekly'}"
    url  = await create_oxapay_invoice(amount, order_id, desc)

    if url:
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay Now", url=url)]])
        await query.edit_message_text(
            t("pay_crypto_instructions", lang, amount=amount, parse_mode="HTML"), parse_mode="HTML",
            reply_markup=markup)
    else:
        await query.edit_message_text(t("error", lang, parse_mode="HTML"), parse_mode="HTML",
                                      reply_markup=back_keyboard(lang))


# ─── Addon admins ─────────────────────────────────────────────────────────────

async def handle_addon_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await get_user_lang(query.from_user.id)
    await query.edit_message_text(
        t("addon_admins_info", lang,
          count=ADDON_EXTRA_ADMINS["count"],
          usd=ADDON_EXTRA_ADMINS["price_usd"],
          stars=STARS_ADDON_ADMINS, parse_mode="HTML"),
        parse_mode="HTML",
        reply_markup=addon_method_keyboard(lang))


async def handle_addon_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await get_user_lang(user_id)

    ws = await get_workspace(user_id)
    if not ws or not ws["is_active"] or ws["plan"] != "pro":
        await query.edit_message_text(
            t("subscription_inactive", lang, owner=OWNER_USERNAME, parse_mode="HTML"), parse_mode="HTML")
        return

    order_id = str(uuid.uuid4())
    await create_payment(ws["id"], user_id, "stars", "addon_admins", "once",
                         order_id, stars_amount=STARS_ADDON_ADMINS)
    await query.edit_message_text(t("payment_pending", lang, parse_mode="HTML"), parse_mode="HTML")
    await context.bot.send_invoice(
        chat_id=user_id,
        title="➕ 5 Extra Admins" if lang == "en" else "➕ 5 أدمنز إضافيين",
        description="Add 5 extra admin slots" if lang == "en" else "إضافة 5 خانات أدمن",
        payload=f"addon_admins_{order_id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="5 Extra Admins", amount=STARS_ADDON_ADMINS)],
    )


async def handle_addon_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang    = await get_user_lang(user_id)

    ws = await get_workspace(user_id)
    if not ws or not ws["is_active"] or ws["plan"] != "pro":
        await query.edit_message_text(
            t("subscription_inactive", lang, owner=OWNER_USERNAME, parse_mode="HTML"), parse_mode="HTML")
        return

    order_id = str(uuid.uuid4())
    await create_payment(ws["id"], user_id, "oxapay", "addon_admins", "once",
                         order_id, amount_usd=1.0)
    url = await create_oxapay_invoice(1.0, order_id, "ad0bot +5 Admin Slots")
    if url:
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay Now", url=url)]])
        await query.edit_message_text(
            t("pay_crypto_instructions", lang, amount=1, parse_mode="HTML"), parse_mode="HTML",
            reply_markup=markup)
    else:
        await query.edit_message_text(t("error", lang, parse_mode="HTML"), parse_mode="HTML",
                                      reply_markup=back_keyboard(lang))


# ─── Pre-checkout + Successful payment ───────────────────────────────────────

async def handle_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang    = await get_user_lang(user_id)
    payload = update.message.successful_payment.invoice_payload

    ws = await get_workspace(user_id)
    if not ws:
        return

    if payload.startswith("pro_"):
        _, period, order_id = payload.split("_", 2)
        days = 30 if period == "monthly" else 7

        base = datetime.fromisoformat(ws["expires_at"]) if ws.get("expires_at") else datetime.now()
        if base < datetime.now():
            base = datetime.now()
        new_expiry = (base + timedelta(days=days)).strftime("%Y-%m-%d %H:%M")

        await activate_workspace(user_id, "pro", new_expiry)
        await mark_payment_paid(order_id)
        await update.message.reply_text(
            t("payment_success", lang, expiry=new_expiry, parse_mode="HTML"), parse_mode="HTML")

    elif payload.startswith("addon_admins_"):
        order_id = payload[len("addon_admins_"):]
        await add_addon_admins(ws["id"], ADDON_EXTRA_ADMINS["count"])
        await mark_payment_paid(order_id)
        count = ADDON_EXTRA_ADMINS["count"]
        msg = f"✅ Added {count} extra admin slots!" if lang == "en" \
              else f"✅ تم إضافة {count} أدمنز إضافيين!"
        await update.message.reply_text(msg, parse_mode="HTML")
