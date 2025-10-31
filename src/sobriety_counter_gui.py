#!/usr/bin/env python3
"""
Sobriety Day Counter GUI - A graphical tool to track and celebrate your sobriety journey
"""

import json
import sys
import random
from datetime import datetime
from pathlib import Path
from urllib import request
from urllib.error import URLError

try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
except ImportError:
    print("Error: tkinter not available. Installing python-tk package...")
    sys.exit(1)

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

DATA_FILE = Path.home() / ".sobriety_counter.json"


def get_random_quote():
    """Get a random motivational quote from an API or fallback to local quotes"""
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
                
                # Filter for relevant themes: recovery, strength, perseverance, change, growth
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
                
                # Check if quote contains relevant keywords or is about general wisdom/life
                has_relevant_theme = any(keyword in quote_lower for keyword in relevant_keywords)
                
                # Avoid quotes that are too specific to other topics (business, money, etc)
                avoid_keywords = ['money', 'business', 'profit', 'market', 'sell', 'buy', 'price']
                has_irrelevant_theme = any(keyword in quote_lower for keyword in avoid_keywords)
                
                if has_relevant_theme and not has_irrelevant_theme:
                    return f"{quote}\n— {author}"
                else:
                    # If quote doesn't match criteria, fallback to local quotes
                    raise ValueError("Quote not relevant")
                    
    except (URLError, Exception):
        pass
    
    # Fallback to local quotes
    return random.choice(QUOTES)


def load_data():
    """Load sobriety start date from file"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return datetime.fromisoformat(data['start_date'])
    return None


def save_data(start_date):
    """Save sobriety start date to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump({'start_date': start_date.isoformat()}, f)


class SobrietyCounterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sobriety Counter")
        self.root.geometry("600x700")
        self.root.configure(bg='#0f0f23')
        self.root.resizable(True, True)
        
        # Try to set window to stay on top initially
        self.root.attributes('-topmost', True)
        self.root.after(1000, lambda: self.root.attributes('-topmost', False))
        
        self.start_date = load_data()
        
        if self.start_date is None:
            self.root.after(100, self.setup_start_date)
        
        self.create_widgets()
        self.update_display()
    
    def setup_start_date(self):
        """Prompt user for start date"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Setup")
        dialog.geometry("480x240")
        dialog.configure(bg='#1a1a2e')
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        tk.Label(
            dialog,
            text="🎉 Welcome!",
            font=('SF Pro Display', 18, 'bold'),
            bg='#1a1a2e',
            fg='#ffffff'
        ).pack(pady=25)
        
        tk.Label(
            dialog,
            text="When did your sobriety journey begin?",
            font=('SF Pro Text', 12),
            bg='#1a1a2e',
            fg='#a0a0a0'
        ).pack(pady=10)
        
        frame = tk.Frame(dialog, bg='#1a1a2e')
        frame.pack(pady=15)
        
        tk.Label(frame, text="Date (YYYY-MM-DD):", bg='#1a1a2e', fg='#a0a0a0', font=('SF Pro Text', 11)).pack(side=tk.LEFT, padx=5)
        date_entry = tk.Entry(frame, width=15, font=('SF Mono', 12), bg='#2a2a40', fg='#ffffff', 
                             insertbackground='#ffffff', relief='flat', bd=5)
        date_entry.pack(side=tk.LEFT, padx=5)
        date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        def submit():
            date_str = date_entry.get().strip()
            try:
                self.start_date = datetime.strptime(date_str, '%Y-%m-%d')
                save_data(self.start_date)
                dialog.destroy()
                self.update_display()
            except ValueError:
                messagebox.showerror("Invalid Date", "Please enter date in YYYY-MM-DD format")
        
        submit_btn = tk.Button(
            dialog,
            text="Start Journey",
            command=submit,
            bg='#5B86E5',
            fg='white',
            font=('SF Pro Text', 12, 'bold'),
            width=18,
            cursor='hand2',
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            activebackground='#4a75d4',
            activeforeground='white'
        )
        submit_btn.pack(pady=25)
        
        date_entry.focus()
        date_entry.bind('<Return>', lambda e: submit())
    
    def create_widgets(self):
        """Create the GUI widgets"""
        # Header with gradient-like effect
        header_frame = tk.Frame(self.root, bg='#0f0f23')
        header_frame.pack(fill=tk.X, pady=(25, 15))
        
        tk.Label(
            header_frame,
            text="SOBRIETY",
            font=('SF Pro Display', 24, 'bold'),
            bg='#0f0f23',
            fg='#ffffff'
        ).pack()
        
        tk.Label(
            header_frame,
            text="COUNTER",
            font=('SF Pro Display', 24, 'bold'),
            bg='#0f0f23',
            fg='#5B86E5'
        ).pack()
        
        # Main counter card with modern gradient-style background
        card_frame = tk.Frame(self.root, bg='#0f0f23')
        card_frame.pack(pady=10, padx=50, fill=tk.BOTH)
        
        # Inner card with border effect
        self.counter_frame = tk.Frame(card_frame, bg='#1a1a2e', padx=30, pady=25, 
                                      highlightbackground='#2a2a40', highlightthickness=1)
        self.counter_frame.pack(fill=tk.BOTH, expand=False)
        
        self.days_label = tk.Label(
            self.counter_frame,
            text="",
            font=('SF Pro Display', 48, 'bold'),
            bg='#1a1a2e',
            fg='#5B86E5'
        )
        self.days_label.pack(pady=(5, 10))
        
        # Divider line
        divider = tk.Frame(self.counter_frame, height=1, bg='#2a2a40')
        divider.pack(fill=tk.X, pady=10)
        
        self.breakdown_label = tk.Label(
            self.counter_frame,
            text="",
            font=('SF Pro Text', 13),
            bg='#1a1a2e',
            fg='#a0a0a0',
            justify=tk.CENTER
        )
        self.breakdown_label.pack(pady=10)
        
        # Quote section with accent
        quote_container = tk.Frame(self.root, bg='#0f0f23')
        quote_container.pack(pady=15, padx=50, fill=tk.BOTH)
        
        quote_card = tk.Frame(quote_container, bg='#16213e', padx=25, pady=20)
        quote_card.pack(fill=tk.BOTH, expand=False)
        
        self.quote_label = tk.Label(
            quote_card,
            text="",
            font=('SF Pro Text', 14, 'italic'),
            bg='#16213e',
            fg='#36D1DC',
            wraplength=450,
            justify=tk.CENTER
        )
        self.quote_label.pack()
        
        # Emoji encouragement
        self.encourage_label = tk.Label(
            self.root,
            text="💪",
            font=('SF Pro Display', 24),
            bg='#0f0f23'
        )
        self.encourage_label.pack(pady=(15, 15))
        
        # Modern buttons with hover effect
        button_frame = tk.Frame(self.root, bg='#0f0f23')
        button_frame.pack(pady=(0, 30))
        
        self.refresh_btn = tk.Button(
            button_frame,
            text="↻  Refresh",
            command=self.update_display,
            bg='#5B86E5',
            fg='#000000',
            font=('SF Pro Text', 11, 'bold'),
            width=12,
            cursor='hand2',
            relief='raised',
            bd=2,
            padx=15,
            pady=8,
            activebackground='#4a75d4',
            activeforeground='#000000',
            highlightthickness=0
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=8)
        
        self.reset_btn = tk.Button(
            button_frame,
            text="⟲  Reset",
            command=self.reset_counter,
            bg='#E67E22',
            fg='#000000',
            font=('SF Pro Text', 11, 'bold'),
            width=12,
            cursor='hand2',
            relief='raised',
            bd=2,
            padx=15,
            pady=8,
            activebackground='#d56d11',
            activeforeground='#000000',
            highlightthickness=0
        )
        self.reset_btn.pack(side=tk.LEFT, padx=8)
    
    def update_display(self):
        """Update the counter display"""
        if self.start_date is None:
            return
        
        now = datetime.now()
        delta = now - self.start_date
        days = delta.days
        
        # Update days with better formatting
        if days == 1:
            self.days_label.config(text=f"{days} Day")
        else:
            self.days_label.config(text=f"{days} Days")
        
        # Update breakdown
        weeks = days // 7
        months = days // 30
        month_remainder = days % 30
        
        if months == 0:
            breakdown = f"{weeks} weeks"
        elif months == 1:
            breakdown = f"{weeks} weeks  •  {months} month and {month_remainder} days"
        else:
            breakdown = f"{weeks} weeks  •  {months} months and {month_remainder} days"
        
        if days >= 365:
            years = days // 365
            remaining_days = days % 365
            breakdown += f"\n{years} year{'s' if years > 1 else ''} and {remaining_days} days"
        
        self.breakdown_label.config(text=breakdown)
        
        # Update quote - always get a fresh random quote
        quote = get_random_quote()
        self.quote_label.config(text=f'"{quote}"')
    
    def reset_counter(self):
        """Reset the counter"""
        result = messagebox.askyesno(
            "Reset Counter",
            "Are you sure you want to reset your counter?\n\nThis will allow you to set a new start date."
        )
        
        if result:
            self.start_date = None
            self.setup_start_date()


def main():
    root = tk.Tk()
    app = SobrietyCounterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
