#!/bin/bash

echo "Creating Sobriety Counter App..."
echo ""

APP_NAME="Sobriety Counter"
SCRIPT_DIR="/Users/alec/Testing"
DESKTOP="$HOME/Desktop"

# Method 1: Create an AppleScript app that launches the Python GUI
APP_PATH="$DESKTOP/${APP_NAME}.app"

# Remove old versions
rm -rf "$APP_PATH"
rm -f "$DESKTOP/Sobriety Counter.command"

# Create using osacompile
cat > /tmp/sobriety_launcher.applescript << 'APPLESCRIPT'
on run
    do shell script "cd /Users/alec/Testing && /opt/homebrew/bin/python3 sobriety_counter_gui.py > /dev/null 2>&1 &"
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
else
    echo "❌ App creation failed. Creating a .command file instead..."
    echo ""
    
    # Fallback: Create .command file
    COMMAND_PATH="$DESKTOP/Sobriety Counter.command"
    cat > "$COMMAND_PATH" << 'LAUNCHER'
#!/bin/bash
cd /Users/alec/Testing
python3 sobriety_counter_gui.py
LAUNCHER
    chmod +x "$COMMAND_PATH"
    
    echo "✅ Created 'Sobriety Counter.command' on Desktop"
    echo "   Double-click it to run (it will open a terminal window)"
fi

