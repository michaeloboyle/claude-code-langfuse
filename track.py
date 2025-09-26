#!/usr/bin/env python3
"""
Claude Code Tracker - Main tracking script for Claude Code interactions
"""

import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

# Try to import required modules
try:
    from claude_logger import ClaudeCodeLogger
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install -r requirements.txt")
    exit(1)


class ClaudeTracker:
    """Main tracker for Claude Code interactions"""

    def __init__(self, user_id: Optional[str] = None):
        """Initialize the tracker"""
        # Load environment variables
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)

        self.user_id = user_id or os.getenv("CLAUDE_USER_ID", "user@example.com")
        self.logger = None
        self.tracking = False

    def start(self, background: bool = False):
        """
        Start tracking Claude Code interactions

        Args:
            background: Run in background mode
        """
        print("🚀 Claude Code LangFuse Tracker")
        print("=" * 50)
        print(f"User: {self.user_id}")
        print(f"LangFuse: {os.getenv('LANGFUSE_HOST', 'http://localhost:3001')}")
        print(f"Mode: {'Background' if background else 'Interactive'}")
        print("=" * 50)

        # Initialize logger
        self.logger = ClaudeCodeLogger(user_id=self.user_id)
        self.logger.start_session({
            "mode": "background" if background else "interactive",
            "start_time": datetime.now().isoformat()
        })

        self.tracking = True

        if background:
            self._run_background()
        else:
            self._run_interactive()

    def _run_background(self):
        """Run in background mode"""
        print("\n📡 Running in background mode...")
        print("   All Claude Code interactions will be tracked automatically")
        print("   Press Ctrl+C to stop\n")

        try:
            while self.tracking:
                # Flush any pending data every 30 seconds
                self.logger.langfuse.flush()
                print(f"💚 Active: {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(30)

        except KeyboardInterrupt:
            print("\n🛑 Stopping tracker...")
            self.stop()

    def _run_interactive(self):
        """Run in interactive mode"""
        print("\n📝 Running in interactive mode...")
        print("   Commands:")
        print("   - 'log': Log an interaction manually")
        print("   - 'status': Show session status")
        print("   - 'url': Get dashboard URL")
        print("   - 'quit': Stop tracking\n")

        try:
            while self.tracking:
                command = input("tracker> ").strip().lower()

                if command == "log":
                    self._log_manual_interaction()
                elif command == "status":
                    self._show_status()
                elif command == "url":
                    self._show_url()
                elif command in ["quit", "exit", "q"]:
                    break
                elif command:
                    print(f"Unknown command: {command}")

        except (KeyboardInterrupt, EOFError):
            print("\n")

        self.stop()

    def _log_manual_interaction(self):
        """Manually log an interaction"""
        print("Enter interaction details (or 'skip' to cancel):")

        prompt = input("  User prompt: ").strip()
        if prompt.lower() == "skip":
            return

        response = input("  Claude response: ").strip()
        if response.lower() == "skip":
            return

        tools_input = input("  Tools used (comma-separated, or enter for none): ").strip()
        tools = []
        if tools_input:
            for tool_name in tools_input.split(","):
                tools.append({"name": tool_name.strip(), "success": True})

        result = self.logger.log_interaction(prompt, response, tools)
        print(f"✅ Logged interaction {result.get('interaction_count', 0)}")
        if result.get("trace_id"):
            print(f"   Trace: {self.logger.get_trace_url(result['trace_id'])}")

    def _show_status(self):
        """Show current session status"""
        if self.logger:
            print(f"\n📊 Session Status:")
            print(f"   Session ID: {self.logger.session_id}")
            print(f"   Interactions: {self.logger.interaction_count}")
            print(f"   User: {self.logger.user_id}")
            duration = (datetime.now() - self.logger.start_time).total_seconds()
            print(f"   Duration: {duration:.0f} seconds")
        else:
            print("No active session")

    def _show_url(self):
        """Show dashboard URL"""
        if self.logger and self.logger.current_trace_id:
            url = self.logger.get_trace_url()
            print(f"\n🔗 Dashboard URL:")
            print(f"   {url}")
        else:
            host = os.getenv("LANGFUSE_HOST", "http://localhost:3001")
            print(f"\n🔗 Dashboard URL:")
            print(f"   {host}/traces")

    def stop(self):
        """Stop tracking"""
        if self.logger:
            stats = self.logger.end_session("Tracking session completed")
            print(f"\n📊 Session Summary:")
            print(f"   Total interactions: {stats.get('total_interactions', 0)}")
            print(f"   Duration: {stats.get('session_duration_seconds', 0):.0f}s")
            print(f"\n✅ Tracking stopped")
            print(f"   View traces at: {os.getenv('LANGFUSE_HOST', 'http://localhost:3001')}")

        self.tracking = False

    def test(self):
        """Test the tracking setup"""
        print("🧪 Testing Claude Code Tracker...")

        # Test LangFuse connection
        try:
            logger = ClaudeCodeLogger(user_id="test@example.com")
            logger.start_session({"test": True})

            # Log a test interaction
            result = logger.log_interaction(
                user_prompt="Test prompt",
                claude_response="Test response",
                tools_used=[{"name": "TestTool", "success": True}]
            )

            if result.get("trace_id"):
                print("✅ LangFuse connection: OK")
                print(f"   Test trace: {logger.get_trace_url(result['trace_id'])}")
            else:
                print("⚠️ LangFuse connection: Trace created but no ID returned")

            logger.end_session("Test completed")

        except Exception as e:
            print(f"❌ LangFuse connection: Failed")
            print(f"   Error: {e}")
            return False

        print("\n✅ All tests passed!")
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Track Claude Code interactions with LangFuse"
    )
    parser.add_argument(
        "--background", "-b",
        action="store_true",
        help="Run in background mode"
    )
    parser.add_argument(
        "--user", "-u",
        help="User ID for tracking",
        default=None
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Test the tracking setup"
    )

    args = parser.parse_args()

    tracker = ClaudeTracker(user_id=args.user)

    if args.test:
        success = tracker.test()
        sys.exit(0 if success else 1)
    else:
        tracker.start(background=args.background)


if __name__ == "__main__":
    main()