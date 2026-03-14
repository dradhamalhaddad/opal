import aiosqlite
import json
import logging
from datetime import datetime

DB_PATH = "bot.db"
logger  = logging.getLogger(__name__)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id            INTEGER UNIQUE NOT NULL,
                plan                TEXT NOT NULL DEFAULT 'basic',
                activated_at        TEXT,
                expires_at          TEXT,
                is_active           INTEGER NOT NULL DEFAULT 0,
                custom_cooldown_minutes INTEGER,
                addon_extra_admins  INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS admins (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                user_id      INTEGER NOT NULL,
                display_name TEXT,
                draft_only   INTEGER NOT NULL DEFAULT 0,
                added_at     TEXT NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
                UNIQUE(workspace_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS channels (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id     INTEGER NOT NULL,
                channel_id       TEXT NOT NULL,
                channel_username TEXT,
                added_at         TEXT NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
                UNIQUE(workspace_id, channel_id)
            );

            CREATE TABLE IF NOT EXISTS broadcasts (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id      INTEGER NOT NULL,
                admin_id          INTEGER NOT NULL,
                message_text      TEXT,
                final_message     TEXT,
                selected_channels TEXT,
                inline_btn_text   TEXT,
                inline_btn_url    TEXT,
                was_pinned        INTEGER DEFAULT 0,
                was_scheduled     INTEGER DEFAULT 0,
                sent_at           TEXT NOT NULL,
                channels_count    INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS cooldowns (
                workspace_id     INTEGER PRIMARY KEY,
                last_broadcast_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS workspace_settings (
                workspace_id      INTEGER PRIMARY KEY,
                header_text       TEXT,
                footer_text       TEXT,
                show_sender_info  INTEGER NOT NULL DEFAULT 0,
                approval_required INTEGER NOT NULL DEFAULT 0,
                auto_pin          INTEGER NOT NULL DEFAULT 0,
                inline_btn_text   TEXT,
                inline_btn_url    TEXT,
                log_enabled       INTEGER NOT NULL DEFAULT 1,
                auto_repeat_text  TEXT,
                auto_repeat_hours INTEGER
            );

            CREATE TABLE IF NOT EXISTS blackout_hours (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                start_hour   INTEGER NOT NULL,
                end_hour     INTEGER NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
                UNIQUE(workspace_id)
            );

            CREATE TABLE IF NOT EXISTS scheduled_broadcasts (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id     INTEGER NOT NULL,
                admin_id         INTEGER NOT NULL,
                message_text     TEXT NOT NULL,
                final_message    TEXT NOT NULL,
                selected_channels TEXT,
                inline_btn_text  TEXT,
                inline_btn_url   TEXT,
                should_pin       INTEGER DEFAULT 0,
                scheduled_at     TEXT NOT NULL,
                created_at       TEXT NOT NULL,
                status           TEXT NOT NULL DEFAULT 'pending',
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
            );

            CREATE TABLE IF NOT EXISTS named_templates (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                name         TEXT NOT NULL,
                content      TEXT NOT NULL,
                created_at   TEXT NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
                UNIQUE(workspace_id, name)
            );

            CREATE TABLE IF NOT EXISTS pending_approvals (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id     INTEGER NOT NULL,
                admin_id         INTEGER NOT NULL,
                message_text     TEXT NOT NULL,
                final_message    TEXT NOT NULL,
                selected_channels TEXT,
                inline_btn_text  TEXT,
                inline_btn_url   TEXT,
                should_pin       INTEGER DEFAULT 0,
                created_at       TEXT NOT NULL,
                status           TEXT NOT NULL DEFAULT 'pending',
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL,
                owner_id     INTEGER NOT NULL,
                amount_usd   REAL,
                stars_amount INTEGER,
                method       TEXT NOT NULL,
                plan         TEXT NOT NULL,
                period       TEXT,
                order_id     TEXT UNIQUE,
                status       TEXT NOT NULL DEFAULT 'pending',
                created_at   TEXT NOT NULL,
                paid_at      TEXT
            );

            CREATE TABLE IF NOT EXISTS user_prefs (
                user_id INTEGER PRIMARY KEY,
                lang    TEXT NOT NULL DEFAULT 'en'
            );
        """)
        await db.commit()
    logger.info("Database initialized")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _row(r): return dict(r) if r else None


# ─── User Prefs ───────────────────────────────────────────────────────────────

async def get_user_lang(user_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT lang FROM user_prefs WHERE user_id=?", (user_id,)) as c:
            r = await c.fetchone()
            return r[0] if r else "en"


async def set_user_lang(user_id: int, lang: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO user_prefs(user_id,lang) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET lang=?",
            (user_id, lang, lang))
        await db.commit()


# ─── Workspaces ───────────────────────────────────────────────────────────────

async def get_workspace(owner_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM workspaces WHERE owner_id=?", (owner_id,)) as c:
            return _row(await c.fetchone())


async def get_workspace_by_id(ws_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM workspaces WHERE id=?", (ws_id,)) as c:
            return _row(await c.fetchone())


async def create_workspace(owner_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT OR IGNORE INTO workspaces(owner_id,plan,is_active) VALUES(?,?,?)",
            (owner_id, "basic", 0))
        await db.commit()
        if cur.lastrowid:
            return cur.lastrowid
        async with db.execute("SELECT id FROM workspaces WHERE owner_id=?", (owner_id,)) as c:
            return (await c.fetchone())[0]


async def activate_workspace(owner_id: int, plan: str, expires_at: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE workspaces SET plan=?,activated_at=?,expires_at=?,is_active=1 WHERE owner_id=?",
            (plan, datetime.now().isoformat(), expires_at, owner_id))
        await db.commit()


async def deactivate_workspace(owner_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE workspaces SET is_active=0 WHERE owner_id=?", (owner_id,))
        await db.commit()


async def extend_workspace(owner_id: int, new_expiry: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE workspaces SET expires_at=?,is_active=1 WHERE owner_id=?",
            (new_expiry, owner_id))
        await db.commit()


async def get_all_workspaces() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM workspaces ORDER BY id") as c:
            return [dict(r) for r in await c.fetchall()]


async def get_expired_workspaces() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.now().isoformat()
        async with db.execute(
            "SELECT * FROM workspaces WHERE is_active=1 AND expires_at IS NOT NULL AND expires_at<?",
            (now,)) as c:
            return [dict(r) for r in await c.fetchall()]


async def set_custom_cooldown(ws_id: int, minutes: int | None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE workspaces SET custom_cooldown_minutes=? WHERE id=?", (minutes, ws_id))
        await db.commit()


async def add_addon_admins(ws_id: int, count: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE workspaces SET addon_extra_admins=addon_extra_admins+? WHERE id=?", (count, ws_id))
        await db.commit()


# ─── Admins ───────────────────────────────────────────────────────────────────

async def get_workspaces_as_admin(user_id: int) -> list:
    """All workspaces where this user is a regular admin (not owner)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT w.* FROM workspaces w JOIN admins a ON a.workspace_id=w.id WHERE a.user_id=?",
            (user_id,)) as c:
            return [dict(r) for r in await c.fetchall()]


async def get_workspace_by_admin(user_id: int) -> dict | None:
    rows = await get_workspaces_as_admin(user_id)
    return rows[0] if rows else None


async def add_admin(ws_id: int, user_id: int, display_name: str = None) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO admins(workspace_id,user_id,display_name,added_at) VALUES(?,?,?,?)",
                (ws_id, user_id, display_name, datetime.now().isoformat()))
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False


async def remove_admin(ws_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM admins WHERE workspace_id=? AND user_id=?", (ws_id, user_id))
        await db.commit()
        return cur.rowcount > 0


async def get_admins(ws_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM admins WHERE workspace_id=?", (ws_id,)) as c:
            return [dict(r) for r in await c.fetchall()]


async def count_admins(ws_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM admins WHERE workspace_id=?", (ws_id,)) as c:
            return (await c.fetchone())[0]


async def set_admin_draft_only(ws_id: int, user_id: int, draft_only: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE admins SET draft_only=? WHERE workspace_id=? AND user_id=?",
            (1 if draft_only else 0, ws_id, user_id))
        await db.commit()


async def is_admin_draft_only(ws_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT draft_only FROM admins WHERE workspace_id=? AND user_id=?",
            (ws_id, user_id)) as c:
            r = await c.fetchone()
            return bool(r[0]) if r else False


# ─── Channels ─────────────────────────────────────────────────────────────────

async def add_channel(ws_id: int, channel_id: str, username: str = None) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO channels(workspace_id,channel_id,channel_username,added_at) VALUES(?,?,?,?)",
                (ws_id, channel_id, username, datetime.now().isoformat()))
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False


async def remove_channel(ws_id: int, channel_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM channels WHERE workspace_id=? AND channel_id=?", (ws_id, channel_id))
        await db.commit()
        return cur.rowcount > 0


async def get_channels(ws_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM channels WHERE workspace_id=?", (ws_id,)) as c:
            return [dict(r) for r in await c.fetchall()]


async def count_channels(ws_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM channels WHERE workspace_id=?", (ws_id,)) as c:
            return (await c.fetchone())[0]


# ─── Cooldowns ────────────────────────────────────────────────────────────────

async def get_last_broadcast(ws_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT last_broadcast_at FROM cooldowns WHERE workspace_id=?", (ws_id,)) as c:
            r = await c.fetchone()
            return r[0] if r else None


async def update_cooldown(ws_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        await db.execute(
            "INSERT INTO cooldowns(workspace_id,last_broadcast_at) VALUES(?,?) "
            "ON CONFLICT(workspace_id) DO UPDATE SET last_broadcast_at=?",
            (ws_id, now, now))
        await db.commit()


# ─── Blackout Hours ───────────────────────────────────────────────────────────

async def set_blackout_hours(ws_id: int, start: int, end: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO blackout_hours(workspace_id,start_hour,end_hour) VALUES(?,?,?) "
            "ON CONFLICT(workspace_id) DO UPDATE SET start_hour=?,end_hour=?",
            (ws_id, start, end, start, end))
        await db.commit()


async def get_blackout_hours(ws_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM blackout_hours WHERE workspace_id=?", (ws_id,)) as c:
            return _row(await c.fetchone())


async def clear_blackout_hours(ws_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM blackout_hours WHERE workspace_id=?", (ws_id,))
        await db.commit()


# ─── Workspace Settings ───────────────────────────────────────────────────────

_DEFAULT_SETTINGS = {
    "workspace_id": None, "header_text": None, "footer_text": None,
    "show_sender_info": 0, "approval_required": 0, "auto_pin": 0,
    "inline_btn_text": None, "inline_btn_url": None,
    "log_enabled": 1, "auto_repeat_text": None, "auto_repeat_hours": None,
}


async def get_settings(ws_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM workspace_settings WHERE workspace_id=?", (ws_id,)) as c:
            r = await c.fetchone()
            if r:
                return dict(r)
            d = dict(_DEFAULT_SETTINGS)
            d["workspace_id"] = ws_id
            return d


async def upsert_settings(ws_id: int, **kwargs):
    s = await get_settings(ws_id)
    s.update(kwargs)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO workspace_settings(
                workspace_id,header_text,footer_text,show_sender_info,
                approval_required,auto_pin,inline_btn_text,inline_btn_url,
                log_enabled,auto_repeat_text,auto_repeat_hours)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(workspace_id) DO UPDATE SET
                header_text=excluded.header_text,
                footer_text=excluded.footer_text,
                show_sender_info=excluded.show_sender_info,
                approval_required=excluded.approval_required,
                auto_pin=excluded.auto_pin,
                inline_btn_text=excluded.inline_btn_text,
                inline_btn_url=excluded.inline_btn_url,
                log_enabled=excluded.log_enabled,
                auto_repeat_text=excluded.auto_repeat_text,
                auto_repeat_hours=excluded.auto_repeat_hours""",
            (ws_id, s.get("header_text"), s.get("footer_text"), s.get("show_sender_info", 0),
             s.get("approval_required", 0), s.get("auto_pin", 0),
             s.get("inline_btn_text"), s.get("inline_btn_url"),
             s.get("log_enabled", 1), s.get("auto_repeat_text"), s.get("auto_repeat_hours")))
        await db.commit()


# ─── Broadcasts Log ───────────────────────────────────────────────────────────

async def log_broadcast(ws_id: int, admin_id: int, message_text: str, final_message: str,
                        channels_count: int, selected_channels: list = None,
                        inline_btn_text: str = None, inline_btn_url: str = None,
                        was_pinned: bool = False, was_scheduled: bool = False) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO broadcasts(workspace_id,admin_id,message_text,final_message,
               selected_channels,inline_btn_text,inline_btn_url,was_pinned,was_scheduled,
               sent_at,channels_count)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (ws_id, admin_id, message_text, final_message,
             json.dumps(selected_channels) if selected_channels else None,
             inline_btn_text, inline_btn_url,
             1 if was_pinned else 0, 1 if was_scheduled else 0,
             datetime.now().isoformat(), channels_count))
        await db.commit()
        return cur.lastrowid


async def get_broadcast_stats(ws_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*),SUM(channels_count) FROM broadcasts WHERE workspace_id=?", (ws_id,)) as c:
            r = await c.fetchone()
            total, reaches = r[0] or 0, r[1] or 0
        async with db.execute(
            "SELECT sent_at FROM broadcasts WHERE workspace_id=? ORDER BY sent_at DESC LIMIT 1", (ws_id,)) as c:
            lr = await c.fetchone()
            last = lr[0] if lr else None
        async with db.execute(
            "SELECT COUNT(*) FROM broadcasts WHERE workspace_id=? AND sent_at>=date('now','-30 days')", (ws_id,)) as c:
            month = (await c.fetchone())[0] or 0
        async with db.execute(
            """SELECT b.sent_at, b.channels_count, b.message_text,
                      a.display_name, a.user_id
               FROM broadcasts b LEFT JOIN admins a ON a.user_id=b.admin_id AND a.workspace_id=b.workspace_id
               WHERE b.workspace_id=? ORDER BY b.sent_at DESC LIMIT 10""", (ws_id,)) as c:
            recent = [dict(zip([d[0] for d in c.description], r)) for r in await c.fetchall()]
    return {"total": total, "reaches": reaches, "last": last, "month": month, "recent": recent}


async def get_broadcast_log(ws_id: int, limit: int = 20) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT b.*, a.display_name, a.user_id as sender_id
               FROM broadcasts b LEFT JOIN admins a ON a.user_id=b.admin_id AND a.workspace_id=b.workspace_id
               WHERE b.workspace_id=? ORDER BY b.sent_at DESC LIMIT ?""", (ws_id, limit)) as c:
            return [dict(zip([d[0] for d in c.description], r)) for r in await c.fetchall()]


# ─── Scheduled Broadcasts ─────────────────────────────────────────────────────

async def create_scheduled(ws_id: int, admin_id: int, message_text: str, final_message: str,
                           scheduled_at: str, selected_channels: list = None,
                           inline_btn_text: str = None, inline_btn_url: str = None,
                           should_pin: bool = False) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO scheduled_broadcasts(workspace_id,admin_id,message_text,final_message,
               selected_channels,inline_btn_text,inline_btn_url,should_pin,scheduled_at,created_at,status)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (ws_id, admin_id, message_text, final_message,
             json.dumps(selected_channels) if selected_channels else None,
             inline_btn_text, inline_btn_url, 1 if should_pin else 0,
             scheduled_at, datetime.now().isoformat(), "pending"))
        await db.commit()
        return cur.lastrowid


async def get_pending_scheduled(ws_id: int = None) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.now().isoformat()
        if ws_id:
            async with db.execute(
                "SELECT * FROM scheduled_broadcasts WHERE workspace_id=? AND status='pending' ORDER BY scheduled_at",
                (ws_id,)) as c:
                return [dict(r) for r in await c.fetchall()]
        async with db.execute(
            "SELECT * FROM scheduled_broadcasts WHERE status='pending' AND scheduled_at<=? ORDER BY scheduled_at",
            (now,)) as c:
            return [dict(r) for r in await c.fetchall()]


async def mark_scheduled_sent(sched_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE scheduled_broadcasts SET status='sent' WHERE id=?", (sched_id,))
        await db.commit()


async def cancel_scheduled(sched_id: int, ws_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "UPDATE scheduled_broadcasts SET status='cancelled' WHERE id=? AND workspace_id=? AND status='pending'",
            (sched_id, ws_id))
        await db.commit()
        return cur.rowcount > 0


# ─── Named Templates ──────────────────────────────────────────────────────────

async def save_template(ws_id: int, name: str, content: str) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO named_templates(workspace_id,name,content,created_at) VALUES(?,?,?,?) "
                "ON CONFLICT(workspace_id,name) DO UPDATE SET content=?",
                (ws_id, name, content, datetime.now().isoformat(), content))
            await db.commit()
            return True
    except Exception:
        return False


async def get_templates(ws_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM named_templates WHERE workspace_id=? ORDER BY name", (ws_id,)) as c:
            return [dict(r) for r in await c.fetchall()]


async def get_template(ws_id: int, name: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM named_templates WHERE workspace_id=? AND name=?", (ws_id, name)) as c:
            return _row(await c.fetchone())


async def delete_template(ws_id: int, name: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM named_templates WHERE workspace_id=? AND name=?", (ws_id, name))
        await db.commit()
        return cur.rowcount > 0


# ─── Pending Approvals ────────────────────────────────────────────────────────

async def create_approval(ws_id: int, admin_id: int, message_text: str, final_message: str,
                          selected_channels: list = None, inline_btn_text: str = None,
                          inline_btn_url: str = None, should_pin: bool = False) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO pending_approvals(workspace_id,admin_id,message_text,final_message,
               selected_channels,inline_btn_text,inline_btn_url,should_pin,created_at,status)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (ws_id, admin_id, message_text, final_message,
             json.dumps(selected_channels) if selected_channels else None,
             inline_btn_text, inline_btn_url, 1 if should_pin else 0,
             datetime.now().isoformat(), "pending"))
        await db.commit()
        return cur.lastrowid


async def get_approval(approval_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM pending_approvals WHERE id=?", (approval_id,)) as c:
            return _row(await c.fetchone())


async def resolve_approval(approval_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE pending_approvals SET status=? WHERE id=?", (status, approval_id))
        await db.commit()


# ─── Payments ─────────────────────────────────────────────────────────────────

async def create_payment(ws_id: int, owner_id: int, method: str, plan: str,
                         period: str, order_id: str,
                         amount_usd: float = None, stars_amount: int = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO payments(workspace_id,owner_id,amount_usd,stars_amount,
               method,plan,period,order_id,status,created_at)
               VALUES(?,?,?,?,?,?,?,?,'pending',?)""",
            (ws_id, owner_id, amount_usd, stars_amount,
             method, plan, period, order_id, datetime.now().isoformat()))
        await db.commit()
        return cur.lastrowid


async def mark_payment_paid(order_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE payments SET status='paid',paid_at=? WHERE order_id=?",
            (datetime.now().isoformat(), order_id))
        await db.commit()


# ─── Lookup (dev tool) ────────────────────────────────────────────────────────

async def lookup_user(user_id: int) -> dict:
    """Return all workspaces owned + admin memberships for a user."""
    owned  = await get_workspace(user_id) or {}
    member = await get_workspaces_as_admin(user_id)
    return {"owned": owned, "member": member}


async def lookup_workspace_by_channel(channel_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT w.* FROM workspaces w JOIN channels c ON c.workspace_id=w.id WHERE c.channel_id=?",
            (str(channel_id),)) as c:
            return _row(await c.fetchone())
