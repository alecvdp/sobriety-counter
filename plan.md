# Implementation Plan: Sobriety Counter Enhancement

## Overview
Major upgrade from single-counter JSON app to multi-tracker SQLite-backed app with milestones, journaling, themes, notifications, system tray, and packaging.

## Implementation Order (dependency-driven)

### Phase 1: Storage & Data Layer
**1. SQLite Storage Migration (`src/sobriety_db.py`)**
- New module replacing JSON storage with SQLite (`~/.sobriety_counter.db`)
- Tables: `trackers`, `journal_entries`, `milestones_achieved`, `settings`
- `trackers` table: id, name, category, start_date, created_at, is_active
- `journal_entries` table: id, tracker_id, entry_date, mood (1-5), content, created_at
- `milestones_achieved` table: id, tracker_id, milestone_days, achieved_date
- `settings` table: key-value pairs for theme, notifications, always_on_top, etc.
- Migration: auto-import from existing `.sobriety_counter.json` on first run
- Keep `sobriety_core.py` as a facade, updating it to use the DB internally

### Phase 2: Core Features
**2. Multiple Tracker Support**
- Update core to support CRUD operations on multiple trackers
- Each tracker has a name and category (e.g., "Alcohol", "Smoking", "Custom")
- GUI: sidebar/tab navigation to switch between trackers
- Add/remove trackers from the GUI

**3. Milestone System**
- Predefined milestones: 1 day, 3 days, 1 week, 2 weeks, 1 month, 60 days, 90 days, 100 days, 6 months, 1 year, 500 days, 2 years, 5 years
- Check milestones on each display update
- Store achieved milestones in DB to avoid re-triggering
- Show celebration popup with confetti-like animation (tkinter Canvas with colored dots)
- Display earned milestone badges in the main view

**4. Daily Journal**
- Journal button opens a panel/dialog
- Text entry with date picker and mood selector (1-5 scale using emoji)
- View past entries in a scrollable list
- Entries tied to the active tracker

### Phase 3: UI Enhancements
**5. Theme System**
- Theme config: dict with all color values (bg, fg, accent, card_bg, etc.)
- Built-in themes: Dark (current), Light, Ocean, Forest
- Store selected theme in settings table
- Settings dialog with theme preview
- All widgets reference theme colors dynamically

**6. Animated Counter**
- Smooth count-up animation when display loads (0 → actual count)
- Use `root.after()` with easing for smooth transitions
- Milestone sparkle effect on the counter number

**7. System Tray Integration**
- Use `pystray` library for cross-platform tray icon
- Tray menu: Show/Hide, Quick Stats, Quit
- Minimize to tray instead of closing (configurable)
- Show day count in tray tooltip

**8. Notification/Reminder System**
- Use `plyer` library for cross-platform desktop notifications
- Daily motivational notification with day count
- Milestone notifications
- Configurable notification time in settings
- Background scheduler using threading.Timer

### Phase 4: Testing & Packaging
**9. Unit Tests (`tests/test_sobriety_core.py`, `tests/test_sobriety_db.py`)**
- Test DB operations (CRUD trackers, journal, milestones, settings)
- Test milestone detection logic
- Test date calculations
- Test theme loading
- Test migration from JSON to SQLite

**10. PyInstaller Packaging**
- `sobriety_counter.spec` file for PyInstaller config
- Build scripts for macOS, Windows, Linux
- Include icon and assets
- `requirements.txt` with all dependencies
- Update install scripts

## New Dependencies
- `pystray` — system tray (cross-platform)
- `Pillow` — image support for tray icon
- `plyer` — desktop notifications (cross-platform)
- `pyinstaller` — packaging (dev dependency)

## Files to Create
- `src/sobriety_db.py` — SQLite database layer
- `src/themes.py` — Theme definitions
- `src/notifications.py` — Notification system
- `src/tray.py` — System tray integration
- `tests/test_sobriety_core.py` — Core logic tests
- `tests/test_sobriety_db.py` — Database tests
- `requirements.txt` — Dependencies
- `sobriety_counter.spec` — PyInstaller spec

## Files to Modify
- `src/sobriety_core.py` — Update to use SQLite, add milestone logic
- `src/sobriety_counter_gui.py` — Major rewrite for multi-tracker, themes, animations, journal, tray
- `src/sobriety_counter.py` — Update CLI for multi-tracker support
