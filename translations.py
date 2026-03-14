# Custom Emoji IDs (Telegram Premium animated emojis)
E = {
    # IDs verified from real Telegram Premium usage
    "tg":        "5852830669599674051",   # ✈️ (tg logo animated)
    "dev":       "5971889748615105853",   # 💻 مطور
    "loading":   "5971837680726576448",   # 🔸 انتظار
    "check":     "5215492745900077682",   # ✅ صح
    "check2":    "5852871561983299073",   # ✅ صح (variant)
    "fail":      "5852812849780362931",   # ❌ فشل
    "fail2":     "5852477713482255786",   # ⛔ فشل (variant)
    "shield":    "5895483165182529286",   # 🛡 أمان
    "pro":       "5978741411158167019",   # 🟢 Pro (green)
    "basic":     "5978878257406152193",   # 🟠 Basic (orange)
    "eyes":      "5267338666224660069",   # 🤬 (animated face)
    "gem":       "5348318749877351830",   # 💎 جيم
    "search":    "5895476993314524652",   # 🔎 بحث
}


def ce(emoji_id: str, fallback: str = "●") -> str:
    """Build a custom emoji entity string for Telegram HTML parse mode."""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


# Shorthand custom emoji tags (HTML)
# Plain emoji — PatchedBot wraps them automatically before sending
C_CHECK  = "✅"
C_FAIL   = "❌"
C_SHIELD = "🛡"
C_PRO    = "🟢"
C_BASIC  = "🟠"
C_EYES   = "🤬"
C_GEM    = "💎"
C_DEV    = "💻"
C_LOAD   = "🔸"
C_TG     = "✈️"


TEXTS = {
    # General
    "choose_lang": {
        "ar": f"{C_TG} <b>اختار لغتك</b>",
        "en": f"{C_TG} <b>Choose your language</b>",
    },
    "lang_set": {
        "ar": f"{C_CHECK} <b>تم تغيير اللغة إلى العربية</b> \U0001f1f8\U0001f1e6",
        "en": f"{C_CHECK} <b>Language set to English</b> \U0001f1ec\U0001f1e7",
    },
    "select_language": {
        "ar": f"{C_TG} <b>اختار لغتك</b>",
        "en": f"{C_TG} <b>Choose your language</b>",
    },
    "error": {
        "ar": f"{C_FAIL} في مشكلة، جرب مرة ثانية",
        "en": f"{C_FAIL} Something went wrong, please try again",
    },
    "cancelled": {
        "ar": f"{C_FAIL} اتلغى",
        "en": f"{C_FAIL} Cancelled",
    },
    "not_authorized": {
        "ar": f"{C_SHIELD} مش معاك صلاحية لده",
        "en": f"{C_SHIELD} You don't have permission for this",
    },

    # Start / Registration
    "welcome_new": {
        "ar": (
            f"{C_TG} <b>أهلاً بك في Ado Bot!</b>\n\n"
            "بوت إدارة إعلانات قنوات تيليجرام — بدون ما الأدمن يكون عضو في القناة.\n\n"
            f"{C_BASIC} <b>Basic — مجاني</b>\n"
            f"  {C_CHECK} 3 أدمنز | قناة واحدة | كل ساعة إعلان\n\n"
            f"{C_PRO} <b>Pro — $5/شهر</b>\n"
            f"  {C_CHECK} 5 أدمنز | 5 قنوات | مقدمة وخاتمة | فاصل مخصص | إحصائيات\n\n"
            "اشترك الآن أو تواصل مع @{owner}."
        ),
        "en": (
            f"{C_TG} <b>Welcome to Ado Bot!</b>\n\n"
            "Manage Telegram channel announcements — admins post via bot, no channel membership needed.\n\n"
            f"{C_BASIC} <b>Basic — Free</b>\n"
            f"  {C_CHECK} 3 admins | 1 channel | 1 broadcast/hr\n\n"
            f"{C_PRO} <b>Pro — $5/month</b>\n"
            f"  {C_CHECK} 5 admins | 5 channels | header &amp; footer | custom cooldown | stats\n\n"
            "Subscribe now or contact @{owner}."
        ),
    },
    "welcome_back": {
        "ar": (
            f"{C_TG} <b>مرحباً بعودتك!</b>\n\n"
            f"{C_CHECK} مساحة عملك نشطة — استخدم الأزرار أدناه."
        ),
        "en": (
            f"{C_TG} <b>Welcome back!</b>\n\n"
            f"{C_CHECK} Your workspace is active — use the buttons below."
        ),
    },
    "subscription_inactive": {
        "ar": (
            f"{C_GEM} <b>أهلاً! مساحة عملك جاهزة</b>\n\n"
            f"{C_BASIC} <b>Basic — مجاني</b>\n"
            f"  {C_CHECK} 3 أدمنز · قناة واحدة · إعلان/ساعة\n\n"
            f"{C_PRO} <b>Pro — $5/شهر · $2/أسبوع</b>\n"
            f"  {C_CHECK} 10 أدمنز · 10 قنوات · جدولة\n"
            f"  {C_CHECK} مقدمة وخاتمة · قوالب · إحصائيات\n"
            f"  {C_CHECK} موافقة المالك · زر Inline · تثبيت\n\n"
            f"{C_LOAD} اشترك دلوقتي أو تواصل مع @{{owner}}"
        ),
        "en": (
            f"{C_GEM} <b>Welcome! Your workspace is ready</b>\n\n"
            f"{C_BASIC} <b>Basic — Free</b>\n"
            f"  {C_CHECK} 3 admins · 1 channel · 1/hr\n\n"
            f"{C_PRO} <b>Pro — $5/mo · $2/wk</b>\n"
            f"  {C_CHECK} 10 admins · 10 channels · scheduling\n"
            f"  {C_CHECK} header/footer · templates · stats\n"
            f"  {C_CHECK} owner approval · inline btn · auto-pin\n\n"
            f"{C_LOAD} Subscribe now or contact @{{owner}}"
        ),
    },
    "subscription_expired": {
        "ar": f"{C_FAIL} انتهى اشتراكك. تواصل مع @{{owner}} للتجديد.",
        "en": f"{C_FAIL} Your subscription has expired. Contact @{{owner}} to renew.",
    },

    # Status
    "status_body": {
        "ar": (
            f"{C_PRO} الباقة: {{plan}}\n"
            f"📅 تنتهي في: {{expiry}}\n"
            f"🫂 الأدمنز: {{admins}}/{{max_admins}}\n"
            f"📡 القنوات: {{channels}}/{{max_channels}}\n"
            f"{C_LOAD} فترة الانتظار: {{cooldown}} دقيقة\n"
            f"👑 أدمنز إضافيين: {{addon_admins}}"
        ),
        "en": (
            f"{C_PRO} Plan: {{plan}}\n"
            f"📅 Expires: {{expiry}}\n"
            f"🫂 Admins: {{admins}}/{{max_admins}}\n"
            f"📡 Channels: {{channels}}/{{max_channels}}\n"
            f"{C_LOAD} Cooldown: {{cooldown}} min\n"
            f"👑 Extra admins: {{addon_admins}}"
        ),
    },

    # Admins
    "admin_added":        {"ar": f"{C_CHECK} تم إضافة الأدمن {{user_id}}", "en": f"{C_CHECK} Admin {{user_id}} added"},
    "admin_removed":      {"ar": f"{C_CHECK} تم حذف الأدمن {{user_id}}", "en": f"{C_CHECK} Admin {{user_id}} removed"},
    "admin_not_found":    {"ar": f"{C_FAIL} الأدمن غير موجود", "en": f"{C_FAIL} Admin not found"},
    "admin_already_exists": {"ar": f"{C_FAIL} هذا المستخدم أدمن بالفعل", "en": f"{C_FAIL} This user is already an admin"},
    "admin_limit_reached": {"ar": f"{C_FAIL} وصلت للحد الأقصى من الأدمنز ({{max}})", "en": f"{C_FAIL} Admin limit reached ({{max}})"},
    "admins_list":        {"ar": "🫂 قائمة الأدمنز:\n{list}", "en": "🫂 Admins list:\n{list}"},
    "no_admins":          {"ar": "لا يوجد أدمنز حتى الآن", "en": "No admins yet"},

    # Channels
    "channel_added":      {"ar": f"{C_CHECK} تم إضافة القناة {{channel}}", "en": f"{C_CHECK} Channel {{channel}} added"},
    "channel_removed":    {"ar": f"{C_CHECK} تم حذف القناة {{channel}}", "en": f"{C_CHECK} Channel {{channel}} removed"},
    "channel_not_found":  {"ar": f"{C_FAIL} القناة غير موجودة", "en": f"{C_FAIL} Channel not found"},
    "channel_already_exists": {"ar": f"{C_FAIL} هذه القناة مضافة بالفعل", "en": f"{C_FAIL} This channel is already added"},
    "channel_limit_reached": {"ar": f"{C_FAIL} وصلت للحد الأقصى من القنوات ({{max}})", "en": f"{C_FAIL} Channel limit reached ({{max}})"},
    "channels_list":      {"ar": "📡 قائمة القنوات:\n{list}", "en": "📡 Channels list:\n{list}"},
    "no_channels":        {"ar": "لا توجد قنوات حتى الآن", "en": "No channels yet"},
    "bot_not_admin_in_channel": {
        "ar": f"{C_FAIL} البوت ليس أدمن في هذه القناة. أضفه أولاً كأدمن.",
        "en": f"{C_FAIL} Bot is not admin in this channel. Add it as admin first.",
    },
    "no_channels_to_broadcast": {
        "ar": f"{C_FAIL} لا توجد قنوات مضافة في مساحة عملك",
        "en": f"{C_FAIL} No channels added to your workspace",
    },

    # Broadcast
    "only_text": {
        "ar": f"{C_FAIL} يُقبل النص فقط. لا صور أو فيديوهات أو ملصقات.",
        "en": f"{C_FAIL} Only plain text messages are accepted.",
    },
    "broadcast_preview": {
        "ar": f"{C_EYES} <b>معاينة الإعلان:</b>\n\n{{message}}\n\nهل تريد النشر؟",
        "en": f"{C_EYES} <b>Broadcast preview:</b>\n\n{{message}}\n\nConfirm posting?",
    },
    "cooldown_active": {
        "ar": f"{C_LOAD} لسه مفيش — استنى {{minutes}}د {{seconds}}ث",
        "en": f"{C_LOAD} Hold on — {{minutes}}m {{seconds}}s remaining",
    },
    "blackout_active": {
        "ar": f"{C_SHIELD} النشر ممنوع من {{start}}:00 حتى {{end}}:00\nحاول بعدين.",
        "en": f"{C_SHIELD} Broadcasting is blocked from {{start}}:00 to {{end}}:00\nPlease try later.",
    },
    "broadcast_sent": {
        "ar": f"{C_CHECK} اتنشر الإعلان في {{count}} قناة",
        "en": f"{C_CHECK} Broadcast sent to {{count}} channel(s)",
    },
    "send_broadcast_text": {
        "ar": f"{C_DEV} ابعت نص الإعلان:",
        "en": f"{C_DEV} Type your broadcast message:",
    },

    # Template
    "template_pro_only": {
        "ar": f"{C_PRO} المقدمة والخاتمة متاحة في باقة Pro فقط.\nاشترك الآن!",
        "en": f"{C_PRO} Header &amp; Footer are available in Pro plan only.\nSubscribe now!",
    },
    "template_menu_title": {"ar": "🎨 إعدادات القالب", "en": "🎨 Template Settings"},
    "template_current": {
        "ar": "الإعدادات الحالية:\n\n📌 المقدمة: {header}\n📌 الخاتمة: {footer}\n🪪 إظهار المرسل: {sender_info}",
        "en": "Current settings:\n\n📌 Header: {header}\n📌 Footer: {footer}\n🪪 Show sender: {sender_info}",
    },
    "send_header_text":  {"ar": f"{C_DEV} أرسل نص المقدمة:", "en": f"{C_DEV} Send header text:"},
    "send_footer_text":  {"ar": f"{C_DEV} أرسل نص الخاتمة:", "en": f"{C_DEV} Send footer text:"},
    "header_set":        {"ar": f"{C_CHECK} تم حفظ المقدمة", "en": f"{C_CHECK} Header saved"},
    "footer_set":        {"ar": f"{C_CHECK} تم حفظ الخاتمة", "en": f"{C_CHECK} Footer saved"},
    "header_cleared":    {"ar": "🧹 تم حذف المقدمة", "en": "🧹 Header cleared"},
    "footer_cleared":    {"ar": "🧹 تم حذف الخاتمة", "en": "🧹 Footer cleared"},
    "sender_info_on":    {"ar": f"{C_CHECK} تم تفعيل إظهار المرسل", "en": f"{C_CHECK} Sender info enabled"},
    "sender_info_off":   {"ar": f"{C_CHECK} تم إيقاف إظهار المرسل", "en": f"{C_CHECK} Sender info disabled"},
    "template_preview_title": {"ar": f"{C_EYES} معاينة القالب:", "en": f"{C_EYES} Template preview:"},
    "sample_broadcast_text": {"ar": "هذا مثال على نص الإعلان", "en": "This is a sample broadcast message"},
    "none_set":  {"ar": "غير محدد", "en": "Not set"},
    "enabled":   {"ar": "مفعّل ✅", "en": "Enabled ✅"},
    "disabled":  {"ar": "معطّل ❌", "en": "Disabled ❌"},

    # Cooldown Settings (Pro)
    "cooldown_pro_only": {
        "ar": f"{C_PRO} التحكم في فترة الانتظار متاح في Pro فقط.",
        "en": f"{C_PRO} Custom cooldown is available in Pro plan only.",
    },
    "cooldown_settings_title": {
        "ar": f"{C_LOAD} إعدادات فترة الانتظار\n\nالحالي: {{current}} دقيقة\nالحد الأدنى: 5 دقائق",
        "en": f"{C_LOAD} Cooldown Settings\n\nCurrent: {{current}} min\nMinimum: 5 min",
    },
    "send_cooldown_minutes": {
        "ar": f"{C_DEV} أرسل فترة الانتظار بالدقائق (5 - 1440):",
        "en": f"{C_DEV} Send cooldown in minutes (5 - 1440):",
    },
    "cooldown_updated": {
        "ar": f"{C_CHECK} تم تحديث فترة الانتظار إلى {{minutes}} دقيقة",
        "en": f"{C_CHECK} Cooldown updated to {{minutes}} minutes",
    },
    "cooldown_invalid": {
        "ar": f"{C_FAIL} رقم غير صحيح. أدخل رقم بين 5 و 1440",
        "en": f"{C_FAIL} Invalid. Enter a number between 5 and 1440",
    },
    "cooldown_reset": {
        "ar": f"{C_CHECK} تم إعادة فترة الانتظار للافتراضي",
        "en": f"{C_CHECK} Cooldown reset to default",
    },

    # Blackout Hours (Pro)
    "blackout_pro_only": {
        "ar": f"{C_PRO} الأوقات الممنوعة متاحة في Pro فقط.",
        "en": f"{C_PRO} Blackout hours are available in Pro plan only.",
    },
    "blackout_menu_title": {
        "ar": "🌙 الأوقات الممنوعة\n\nالحالي: {current}",
        "en": "🌙 Blackout Hours\n\nCurrent: {current}",
    },
    "blackout_none":    {"ar": "غير محدد", "en": "Not set"},
    "blackout_current": {"ar": "من {start}:00 حتى {end}:00", "en": "From {start}:00 to {end}:00"},
    "send_blackout_range": {
        "ar": f"{C_DEV} أرسل نطاق الساعات بالصيغة:\n<code>بداية-نهاية</code>\nمثال: <code>23-7</code> يعني من 11 مساءً حتى 7 صباحاً",
        "en": f"{C_DEV} Send hour range as:\n<code>start-end</code>\nExample: <code>23-7</code> means 11 PM to 7 AM",
    },
    "blackout_set": {
        "ar": f"{C_CHECK} تم تعيين الأوقات الممنوعة: {{start}}:00 - {{end}}:00",
        "en": f"{C_CHECK} Blackout set: {{start}}:00 - {{end}}:00",
    },
    "blackout_invalid": {
        "ar": f"{C_FAIL} صيغة غير صحيحة. أرسل مثلاً: <code>23-7</code>",
        "en": f"{C_FAIL} Invalid format. Example: <code>23-7</code>",
    },
    "blackout_cleared": {"ar": f"{C_CHECK} تم حذف الأوقات الممنوعة", "en": f"{C_CHECK} Blackout hours cleared"},

    # Stats
    "stats_pro_only": {
        "ar": f"{C_PRO} الإحصائيات متاحة في Pro فقط.",
        "en": f"{C_PRO} Statistics are available in Pro plan only.",
    },
    "stats_title": {
        "ar": (
            f"📈 <b>إحصائيات مساحة عملك</b>\n\n"
            f"🚀 إجمالي الإعلانات: {{total}}\n"
            f"📅 هذا الشهر: {{month}}\n"
            f"📡 إجمالي الوصول: {{reaches}} قناة\n"
            f"🕐 آخر إعلان: {{last}}"
        ),
        "en": (
            f"📈 <b>Workspace Statistics</b>\n\n"
            f"🚀 Total broadcasts: {{total}}\n"
            f"📅 This month: {{month}}\n"
            f"📡 Total reaches: {{reaches}} channel(s)\n"
            f"🕐 Last broadcast: {{last}}"
        ),
    },
    "stats_no_data": {"ar": "لا توجد إعلانات حتى الآن", "en": "No broadcasts yet"},

    # Payments / Subscribe
    "subscribe_title": {
        "ar": (
            f"{C_GEM} <b>اشترك في Pro</b>\n\n"
            f"  {C_CHECK} حتى 5 أدمنز\n"
            f"  {C_CHECK} حتى 5 قنوات\n"
            f"  {C_CHECK} مقدمة وخاتمة\n"
            f"  {C_CHECK} تحكم في فترة الانتظار\n"
            f"  {C_CHECK} أوقات ممنوعة\n"
            f"  {C_CHECK} إحصائيات\n\n"
            "اختار طريقة الدفع:"
        ),
        "en": (
            f"{C_GEM} <b>Subscribe to Pro</b>\n\n"
            f"  {C_CHECK} Up to 5 admins\n"
            f"  {C_CHECK} Up to 5 channels\n"
            f"  {C_CHECK} Header &amp; Footer\n"
            f"  {C_CHECK} Custom cooldown\n"
            f"  {C_CHECK} Blackout hours\n"
            f"  {C_CHECK} Statistics\n\n"
            "Choose payment method:"
        ),
    },
    "subscribe_period": {
        "ar": "اختار مدة الاشتراك:",
        "en": "Choose subscription period:",
    },
    "pay_stars_invoice_title": {
        "ar": "اشتراك Pro — {period}",
        "en": "Pro Subscription — {period}",
    },
    "pay_stars_invoice_desc": {
        "ar": "تفعيل باقة Pro لمساحة عملك",
        "en": "Activate Pro plan for your workspace",
    },
    "pay_crypto_instructions": {
        "ar": f"{C_SHIELD} <b>الدفع بالكريبتو</b>\n\nالمبلغ: ${{amount}}\nاضغط الزر أدناه لإتمام الدفع عبر OxaPay\n\n{C_LOAD} بعد الدفع سيتم التفعيل تلقائياً",
        "en": f"{C_SHIELD} <b>Crypto Payment</b>\n\nAmount: ${{amount}}\nTap below to pay via OxaPay\n\n{C_LOAD} Activation is automatic after payment",
    },
    "payment_success": {
        "ar": f"{C_GEM} <b>تم الدفع بنجاح!</b>\nتم تفعيل باقة Pro حتى {{expiry}}",
        "en": f"{C_GEM} <b>Payment successful!</b>\nPro plan activated until {{expiry}}",
    },
    "payment_pending": {
        "ar": f"{C_LOAD} في انتظار تأكيد الدفع...\nسيتم التفعيل تلقائياً",
        "en": f"{C_LOAD} Waiting for payment confirmation...\nActivation is automatic",
    },
    "addon_admins_title": {
        "ar": f"👑 <b>إضافة 5 أدمنز إضافيين</b>\n\nالسعر: $1 (مرة واحدة)\n\nاختار طريقة الدفع:",
        "en": f"👑 <b>Add 5 Extra Admins</b>\n\nPrice: $1 (one-time)\n\nChoose payment method:",
    },

    # Owner commands
    "workspace_activated": {
        "ar": f"{C_CHECK} تم تفعيل مساحة العمل للمستخدم {{user_id}}\nالباقة: {{plan}}\nتنتهي في: {{expiry}}",
        "en": f"{C_CHECK} Workspace activated for user {{user_id}}\nPlan: {{plan}}\nExpires: {{expiry}}",
    },
    "workspace_deactivated": {
        "ar": f"{C_CHECK} تم إيقاف مساحة العمل للمستخدم {{user_id}}",
        "en": f"{C_CHECK} Workspace deactivated for user {{user_id}}",
    },
    "workspace_extended": {
        "ar": f"{C_CHECK} تم تمديد الاشتراك {{days}} يوم للمستخدم {{user_id}}",
        "en": f"{C_CHECK} Subscription extended by {{days}} days for user {{user_id}}",
    },
    "workspace_not_found": {
        "ar": f"{C_FAIL} لا يوجد workspace لهذا المستخدم",
        "en": f"{C_FAIL} No workspace found for this user",
    },
    "workspaces_list": {"ar": "📋 مساحات العمل:\n\n{list}", "en": "📋 Workspaces:\n\n{list}"},
    "no_workspaces":   {"ar": "لا توجد مساحات عمل", "en": "No workspaces found"},
    "usage_activate": {
        "ar": f"{C_DEV} الاستخدام: /activate &lt;user_id&gt; &lt;basic|pro&gt; &lt;days&gt;",
        "en": f"{C_DEV} Usage: /activate &lt;user_id&gt; &lt;basic|pro&gt; &lt;days&gt;",
    },
    "usage_deactivate": {
        "ar": f"{C_DEV} الاستخدام: /deactivate &lt;user_id&gt;",
        "en": f"{C_DEV} Usage: /deactivate &lt;user_id&gt;",
    },
    "usage_extend": {
        "ar": f"{C_DEV} الاستخدام: /extend &lt;user_id&gt; &lt;days&gt;",
        "en": f"{C_DEV} Usage: /extend &lt;user_id&gt; &lt;days&gt;",
    },
    "notify_activated": {
        "ar": f"{C_GEM} <b>تم تفعيل اشتراكك!</b>\nالباقة: {{plan}}\nتنتهي في: {{expiry}}\n\nيمكنك البدء الآن.",
        "en": f"{C_GEM} <b>Your subscription has been activated!</b>\nPlan: {{plan}}\nExpires: {{expiry}}\n\nYou can start now.",
    },

    # Buttons
    "btn_status":        {"ar": "🔮 الحالة",              "en": "🔮 Status"},
    "btn_admins":        {"ar": "🫂 الأدمنز",             "en": "🫂 Admins"},
    "btn_channels":      {"ar": "📡 القنوات",             "en": "📡 Channels"},
    "btn_template":      {"ar": "🎨 القالب",              "en": "🎨 Template"},
    "btn_language":      {"ar": "🌍 اللغة",               "en": "🌍 Language"},
    "btn_stats":         {"ar": "📈 الإحصائيات",          "en": "📈 Statistics"},
    "btn_cooldown":      {"ar": "⏳ فترة الانتظار",        "en": "⏳ Cooldown"},
    "btn_blackout":      {"ar": "🌙 أوقات ممنوعة",        "en": "🌙 Blackout Hours"},
    "btn_subscribe":     {"ar": "💎 ترقية إلى Pro",       "en": "💎 Upgrade to Pro"},
    "btn_addon_admins":  {"ar": "👑 +5 أدمنز — $1 · 150 ⭐","en": "👑 +5 Admins — $1 · 150 ⭐"},
    "btn_confirm":       {"ar": "✨ نشر الآن",            "en": "✨ Publish Now"},
    "btn_cancel":        {"ar": "🗑️ إلغاء",              "en": "🗑️ Cancel"},
    "btn_set_header":    {"ar": "🔝 تعيين المقدمة",       "en": "🔝 Set Header"},
    "btn_set_footer":    {"ar": "🔚 تعيين الخاتمة",       "en": "🔚 Set Footer"},
    "btn_clear_header":  {"ar": "🧹 حذف المقدمة",         "en": "🧹 Clear Header"},
    "btn_clear_footer":  {"ar": "🧹 حذف الخاتمة",         "en": "🧹 Clear Footer"},
    "btn_preview":       {"ar": "🪄 معاينة",              "en": "🪄 Preview"},
    "btn_back":          {"ar": "↩️ رجوع",               "en": "↩️ Back"},
    "btn_sender_on":     {"ar": "🪪 المرسل: مفعّل ✅",   "en": "🪪 Sender: ON ✅"},
    "btn_sender_off":    {"ar": "🪪 المرسل: معطّل ❌",   "en": "🪪 Sender: OFF ❌"},
    "btn_broadcast":     {"ar": "🚀 نشر إعلان",         "en": "🚀 New Broadcast"},
    "btn_pay_stars":     {"ar": "⭐ Stars",               "en": "⭐ Stars"},
    "btn_pay_crypto":    {"ar": "🔐 Crypto · USDT",       "en": "🔐 Crypto · USDT"},
    "btn_monthly":       {"ar": "🗓 شهري — $5 · 600 ⭐",  "en": "🗓 Monthly — $5 · 600 ⭐"},
    "btn_weekly":        {"ar": "📅 أسبوعي — $2 · 250 ⭐","en": "📅 Weekly — $2 · 250 ⭐"},
    "btn_reset_cooldown":{"ar": "↺ إعادة للافتراضي",     "en": "↺ Reset to default"},
    "btn_clear_blackout":{"ar": "🧹 حذف الأوقات الممنوعة","en": "🧹 Clear Blackout"},
    "btn_set_blackout":  {"ar": "🌙 تعيين الأوقات",       "en": "🌙 Set Hours"},
}


def t(key: str, lang: str, **kwargs) -> str:
    text = TEXTS.get(key, {}).get(lang) or TEXTS.get(key, {}).get("en", key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text


# HTML parse mode constant - import this in handlers
PARSE_HTML = {"parse_mode": "HTML"}

# ─── v3 additions ─────────────────────────────────────────────────────────────

TEXTS.update({
    # Workspace picker
    "pick_workspace": {
        "ar": f"👋 أهلاً! اختار مساحة العمل:",
        "en": "👋 Welcome! Choose a workspace:",
    },

    # Broadcast log
    "broadcast_log_entry": {
        "ar": (
            "📋 <b>سجل إعلان جديد</b>\n\n"
            "👤 المرسل: {sender}\n"
            "📡 القنوات: {channels}\n"
            "🕐 الوقت: {time}\n"
            "{pin_line}"
            "✅ نجح: {ok} | ❌ فشل: {fail}\n\n"
            "─────────────\n"
            "{text}"
        ),
        "en": (
            "📋 <b>New Broadcast Log</b>\n\n"
            "👤 Sender: {sender}\n"
            "📡 Channels: {channels}\n"
            "🕐 Time: {time}\n"
            "{pin_line}"
            "✅ Sent: {ok} | ❌ Failed: {fail}\n\n"
            "─────────────\n"
            "{text}"
        ),
    },
    "log_pinned_line": {
        "ar": "📌 تم التثبيت\n",
        "en": "📌 Pinned\n",
    },

    # Channel selection
    "select_channels": {
        "ar": "📡 اختار القنوات اللي عايز ترسل ليها:",
        "en": "📡 Select channels to broadcast to:",
    },
    "no_channels_selected": {
        "ar": f"❌ اختار قناة واحدة على الأقل",
        "en": f"❌ Select at least one channel",
    },

    # Broadcast options
    "broadcast_options": {
        "ar": "⚙️ خيارات النشر:",
        "en": "⚙️ Broadcast options:",
    },

    # Schedule
    "send_schedule_time": {
        "ar": (
            "⏰ أرسل وقت النشر بالصيغة:\n"
            "<code>YYYY-MM-DD HH:MM</code>\n\n"
            "مثال: <code>2025-03-20 14:30</code>\n"
            "أو بعد كذا ساعة: <code>+2h</code> أو <code>+30m</code>"
        ),
        "en": (
            "⏰ Send the scheduled time:\n"
            "<code>YYYY-MM-DD HH:MM</code>\n\n"
            "Example: <code>2025-03-20 14:30</code>\n"
            "Or relative: <code>+2h</code> or <code>+30m</code>"
        ),
    },
    "schedule_invalid": {
        "ar": "❌ صيغة غير صحيحة. مثال: <code>2025-03-20 14:30</code> أو <code>+2h</code>",
        "en": "❌ Invalid format. Example: <code>2025-03-20 14:30</code> or <code>+2h</code>",
    },
    "schedule_past": {
        "ar": "❌ الوقت ده في الماضي. اختار وقت في المستقبل.",
        "en": "❌ That time is in the past. Choose a future time.",
    },
    "scheduled_ok": {
        "ar": "✅ تم جدولة الإعلان للنشر في {time}",
        "en": "✅ Broadcast scheduled for {time}",
    },
    "schedule_menu_empty": {
        "ar": "لا توجد إعلانات مجدولة",
        "en": "No scheduled broadcasts",
    },
    "scheduled_cancelled": {
        "ar": "✅ تم إلغاء الإعلان المجدول",
        "en": "✅ Scheduled broadcast cancelled",
    },

    # Inline button
    "send_inline_btn": {
        "ar": "🔘 أرسل نص الزر والرابط بالصيغة:\n<code>نص الزر | https://example.com</code>",
        "en": "🔘 Send button text and URL:\n<code>Button text | https://example.com</code>",
    },
    "inline_btn_invalid": {
        "ar": "❌ صيغة غير صحيحة. مثال: <code>زيارة الموقع | https://example.com</code>",
        "en": "❌ Invalid format. Example: <code>Visit Site | https://example.com</code>",
    },
    "inline_btn_set": {
        "ar": "✅ تم إضافة الزر: <b>{text}</b>",
        "en": "✅ Button added: <b>{text}</b>",
    },

    # Approval
    "approval_request": {
        "ar": (
            "⏳ <b>طلب موافقة على إعلان</b>\n\n"
            "👤 المرسل: {sender}\n"
            "📡 القنوات: {channels}\n\n"
            "─────────────\n"
            "{text}"
        ),
        "en": (
            "⏳ <b>Broadcast Approval Request</b>\n\n"
            "👤 Sender: {sender}\n"
            "📡 Channels: {channels}\n\n"
            "─────────────\n"
            "{text}"
        ),
    },
    "approval_pending_notice": {
        "ar": "⏳ تم إرسال إعلانك للمالك للموافقة عليه.",
        "en": "⏳ Your broadcast has been sent to the owner for approval.",
    },
    "approval_approved": {
        "ar": "✅ تمت الموافقة على الإعلان ونُشر.",
        "en": "✅ Broadcast approved and published.",
    },
    "approval_rejected": {
        "ar": "❌ تم رفض الإعلان من قِبل المالك.",
        "en": "❌ Broadcast rejected by owner.",
    },
    "approval_notif_approved": {
        "ar": "✅ وافقت على الإعلان وتم نشره.",
        "en": "✅ You approved the broadcast and it was published.",
    },
    "approval_notif_rejected": {
        "ar": "❌ رفضت الإعلان.",
        "en": "❌ You rejected the broadcast.",
    },

    # Named templates
    "named_templates_menu": {
        "ar": "📋 <b>القوالب المسماة</b>\n\nاختار قالب لاستخدامه أو أضف جديد:",
        "en": "📋 <b>Named Templates</b>\n\nSelect a template or add a new one:",
    },
    "named_templates_empty": {
        "ar": "لا توجد قوالب. أضف قالب جديد!",
        "en": "No templates yet. Add one!",
    },
    "send_template_name": {
        "ar": "📝 أرسل اسم القالب (كلمة واحدة بدون مسافات):",
        "en": "📝 Send the template name (one word, no spaces):",
    },
    "send_template_content": {
        "ar": "📝 أرسل محتوى القالب:",
        "en": "📝 Send the template content:",
    },
    "template_saved": {
        "ar": "✅ تم حفظ القالب <b>{name}</b>",
        "en": "✅ Template <b>{name}</b> saved",
    },
    "template_deleted": {
        "ar": "🧹 تم حذف القالب <b>{name}</b>",
        "en": "🧹 Template <b>{name}</b> deleted",
    },
    "template_name_invalid": {
        "ar": "❌ الاسم يجب أن يكون كلمة واحدة بدون مسافات أو رموز خاصة",
        "en": "❌ Name must be a single word with no spaces or special characters",
    },

    # Pro settings
    "pro_settings_title": {
        "ar": "⚙️ <b>إعدادات Pro</b>\n\nالإعدادات الخاصة بك كمالك:",
        "en": "⚙️ <b>Pro Settings</b>\n\nOwner-only settings:",
    },
    "pro_setting_toggled": {
        "ar": "✅ تم تحديث الإعداد",
        "en": "✅ Setting updated",
    },
    "inline_btn_cleared": {
        "ar": "🧹 تم حذف زر الإعلان الافتراضي",
        "en": "🧹 Default inline button cleared",
    },

    # Draft-only
    "draft_only_menu": {
        "ar": "👤 <b>إدارة صلاحيات الأدمنز</b>\n\nاختار أدمن لتغيير صلاحيته:",
        "en": "👤 <b>Admin Permissions</b>\n\nSelect an admin to toggle their permissions:",
    },
    "draft_only_set": {
        "ar": "✅ {user} — وضع المسودة فقط: {status}",
        "en": "✅ {user} — Draft-only mode: {status}",
    },
    "draft_only_blocked": {
        "ar": "⛔ أنت في وضع المسودة فقط. المالك يجب يوافق على إعلاناتك.",
        "en": "⛔ You're in draft-only mode. The owner must approve your broadcasts.",
    },

    # Broadcast log viewer
    "log_title": {
        "ar": "📋 <b>سجل آخر الإعلانات</b>",
        "en": "📋 <b>Recent Broadcast Log</b>",
    },
    "log_empty": {
        "ar": "لا توجد إعلانات حتى الآن",
        "en": "No broadcasts yet",
    },
    "log_entry": {
        "ar": "• {time} | {sender} → {channels} قناة\n  <i>{text}</i>",
        "en": "• {time} | {sender} → {channels} ch\n  <i>{text}</i>",
    },

    # Lookup
    "lookup_user_result": {
        "ar": (
            "🔍 <b>نتيجة البحث</b>\n\n"
            "👤 المستخدم: {user}\n\n"
            "🏠 <b>مالك في:</b>\n{owned}\n\n"
            "🫂 <b>أدمن في:</b>\n{member}"
        ),
        "en": (
            "🔍 <b>Lookup Result</b>\n\n"
            "👤 User: {user}\n\n"
            "🏠 <b>Owner of:</b>\n{owned}\n\n"
            "🫂 <b>Admin in:</b>\n{member}"
        ),
    },
    "lookup_not_found": {
        "ar": "❌ لا توجد بيانات لهذا المستخدم/القناة",
        "en": "❌ No data found for this user/channel",
    },
    "lookup_usage": {
        "ar": "الاستخدام: /lookup <user_id أو @username>",
        "en": "Usage: /lookup <user_id or @username>",
    },

    # New buttons
    "btn_schedule":         {"ar": "⏰ الإعلانات المجدولة","en": "⏰ Scheduled Broadcasts"},
    "btn_pro_settings":     {"ar": "⚙️ إعدادات Pro",     "en": "⚙️ Pro Settings"},
    "btn_log":              {"ar": "📋 السجل",            "en": "📋 Log"},
    "btn_templates_named":  {"ar": "📋 القوالب",          "en": "📋 Templates"},
    "btn_named_templates":  {"ar": "📋 استخدام قالب",    "en": "📋 Use Template"},
    "btn_new_template":     {"ar": "➕ قالب جديد",        "en": "➕ New Template"},
    "btn_approval":         {"ar": "🔐 موافقة المالك",   "en": "🔐 Owner Approval"},
    "btn_auto_pin":         {"ar": "📌 تثبيت بعد النشر", "en": "📌 Auto-pin"},
    "btn_log_toggle":       {"ar": "📋 سجل النشر",       "en": "📋 Broadcast Log"},
    "btn_inline_btn_setup": {"ar": "🔘 زر افتراضي للإعلانات","en": "🔘 Default Inline Button"},
    "btn_draft_only_setup": {"ar": "👤 صلاحيات الأدمنز", "en": "👤 Admin Permissions"},
    "btn_select_all":       {"ar": "✅ الكل",             "en": "✅ All"},
    "btn_clear_sel":        {"ar": "☐ إلغاء الكل",       "en": "☐ Clear"},
    "btn_next":             {"ar": "▶️ تأكيد الاختيار",  "en": "▶️ Confirm Selection"},
    "btn_send_now":         {"ar": "🚀 نشر الآن",         "en": "🚀 Publish Now"},
    "btn_add_inline_btn":   {"ar": "🔘 إضافة زر",        "en": "🔘 Add Button"},
    "btn_approve":          {"ar": "✅ موافقة",           "en": "✅ Approve"},
    "btn_reject":           {"ar": "❌ رفض",              "en": "❌ Reject"},
})

# Make btn_ entries work with t() like the others
for _k, _v in list(TEXTS.items()):
    if isinstance(_v, str):
        TEXTS[_k] = {"ar": _v, "en": _v}

# ── Missing keys (account, owner panel, language) ─────────────────────────────
TEXTS.update({
    "language_set": {
        "ar": f"{C_CHECK} <b>تم التغيير للعربية</b> 🇸🇦\n\nاستخدم الأزرار أدناه للمتابعة.",
        "en": f"{C_CHECK} <b>Language set to English</b> 🇬🇧\n\nUse the buttons below to continue.",
    },
    "select_language": {
        "ar": f"{C_TG} <b>اختار لغتك</b>",
        "en": f"{C_TG} <b>Choose your language</b>",
    },
    "btn_my_account": {
        "ar": f"🪪 حسابي",
        "en": f"🪪 My Account",
    },
    "btn_owner_panel": {
        "ar": f"👑 لوحة التحكم",
        "en": f"👑 Dev Panel",
    },
    "account_info": {
        "ar": (
            f"{C_GEM} <b>حسابي</b>\n\n"
            f"{C_PRO} الباقة: <b>{{plan}}</b>\n"
            f"📅 تنتهي في: <code>{{expiry}}</code>\n"
            f"🫂 الأدمنز: {{admins}} / {{max_admins}}\n"
            f"📡 القنوات: {{channels}} / {{max_channels}}\n"
            f"{C_LOAD} فترة الانتظار: {{cooldown}} دقيقة\n"
            f"👑 أدمنز إضافيين: {{addon_admins}}\n\n"
            f"{C_SHIELD} ID: <code>{{user_id}}</code>"
        ),
        "en": (
            f"{C_GEM} <b>My Account</b>\n\n"
            f"{C_PRO} Plan: <b>{{plan}}</b>\n"
            f"📅 Expires: <code>{{expiry}}</code>\n"
            f"🫂 Admins: {{admins}} / {{max_admins}}\n"
            f"📡 Channels: {{channels}} / {{max_channels}}\n"
            f"{C_LOAD} Cooldown: {{cooldown}} min\n"
            f"👑 Extra admins: {{addon_admins}}\n\n"
            f"{C_SHIELD} ID: <code>{{user_id}}</code>"
        ),
    },
    "account_admin_info": {
        "ar": (
            f"{C_DEV} <b>حسابي — أدمن</b>\n\n"
            f"🫂 أنت أدمن في workspace #{{ws_id}}\n"
            f"{C_PRO} الباقة: <b>{{plan}}</b>\n"
            f"📅 تنتهي في: <code>{{expiry}}</code>\n"
            f"{C_LOAD} فترة الانتظار: {{cooldown}} دقيقة\n\n"
            f"{C_SHIELD} ID: <code>{{user_id}}</code>"
        ),
        "en": (
            f"{C_DEV} <b>My Account — Admin</b>\n\n"
            f"🫂 You are admin in workspace #{{ws_id}}\n"
            f"{C_PRO} Plan: <b>{{plan}}</b>\n"
            f"📅 Expires: <code>{{expiry}}</code>\n"
            f"{C_LOAD} Cooldown: {{cooldown}} min\n\n"
            f"{C_SHIELD} ID: <code>{{user_id}}</code>"
        ),
    },
    "owner_panel": {
        "ar": (
            f"{C_DEV} <b>لوحة المطور</b>\n\n"
            f"{C_SHIELD} الأوامر:\n"
            f"  /activate — تفعيل workspace\n"
            f"  /deactivate — إيقاف workspace\n"
            f"  /extend — تمديد الاشتراك\n"
            f"  /workspaces — عرض كل الـ workspaces\n"
            f"  /lookup — البحث عن مستخدم أو قناة\n"
            f"  /backup — نسخة احتياطية فورية"
        ),
        "en": (
            f"{C_DEV} <b>Developer Panel</b>\n\n"
            f"{C_SHIELD} Commands:\n"
            f"  /activate — activate workspace\n"
            f"  /deactivate — deactivate workspace\n"
            f"  /extend — extend subscription\n"
            f"  /workspaces — list all workspaces\n"
            f"  /lookup — search user or channel\n"
            f"  /backup — instant backup"
        ),
    },
})
