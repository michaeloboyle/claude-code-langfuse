#!/usr/bin/env python3
"""
Test suite for ClaudeCodeLogger
"""

import os
import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_logger import ClaudeCodeLogger, quick_log


class MockLangfuse:
    """Mock LangFuse client for testing"""

    def __init__(self, *args, **kwargs):
        self.spans = []
        self.scores = []
        self.traces = []
        self.current_span = Mock()
        self.current_trace_id = "test-trace-123"

    def start_as_current_span(self, name):
        span = Mock()
        span.__enter__ = Mock(return_value=span)
        span.__exit__ = Mock(return_value=None)
        self.spans.append({"name": name, "span": span})
        return span

    def update_current_span(self, input=None, output=None, metadata=None):
        pass

    def get_current_trace_id(self):
        return self.current_trace_id

    def create_score(self, name, trace_id, value, comment=None):
        self.scores.append({
            "name": name,
            "trace_id": trace_id,
            "value": value,
            "comment": comment
        })

    def flush(self):
        pass


class TestClaudeCodeLogger:
    """Test cases for ClaudeCodeLogger"""

    @pytest.fixture
    def mock_langfuse(self):
        """Fixture providing a mock LangFuse client"""
        return MockLangfuse()

    @pytest.fixture
    def logger(self, mock_langfuse):
        """Fixture providing a ClaudeCodeLogger with mocked LangFuse"""
        with patch('claude_logger.Langfuse', return_value=mock_langfuse):
            logger = ClaudeCodeLogger(
                user_id="test@example.com",
                session_id="test-session-123"
            )
            logger.langfuse = mock_langfuse
            return logger

    def test_initialization(self):
        """Test logger initialization"""
        with patch('claude_logger.Langfuse') as mock_langfuse_class:
            mock_client = Mock()
            mock_langfuse_class.return_value = mock_client

            logger = ClaudeCodeLogger(
                user_id="test@example.com",
                session_id="custom-session"
            )

            assert logger.user_id == "test@example.com"
            assert logger.session_id == "custom-session"
            assert logger.interaction_count == 0
            assert isinstance(logger.start_time, datetime)
            assert logger.langfuse == mock_client

    def test_initialization_with_defaults(self):
        """Test logger initialization with default values"""
        with patch('claude_logger.Langfuse') as mock_langfuse_class:
            mock_client = Mock()
            mock_langfuse_class.return_value = mock_client

            logger = ClaudeCodeLogger()

            assert logger.user_id in ["anonymous", os.getenv("CLAUDE_USER_ID", "anonymous")]
            assert logger.session_id.startswith("claude_session_")
            assert logger.interaction_count == 0

    def test_start_session(self, logger, mock_langfuse):
        """Test session start functionality"""
        metadata = {"project": "test", "goal": "testing"}

        with patch.object(logger.langfuse, 'start_as_current_span') as mock_span:
            mock_span.return_value.__enter__ = Mock()
            mock_span.return_value.__exit__ = Mock()

            session_id = logger.start_session(metadata)

            assert session_id == logger.session_id
            mock_span.assert_called_once_with(name="claude_code_session")

    def test_log_interaction_basic(self, logger, mock_langfuse):
        """Test basic interaction logging"""
        with patch.object(logger.langfuse, 'start_as_current_span') as mock_span:
            mock_span.return_value.__enter__ = Mock()
            mock_span.return_value.__exit__ = Mock()

            result = logger.log_interaction(
                user_prompt="Test prompt",
                claude_response="Test response"
            )

            assert logger.interaction_count == 1
            assert result["interaction_id"] == f"{logger.session_id}_1"
            assert "trace_id" in result
            mock_span.assert_called_once_with(name="claude_interaction")

    def test_log_interaction_with_tools(self, logger, mock_langfuse):
        """Test interaction logging with tools"""
        tools = [
            {"name": "Write", "input": {"file": "test.py"}, "success": True},
            {"name": "Bash", "input": {"command": "python test.py"}, "success": True}
        ]

        with patch.object(logger.langfuse, 'start_as_current_span') as mock_span:
            mock_span.return_value.__enter__ = Mock()
            mock_span.return_value.__exit__ = Mock()

            with patch.object(logger, '_log_tool_usage') as mock_tool_log:
                result = logger.log_interaction(
                    user_prompt="Test with tools",
                    claude_response="Used tools successfully",
                    tools_used=tools
                )

                assert logger.interaction_count == 1
                assert mock_tool_log.call_count == 2

    def test_log_tool_usage(self, logger, mock_langfuse):
        """Test individual tool usage logging"""
        tool_info = {
            "name": "Write",
            "input": {"file": "test.py"},
            "output": {"success": True},
            "success": True,
            "duration_ms": 100
        }

        with patch.object(logger.langfuse, 'start_as_current_span') as mock_span:
            mock_span.return_value.__enter__ = Mock()
            mock_span.return_value.__exit__ = Mock()

            logger._log_tool_usage(tool_info)

            mock_span.assert_called_once_with(name="tool_Write")

    def test_calculate_quality_score(self, logger):
        """Test quality score calculation"""
        # Test base score
        score = logger._calculate_quality_score("hi", "hello")
        assert score == 0.5

        # Test detailed prompt bonus
        score = logger._calculate_quality_score("a" * 60, "hello")
        assert score == 0.7

        # Test detailed response bonus
        score = logger._calculate_quality_score("hi", "a" * 150)
        assert score == 0.7

        # Test tool usage bonus
        tools = [{"name": "tool1"}, {"name": "tool2"}]
        score = logger._calculate_quality_score("hi", "hello", tools)
        assert score == 0.7

        # Test maximum score
        long_prompt = "a" * 60
        long_response = "a" * 150
        many_tools = [{"name": f"tool{i}"} for i in range(5)]
        score = logger._calculate_quality_score(long_prompt, long_response, many_tools)
        assert score == 1.0

    def test_end_session(self, logger, mock_langfuse):
        """Test session end functionality"""
        # Simulate some interactions
        logger.interaction_count = 3
        logger.current_trace_id = "test-trace-123"

        with patch.object(logger.langfuse, 'start_as_current_span') as mock_span:
            mock_span.return_value.__enter__ = Mock()
            mock_span.return_value.__exit__ = Mock()

            stats = logger.end_session("Test session completed")

            assert "total_interactions" in stats
            assert stats["total_interactions"] == 3
            assert "session_duration_seconds" in stats
            mock_span.assert_called_once_with(name="session_end")

    def test_get_trace_url(self, logger):
        """Test trace URL generation"""
        logger.current_trace_id = "test-trace-123"

        with patch.dict(os.environ, {
            "LANGFUSE_HOST": "http://localhost:3001",
            "LANGFUSE_PROJECT_ID": "test-project"
        }):
            url = logger.get_trace_url()
            expected = "http://localhost:3001/project/test-project/traces/test-trace-123"
            assert url == expected

        # Test with custom trace ID
        url = logger.get_trace_url("custom-trace-456")
        expected = "http://localhost:3001/project/test-project/traces/custom-trace-456"
        assert url == expected

    def test_context_manager(self, mock_langfuse):
        """Test context manager functionality"""
        with patch('claude_logger.Langfuse', return_value=mock_langfuse):
            with ClaudeCodeLogger(user_id="test@example.com") as logger:
                assert isinstance(logger, ClaudeCodeLogger)
                assert logger.user_id == "test@example.com"

    def test_context_manager_exception_handling(self, mock_langfuse):
        """Test context manager handles exceptions properly"""
        with patch('claude_logger.Langfuse', return_value=mock_langfuse):
            try:
                with ClaudeCodeLogger(user_id="test@example.com") as logger:
                    raise ValueError("Test exception")
            except ValueError:
                pass  # Expected

    def test_langfuse_initialization_with_config(self):
        """Test LangFuse initialization with custom configuration"""
        config = {
            "host": "http://custom-host:3000",
            "public_key": "pk-test-123",
            "secret_key": "sk-test-456"
        }

        with patch('claude_logger.Langfuse') as mock_langfuse_class:
            mock_client = Mock()
            mock_langfuse_class.return_value = mock_client

            logger = ClaudeCodeLogger(config=config)

            mock_langfuse_class.assert_called_once_with(
                host="http://custom-host:3000",
                public_key="pk-test-123",
                secret_key="sk-test-456"
            )

    def test_langfuse_initialization_with_env_vars(self):
        """Test LangFuse initialization with environment variables"""
        with patch.dict(os.environ, {
            "LANGFUSE_HOST": "http://env-host:3000",
            "LANGFUSE_PUBLIC_KEY": "pk-env-123",
            "LANGFUSE_SECRET_KEY": "sk-env-456"
        }):
            with patch('claude_logger.Langfuse') as mock_langfuse_class:
                mock_client = Mock()
                mock_langfuse_class.return_value = mock_client

                logger = ClaudeCodeLogger()

                mock_langfuse_class.assert_called_once_with(
                    host="http://env-host:3000",
                    public_key="pk-env-123",
                    secret_key="sk-env-456"
                )

    def test_error_handling_in_log_interaction(self, logger):
        """Test error handling in log_interaction"""
        # Mock langfuse to raise an exception
        logger.langfuse.start_as_current_span = Mock(side_effect=Exception("Test error"))

        result = logger.log_interaction("test", "test")

        assert "error" in result
        assert result["error"] == "Test error"

    def test_error_handling_in_tool_logging(self, logger):
        """Test error handling in tool logging"""
        # Mock langfuse to raise an exception
        logger.langfuse.start_as_current_span = Mock(side_effect=Exception("Tool error"))

        # Should not raise exception
        logger._log_tool_usage({"name": "TestTool"})


class TestQuickLog:
    """Test cases for quick_log convenience function"""

    @patch('claude_logger.ClaudeCodeLogger')
    def test_quick_log(self, mock_logger_class):
        """Test quick_log function"""
        mock_logger = Mock()
        mock_logger.log_interaction.return_value = {"trace_id": "test-123"}
        mock_logger_class.return_value = mock_logger

        result = quick_log("test prompt", "test response")

        mock_logger_class.assert_called_once()
        mock_logger.start_session.assert_called_once()
        mock_logger.log_interaction.assert_called_once_with(
            "test prompt", "test response", None
        )
        mock_logger.end_session.assert_called_once()

    @patch('claude_logger.ClaudeCodeLogger')
    def test_quick_log_with_tools(self, mock_logger_class):
        """Test quick_log function with tools"""
        mock_logger = Mock()
        mock_logger.log_interaction.return_value = {"trace_id": "test-123"}
        mock_logger_class.return_value = mock_logger

        tools = [{"name": "Write", "success": True}]
        result = quick_log("test prompt", "test response", tools)

        mock_logger.log_interaction.assert_called_once_with(
            "test prompt", "test response", tools
        )


class TestIntegration:
    """Integration tests"""

    def test_full_workflow(self):
        """Test complete workflow without actual LangFuse calls"""
        with patch('claude_logger.Langfuse') as mock_langfuse_class:
            mock_client = MockLangfuse()
            mock_langfuse_class.return_value = mock_client

            # Test full workflow
            with ClaudeCodeLogger(user_id="integration@test.com") as logger:
                # Log multiple interactions
                result1 = logger.log_interaction(
                    "First prompt",
                    "First response",
                    [{"name": "Write", "success": True}]
                )

                result2 = logger.log_interaction(
                    "Second prompt",
                    "Second response",
                    [{"name": "Bash", "success": True}, {"name": "Read", "success": True}]
                )

                assert logger.interaction_count == 2
                assert len(mock_client.spans) >= 4  # 2 interactions + 3 tools
                assert len(mock_client.scores) >= 2  # Quality scores for interactions

    def test_session_statistics(self):
        """Test session statistics calculation"""
        with patch('claude_logger.Langfuse') as mock_langfuse_class:
            mock_client = MockLangfuse()
            mock_langfuse_class.return_value = mock_client

            logger = ClaudeCodeLogger(user_id="stats@test.com")
            logger.start_session()

            # Simulate some time passing and interactions
            time.sleep(0.1)
            logger.log_interaction("test", "test")
            logger.log_interaction("test2", "test2")

            stats = logger.end_session()

            assert stats["total_interactions"] == 2
            assert stats["session_duration_seconds"] > 0
            assert stats["average_interaction_time"] > 0


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])