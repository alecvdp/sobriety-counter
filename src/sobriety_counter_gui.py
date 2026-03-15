#!/usr/bin/env python3
"""
Sobriety Day Counter GUI — A graphical tool to track and celebrate your sobriety journey.
Features: multiple trackers, milestones, journal, themes, animated counter,
system tray, and desktop notifications.
"""

import math
import random
import sys
import threading
from datetime import date, datetime

import sobriety_core as core
import sobriety_db as db
from themes import THEMES, DEFAULT_THEME, TRACKER_CATEGORIES, MOOD_EMOJIS
from notifications import notify_milestone, ReminderScheduler, HAS_PLYER
from tray import TrayManager, HAS_TRAY

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("Error: tkinter not available.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _font(family="SF Pro Text", size=12, weight="normal"):
    """Build a font tuple, falling back gracefully."""
    return (family, size, weight)


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class SobrietyCounterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sobriety Counter")
        self.root.geometry("780x720")
        self.root.minsize(680, 600)

        # Database
        core.init()
        self.conn = db.get_connection()

        # Theme
        theme_key = db.get_setting(self.conn, "theme", DEFAULT_THEME)
        self.theme = THEMES.get(theme_key, THEMES[DEFAULT_THEME])

        self.root.configure(bg=self.theme["bg"])

        # Active tracker
        self.trackers = db.get_trackers(self.conn)
        self.active_tracker = self.trackers[0] if self.trackers else None

        # Animation state
        self._anim_target = 0
        self._anim_current = 0.0
        self._anim_id = None

        # Try to set window on top briefly
        try:
            self.root.attributes('-topmost', True)
            self.root.after(1000, lambda: self.root.attributes('-topmost', False))
        except tk.TclError:
            pass

        # Build UI
        self._build_ui()

        # If no trackers, prompt setup
        if not self.active_tracker:
            self.root.after(100, self._setup_first_tracker)
        else:
            self._refresh_display()

        # Notification scheduler
        self._scheduler = None
        if db.get_setting(self.conn, "notifications", "1") == "1":
            self._start_scheduler()

        # System tray
        self._tray = None
        if HAS_TRAY and db.get_setting(self.conn, "tray", "1") == "1":
            self._start_tray()

        # Close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        t = self.theme

        # Main horizontal layout: sidebar + content
        self.main_frame = tk.Frame(self.root, bg=t["bg"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Sidebar ---
        self.sidebar = tk.Frame(self.main_frame, bg=t["sidebar_bg"], width=180)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="TRACKERS", font=_font("SF Pro Display", 11, "bold"),
                 bg=t["sidebar_bg"], fg=t["fg_dim"]).pack(pady=(15, 8), padx=12, anchor="w")

        self.tracker_list_frame = tk.Frame(self.sidebar, bg=t["sidebar_bg"])
        self.tracker_list_frame.pack(fill=tk.BOTH, expand=True, padx=8)

        self._rebuild_tracker_list()

        # Sidebar buttons
        btn_frame = tk.Frame(self.sidebar, bg=t["sidebar_bg"])
        btn_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        tk.Button(btn_frame, text="+ Add Tracker", command=self._add_tracker_dialog,
                  bg=t["accent"], fg=t["button_fg"], font=_font(size=10, weight="bold"),
                  relief="flat", cursor="hand2", pady=6,
                  activebackground=t["accent_hover"]).pack(fill=tk.X, pady=2)

        tk.Button(btn_frame, text="Settings", command=self._settings_dialog,
                  bg=t["card_bg"], fg=t["fg_dim"], font=_font(size=10),
                  relief="flat", cursor="hand2", pady=6,
                  activebackground=t["card_border"]).pack(fill=tk.X, pady=2)

        # --- Content Area ---
        self.content = tk.Frame(self.main_frame, bg=t["bg"])
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_content()

    def _build_content(self):
        """Build the main content area (counter, quote, journal, milestones)."""
        t = self.theme

        # Clear existing
        for w in self.content.winfo_children():
            w.destroy()

        # Scrollable content
        canvas = tk.Canvas(self.content, bg=t["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=t["bg"])

        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        inner = self.scroll_frame

        # --- Header ---
        header = tk.Frame(inner, bg=t["bg"])
        header.pack(fill=tk.X, pady=(20, 10), padx=30)

        self.header_name = tk.Label(header, text="", font=_font("SF Pro Display", 22, "bold"),
                                    bg=t["bg"], fg=t["fg"])
        self.header_name.pack(anchor="w")

        self.header_category = tk.Label(header, text="", font=_font(size=11),
                                        bg=t["bg"], fg=t["fg_dim"])
        self.header_category.pack(anchor="w")

        # --- Counter Card ---
        card_outer = tk.Frame(inner, bg=t["bg"])
        card_outer.pack(pady=10, padx=30, fill=tk.X)

        self.counter_card = tk.Frame(card_outer, bg=t["card_bg"], padx=30, pady=25,
                                     highlightbackground=t["card_border"], highlightthickness=1)
        self.counter_card.pack(fill=tk.X)

        self.days_label = tk.Label(self.counter_card, text="0 Days",
                                   font=_font("SF Pro Display", 48, "bold"),
                                   bg=t["card_bg"], fg=t["accent"])
        self.days_label.pack(pady=(5, 8))

        # Next milestone progress
        self.milestone_progress_label = tk.Label(self.counter_card, text="",
                                                  font=_font(size=10), bg=t["card_bg"], fg=t["fg_dim"])
        self.milestone_progress_label.pack(pady=(0, 8))

        # Progress bar canvas
        self.progress_canvas = tk.Canvas(self.counter_card, height=8, bg=t["card_bg"],
                                          highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Frame(self.counter_card, height=1, bg=t["divider"]).pack(fill=tk.X, pady=8)

        self.breakdown_label = tk.Label(self.counter_card, text="",
                                        font=_font(size=13), bg=t["card_bg"], fg=t["fg_dim"],
                                        justify=tk.CENTER)
        self.breakdown_label.pack(pady=8)

        # --- Milestones Badge Row ---
        self.badge_frame = tk.Frame(inner, bg=t["bg"])
        self.badge_frame.pack(fill=tk.X, padx=30, pady=(5, 5))

        # --- Quote Card ---
        quote_outer = tk.Frame(inner, bg=t["bg"])
        quote_outer.pack(pady=10, padx=30, fill=tk.X)

        quote_card = tk.Frame(quote_outer, bg=t["quote_bg"], padx=25, pady=18)
        quote_card.pack(fill=tk.X)

        self.quote_label = tk.Label(quote_card, text="Loading quote...",
                                    font=_font(size=13, weight="italic"),
                                    bg=t["quote_bg"], fg=t["accent2"],
                                    wraplength=420, justify=tk.CENTER)
        self.quote_label.pack()

        # --- Encouragement ---
        self.encourage_label = tk.Label(inner, text="💪",
                                        font=_font("SF Pro Display", 22),
                                        bg=t["bg"])
        self.encourage_label.pack(pady=(10, 5))

        # --- Action Buttons ---
        btn_row = tk.Frame(inner, bg=t["bg"])
        btn_row.pack(pady=(0, 8))

        tk.Button(btn_row, text="↻  Refresh", command=self._refresh_display,
                  bg=t["accent"], fg=t["button_fg"], font=_font(size=11, weight="bold"),
                  width=11, cursor="hand2", relief="flat", bd=0, padx=12, pady=7,
                  activebackground=t["accent_hover"]).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_row, text="📓  Journal", command=self._journal_dialog,
                  bg=t["accent2"], fg=t["button_fg"], font=_font(size=11, weight="bold"),
                  width=11, cursor="hand2", relief="flat", bd=0, padx=12, pady=7,
                  activebackground=t["accent_hover"]).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_row, text="⟲  Reset", command=self._reset_counter,
                  bg=t["warning"], fg=t["button_fg"], font=_font(size=11, weight="bold"),
                  width=11, cursor="hand2", relief="flat", bd=0, padx=12, pady=7,
                  activebackground=t["warning_hover"]).pack(side=tk.LEFT, padx=5)

        # --- Journal History ---
        journal_header = tk.Frame(inner, bg=t["bg"])
        journal_header.pack(fill=tk.X, padx=30, pady=(15, 5))
        tk.Label(journal_header, text="RECENT JOURNAL ENTRIES",
                 font=_font("SF Pro Display", 11, "bold"),
                 bg=t["bg"], fg=t["fg_dim"]).pack(anchor="w")

        self.journal_list_frame = tk.Frame(inner, bg=t["bg"])
        self.journal_list_frame.pack(fill=tk.X, padx=30, pady=(0, 20))

    # ------------------------------------------------------------------
    # Tracker Sidebar
    # ------------------------------------------------------------------

    def _rebuild_tracker_list(self):
        t = self.theme
        for w in self.tracker_list_frame.winfo_children():
            w.destroy()

        self.trackers = db.get_trackers(self.conn)
        for tr in self.trackers:
            is_active = self.active_tracker and tr['id'] == self.active_tracker['id']
            bg = t["sidebar_item_active"] if is_active else t["sidebar_item"]
            fg = t["accent"] if is_active else t["fg"]

            frame = tk.Frame(self.tracker_list_frame, bg=bg, cursor="hand2")
            frame.pack(fill=tk.X, pady=2)

            lbl = tk.Label(frame, text=tr['name'], font=_font(size=11, weight="bold" if is_active else "normal"),
                           bg=bg, fg=fg, anchor="w", padx=10, pady=8)
            lbl.pack(fill=tk.X)

            cat_lbl = tk.Label(frame, text=tr['category'], font=_font(size=9),
                               bg=bg, fg=t["fg_dim"], anchor="w", padx=10)
            cat_lbl.pack(fill=tk.X)

            # Bind click to all widgets in frame
            tracker_id = tr['id']
            for widget in (frame, lbl, cat_lbl):
                widget.bind("<Button-1>", lambda e, tid=tracker_id: self._switch_tracker(tid))

    def _switch_tracker(self, tracker_id):
        self.active_tracker = db.get_tracker(self.conn, tracker_id)
        self._rebuild_tracker_list()
        self._refresh_display()

    # ------------------------------------------------------------------
    # Display Update & Animation
    # ------------------------------------------------------------------

    def _refresh_display(self):
        if not self.active_tracker:
            return
        t = self.theme
        tr = self.active_tracker
        start = date.fromisoformat(tr['start_date'])
        days = core.calc_days(start)
        breakdown = core.calc_breakdown(days)

        # Header
        self.header_name.config(text=tr['name'])
        self.header_category.config(text=tr['category'])

        # Animated counter
        self._start_count_animation(days)

        # Breakdown text
        w, m, mr = breakdown['weeks'], breakdown['months'], breakdown['month_remainder']
        if m == 0:
            text = f"{w} weeks"
        elif m == 1:
            text = f"{w} weeks  •  {m} month and {mr} days"
        else:
            text = f"{w} weeks  •  {m} months and {mr} days"
        if days >= 365:
            y, yr = breakdown['years'], breakdown['year_remainder']
            text += f"\n{y} year{'s' if y > 1 else ''} and {yr} days"
        self.breakdown_label.config(text=text)

        # Next milestone progress bar
        nxt = db.get_next_milestone(days)
        if nxt:
            prev_days = 0
            for ms_days, _, _ in db.MILESTONES:
                if ms_days > days:
                    break
                prev_days = ms_days
            progress = (days - prev_days) / max(1, nxt[0] - prev_days)
            self.milestone_progress_label.config(
                text=f"Next: {nxt[2]} {nxt[1]} ({nxt[0] - days} days to go)")
            self._draw_progress_bar(progress)
        else:
            self.milestone_progress_label.config(text="All milestones achieved!")
            self._draw_progress_bar(1.0)

        # Check for new milestones
        new_ms = db.check_new_milestones(self.conn, tr['id'], days)
        for ms_days, label, emoji in new_ms:
            self._show_milestone_popup(label, emoji, ms_days)
            notify_milestone(label, emoji, ms_days)

        # Milestone badges
        self._draw_badges()

        # Quote (async)
        self._fetch_quote_async()

        # Journal entries
        self._draw_journal_entries()

    def _draw_progress_bar(self, progress):
        t = self.theme
        c = self.progress_canvas
        c.delete("all")
        c.update_idletasks()
        w = c.winfo_width() or 400
        h = 8
        # Background
        c.create_rectangle(0, 0, w, h, fill=t["card_border"], outline="")
        # Fill
        fill_w = int(w * min(1.0, progress))
        if fill_w > 0:
            c.create_rectangle(0, 0, fill_w, h, fill=t["accent"], outline="")

    def _draw_badges(self):
        t = self.theme
        for w in self.badge_frame.winfo_children():
            w.destroy()
        if not self.active_tracker:
            return
        achieved = db.get_achieved_milestones(self.conn, self.active_tracker['id'])
        if not achieved:
            return

        # Map milestone_days to emoji/label
        ms_map = {d: (l, e) for d, l, e in db.MILESTONES}

        row = tk.Frame(self.badge_frame, bg=t["bg"])
        row.pack(anchor="w")

        for a in achieved:
            md = a['milestone_days']
            if md in ms_map:
                label, emoji = ms_map[md]
                badge = tk.Label(row, text=f"{emoji}", font=_font(size=16),
                                 bg=t["card_bg"], padx=6, pady=3, cursor="hand2",
                                 highlightbackground=t["card_border"], highlightthickness=1)
                badge.pack(side=tk.LEFT, padx=2, pady=2)
                # Tooltip on hover
                badge.bind("<Enter>", lambda e, l=label, d=md: self._show_tooltip(e, f"{l} ({d} days)"))
                badge.bind("<Leave>", self._hide_tooltip)

    def _show_tooltip(self, event, text):
        t = self.theme
        self._tooltip = tk.Toplevel(self.root)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        lbl = tk.Label(self._tooltip, text=text, bg=t["card_bg"], fg=t["fg"],
                       font=_font(size=10), padx=8, pady=4,
                       highlightbackground=t["card_border"], highlightthickness=1)
        lbl.pack()

    def _hide_tooltip(self, event):
        if hasattr(self, '_tooltip') and self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None

    # --- Count Animation ---

    def _start_count_animation(self, target):
        if self._anim_id:
            self.root.after_cancel(self._anim_id)
        self._anim_target = target
        self._anim_current = 0.0
        self._animate_count()

    def _animate_count(self):
        diff = self._anim_target - self._anim_current
        if abs(diff) < 1:
            self._anim_current = self._anim_target
            self._update_days_label(self._anim_target)
            self._anim_id = None
            return
        # Ease-out
        step = diff * 0.12
        if abs(step) < 1:
            step = 1 if diff > 0 else -1
        self._anim_current += step
        self._update_days_label(int(self._anim_current))
        self._anim_id = self.root.after(16, self._animate_count)  # ~60fps

    def _update_days_label(self, count):
        suffix = "Day" if count == 1 else "Days"
        self.days_label.config(text=f"{count} {suffix}")

    # --- Milestone Celebration Popup ---

    def _show_milestone_popup(self, label, emoji, days):
        t = self.theme
        popup = tk.Toplevel(self.root)
        popup.title("Milestone!")
        popup.geometry("400x300")
        popup.configure(bg=t["card_bg"])
        popup.transient(self.root)
        popup.grab_set()
        popup.resizable(False, False)

        # Confetti canvas
        confetti = tk.Canvas(popup, width=400, height=300, bg=t["card_bg"], highlightthickness=0)
        confetti.pack(fill=tk.BOTH, expand=True)

        # Draw confetti particles
        colors = ["#ff6b6b", "#ffd93d", "#6bcf7f", "#4ecdc4", "#45b7d1", "#f7b267", "#e056a0"]
        particles = []
        for _ in range(60):
            x = random.randint(0, 400)
            y = random.randint(-300, 0)
            size = random.randint(4, 10)
            color = random.choice(colors)
            pid = confetti.create_oval(x, y, x + size, y + size, fill=color, outline="")
            particles.append((pid, random.uniform(1, 3), random.uniform(-1, 1)))

        # Overlay text
        confetti.create_text(200, 100, text=emoji, font=_font(size=48), fill=t["fg"])
        confetti.create_text(200, 170, text=label, font=_font("SF Pro Display", 20, "bold"), fill=t["fg"])
        confetti.create_text(200, 210, text=f"{days} days!", font=_font(size=16), fill=t["accent"])
        confetti.create_text(200, 250, text="Congratulations!", font=_font(size=14), fill=t["accent2"])

        # Animate confetti falling
        def animate_confetti():
            all_done = True
            for i, (pid, speed, drift) in enumerate(particles):
                confetti.move(pid, drift, speed)
                coords = confetti.coords(pid)
                if coords and coords[1] < 320:
                    all_done = False
            if not all_done:
                popup.after(30, animate_confetti)

        popup.after(50, animate_confetti)

        # Auto-close after 5 seconds
        popup.after(5000, popup.destroy)

    # --- Quote ---

    def _fetch_quote_async(self):
        def fetch():
            quote = core.get_random_quote(allow_network=True)
            self.root.after(0, lambda: self.quote_label.config(text=f'"{quote}"'))
        threading.Thread(target=fetch, daemon=True).start()

    # --- Journal ---

    def _journal_dialog(self):
        if not self.active_tracker:
            return
        t = self.theme
        dialog = tk.Toplevel(self.root)
        dialog.title("Journal Entry")
        dialog.geometry("450x380")
        dialog.configure(bg=t["card_bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(dialog, text="📓 Daily Journal", font=_font("SF Pro Display", 16, "bold"),
                 bg=t["card_bg"], fg=t["fg"]).pack(pady=(20, 10))

        tk.Label(dialog, text=f"Date: {date.today().isoformat()}", font=_font(size=11),
                 bg=t["card_bg"], fg=t["fg_dim"]).pack(pady=(0, 10))

        # Mood selector
        mood_frame = tk.Frame(dialog, bg=t["card_bg"])
        mood_frame.pack(pady=5)
        tk.Label(mood_frame, text="Mood:", font=_font(size=11),
                 bg=t["card_bg"], fg=t["fg_dim"]).pack(side=tk.LEFT, padx=(0, 10))

        mood_var = tk.IntVar(value=3)
        for val, emoji in MOOD_EMOJIS.items():
            rb = tk.Radiobutton(mood_frame, text=emoji, variable=mood_var, value=val,
                                font=_font(size=16), bg=t["card_bg"], fg=t["fg"],
                                selectcolor=t["card_border"], activebackground=t["card_bg"],
                                indicatoron=False, padx=8, pady=4, cursor="hand2",
                                highlightthickness=0, bd=1, relief="flat")
            rb.pack(side=tk.LEFT, padx=3)

        # Text entry
        tk.Label(dialog, text="How are you feeling today?", font=_font(size=11),
                 bg=t["card_bg"], fg=t["fg_dim"]).pack(pady=(10, 5))

        text_widget = tk.Text(dialog, width=45, height=6, font=_font("SF Mono", 11),
                              bg=t["input_bg"], fg=t["fg"], insertbackground=t["fg"],
                              relief="flat", bd=5, wrap=tk.WORD)
        text_widget.pack(padx=20, pady=5)

        # Pre-fill if entry exists for today
        existing = db.get_journal_entry(self.conn, self.active_tracker['id'], date.today())
        if existing:
            text_widget.insert("1.0", existing['content'])
            mood_var.set(existing['mood'])

        def save():
            content = text_widget.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("Empty Entry", "Please write something before saving.")
                return
            db.add_journal_entry(self.conn, self.active_tracker['id'],
                                 date.today(), mood_var.get(), content)
            dialog.destroy()
            self._draw_journal_entries()

        tk.Button(dialog, text="Save Entry", command=save,
                  bg=t["accent"], fg=t["button_fg"], font=_font(size=12, weight="bold"),
                  cursor="hand2", relief="flat", padx=20, pady=8,
                  activebackground=t["accent_hover"]).pack(pady=15)

        text_widget.focus()

    def _draw_journal_entries(self):
        t = self.theme
        for w in self.journal_list_frame.winfo_children():
            w.destroy()
        if not self.active_tracker:
            return

        entries = db.get_journal_entries(self.conn, self.active_tracker['id'], limit=5)
        if not entries:
            tk.Label(self.journal_list_frame, text="No journal entries yet. Click Journal to add one!",
                     font=_font(size=11), bg=t["bg"], fg=t["fg_dim"]).pack(anchor="w", pady=5)
            return

        for entry in entries:
            frame = tk.Frame(self.journal_list_frame, bg=t["card_bg"], padx=15, pady=10,
                             highlightbackground=t["card_border"], highlightthickness=1)
            frame.pack(fill=tk.X, pady=3)

            header = tk.Frame(frame, bg=t["card_bg"])
            header.pack(fill=tk.X)

            mood_emoji = MOOD_EMOJIS.get(entry['mood'], "")
            tk.Label(header, text=f"{mood_emoji}  {entry['entry_date']}",
                     font=_font(size=11, weight="bold"), bg=t["card_bg"], fg=t["fg"]).pack(side=tk.LEFT)

            # Truncate long entries
            content = entry['content']
            if len(content) > 120:
                content = content[:120] + "..."
            tk.Label(frame, text=content, font=_font(size=10), bg=t["card_bg"], fg=t["fg_dim"],
                     wraplength=450, justify=tk.LEFT, anchor="w").pack(fill=tk.X, pady=(5, 0))

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------

    def _setup_first_tracker(self):
        self._add_tracker_dialog(first_time=True)

    def _add_tracker_dialog(self, first_time=False):
        t = self.theme
        dialog = tk.Toplevel(self.root)
        dialog.title("Setup" if first_time else "Add Tracker")
        dialog.geometry("480x320")
        dialog.configure(bg=t["card_bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        title = "🎉 Welcome!" if first_time else "Add New Tracker"
        tk.Label(dialog, text=title, font=_font("SF Pro Display", 18, "bold"),
                 bg=t["card_bg"], fg=t["fg"]).pack(pady=(20, 10))

        # Name
        name_frame = tk.Frame(dialog, bg=t["card_bg"])
        name_frame.pack(fill=tk.X, padx=40, pady=5)
        tk.Label(name_frame, text="Name:", bg=t["card_bg"], fg=t["fg_dim"],
                 font=_font(size=11)).pack(side=tk.LEFT, padx=(0, 10))
        name_entry = tk.Entry(name_frame, width=25, font=_font("SF Mono", 12),
                              bg=t["input_bg"], fg=t["fg"], insertbackground=t["fg"],
                              relief="flat", bd=5)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        name_entry.insert(0, "My Sobriety")

        # Category
        cat_frame = tk.Frame(dialog, bg=t["card_bg"])
        cat_frame.pack(fill=tk.X, padx=40, pady=5)
        tk.Label(cat_frame, text="Category:", bg=t["card_bg"], fg=t["fg_dim"],
                 font=_font(size=11)).pack(side=tk.LEFT, padx=(0, 10))
        cat_var = tk.StringVar(value=TRACKER_CATEGORIES[0])
        cat_menu = tk.OptionMenu(cat_frame, cat_var, *TRACKER_CATEGORIES)
        cat_menu.config(bg=t["input_bg"], fg=t["fg"], font=_font(size=11),
                        activebackground=t["card_border"], highlightthickness=0, relief="flat")
        cat_menu.pack(side=tk.LEFT)

        # Date
        date_frame = tk.Frame(dialog, bg=t["card_bg"])
        date_frame.pack(fill=tk.X, padx=40, pady=5)
        tk.Label(date_frame, text="Start Date:", bg=t["card_bg"], fg=t["fg_dim"],
                 font=_font(size=11)).pack(side=tk.LEFT, padx=(0, 10))
        date_entry = tk.Entry(date_frame, width=15, font=_font("SF Mono", 12),
                              bg=t["input_bg"], fg=t["fg"], insertbackground=t["fg"],
                              relief="flat", bd=5)
        date_entry.pack(side=tk.LEFT)
        date_entry.insert(0, date.today().isoformat())

        def submit():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a name.")
                return
            try:
                start = date.fromisoformat(date_entry.get().strip())
            except ValueError:
                messagebox.showerror("Invalid Date", "Please enter date in YYYY-MM-DD format.")
                return
            tid = db.add_tracker(self.conn, name, cat_var.get(), start)
            self.active_tracker = db.get_tracker(self.conn, tid)
            dialog.destroy()
            self._rebuild_tracker_list()
            self._refresh_display()

        tk.Button(dialog, text="Start Journey" if first_time else "Add Tracker", command=submit,
                  bg=t["accent"], fg=t["button_fg"], font=_font(size=12, weight="bold"),
                  cursor="hand2", relief="flat", padx=20, pady=10,
                  activebackground=t["accent_hover"]).pack(pady=20)

        name_entry.focus()
        name_entry.bind('<Return>', lambda e: submit())

    def _settings_dialog(self):
        t = self.theme
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("420x400")
        dialog.configure(bg=t["card_bg"])
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(dialog, text="Settings", font=_font("SF Pro Display", 18, "bold"),
                 bg=t["card_bg"], fg=t["fg"]).pack(pady=(20, 15))

        # Theme selection
        theme_frame = tk.Frame(dialog, bg=t["card_bg"])
        theme_frame.pack(fill=tk.X, padx=30, pady=8)
        tk.Label(theme_frame, text="Theme:", font=_font(size=12),
                 bg=t["card_bg"], fg=t["fg"]).pack(side=tk.LEFT, padx=(0, 10))

        current_theme = db.get_setting(self.conn, "theme", DEFAULT_THEME)
        theme_var = tk.StringVar(value=current_theme)
        theme_names = {k: v["name"] for k, v in THEMES.items()}
        theme_menu = tk.OptionMenu(theme_frame, theme_var, *theme_names.keys())
        theme_menu.config(bg=t["input_bg"], fg=t["fg"], font=_font(size=11),
                          activebackground=t["card_border"], highlightthickness=0, relief="flat")
        theme_menu.pack(side=tk.LEFT)

        # Notifications toggle
        notif_var = tk.BooleanVar(value=db.get_setting(self.conn, "notifications", "1") == "1")
        tk.Checkbutton(dialog, text="Daily motivational notifications",
                       variable=notif_var, font=_font(size=12),
                       bg=t["card_bg"], fg=t["fg"], selectcolor=t["input_bg"],
                       activebackground=t["card_bg"], activeforeground=t["fg"],
                       highlightthickness=0).pack(padx=30, pady=8, anchor="w")

        # Notification time
        time_frame = tk.Frame(dialog, bg=t["card_bg"])
        time_frame.pack(fill=tk.X, padx=30, pady=5)
        tk.Label(time_frame, text="Reminder time:", font=_font(size=11),
                 bg=t["card_bg"], fg=t["fg_dim"]).pack(side=tk.LEFT, padx=(0, 10))

        hour_str = db.get_setting(self.conn, "notif_hour", "9")
        min_str = db.get_setting(self.conn, "notif_minute", "0")
        time_entry = tk.Entry(time_frame, width=6, font=_font("SF Mono", 12),
                              bg=t["input_bg"], fg=t["fg"], insertbackground=t["fg"],
                              relief="flat", bd=5)
        time_entry.pack(side=tk.LEFT)
        time_entry.insert(0, f"{int(hour_str):02d}:{int(min_str):02d}")

        # System tray toggle
        tray_var = tk.BooleanVar(value=db.get_setting(self.conn, "tray", "1") == "1")
        tray_cb = tk.Checkbutton(dialog, text="System tray icon",
                                 variable=tray_var, font=_font(size=12),
                                 bg=t["card_bg"], fg=t["fg"], selectcolor=t["input_bg"],
                                 activebackground=t["card_bg"], activeforeground=t["fg"],
                                 highlightthickness=0)
        tray_cb.pack(padx=30, pady=8, anchor="w")
        if not HAS_TRAY:
            tray_cb.config(state="disabled")
            tk.Label(dialog, text="(Install pystray + Pillow for tray support)",
                     font=_font(size=9), bg=t["card_bg"], fg=t["fg_dim"]).pack(padx=30, anchor="w")

        # Always on top
        aot_var = tk.BooleanVar(value=db.get_setting(self.conn, "always_on_top", "0") == "1")
        tk.Checkbutton(dialog, text="Always on top",
                       variable=aot_var, font=_font(size=12),
                       bg=t["card_bg"], fg=t["fg"], selectcolor=t["input_bg"],
                       activebackground=t["card_bg"], activeforeground=t["fg"],
                       highlightthickness=0).pack(padx=30, pady=8, anchor="w")

        def save_settings():
            # Theme
            new_theme = theme_var.get()
            db.set_setting(self.conn, "theme", new_theme)

            # Notifications
            db.set_setting(self.conn, "notifications", "1" if notif_var.get() else "0")

            # Parse time
            try:
                parts = time_entry.get().strip().split(":")
                h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
                db.set_setting(self.conn, "notif_hour", str(h))
                db.set_setting(self.conn, "notif_minute", str(m))
            except (ValueError, IndexError):
                pass

            # Tray
            db.set_setting(self.conn, "tray", "1" if tray_var.get() else "0")

            # Always on top
            db.set_setting(self.conn, "always_on_top", "1" if aot_var.get() else "0")
            try:
                self.root.attributes('-topmost', aot_var.get())
            except tk.TclError:
                pass

            dialog.destroy()

            # Apply theme change (requires restart for full effect)
            if new_theme != current_theme:
                self.theme = THEMES.get(new_theme, THEMES[DEFAULT_THEME])
                messagebox.showinfo("Theme Changed",
                                    "Theme updated! Restart the app for the full effect.")

            # Update scheduler
            if notif_var.get():
                self._start_scheduler()
            else:
                self._stop_scheduler()

            # Update tray
            if tray_var.get() and HAS_TRAY and not self._tray:
                self._start_tray()
            elif not tray_var.get() and self._tray:
                self._stop_tray()

        tk.Button(dialog, text="Save", command=save_settings,
                  bg=t["accent"], fg=t["button_fg"], font=_font(size=12, weight="bold"),
                  cursor="hand2", relief="flat", padx=30, pady=10,
                  activebackground=t["accent_hover"]).pack(pady=15)

        # Delete tracker button
        if self.active_tracker:
            def delete_tracker():
                result = messagebox.askyesno(
                    "Delete Tracker",
                    f"Permanently delete '{self.active_tracker['name']}'?\n"
                    "This will also delete all journal entries and milestones."
                )
                if result:
                    db.delete_tracker(self.conn, self.active_tracker['id'])
                    self.trackers = db.get_trackers(self.conn)
                    self.active_tracker = self.trackers[0] if self.trackers else None
                    dialog.destroy()
                    self._rebuild_tracker_list()
                    if self.active_tracker:
                        self._refresh_display()
                    else:
                        self.root.after(100, self._setup_first_tracker)

            tk.Button(dialog, text="Delete Current Tracker", command=delete_tracker,
                      bg=t["danger"], fg="#ffffff", font=_font(size=10),
                      cursor="hand2", relief="flat", padx=15, pady=5,
                      activebackground="#c0392b").pack(pady=(0, 10))

    def _reset_counter(self):
        if not self.active_tracker:
            return
        result = messagebox.askyesno(
            "Reset Counter",
            "Are you sure you want to reset your counter?\nThis will allow you to set a new start date."
        )
        if result:
            self._reset_date_dialog()

    def _reset_date_dialog(self):
        t = self.theme
        dialog = tk.Toplevel(self.root)
        dialog.title("New Start Date")
        dialog.geometry("380x180")
        dialog.configure(bg=t["card_bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="New start date (YYYY-MM-DD):", font=_font(size=12),
                 bg=t["card_bg"], fg=t["fg"]).pack(pady=(25, 10))

        entry = tk.Entry(dialog, width=15, font=_font("SF Mono", 12),
                         bg=t["input_bg"], fg=t["fg"], insertbackground=t["fg"],
                         relief="flat", bd=5)
        entry.pack()
        entry.insert(0, date.today().isoformat())
        entry.focus()

        def submit():
            try:
                new_date = date.fromisoformat(entry.get().strip())
            except ValueError:
                messagebox.showerror("Invalid Date", "Please enter date in YYYY-MM-DD format.")
                return
            db.update_tracker(self.conn, self.active_tracker['id'], start_date=new_date)
            self.active_tracker = db.get_tracker(self.conn, self.active_tracker['id'])
            # Clear achieved milestones so they can re-trigger
            self.conn.execute("DELETE FROM milestones_achieved WHERE tracker_id = ?",
                              (self.active_tracker['id'],))
            self.conn.commit()
            dialog.destroy()
            self._refresh_display()

        entry.bind('<Return>', lambda e: submit())
        tk.Button(dialog, text="Update", command=submit,
                  bg=t["accent"], fg=t["button_fg"], font=_font(size=12, weight="bold"),
                  cursor="hand2", relief="flat", padx=20, pady=8,
                  activebackground=t["accent_hover"]).pack(pady=15)

    # ------------------------------------------------------------------
    # Notification Scheduler
    # ------------------------------------------------------------------

    def _get_stats(self):
        """Return list of (name, days_sober) for all active trackers."""
        trackers = db.get_trackers(self.conn)
        stats = []
        for tr in trackers:
            start = date.fromisoformat(tr['start_date'])
            days = (date.today() - start).days
            stats.append((tr['name'], days))
        return stats

    def _start_scheduler(self):
        self._stop_scheduler()
        h = int(db.get_setting(self.conn, "notif_hour", "9"))
        m = int(db.get_setting(self.conn, "notif_minute", "0"))
        self._scheduler = ReminderScheduler(self._get_stats, hour=h, minute=m)
        self._scheduler.start()

    def _stop_scheduler(self):
        if self._scheduler:
            self._scheduler.stop()
            self._scheduler = None

    # ------------------------------------------------------------------
    # System Tray
    # ------------------------------------------------------------------

    def _start_tray(self):
        self._tray = TrayManager(
            show_callback=self._show_from_tray,
            quit_callback=self._quit_from_tray,
            get_stats_fn=self._get_stats,
        )
        self._tray.start()

    def _stop_tray(self):
        if self._tray:
            self._tray.stop()
            self._tray = None

    def _show_from_tray(self):
        self.root.after(0, self.root.deiconify)

    def _quit_from_tray(self):
        self.root.after(0, self._on_close)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_close(self):
        self._stop_scheduler()
        self._stop_tray()
        if self.conn:
            self.conn.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = SobrietyCounterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
