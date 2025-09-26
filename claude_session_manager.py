#!/usr/bin/env python3
"""
Claude Session Manager
Manages LangFuse sessions for individual Claude Code processes
"""

import os
import sys
import json
import time
import signal
import psutil
from pathlib import Path
from typing import Dict, Optional
from claude_logger import ClaudeCodeLogger
import logging

logger = logging.getLogger(__name__)

class ClaudeSessionManager:
    """
    Manages LangFuse observability for a specific Claude Code session
    Designed to be embedded within each Claude process
    """

    def __init__(self, auto_detect: bool = True):
        self.logger_instance: Optional[ClaudeCodeLogger] = None
        self.session_id: Optional[str] = None
        self.pid = os.getpid()
        self.auto_enabled = os.getenv("CLAUDE_LANGFUSE_AUTO", "true").lower() == "true"

        if auto_detect and self.auto_enabled:
            self._auto_initialize()

    def _auto_initialize(self):
        """Automatically initialize session based on current process"""
        try:
            # Get current process info
            proc = psutil.Process(self.pid)
            terminal = self._detect_terminal()
            working_dir = os.getcwd()

            # Generate session ID
            timestamp = int(time.time())
            self.session_id = f"claude_session_{terminal}_{timestamp}_{self.pid}"

            # Initialize logger
            self.logger_instance = ClaudeCodeLogger(
                user_id=os.getenv("CLAUDE_USER_ID", f"user_{self.pid}"),
                session_id=self.session_id
            )

            # Start session with metadata
            metadata = {
                "pid": self.pid,
                "terminal": terminal,
                "working_directory": working_dir,
                "auto_instrumented": True,
                "session_type": "embedded"
            }

            self.logger_instance.start_session(metadata)
            logger.info(f"Auto-initialized Claude session {self.session_id}")

            # Register cleanup handler
            signal.signal(signal.SIGTERM, self._cleanup_handler)
            signal.signal(signal.SIGINT, self._cleanup_handler)

        except Exception as e:
            logger.error(f"Failed to auto-initialize session: {e}")

    def _detect_terminal(self) -> str:
        """Detect terminal session identifier"""
        try:
            # Try various methods to identify terminal
            terminal_methods = [
                lambda: os.getenv("TERM_SESSION_ID"),
                lambda: os.getenv("TMUX_PANE"),
                lambda: os.getenv("WINDOWID"),
                lambda: f"tty_{os.ttyname(sys.stdin.fileno()).split('/')[-1]}",
                lambda: f"pid_{self.pid}"
            ]

            for method in terminal_methods:
                try:
                    result = method()
                    if result:
                        return str(result)
                except:
                    continue

            return f"unknown_{self.pid}"

        except Exception:
            return f"fallback_{self.pid}"

    def log_interaction(self, user_prompt: str, claude_response: str, tools_used: Optional[list] = None) -> Dict:
        """Log a Claude Code interaction"""
        if not self.logger_instance:
            return {"error": "Session not initialized"}

        return self.logger_instance.log_interaction(user_prompt, claude_response, tools_used)

    def log_tool_usage(self, tool_name: str, tool_input: Dict, tool_output: Dict, success: bool = True):
        """Log individual tool usage"""
        if not self.logger_instance:
            return

        tool_info = {
            "name": tool_name,
            "input": tool_input,
            "output": tool_output,
            "success": success
        }

        self.logger_instance._log_tool_usage(tool_info)

    def get_trace_url(self) -> Optional[str]:
        """Get the current trace URL"""
        if not self.logger_instance:
            return None

        return self.logger_instance.get_trace_url()

    def end_session(self, reason: str = "Session ended"):
        """End the current session"""
        if self.logger_instance:
            try:
                stats = self.logger_instance.end_session(reason)
                logger.info(f"Session {self.session_id} ended: {stats}")
                return stats
            except Exception as e:
                logger.error(f"Error ending session: {e}")
            finally:
                self.logger_instance = None

    def _cleanup_handler(self, signum, frame):
        """Signal handler for cleanup"""
        logger.info(f"Received signal {signum}, cleaning up session")
        self.end_session(f"Process terminated with signal {signum}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type:
            self.end_session(f"Session ended with exception: {exc_type.__name__}")
        else:
            self.end_session("Session completed normally")

# Global session manager instance
_session_manager: Optional[ClaudeSessionManager] = None

def get_session_manager() -> ClaudeSessionManager:
    """Get or create global session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = ClaudeSessionManager()
    return _session_manager

def log_interaction(user_prompt: str, claude_response: str, tools_used: Optional[list] = None) -> Dict:
    """Convenience function to log interaction"""
    return get_session_manager().log_interaction(user_prompt, claude_response, tools_used)

def log_tool_usage(tool_name: str, tool_input: Dict, tool_output: Dict, success: bool = True):
    """Convenience function to log tool usage"""
    return get_session_manager().log_tool_usage(tool_name, tool_input, tool_output, success)

def get_trace_url() -> Optional[str]:
    """Convenience function to get trace URL"""
    return get_session_manager().get_trace_url()

if __name__ == "__main__":
    # Test the session manager
    with ClaudeSessionManager() as manager:
        result = manager.log_interaction(
            "Test prompt",
            "Test response",
            [{"name": "TestTool", "input": {}, "output": {}, "success": True}]
        )
        print(f"Logged interaction: {result}")
        print(f"Trace URL: {manager.get_trace_url()}")