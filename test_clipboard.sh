#!/bin/bash
# Quick clipboard test script

echo "🔍 Checking clipboard setup..."
echo ""

# Check if history file exists
HISTORY_FILE="$HOME/.cache/gell/clipboard_history.txt"

if [ -f "$HISTORY_FILE" ]; then
    echo "✅ History file exists: $HISTORY_FILE"
    echo ""
    echo "📄 File size: $(wc -c < "$HISTORY_FILE") bytes"
    echo "📝 Number of entries: $(grep -c "---CLIP---" "$HISTORY_FILE" || echo 0)"
    echo ""
    echo "📋 First 5 entries:"
    echo "===================="
    head -n 20 "$HISTORY_FILE"
    echo ""
else
    echo "❌ History file does not exist: $HISTORY_FILE"
    echo ""
    echo "Creating test entries..."
    mkdir -p "$HOME/.cache/gell"
    
    cat > "$HISTORY_FILE" << 'EOF'
Test clipboard entry 1
This is a longer test entry
---CLIP---
https://github.com/example/repo
---CLIP---
echo "Hello World"
ls -la | grep test
cd ~/projects
---CLIP---
Multi-line
clipboard
entry
with several lines
of text
---CLIP---
Short entry
EOF
    
    echo "✅ Created test entries in $HISTORY_FILE"
    echo ""
    echo "Now run your app and press Shift+Down to see clipboard panel"
fi

echo ""
echo "🔍 Checking clipboard monitor..."
if pgrep -f "clipboard_monitor.py" > /dev/null; then
    echo "✅ Clipboard monitor is running (PID: $(pgrep -f clipboard_monitor.py))"
else
    echo "❌ Clipboard monitor is NOT running"
    echo ""
    echo "Start it with:"
    echo "  python clipboard_monitor.py &"
fi

echo ""
echo "🧪 Testing wl-clipboard..."
if command -v wl-paste &> /dev/null; then
    echo "✅ wl-paste found"
    echo "Current clipboard content:"
    echo "------------------------"
    wl-paste 2>/dev/null || echo "(empty or error)"
else
    echo "❌ wl-paste not found - install with: sudo pacman -S wl-clipboard"
fi

echo ""
echo "Done! 🎉"