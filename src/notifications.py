"""
Desktop notification system for Sobriety Counter.
Uses plyer for cross-platform notifications.
Runs a background scheduler for daily reminders.
"""
import threading
from datetime import datetime, timedelta

try:
    from plyer import notification as plyer_notify
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False


def notify(title, message, timeout=10):
    """Send a desktop notification. Fails silently if plyer unavailable."""
    if not HAS_PLYER:
        return
    try:
        plyer_notify.notify(
            title=title,
            message=message,
            app_name="Sobriety Counter",
            timeout=timeout,
        )
    except Exception:
        pass


def notify_milestone(label, emoji, days):
    """Send a milestone celebration notification."""
    notify(
        f"{emoji} Milestone Reached!",
        f"Congratulations! You've reached {days} days — {label}!",
        timeout=15,
    )


def notify_daily(tracker_name, days):
    """Send a daily motivational notification."""
    notify(
        f"Day {days} — {tracker_name}",
        f"You've been going strong for {days} days. Keep it up!",
    )


class ReminderScheduler:
    """Background scheduler that fires daily notifications at a configured time."""

    def __init__(self, get_stats_fn, hour=9, minute=0):
        """
        get_stats_fn: callable returning list of (tracker_name, days_sober) tuples
        hour/minute: time of day to send the reminder (24h format)
        """
        self._get_stats = get_stats_fn
        self.hour = hour
        self.minute = minute
        self._timer = None
        self._running = False

    def start(self):
        self._running = True
        self._schedule_next()

    def stop(self):
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def update_time(self, hour, minute):
        self.hour = hour
        self.minute = minute
        if self._running:
            self.stop()
            self.start()

    def _schedule_next(self):
        if not self._running:
            return
        now = datetime.now()
        target = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        delay = (target - now).total_seconds()
        self._timer = threading.Timer(delay, self._fire)
        self._timer.daemon = True
        self._timer.start()

    def _fire(self):
        if not self._running:
            return
        try:
            stats = self._get_stats()
            for name, days in stats:
                notify_daily(name, days)
        except Exception:
            pass
        self._schedule_next()
