#!/usr/bin/env python3
"""
Sobriety Day Counter - A tool to track and celebrate your sobriety journey
"""

import sys
from datetime import date, datetime
import sobriety_core as core

def display_counter(start_date):
    """Display the sobriety counter and daily quote"""
    today = date.today()
    delta = today - start_date
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
    # Use local quotes only for CLI to ensure instant response
    print(f'\n  "{core.get_random_quote(allow_network=False)}"')
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
        start_date = date.today()
        print(f"\n✓ Starting today: {start_date.isoformat()}")
    else:
        try:
            # Parse string to date
            start_date = date.fromisoformat(date_input)
            print(f"\n✓ Start date set to: {start_date.isoformat()}")
        except ValueError:
            print("\n✗ Invalid date format. Using today instead.")
            start_date = date.today()
    
    core.save_data(start_date)
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
    start_date = core.load_data()
    
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
