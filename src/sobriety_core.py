"""
Core logic for Sobriety Counter applications (CLI and GUI).
Acts as a facade over the SQLite database layer while maintaining
backward-compatible helper functions.
"""
import json
import random
from datetime import date, datetime
from pathlib import Path
from urllib import request
from urllib.error import URLError

import sobriety_db as db

# Legacy data file (used for migration only)
DATA_FILE = Path.home() / ".sobriety_counter.json"

QUOTES = [
    "One day at a time.\n— Anonymous",
    "Progress, not perfection.\n— Anonymous",
    "You are stronger than you think.\n— A.A. Milne",
    "Every day sober is a victory.\n— Anonymous",
    "Recovery is worth it. You are worth it.\n— Anonymous",
    "Fall seven times, stand up eight.\n— Japanese Proverb",
    "The only way out is through.\n— Robert Frost",
    "You didn't come this far to only come this far.\n— Anonymous",
    "Courage doesn't mean you're not afraid.\nIt means you go anyway.\n— Anonymous",
    "Small steps every day lead to big changes.\n— Anonymous",
    "Be proud of how hard you're trying.\n— Anonymous",
    "Your future is created by what you do today,\nnot tomorrow.\n— Anonymous",
    "Healing is not linear,\nbut you're moving forward.\n— Anonymous",
    "You are doing something incredibly brave.\n— Anonymous",
    "The best view comes after the hardest climb.\n— Anonymous",
    "Rock bottom became the solid foundation\non which I rebuilt my life.\n— J.K. Rowling",
    "Sobriety was the greatest gift I ever gave myself.\n— Rob Lowe",
    "The opposite of addiction is connection.\n— Johann Hari",
    "You are worthy of a beautiful life.\n— Anonymous",
    "Recovery is an acceptance that your life is in shambles\nand you have to change.\n— Jamie Lee Curtis",
    "She stood in the storm, and when the wind\ndid not blow her away, she adjusted her sails.\n— Elizabeth Edwards",
    "What lies behind us and what lies before us\nare tiny matters compared to what lies within us.\n— Ralph Waldo Emerson",
    "You don't have to see the whole staircase,\njust take the first step.\n— Martin Luther King Jr.",
    "The greatest glory in living lies not in never falling,\nbut in rising every time we fall.\n— Nelson Mandela",
    "It does not matter how slowly you go\nas long as you do not stop.\n— Confucius",
]


def init():
    """Initialize the database and run any migrations."""
    db.migrate_from_json()


def get_connection():
    """Get a database connection."""
    return db.get_connection()


# --- Backward-compatible helpers (operate on first tracker) ---

def load_data():
    """
    Load sobriety start date from the database.
    Returns a date object or None.
    For backward compatibility, returns the first active tracker's start date.
    """
    conn = db.get_connection()
    trackers = db.get_trackers(conn)
    conn.close()
    if trackers:
        return date.fromisoformat(trackers[0]['start_date'])
    return None


def save_data(start_date):
    """
    Save sobriety start date.
    For backward compatibility, creates or updates the first tracker.
    """
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    conn = db.get_connection()
    trackers = db.get_trackers(conn)
    if trackers:
        db.update_tracker(conn, trackers[0]['id'], start_date=start_date)
    else:
        db.add_tracker(conn, "My Sobriety", "Alcohol", start_date)
    conn.close()


# --- Quote fetching ---

def get_random_quote(allow_network=True):
    """
    Get a random motivational quote.
    If allow_network is True, tries to fetch from ZenQuotes API.
    Falls back to local QUOTES list on failure.
    """
    if allow_network:
        try:
            req = request.Request(
                'https://zenquotes.io/api/random',
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                if data and len(data) > 0:
                    quote = data[0]['q']
                    author = data[0]['a']

                    if len(quote) > 150:
                        raise ValueError("Quote too long")

                    relevant_keywords = [
                        'strength', 'strong', 'courage', 'brave', 'persist', 'persever',
                        'change', 'grow', 'progress', 'journey', 'overcome', 'triumph',
                        'difficult', 'hard', 'struggle', 'challenge', 'endure', 'fight',
                        'step', 'forward', 'better', 'improve', 'heal', 'recovery',
                        'today', 'tomorrow', 'future', 'hope', 'believe', 'faith',
                        'fall', 'rise', 'fail', 'success', 'try', 'effort',
                        'mind', 'will', 'power', 'control', 'choice', 'decide',
                        'worth', 'deserve', 'value', 'life', 'live', 'light', 'dark'
                    ]

                    quote_lower = quote.lower()
                    has_relevant_theme = any(kw in quote_lower for kw in relevant_keywords)

                    avoid_keywords = ['money', 'business', 'profit', 'market', 'sell', 'buy', 'price']
                    has_irrelevant_theme = any(kw in quote_lower for kw in avoid_keywords)

                    if has_relevant_theme and not has_irrelevant_theme:
                        return f"{quote}\n— {author}"
        except (URLError, Exception):
            pass

    return random.choice(QUOTES)


# --- Calculation helpers ---

def calc_days(start_date):
    """Calculate days since start_date."""
    return (date.today() - start_date).days


def calc_breakdown(days):
    """Return a dict with weeks, months, month_remainder, years, year_remainder."""
    return {
        'weeks': days // 7,
        'months': days // 30,
        'month_remainder': days % 30,
        'years': days // 365,
        'year_remainder': days % 365,
    }
