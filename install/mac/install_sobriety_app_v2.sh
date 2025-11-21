#!/bin/bash

echo "Creating Sobriety Counter App..."
echo ""

APP_NAME="Sobriety Counter"

# Get the absolute path to the directory containing this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Resolve the src directory (assuming it's at ../../src relative to this script)
SRC_DIR="$( cd "$SCRIPT_DIR/../../src" && pwd )"

echo "Detected Source Directory: $SRC_DIR"

# Detect Python path
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    # Fallback for Homebrew or standard install if 'which' fails in this context
    if [ -f "/opt/homebrew/bin/python3" ]; then
        PYTHON_PATH="/opt/homebrew/bin/python3"
    elif [ -f "/usr/local/bin/python3" ]; then
        PYTHON_PATH="/usr/local/bin/python3"
    else
        PYTHON_PATH="/usr/bin/python3"
    fi
fi

echo "Detected Python Path: $PYTHON_PATH"

DESKTOP="$HOME/Desktop"

# Method 1: Create an AppleScript app that launches the Python GUI
APP_PATH="$DESKTOP/${APP_NAME}.app"

# Remove old versions
rm -rf "$APP_PATH"
rm -f "$DESKTOP/Sobriety Counter.command"

# Create using osacompile
# We use a here-doc with variable expansion for the path
# Added logging to /tmp/sobriety_debug.log for troubleshooting
cat > /tmp/sobriety_launcher.applescript << APPLESCRIPT
on run
    do shell script "cd \"$SRC_DIR\" && \"$PYTHON_PATH\" sobriety_counter_gui.py > /tmp/sobriety.log 2>&1 &"
end run
APPLESCRIPT

osacompile -o "$APP_PATH" /tmp/sobriety_launcher.applescript
rm /tmp/sobriety_launcher.applescript

if [ -d "$APP_PATH" ]; then
    echo "✅ Success! 'Sobriety Counter.app' created on Desktop"
    echo ""
    echo "You can now:"
    echo "  • Double-click the app to open"
    echo "  • Drag it to your Dock"
    echo "  • Move it anywhere you like"
    echo ""
    echo "Debug log will be at: /tmp/sobriety.log"
    echo ""
else
    echo "❌ App creation failed. Creating a .command file instead..."
    echo ""
    
    # Fallback: Create .command file
    COMMAND_PATH="$DESKTOP/Sobriety Counter.command"
    cat > "$COMMAND_PATH" << LAUNCHER
#!/bin/bash
cd "$SRC_DIR"
"$PYTHON_PATH" sobriety_counter_gui.py
LAUNCHER
    chmod +x "$COMMAND_PATH"
    
    echo "✅ Created 'Sobriety Counter.command' on Desktop"
    echo "   Double-click it to run (it will open a terminal window)"
fi

