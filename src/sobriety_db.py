"""
SQLite database layer for Sobriety Counter.
Handles all persistent storage: trackers, journal entries, milestones, and settings.
"""
import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

DB_FILE = Path.home() / ".sobriety_counter.db"
LEGACY_JSON = Path.home() / ".sobriety_counter.json"

# Milestone definitions: (days, label, emoji)
MILESTONES = [
    (1, "First Day", "🌅"),
    (3, "3 Days Strong", "💪"),
    (7, "One Week", "⭐"),
    (14, "Two Weeks", "🌟"),
    (30, "One Month", "🏅"),
    (60, "Two Months", "🎖️"),
    (90, "Three Months", "🏆"),
    (100, "100 Days!", "💯"),
    (180, "Six Months", "🔥"),
    (365, "One Year!", "👑"),
    (500, "500 Days!", "💎"),
    (730, "Two Years!", "🌈"),
    (1000, "1000 Days!", "🚀"),
    (1825, "Five Years!", "🎇"),
]


def get_connection():
    """Get a database connection, creating tables if needed."""
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _create_tables(conn)
    return conn


def _create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS trackers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Custom',
            start_date TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracker_id INTEGER NOT NULL,
            entry_date TEXT NOT NULL,
            mood INTEGER CHECK(mood BETWEEN 1 AND 5),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (tracker_id) REFERENCES trackers(id) ON DELETE CASCADE,
            UNIQUE(tracker_id, entry_date)
        );

        CREATE TABLE IF NOT EXISTS milestones_achieved (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracker_id INTEGER NOT NULL,
            milestone_days INTEGER NOT NULL,
            achieved_date TEXT NOT NULL,
            FOREIGN KEY (tracker_id) REFERENCES trackers(id) ON DELETE CASCADE,
            UNIQUE(tracker_id, milestone_days)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()


def migrate_from_json():
    """Import data from legacy JSON file if it exists and DB is empty."""
    if not LEGACY_JSON.exists():
        return
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM trackers").fetchone()[0]
    if count > 0:
        conn.close()
        return
    try:
        with open(LEGACY_JSON, 'r') as f:
            data = json.load(f)
            date_str = data.get('start_date')
            if date_str:
                # Normalize datetime strings to date
                try:
                    d = date.fromisoformat(date_str)
                except ValueError:
                    d = datetime.fromisoformat(date_str).date()
                add_tracker(conn, "My Sobriety", "Alcohol", d)
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    conn.close()


# --- Tracker CRUD ---

def add_tracker(conn, name, category, start_date):
    """Add a new tracker. Returns the new tracker id."""
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    cur = conn.execute(
        "INSERT INTO trackers (name, category, start_date) VALUES (?, ?, ?)",
        (name, category, start_date.isoformat())
    )
    conn.commit()
    return cur.lastrowid


def get_trackers(conn, active_only=True):
    """Get all trackers as a list of dicts."""
    sql = "SELECT * FROM trackers"
    if active_only:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY created_at"
    rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


def get_tracker(conn, tracker_id):
    """Get a single tracker by id."""
    row = conn.execute("SELECT * FROM trackers WHERE id = ?", (tracker_id,)).fetchone()
    return dict(row) if row else None


def update_tracker(conn, tracker_id, name=None, category=None, start_date=None):
    """Update tracker fields."""
    fields, values = [], []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if category is not None:
        fields.append("category = ?")
        values.append(category)
    if start_date is not None:
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        fields.append("start_date = ?")
        values.append(start_date.isoformat())
    if not fields:
        return
    values.append(tracker_id)
    conn.execute(f"UPDATE trackers SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()


def delete_tracker(conn, tracker_id):
    """Delete a tracker and its associated data."""
    conn.execute("DELETE FROM trackers WHERE id = ?", (tracker_id,))
    conn.commit()


# --- Journal ---

def add_journal_entry(conn, tracker_id, entry_date, mood, content):
    """Add or update a journal entry for a given date."""
    if isinstance(entry_date, (date, datetime)):
        entry_date = entry_date.isoformat()
    conn.execute(
        """INSERT INTO journal_entries (tracker_id, entry_date, mood, content)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(tracker_id, entry_date)
           DO UPDATE SET mood=excluded.mood, content=excluded.content""",
        (tracker_id, entry_date, mood, content)
    )
    conn.commit()


def get_journal_entries(conn, tracker_id, limit=30, offset=0):
    """Get journal entries for a tracker, most recent first."""
    rows = conn.execute(
        """SELECT * FROM journal_entries WHERE tracker_id = ?
           ORDER BY entry_date DESC LIMIT ? OFFSET ?""",
        (tracker_id, limit, offset)
    ).fetchall()
    return [dict(r) for r in rows]


def get_journal_entry(conn, tracker_id, entry_date):
    """Get a single journal entry for a specific date."""
    if isinstance(entry_date, (date, datetime)):
        entry_date = entry_date.isoformat()
    row = conn.execute(
        "SELECT * FROM journal_entries WHERE tracker_id = ? AND entry_date = ?",
        (tracker_id, entry_date)
    ).fetchone()
    return dict(row) if row else None


# --- Milestones ---

def get_achieved_milestones(conn, tracker_id):
    """Get all achieved milestones for a tracker."""
    rows = conn.execute(
        "SELECT * FROM milestones_achieved WHERE tracker_id = ? ORDER BY milestone_days",
        (tracker_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def check_new_milestones(conn, tracker_id, days_sober):
    """Check if any new milestones have been reached. Returns list of newly achieved milestones."""
    achieved = {r['milestone_days'] for r in get_achieved_milestones(conn, tracker_id)}
    new_milestones = []
    for days, label, emoji in MILESTONES:
        if days <= days_sober and days not in achieved:
            conn.execute(
                "INSERT INTO milestones_achieved (tracker_id, milestone_days, achieved_date) VALUES (?, ?, ?)",
                (tracker_id, days, date.today().isoformat())
            )
            new_milestones.append((days, label, emoji))
    if new_milestones:
        conn.commit()
    return new_milestones


def get_next_milestone(days_sober):
    """Get the next milestone to reach."""
    for days, label, emoji in MILESTONES:
        if days > days_sober:
            return (days, label, emoji)
    return None


# --- Settings ---

def get_setting(conn, key, default=None):
    """Get a setting value."""
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row['value'] if row else default


def set_setting(conn, key, value):
    """Set a setting value."""
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value))
    )
    conn.commit()


def get_all_settings(conn):
    """Get all settings as a dict."""
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {r['key']: r['value'] for r in rows}
