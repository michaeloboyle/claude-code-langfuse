#!/usr/bin/env python3
"""
Claude Code Logger - Core functionality for tracking Claude Code interactions
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    # Try to load from current directory first, then from user's claude directory
    env_paths = [
        Path.cwd() / '.env',
        Path.home() / '.claude' / 'langfuse.env',
        Path(__file__).parent / '.env'
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

try:
    from langfuse import Langfuse
except ImportError:
    print("❌ LangFuse not installed. Run: pip install langfuse")
    exit(1)


class ClaudeCodeLogger:
    """
    Logger for Claude Code interactions with LangFuse integration

    Features:
    - Automatic session management
    - Tool usage tracking
    - Quality scoring
    - Context preservation
    """

    def __init__(self,
                 user_id: Optional[str] = None,
                 session_id: Optional[str] = None,
                 config: Optional[Dict] = None):
        """
        Initialize the Claude Code logger

        Args:
            user_id: User identifier (email or username)
            session_id: Optional session ID (auto-generated if not provided)
            config: Optional configuration dictionary
        """
        self.user_id = user_id or os.getenv("CLAUDE_USER_ID", "anonymous")
        self.session_id = session_id or f"claude_session_{int(time.time())}"
        self.interaction_count = 0
        self.start_time = datetime.now()

        # Initialize LangFuse
        self.langfuse = self._init_langfuse(config)
        self.current_trace_id = None

    def _init_langfuse(self, config: Optional[Dict] = None) -> Langfuse:
        """Initialize LangFuse client with configuration"""
        if config:
            return Langfuse(
                host=config.get("host", "http://localhost:3001"),
                public_key=config["public_key"],
                secret_key=config["secret_key"]
            )
        else:
            # Use environment variables
            return Langfuse(
                host=os.getenv("LANGFUSE_HOST", "http://localhost:3001"),
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY")
            )

    def start_session(self, metadata: Optional[Dict] = None) -> str:
        """
        Start a new tracking session

        Args:
            metadata: Optional session metadata

        Returns:
            Session ID
        """
        try:
            # Start a span and update the trace with proper session and user associations
            with self.langfuse.start_as_current_span(
                name="claude_code_session"
            ) as span:
                # Enhanced session metadata
                session_input = {
                    "session_start": datetime.now().isoformat(),
                    "user_id": self.user_id,
                    "session_id": self.session_id,
                    "session_type": "claude_code_session"
                }

                # Merge with provided metadata
                full_metadata = {**(metadata or {})}
                if "project_name" in full_metadata:
                    session_input["project"] = full_metadata["project_name"]
                if "project_path" in full_metadata:
                    session_input["project_path"] = full_metadata["project_path"]

                # CRITICAL: Update the trace with session and user IDs at trace level
                # This is what makes sessions appear in the LangFuse Sessions view
                self.langfuse.update_current_trace(
                    name="claude_code_session",
                    user_id=self.user_id,
                    session_id=self.session_id,
                    input=session_input,
                    metadata=full_metadata,
                    tags=full_metadata.get("tags", ["claude-code", "auto-discovered"])
                )

                # Update span with session information
                self.langfuse.update_current_span(
                    input=session_input,
                    metadata=full_metadata
                )

                # Store trace ID for later use
                self.current_trace_id = self.langfuse.get_current_trace_id()

                # Create a score for session tracking
                if self.current_trace_id:
                    self.langfuse.create_score(
                        name="session_active",
                        trace_id=self.current_trace_id,
                        value=1.0,
                        comment=f"Active session: {self.session_id}"
                    )

            print(f"✅ Session started: {self.session_id}")
            return self.session_id

        except Exception as e:
            print(f"⚠️ Failed to start session: {e}")
            return self.session_id

    def log_interaction(self,
                       user_prompt: str,
                       claude_response: str,
                       tools_used: Optional[List[Dict]] = None,
                       context: Optional[Dict] = None,
                       duration_ms: Optional[int] = None) -> Dict[str, Any]:
        """
        Log a Claude Code interaction

        Args:
            user_prompt: The user's input
            claude_response: Claude's response
            tools_used: List of tools used with their details
            context: Additional context
            duration_ms: Response time in milliseconds

        Returns:
            Interaction details including trace ID
        """
        self.interaction_count += 1
        interaction_id = f"{self.session_id}_{self.interaction_count}"

        try:
            with self.langfuse.start_as_current_span(
                name="claude_interaction"
            ) as span:

                # CRITICAL: Ensure this interaction is associated with the session
                self.langfuse.update_current_trace(
                    user_id=self.user_id,
                    session_id=self.session_id
                )

                # Log the interaction
                self.langfuse.update_current_span(
                    input={
                        "prompt": user_prompt,
                        "interaction_number": self.interaction_count,
                        "context": context or {}
                    },
                    output={
                        "response": claude_response,
                        "tools_used": tools_used or [],
                        "duration_ms": duration_ms
                    },
                    metadata={
                        "user_id": self.user_id,
                        "session_id": self.session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                )

                # Log individual tool usage
                if tools_used:
                    for tool in tools_used:
                        self._log_tool_usage(tool)

                # Calculate and add score
                trace_id = self.langfuse.get_current_trace_id()
                if trace_id:
                    score = self._calculate_quality_score(
                        user_prompt, claude_response, tools_used
                    )
                    self.langfuse.create_score(
                        name="interaction_quality",
                        trace_id=trace_id,
                        value=score,
                        comment=f"Interaction {self.interaction_count}"
                    )

                # Flush for real-time tracking
                self.langfuse.flush()

                return {
                    "interaction_id": interaction_id,
                    "trace_id": trace_id,
                    "interaction_count": self.interaction_count
                }

        except Exception as e:
            print(f"⚠️ Failed to log interaction: {e}")
            return {"interaction_id": interaction_id, "error": str(e)}

    def _log_tool_usage(self, tool_info: Dict[str, Any]):
        """Log individual tool usage"""
        try:
            with self.langfuse.start_as_current_span(
                name=f"tool_{tool_info.get('name', 'unknown')}"
            ) as span:

                # CRITICAL: Ensure tool usage is associated with the session
                self.langfuse.update_current_trace(
                    user_id=self.user_id,
                    session_id=self.session_id
                )

                self.langfuse.update_current_span(
                    input=tool_info.get("input", {}),
                    output=tool_info.get("output", {}),
                    metadata={
                        "tool_name": tool_info.get("name"),
                        "success": tool_info.get("success", True),
                        "duration_ms": tool_info.get("duration_ms", 0),
                        "user_id": self.user_id,
                        "session_id": self.session_id
                    }
                )

        except Exception as e:
            print(f"⚠️ Failed to log tool: {e}")

    def _calculate_quality_score(self,
                                prompt: str,
                                response: str,
                                tools: Optional[List] = None) -> float:
        """
        Calculate quality score for an interaction

        Simple heuristic-based scoring:
        - Base score: 0.5
        - +0.2 for detailed prompts (>50 chars)
        - +0.2 for detailed responses (>100 chars)
        - +0.1 for each tool used (max 0.3)
        """
        score = 0.5

        if len(prompt) > 50:
            score += 0.2

        if len(response) > 100:
            score += 0.2

        if tools:
            tool_bonus = min(0.3, len(tools) * 0.1)
            score += tool_bonus

        return min(1.0, score)

    def end_session(self, summary: Optional[str] = None) -> Dict[str, Any]:
        """
        End the tracking session

        Args:
            summary: Optional session summary

        Returns:
            Session statistics
        """
        duration = (datetime.now() - self.start_time).total_seconds()

        try:
            # Log session end
            with self.langfuse.start_as_current_span(
                name="session_end"
            ) as span:

                # CRITICAL: Ensure session end is associated with the session
                self.langfuse.update_current_trace(
                    user_id=self.user_id,
                    session_id=self.session_id
                )

                stats = {
                    "total_interactions": self.interaction_count,
                    "session_duration_seconds": duration,
                    "average_interaction_time": duration / max(1, self.interaction_count)
                }

                self.langfuse.update_current_span(
                    output={
                        "summary": summary or "Session completed",
                        "statistics": stats
                    },
                    metadata={
                        "user_id": self.user_id,
                        "session_id": self.session_id,
                        "end_time": datetime.now().isoformat()
                    }
                )

            # Add session score
            if self.current_trace_id:
                productivity_score = min(1.0, self.interaction_count / 10.0)
                self.langfuse.create_score(
                    name="session_productivity",
                    trace_id=self.current_trace_id,
                    value=productivity_score,
                    comment=f"{self.interaction_count} interactions over {duration:.0f}s"
                )

            # Final flush
            self.langfuse.flush()

            print(f"✅ Session ended: {self.session_id}")
            print(f"   Total interactions: {self.interaction_count}")
            print(f"   Duration: {duration:.0f} seconds")

            return stats

        except Exception as e:
            print(f"⚠️ Failed to end session: {e}")
            return {"error": str(e)}

    def get_trace_url(self, trace_id: Optional[str] = None) -> str:
        """
        Get the LangFuse dashboard URL for a trace

        Args:
            trace_id: Optional trace ID (uses current if not provided)

        Returns:
            Dashboard URL
        """
        tid = trace_id or self.current_trace_id
        if tid:
            host = os.getenv("LANGFUSE_HOST", "http://localhost:3001")
            project = os.getenv("LANGFUSE_PROJECT_ID", "default")
            return f"{host}/project/{project}/traces/{tid}"
        return ""

    def __enter__(self):
        """Context manager entry"""
        self.start_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.end_session()


# Convenience functions
def quick_log(prompt: str, response: str, tools: Optional[List] = None):
    """Quick logging without session management"""
    logger = ClaudeCodeLogger()
    logger.start_session()
    result = logger.log_interaction(prompt, response, tools)
    logger.end_session()
    return result