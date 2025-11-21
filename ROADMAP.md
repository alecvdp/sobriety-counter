# Future Roadmap & Feature Ideas

This document outlines potential features and improvements for the Sobriety Counter application.

## 🚀 Planned Features

### 1. Milestone Celebrations
- **Concept:** Display special animations or popup messages when the user hits key milestones (e.g., 1 week, 1 month, 100 days, 1 year).
- **Implementation:**
  - Check `days_sober` against a list of milestone integers.
  - Use `tkinter` message boxes or a custom "Confetti" window.

### 2. Daily Journal
- **Concept:** Allow users to write a brief note or reflection for each day.
- **Implementation:**
  - Add a "Journal" button to the GUI.
  - Store entries in a separate JSON file or a simple SQLite database.
  - View past entries by date.

### 3. Progress Visualization
- **Concept:** Visual representation of the journey.
- **Implementation:**
  - A simple progress bar towards the next major milestone.
  - A calendar view showing days sober (green checks) vs. relapse days.
  - Use `matplotlib` or `tkinter.Canvas` for drawing.

### 4. Emergency "Panic Button"
- **Concept:** A button for moments of weakness.
- **Implementation:**
  - Displays a highly motivational quote, a breathing exercise, or links to support resources.
  - Could play a calming sound or song.

### 5. Settings & Customization
- **Concept:** Allow users to personalize the app.
- **Implementation:**
  - Theme selector (Dark/Light/Custom Colors).
  - Custom name ("Alec's Journey").
  - Toggle for "Always on Top".

## 🛠 Technical Improvements

- **Packaging:** Create a standalone executable (using `pyinstaller`) so Python doesn't need to be installed on the target machine.
- **Cross-Platform Support:** Create dedicated installers for Windows (.exe/.msi) and Linux (.deb/AppImage) alongside the Mac installer.
- **Cloud Sync:** Sync data to a private Gist or cloud storage so the count is accessible across devices.
- **Tests:** Add unit tests for `sobriety_core.py` to ensure logic remains correct during future refactors.
