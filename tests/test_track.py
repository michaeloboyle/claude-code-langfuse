#!/usr/bin/env python3
"""
Test suite for track.py - Main tracking script
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from io import StringIO

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent))

from track import ClaudeTracker, main


class TestClaudeTracker:
    """Test cases for ClaudeTracker"""

    @pytest.fixture
    def mock_logger(self):
        """Fixture providing a mock ClaudeCodeLogger"""
        logger = Mock()
        logger.session_id = "test-session-123"
        logger.interaction_count = 0
        logger.user_id = "test@example.com"
        logger.start_time = Mock()
        logger.current_trace_id = "test-trace-456"
        return logger

    @pytest.fixture
    def tracker(self):
        """Fixture providing a ClaudeTracker instance"""
        with patch.dict(os.environ, {"CLAUDE_USER_ID": "test@example.com"}):
            return ClaudeTracker()

    def test_initialization(self, tracker):
        """Test tracker initialization"""
        assert tracker.user_id == "test@example.com"
        assert tracker.logger is None
        assert tracker.tracking is False

    def test_initialization_with_custom_user(self):
        """Test tracker initialization with custom user ID"""
        tracker = ClaudeTracker(user_id="custom@example.com")
        assert tracker.user_id == "custom@example.com"

    @patch('track.ClaudeCodeLogger')
    def test_start_interactive_mode(self, mock_logger_class, tracker, mock_logger):
        """Test starting tracker in interactive mode"""
        mock_logger_class.return_value = mock_logger

        with patch.object(tracker, '_run_interactive') as mock_run:
            tracker.start(background=False)

            mock_logger_class.assert_called_once_with(user_id=tracker.user_id)
            mock_logger.start_session.assert_called_once()
            assert tracker.tracking is True
            mock_run.assert_called_once()

    @patch('track.ClaudeCodeLogger')
    def test_start_background_mode(self, mock_logger_class, tracker, mock_logger):
        """Test starting tracker in background mode"""
        mock_logger_class.return_value = mock_logger

        with patch.object(tracker, '_run_background') as mock_run:
            tracker.start(background=True)

            mock_logger_class.assert_called_once_with(user_id=tracker.user_id)
            mock_logger.start_session.assert_called_once()
            assert tracker.tracking is True
            mock_run.assert_called_once()

    def test_run_background_keyboard_interrupt(self, tracker, mock_logger):
        """Test background mode handles keyboard interrupt"""
        tracker.logger = mock_logger
        tracker.tracking = True

        with patch('time.sleep', side_effect=KeyboardInterrupt):
            with patch.object(tracker, 'stop') as mock_stop:
                tracker._run_background()
                mock_stop.assert_called_once()

    def test_run_interactive_quit_command(self, tracker, mock_logger):
        """Test interactive mode quit command"""
        tracker.logger = mock_logger
        tracker.tracking = True

        with patch('builtins.input', side_effect=['quit']):
            with patch.object(tracker, 'stop') as mock_stop:
                tracker._run_interactive()
                mock_stop.assert_called_once()

    def test_run_interactive_status_command(self, tracker, mock_logger):
        """Test interactive mode status command"""
        tracker.logger = mock_logger
        tracker.tracking = True
        mock_logger.session_id = "test-session-123"
        mock_logger.interaction_count = 5
        mock_logger.user_id = "test@example.com"

        with patch('builtins.input', side_effect=['status', 'quit']):
            with patch('builtins.print') as mock_print:
                with patch.object(tracker, 'stop'):
                    tracker._run_interactive()

                # Check that status information was printed
                printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
                assert 'Session Status' in printed_text or 'test-session-123' in printed_text

    def test_run_interactive_url_command(self, tracker, mock_logger):
        """Test interactive mode url command"""
        tracker.logger = mock_logger
        tracker.tracking = True
        mock_logger.current_trace_id = "test-trace-456"
        mock_logger.get_trace_url.return_value = "http://localhost:3001/traces/test-trace-456"

        with patch('builtins.input', side_effect=['url', 'quit']):
            with patch('builtins.print') as mock_print:
                with patch.object(tracker, 'stop'):
                    tracker._run_interactive()

                mock_logger.get_trace_url.assert_called()

    def test_run_interactive_log_command(self, tracker, mock_logger):
        """Test interactive mode log command"""
        tracker.logger = mock_logger
        tracker.tracking = True
        mock_logger.log_interaction.return_value = {"interaction_count": 1, "trace_id": "test"}

        input_sequence = [
            'log',
            'Test prompt',  # user prompt
            'Test response',  # claude response
            'Write,Bash',  # tools used
            'quit'
        ]

        with patch('builtins.input', side_effect=input_sequence):
            with patch('builtins.print'):
                with patch.object(tracker, 'stop'):
                    tracker._run_interactive()

                mock_logger.log_interaction.assert_called_once()
                call_args = mock_logger.log_interaction.call_args
                assert call_args[0][0] == 'Test prompt'
                assert call_args[0][1] == 'Test response'
                assert len(call_args[0][2]) == 2  # Two tools

    def test_run_interactive_log_command_skip(self, tracker, mock_logger):
        """Test interactive mode log command with skip"""
        tracker.logger = mock_logger
        tracker.tracking = True

        input_sequence = [
            'log',
            'skip',  # Skip the log command
            'quit'
        ]

        with patch('builtins.input', side_effect=input_sequence):
            with patch('builtins.print'):
                with patch.object(tracker, 'stop'):
                    tracker._run_interactive()

                mock_logger.log_interaction.assert_not_called()

    def test_run_interactive_unknown_command(self, tracker, mock_logger):
        """Test interactive mode unknown command"""
        tracker.logger = mock_logger
        tracker.tracking = True

        with patch('builtins.input', side_effect=['unknown_command', 'quit']):
            with patch('builtins.print') as mock_print:
                with patch.object(tracker, 'stop'):
                    tracker._run_interactive()

                # Check that unknown command message was printed
                printed_text = ' '.join(str(call) for call in mock_print.call_args_list)
                assert 'Unknown command' in printed_text

    def test_run_interactive_keyboard_interrupt(self, tracker, mock_logger):
        """Test interactive mode handles keyboard interrupt"""
        tracker.logger = mock_logger
        tracker.tracking = True

        with patch('builtins.input', side_effect=KeyboardInterrupt):
            with patch.object(tracker, 'stop') as mock_stop:
                tracker._run_interactive()
                mock_stop.assert_called_once()

    def test_show_status_no_logger(self, tracker):
        """Test show_status when no logger is active"""
        tracker.logger = None

        with patch('builtins.print') as mock_print:
            tracker._show_status()

            printed_text = str(mock_print.call_args_list)
            assert 'No active session' in printed_text

    def test_show_url_no_trace(self, tracker, mock_logger):
        """Test show_url when no trace ID is available"""
        tracker.logger = mock_logger
        mock_logger.current_trace_id = None

        with patch('builtins.print') as mock_print:
            with patch.dict(os.environ, {"LANGFUSE_HOST": "http://localhost:3001"}):
                tracker._show_url()

                printed_text = str(mock_print.call_args_list)
                assert 'http://localhost:3001/traces' in printed_text

    def test_stop(self, tracker, mock_logger):
        """Test stopping the tracker"""
        tracker.logger = mock_logger
        tracker.tracking = True
        mock_logger.end_session.return_value = {
            "total_interactions": 5,
            "session_duration_seconds": 120
        }

        with patch('builtins.print'):
            tracker.stop()

        mock_logger.end_session.assert_called_once()
        assert tracker.tracking is False

    def test_stop_no_logger(self, tracker):
        """Test stopping tracker when no logger is active"""
        tracker.logger = None
        tracker.tracking = True

        tracker.stop()

        assert tracker.tracking is False

    @patch('track.ClaudeCodeLogger')
    def test_test_method_success(self, mock_logger_class, tracker):
        """Test the test method with successful connection"""
        mock_logger = Mock()
        mock_logger.log_interaction.return_value = {"trace_id": "test-123"}
        mock_logger.get_trace_url.return_value = "http://localhost:3001/traces/test-123"
        mock_logger_class.return_value = mock_logger

        with patch('builtins.print'):
            result = tracker.test()

        assert result is True
        mock_logger.start_session.assert_called_once_with({"test": True})
        mock_logger.log_interaction.assert_called_once()
        mock_logger.end_session.assert_called_once_with("Test completed")

    @patch('track.ClaudeCodeLogger')
    def test_test_method_no_trace_id(self, mock_logger_class, tracker):
        """Test the test method when no trace ID is returned"""
        mock_logger = Mock()
        mock_logger.log_interaction.return_value = {"interaction_id": "test"}  # No trace_id
        mock_logger_class.return_value = mock_logger

        with patch('builtins.print'):
            result = tracker.test()

        assert result is True  # Should still pass

    @patch('track.ClaudeCodeLogger')
    def test_test_method_failure(self, mock_logger_class, tracker):
        """Test the test method with connection failure"""
        mock_logger_class.side_effect = Exception("Connection failed")

        with patch('builtins.print'):
            result = tracker.test()

        assert result is False


class TestMain:
    """Test cases for the main function"""

    @patch('track.ClaudeTracker')
    def test_main_default(self, mock_tracker_class):
        """Test main function with default arguments"""
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker

        with patch('sys.argv', ['track.py']):
            main()

        mock_tracker_class.assert_called_once_with(user_id=None)
        mock_tracker.start.assert_called_once_with(background=False)

    @patch('track.ClaudeTracker')
    def test_main_background_mode(self, mock_tracker_class):
        """Test main function with background flag"""
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker

        with patch('sys.argv', ['track.py', '--background']):
            main()

        mock_tracker.start.assert_called_once_with(background=True)

    @patch('track.ClaudeTracker')
    def test_main_custom_user(self, mock_tracker_class):
        """Test main function with custom user"""
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker

        with patch('sys.argv', ['track.py', '--user', 'custom@example.com']):
            main()

        mock_tracker_class.assert_called_once_with(user_id='custom@example.com')

    @patch('track.ClaudeTracker')
    def test_main_test_mode_success(self, mock_tracker_class):
        """Test main function in test mode with success"""
        mock_tracker = Mock()
        mock_tracker.test.return_value = True
        mock_tracker_class.return_value = mock_tracker

        with patch('sys.argv', ['track.py', '--test']):
            with patch('sys.exit') as mock_exit:
                main()

        mock_tracker.test.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('track.ClaudeTracker')
    def test_main_test_mode_failure(self, mock_tracker_class):
        """Test main function in test mode with failure"""
        mock_tracker = Mock()
        mock_tracker.test.return_value = False
        mock_tracker_class.return_value = mock_tracker

        with patch('sys.argv', ['track.py', '--test']):
            with patch('sys.exit') as mock_exit:
                main()

        mock_tracker.test.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch('track.ClaudeTracker')
    def test_main_short_flags(self, mock_tracker_class):
        """Test main function with short flag arguments"""
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker

        with patch('sys.argv', ['track.py', '-b', '-u', 'short@example.com']):
            main()

        mock_tracker_class.assert_called_once_with(user_id='short@example.com')
        mock_tracker.start.assert_called_once_with(background=True)


class TestEnvironmentVariables:
    """Test environment variable handling"""

    def test_env_var_user_id(self):
        """Test CLAUDE_USER_ID environment variable"""
        with patch.dict(os.environ, {"CLAUDE_USER_ID": "env@example.com"}):
            tracker = ClaudeTracker()
            assert tracker.user_id == "env@example.com"

    def test_env_var_langfuse_host(self):
        """Test LANGFUSE_HOST environment variable usage"""
        with patch.dict(os.environ, {"LANGFUSE_HOST": "http://custom:3000"}):
            tracker = ClaudeTracker()
            tracker.logger = Mock()
            tracker.logger.current_trace_id = None

            with patch('builtins.print') as mock_print:
                tracker._show_url()

            printed_text = str(mock_print.call_args_list)
            assert 'http://custom:3000/traces' in printed_text


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])