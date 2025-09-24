#!/usr/bin/env python3
"""
Generic Notification System for Claude Code Hooks
Provides cross-platform voice and popup notifications
Message is passed via command line argument or environment variable
"""

import sys
import os
import platform
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class NotificationSystem:
    """Cross-platform notification system"""
    
    def __init__(self):
        self.system = platform.system()
        self.project_dir = Path(os.getenv('CLAUDE_PROJECT_DIR', Path.cwd()))
        
    def send_voice(self, message: str) -> bool:
        """Send voice notification (text-to-speech)"""
        try:
            if self.system == "Darwin":  # macOS
                subprocess.run(["say", message], check=False, capture_output=True)
                return True
            
            elif self.system == "Windows":
                # Windows PowerShell text-to-speech
                ps_command = f'Add-Type -AssemblyName System.Speech; ' \
                           f'$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; ' \
                           f'$speak.Speak("{message}")'
                subprocess.run(
                    ["powershell", "-Command", ps_command],
                    check=False,
                    capture_output=True
                )
                return True
            
            elif self.system == "Linux":
                # Try espeak first, then festival
                if subprocess.run(["which", "espeak"], capture_output=True).returncode == 0:
                    subprocess.run(["espeak", message], check=False, capture_output=True)
                    return True
                elif subprocess.run(["which", "festival"], capture_output=True).returncode == 0:
                    subprocess.run(
                        ["festival", "--tts"],
                        input=message.encode(),
                        check=False,
                        capture_output=True
                    )
                    return True
            
            return False
            
        except Exception as e:
            return False
    
    def send_popup(self, message: str, title: str = "Claude Code") -> bool:
        """Send popup/desktop notification"""
        try:
            if self.system == "Darwin":  # macOS
                # Use osascript for native macOS notifications
                script = f'display notification "{message}" with title "{title}"'
                subprocess.run(
                    ["osascript", "-e", script],
                    check=False,
                    capture_output=True
                )
                return True
            
            elif self.system == "Windows":
                # Windows 10+ toast notification via PowerShell
                ps_command = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
                
                $template = @"
                <toast>
                    <visual>
                        <binding template="ToastText02">
                            <text id="1">{title}</text>
                            <text id="2">{message}</text>
                        </binding>
                    </visual>
                    <audio src="ms-winsoundevent:Notification.Default" />
                </toast>
"@
                
                $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
                $xml.LoadXml($template)
                $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude Code").Show($toast)
                '''
                
                subprocess.run(
                    ["powershell", "-Command", ps_command],
                    check=False,
                    capture_output=True
                )
                return True
            
            elif self.system == "Linux":
                # Try notify-send for Linux desktop notifications
                if subprocess.run(["which", "notify-send"], capture_output=True).returncode == 0:
                    subprocess.run(
                        ["notify-send", title, message, "-t", "5000"],
                        check=False,
                        capture_output=True
                    )
                    return True
            
            return False
            
        except Exception as e:
            return False
    
    def send_terminal(self, message: str):
        """Fallback: Print to terminal"""
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"🔔 NOTIFICATION: {message}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)


def get_message_from_args() -> tuple[str, str]:
    """
    Get message from command line arguments or environment variable
    Returns: (message, title)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Send notifications from Claude Code hooks')
    parser.add_argument('message', nargs='?', help='Message to send')
    parser.add_argument('--title', default='Claude Code', help='Notification title')
    parser.add_argument('--method', choices=['voice', 'popup', 'terminal', 'all'], 
                       default='all', help='Notification method')
    
    args = parser.parse_args()
    
    # Priority: 1. Command line arg, 2. Environment variable, 3. Default
    message = args.message
    
    if not message:
        # Try environment variable (for complex messages with quotes)
        message = os.getenv('NOTIFICATION_MESSAGE')
    
    if not message:
        # Try reading from stdin (for hook compatibility)
        try:
            # Read JSON from stdin if available
            input_data = json.load(sys.stdin)
            # Ignore the JSON data, just use as trigger
            message = "Task completed"
        except:
            message = "Task completed"
    
    return message, args.title, args.method


def main():
    """Main entry point for notification system"""
    # Get message and settings
    message, title, method = get_message_from_args()
    
    # Initialize notification system
    notifier = NotificationSystem()
    
    # Send notifications based on method
    success = False
    
    if method in ['popup', 'all']:
        if notifier.send_popup(message, title):
            success = True
    
    if method in ['voice', 'all']:
        if notifier.send_voice(message):
            success = True
    
    if method == 'terminal' or (method == 'all' and not success):
        # Use terminal as fallback or when specifically requested
        notifier.send_terminal(message)
        success = True
    
    sys.exit(0)


if __name__ == "__main__":
    main()