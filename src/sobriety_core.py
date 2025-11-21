"""
Core logic for Sobriety Counter applications (CLI and GUI).
"""
import json
import random
from datetime import date, datetime
from pathlib import Path
from urllib import request
from urllib.error import URLError

# Constants
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

def load_data():
    """
    Load sobriety start date from file.
    Returns a date object (YYYY-MM-DD) or None.
    Handles backward compatibility with datetime strings.
    """
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                date_str = data.get('start_date')
                if not date_str:
                    return None
                
                # Handle both date and datetime strings
                try:
                    return date.fromisoformat(date_str)
                except ValueError:
                    # Try parsing as datetime and converting to date
                    return datetime.fromisoformat(date_str).date()
        except (json.JSONDecodeError, ValueError):
            # If file is corrupted, return None (effectively reset)
            return None
    return None

def save_data(start_date):
    """
    Save sobriety start date to file.
    Accepts date or datetime object.
    """
    # Ensure we are saving a date object (stripping time if present)
    if isinstance(start_date, datetime):
        start_date = start_date.date()
        
    with open(DATA_FILE, 'w') as f:
        json.dump({'start_date': start_date.isoformat()}, f)

def get_random_quote(allow_network=True):
    """
    Get a random motivational quote.
    If allow_network is True, tries to fetch from ZenQuotes API.
    Falls back to local QUOTES list on failure.
    """
    if allow_network:
        try:
            # Try to get a quote from ZenQuotes API (free, no key required)
            req = request.Request(
                'https://zenquotes.io/api/random',
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                if data and len(data) > 0:
                    quote = data[0]['q']
                    author = data[0]['a']
                    
                    # Keep quotes reasonably short
                    if len(quote) > 150:
                        raise ValueError("Quote too long")
                    
                    # Filter for relevant themes
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
                    
                    # Check if quote contains relevant keywords
                    has_relevant_theme = any(keyword in quote_lower for keyword in relevant_keywords)
                    
                    # Avoid quotes that are too specific to other topics
                    avoid_keywords = ['money', 'business', 'profit', 'market', 'sell', 'buy', 'price']
                    has_irrelevant_theme = any(keyword in quote_lower for keyword in avoid_keywords)
                    
                    if has_relevant_theme and not has_irrelevant_theme:
                        return f"{quote}\n— {author}"
        except (URLError, Exception):
            pass
    
    # Fallback to local quotes
    return random.choice(QUOTES)
