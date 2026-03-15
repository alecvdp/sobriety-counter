#!/usr/bin/env python3
"""
Sobriety Day Counter CLI — A terminal tool to track and celebrate your sobriety journey.
Supports multiple trackers via the shared SQLite database.
"""

from datetime import date

import sobriety_core as core
import sobriety_db as db
from themes import MOOD_EMOJIS


def display_counter(conn, tracker):
    """Display the sobriety counter and daily quote for a tracker."""
    start = date.fromisoformat(tracker['start_date'])
    days = core.calc_days(start)
    bd = core.calc_breakdown(days)

    print("\n" + "=" * 55)
    print(f"  🌟  {tracker['name']}  ({tracker['category']})  🌟".center(55))
    print("=" * 55)
    print(f"\n  Days Sober: {days}")
    print(f"  Weeks: {bd['weeks']}")
    print(f"  Months: {bd['months']}")

    if days >= 365:
        print(f"  Years: {bd['years']} (and {bd['year_remainder']} days)")

    # Next milestone
    nxt = db.get_next_milestone(days)
    if nxt:
        print(f"\n  Next milestone: {nxt[2]} {nxt[1]} ({nxt[0] - days} days to go)")

    # Achieved milestones
    achieved = db.get_achieved_milestones(conn, tracker['id'])
    ms_map = {d: (l, e) for d, l, e in db.MILESTONES}
    if achieved:
        badges = " ".join(ms_map[a['milestone_days']][1] for a in achieved if a['milestone_days'] in ms_map)
        print(f"  Badges: {badges}")

    print("\n" + "-" * 55)
    print(f'\n  "{core.get_random_quote(allow_network=False)}"')
    print("\n" + "-" * 55)

    # Check new milestones
    new_ms = db.check_new_milestones(conn, tracker['id'], days)
    for ms_days, label, emoji in new_ms:
        print(f"\n  🎉 MILESTONE REACHED: {emoji} {label} ({ms_days} days)! 🎉")

    print(f"\n  Keep going! 💪")
    print("=" * 55 + "\n")


def set_start_date(conn, name="My Sobriety", category="Alcohol"):
    """Create a new tracker with a start date."""
    print(f"\n🎉 Setting up tracker: {name}")
    print("\nWhen did your journey begin?")
    print("Enter date in YYYY-MM-DD format (or press Enter for today): ", end="")

    date_input = input().strip()

    if not date_input:
        start_date = date.today()
        print(f"\n✓ Starting today: {start_date.isoformat()}")
    else:
        try:
            start_date = date.fromisoformat(date_input)
            print(f"\n✓ Start date set to: {start_date.isoformat()}")
        except ValueError:
            print("\n✗ Invalid date format. Using today instead.")
            start_date = date.today()

    tid = db.add_tracker(conn, name, category, start_date)
    return db.get_tracker(conn, tid)


def select_tracker(conn, trackers):
    """Let user select from existing trackers."""
    print("\n  Your Trackers:")
    for i, tr in enumerate(trackers, 1):
        start = date.fromisoformat(tr['start_date'])
        days = core.calc_days(start)
        print(f"  {i}. {tr['name']} ({tr['category']}) — {days} days")
    print(f"  {len(trackers) + 1}. Add new tracker")
    print()

    while True:
        print("Select tracker: ", end="")
        choice = input().strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(trackers):
                return trackers[idx - 1]
            elif idx == len(trackers) + 1:
                return None  # signal to add new
        except ValueError:
            pass
        print("  Invalid choice, try again.")


def add_journal_entry_cli(conn, tracker):
    """Add a journal entry from the CLI."""
    print(f"\n📓 Journal Entry for {date.today().isoformat()}")
    print("Mood (1=😞 2=😐 3=🙂 4=😊 5=😄): ", end="")
    try:
        mood = int(input().strip())
        if mood < 1 or mood > 5:
            mood = 3
    except ValueError:
        mood = 3

    print("How are you feeling? (Enter to finish):")
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)

    content = "\n".join(lines).strip()
    if content:
        db.add_journal_entry(conn, tracker['id'], date.today(), mood, content)
        print(f"\n✓ Journal entry saved! {MOOD_EMOJIS.get(mood, '')}")
    else:
        print("\n✗ Empty entry, not saved.")


def main():
    """Main function."""
    core.init()
    conn = db.get_connection()

    trackers = db.get_trackers(conn)

    if not trackers:
        tracker = set_start_date(conn)
    elif len(trackers) == 1:
        tracker = trackers[0]
    else:
        tracker = select_tracker(conn, trackers)
        if tracker is None:
            # Add new tracker
            print("Tracker name: ", end="")
            name = input().strip() or "My Tracker"
            print("Category (Alcohol/Smoking/Substances/Gambling/Sugar/Social Media/Custom): ", end="")
            cat = input().strip() or "Custom"
            tracker = set_start_date(conn, name, cat)

    while True:
        display_counter(conn, tracker)

        print("Options: [Enter] refresh | [r] reset | [j] journal | [s] switch tracker | [q] quit")
        choice = input("Your choice: ").strip().lower()

        if choice == 'q':
            print("\n💚 Keep up the great work! See you next time.\n")
            break
        elif choice == 'r':
            print("\nAre you sure you want to reset? (yes/no): ", end="")
            if input().strip().lower() in ('yes', 'y'):
                print("New start date (YYYY-MM-DD, Enter for today): ", end="")
                ds = input().strip()
                new_date = date.today()
                if ds:
                    try:
                        new_date = date.fromisoformat(ds)
                    except ValueError:
                        print("Invalid date, using today.")
                db.update_tracker(conn, tracker['id'], start_date=new_date)
                conn.execute("DELETE FROM milestones_achieved WHERE tracker_id = ?", (tracker['id'],))
                conn.commit()
                tracker = db.get_tracker(conn, tracker['id'])
        elif choice == 'j':
            add_journal_entry_cli(conn, tracker)
        elif choice == 's':
            trackers = db.get_trackers(conn)
            selected = select_tracker(conn, trackers)
            if selected is None:
                print("Tracker name: ", end="")
                name = input().strip() or "My Tracker"
                print("Category: ", end="")
                cat = input().strip() or "Custom"
                selected = set_start_date(conn, name, cat)
            tracker = selected

    conn.close()


if __name__ == "__main__":
    main()
