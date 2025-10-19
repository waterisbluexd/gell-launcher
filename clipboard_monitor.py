#!/usr/bin/env python3
"""
Clipboard Monitor Daemon - Watches clipboard and saves history automatically
Run this in the background to continuously monitor clipboard changes.
"""
import subprocess
import time
from pathlib import Path
import signal
import sys

HISTORY_FILE = Path.home() / ".cache/gell/clipboard_history.txt"
MAX_HISTORY_ITEMS = 50
CHECK_INTERVAL = 0.5  # Check every 0.5 seconds
MIN_CLIPBOARD_LENGTH = 1  # Minimum characters to save
MAX_CLIPBOARD_LENGTH = 10000  # Don't save huge clipboards

# Store the last clipboard content to detect changes
last_clipboard = ""


def get_clipboard() -> str:
    """Get current clipboard content using wl-paste."""
    try:
        result = subprocess.run(
            ['wl-paste', '--no-newline'],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            return result.stdout
        else:
            # Debug: print error
            if result.stderr:
                print(f"🔴 wl-paste error: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("🔴 wl-paste timeout")
    except FileNotFoundError:
        print("🔴 wl-paste not found! Install with: sudo pacman -S wl-clipboard")
        sys.exit(1)
    except Exception as e:
        print(f"🔴 Error getting clipboard: {e}")
    return ""


def load_history() -> list[str]:
    """Load clipboard history from file."""
    if HISTORY_FILE.exists():
        try:
            with HISTORY_FILE.open('r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n---CLIP---\n')
                return [line.strip() for line in lines if line.strip()][:MAX_HISTORY_ITEMS]
        except Exception as e:
            print(f"🔴 Error loading history: {e}")
    return []


def save_history(history: list[str]):
    """Save clipboard history to file."""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with HISTORY_FILE.open('w', encoding='utf-8') as f:
            f.write('\n---CLIP---\n'.join(history))
    except Exception as e:
        print(f"🔴 Error saving history: {e}")


def add_to_history(text: str, history: list[str]) -> list[str]:
    """Add new clipboard entry to history."""
    if not text or not text.strip():
        return history
    
    # Check length constraints
    if len(text) < MIN_CLIPBOARD_LENGTH or len(text) > MAX_CLIPBOARD_LENGTH:
        print(f"⚠️  Skipped (length {len(text)} not in range {MIN_CLIPBOARD_LENGTH}-{MAX_CLIPBOARD_LENGTH})")
        return history
    
    text = text.strip()
    
    # Remove if already exists
    if text in history:
        history.remove(text)
        print(f"♻️  Moved to top (was already in history)")
    
    # Add to beginning
    history.insert(0, text)
    
    # Limit history size
    return history[:MAX_HISTORY_ITEMS]


def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    print("\n🛑 Clipboard monitor stopped")
    sys.exit(0)


def main():
    """Main monitoring loop."""
    global last_clipboard
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("📋 Clipboard monitor started")
    print(f"💾 Saving to: {HISTORY_FILE}")
    print(f"🔍 Checking every {CHECK_INTERVAL}s")
    print("Press Ctrl+C to stop")
    print("\n" + "="*50)
    print("🎯 Waiting for clipboard changes...")
    print("="*50 + "\n")
    
    # Load existing history
    history = load_history()
    print(f"📚 Loaded {len(history)} existing entries\n")
    
    # Get initial clipboard state
    last_clipboard = get_clipboard()
    if last_clipboard:
        print(f"📎 Initial clipboard: {last_clipboard[:50]}{'...' if len(last_clipboard) > 50 else ''}\n")
    else:
        print("📎 Initial clipboard: (empty)\n")
    
    iteration = 0
    try:
        while True:
            iteration += 1
            
            # Debug: print heartbeat every 10 seconds
            if iteration % 20 == 0:
                print(f"💓 Still running... (checked {iteration} times)")
            
            # Get current clipboard
            current_clipboard = get_clipboard()
            
            # Debug: Show what we got (only if different from last)
            if current_clipboard != last_clipboard:
                print(f"\n🔍 Clipboard changed!")
                print(f"   Old: {last_clipboard[:50] if last_clipboard else '(empty)'}{'...' if len(last_clipboard) > 50 else ''}")
                print(f"   New: {current_clipboard[:50] if current_clipboard else '(empty)'}{'...' if len(current_clipboard) > 50 else ''}")
            
            # Check if clipboard changed and has content
            if current_clipboard and current_clipboard != last_clipboard:
                # Update history
                history = add_to_history(current_clipboard, history)
                save_history(history)
                
                # Show preview (first 50 chars)
                preview = current_clipboard[:50].replace('\n', ' ')
                if len(current_clipboard) > 50:
                    preview += "..."
                print(f"✅ Saved: {preview}")
                print(f"   Total entries: {len(history)}\n")
                
                # Update last clipboard
                last_clipboard = current_clipboard
            
            # Wait before next check
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n🛑 Clipboard monitor stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()