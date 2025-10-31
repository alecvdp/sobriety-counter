#!/usr/bin/env python3
"""
Sobriety Day Counter - A tool to track and celebrate your sobriety journey
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

QUOTES = [
    "One day at a time.",
    "Progress, not perfection.",
    "You are stronger than you think.",
    "Every day sober is a victory.",
    "Recovery is worth it. You are worth it.",
    "Fall seven times, stand up eight.",
    "The only way out is through.",
    "You didn't come this far to only come this far.",
    "Courage doesn't mean you're not afraid. It means you go anyway.",
    "Small steps every day lead to big changes.",
    "Be proud of how hard you're trying.",
    "Your future is created by what you do today, not tomorrow.",
    "Healing is not linear, but you're moving forward.",
    "You are doing something incredibly brave.",
    "The best view comes after the hardest climb.",
]

DATA_FILE = Path.home() / ".sobriety_counter.json"


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


def get_daily_quote(days):
    """Get a consistent quote for the day based on days sober"""
    return QUOTES[days % len(QUOTES)]


def display_counter(start_date):
    """Display the sobriety counter and daily quote"""
    now = datetime.now()
    delta = now - start_date
    days = delta.days
    
    print("\n" + "=" * 50)
    print("🌟  SOBRIETY COUNTER  🌟".center(50))
    print("=" * 50)
    print(f"\n  Days Sober: {days}")
    print(f"  Weeks: {days // 7}")
    print(f"  Months: {days // 30}")
    
    if days >= 365:
        years = days // 365
        remaining_days = days % 365
        print(f"  Years: {years} (and {remaining_days} days)")
    
    print("\n" + "-" * 50)
    print(f'\n  "{get_daily_quote(days)}"')
    print("\n" + "-" * 50)
    print(f"\n  Keep going! 💪")
    print("=" * 50 + "\n")


def set_start_date():
    """Set the sobriety start date"""
    print("\n🎉 Setting up your sobriety counter!")
    print("\nWhen did your sobriety journey begin?")
    print("Enter date in YYYY-MM-DD format (or press Enter for today): ", end="")
    
    date_input = input().strip()
    
    if not date_input:
        start_date = datetime.now()
        print(f"\n✓ Starting today: {start_date.strftime('%Y-%m-%d')}")
    else:
        try:
            start_date = datetime.strptime(date_input, '%Y-%m-%d')
            print(f"\n✓ Start date set to: {start_date.strftime('%Y-%m-%d')}")
        except ValueError:
            print("\n✗ Invalid date format. Using today instead.")
            start_date = datetime.now()
    
    save_data(start_date)
    return start_date


def reset_counter():
    """Reset the counter"""
    print("\nAre you sure you want to reset your counter? (yes/no): ", end="")
    confirm = input().strip().lower()
    
    if confirm in ['yes', 'y']:
        start_date = set_start_date()
        return start_date
    else:
        print("\nCounter not reset.")
        return None


def main():
    """Main function"""
    start_date = load_data()
    
    if start_date is None:
        start_date = set_start_date()
    
    while True:
        display_counter(start_date)
        
        print("Options: [Enter] to refresh | [r] to reset | [q] to quit")
        choice = input("Your choice: ").strip().lower()
        
        if choice == 'q':
            print("\n💚 Keep up the great work! See you next time.\n")
            break
        elif choice == 'r':
            new_start = reset_counter()
            if new_start:
                start_date = new_start
        else:
            continue


if __name__ == "__main__":
    main()
