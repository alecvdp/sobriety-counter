#!/bin/bash

APP_NAME="Sobriety Counter"
SCRIPT_PATH="/Users/alec/Testing/sobriety_counter_gui.py"

# Use Automator to create a proper macOS app
osascript <<APPLESCRIPT
tell application "Automator"
    set newAction to make new workflow
    tell newAction
        set the path to POSIX file ("$HOME/Desktop/${APP_NAME}.workflow")
    end tell
end tell
APPLESCRIPT

# Alternative: Create a simple launcher script approach
LAUNCHER_PATH="$HOME/Desktop/Sobriety Counter.command"

cat > "$LAUNCHER_PATH" << 'LAUNCHER'
#!/bin/bash
cd "/Users/alec/Testing"
python3 sobriety_counter_gui.py
LAUNCHER

chmod +x "$LAUNCHER_PATH"

echo "Created launcher: $LAUNCHER_PATH"
echo "Double-click 'Sobriety Counter.command' to run the app"
