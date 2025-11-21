#!/usr/bin/env python3
"""
Sobriety Day Counter GUI - A graphical tool to track and celebrate your sobriety journey
"""

import sys
import threading
from datetime import date, datetime
import sobriety_core as core

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("Error: tkinter not available. Installing python-tk package...")
    sys.exit(1)


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
        
        self.start_date = core.load_data()
        
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
        date_entry.insert(0, date.today().isoformat())
        
        def submit():
            date_str = date_entry.get().strip()
            try:
                self.start_date = date.fromisoformat(date_str)
                core.save_data(self.start_date)
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
            text="Loading quote...",
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
        
        today = date.today()
        delta = today - self.start_date
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
        
        # Update quote in background thread
        self.fetch_quote_async()
        
    def fetch_quote_async(self):
        """Fetch quote in a background thread to prevent UI freezing"""
        self.refresh_btn.config(state='disabled', text="Loading...")
        
        def fetch():
            quote = core.get_random_quote(allow_network=True)
            # Schedule UI update on main thread
            self.root.after(0, lambda: self.finish_quote_update(quote))
            
        threading.Thread(target=fetch, daemon=True).start()
        
    def finish_quote_update(self, quote):
        """Update UI with fetched quote"""
        self.quote_label.config(text=f'"{quote}"')
        self.refresh_btn.config(state='normal', text="↻  Refresh")
    
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
