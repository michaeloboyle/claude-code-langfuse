#!/usr/bin/env python3
"""
Global Claude Code Observer
Automatically discovers and instruments all Claude Code processes with LangFuse observability
"""

import os
import sys
import json
import time
import psutil
import signal
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import threading
from claude_logger import ClaudeCodeLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/.claude/observer.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ClaudeProcess:
    """Represents a discovered Claude Code process"""
    pid: int
    cmdline: List[str]
    terminal: str
    start_time: float
    working_directory: Optional[str] = None
    session_id: Optional[str] = None
    logger_instance: Optional[ClaudeCodeLogger] = None

class GlobalClaudeObserver:
    """
    Discovers and instruments all Claude Code processes with LangFuse observability
    """

    def __init__(self):
        self.discovered_processes: Dict[int, ClaudeProcess] = {}
        self.running = False
        self.registry_file = Path.home() / '.claude' / 'observer_registry.json'
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure necessary directories exist"""
        claude_dir = Path.home() / '.claude'
        claude_dir.mkdir(exist_ok=True)

    def discover_claude_processes(self) -> List[ClaudeProcess]:
        """Discover all running Claude Code processes"""
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'terminal']):
            try:
                info = proc.info
                cmdline = info['cmdline'] or []

                # Check if this is a Claude Code process
                if self._is_claude_process(cmdline, info['name']):
                    # Extract terminal session
                    terminal = self._extract_terminal(proc)

                    # Get working directory
                    try:
                        cwd = proc.cwd()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        cwd = None

                    claude_proc = ClaudeProcess(
                        pid=info['pid'],
                        cmdline=cmdline,
                        terminal=terminal,
                        start_time=info['create_time'],
                        working_directory=cwd
                    )
                    processes.append(claude_proc)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return processes

    def _is_claude_process(self, cmdline: List[str], name: str) -> bool:
        """Check if process is a Claude Code instance"""
        if not cmdline:
            return False

        # Main claude binary - check if first argument is 'claude'
        if len(cmdline) > 0 and cmdline[0] == 'claude':
            # Exclude claude-flow processes
            if not any('claude-flow' in str(arg) for arg in cmdline):
                return True

        # Also check process name for direct claude binary
        if name == 'claude':
            return True

        return False

    def _extract_terminal(self, proc) -> str:
        """Extract terminal session identifier"""
        try:
            # Try to get terminal info from process
            terminal_info = proc.terminal()
            if terminal_info:
                return terminal_info

            # Fallback: extract from environment or parent
            return f"term_{proc.pid}"
        except:
            return f"unknown_{proc.pid}"

    def instrument_process(self, claude_proc: ClaudeProcess) -> bool:
        """Instrument a Claude process with LangFuse observability"""
        try:
            # Generate session ID based on process info
            session_id = self._generate_session_id(claude_proc)
            claude_proc.session_id = session_id

            # Create logger instance
            logger_instance = ClaudeCodeLogger(
                user_id=os.getenv("CLAUDE_USER_ID", "global_observer"),
                session_id=session_id
            )

            # Extract project information
            project_info = self._extract_project_info(claude_proc.working_directory)

            # Start session with rich metadata
            metadata = {
                "pid": claude_proc.pid,
                "terminal": claude_proc.terminal,
                "working_directory": claude_proc.working_directory,
                "project_name": project_info["name"],
                "project_path": project_info["path"],
                "start_time": datetime.fromtimestamp(claude_proc.start_time).isoformat(),
                "cmdline": ' '.join(claude_proc.cmdline),
                "auto_instrumented": True,
                "session_type": "global_observer",
                "tags": ["claude-code", "auto-discovered", project_info["name"]]
            }

            logger_instance.start_session(metadata)
            claude_proc.logger_instance = logger_instance

            logger.info(f"Instrumented Claude process PID {claude_proc.pid} with session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to instrument process {claude_proc.pid}: {e}")
            return False

    def _generate_session_id(self, claude_proc: ClaudeProcess) -> str:
        """Generate unique session ID for a Claude process"""
        timestamp = datetime.fromtimestamp(claude_proc.start_time).strftime("%Y%m%d_%H%M%S")

        # Extract project name from working directory
        project_name = "unknown"
        if claude_proc.working_directory:
            try:
                path_parts = Path(claude_proc.working_directory).parts
                if len(path_parts) >= 2:
                    # Look for github directory structure
                    if 'github' in path_parts:
                        github_idx = path_parts.index('github')
                        if len(path_parts) > github_idx + 1:
                            project_name = path_parts[github_idx + 1]
                    else:
                        # Use last directory name
                        project_name = path_parts[-1]
            except:
                project_name = "unknown"

        terminal_short = claude_proc.terminal.split('/')[-1] if '/' in claude_proc.terminal else claude_proc.terminal
        return f"claude_{project_name}_{terminal_short}_{timestamp}_{claude_proc.pid}"

    def _extract_project_info(self, working_directory: Optional[str]) -> Dict[str, str]:
        """Extract project information from working directory"""
        if not working_directory:
            return {"name": "unknown", "path": "unknown"}

        try:
            path = Path(working_directory)

            # Look for github directory structure
            path_parts = path.parts
            if 'github' in path_parts:
                github_idx = path_parts.index('github')
                if len(path_parts) > github_idx + 1:
                    project_name = path_parts[github_idx + 1]
                    project_path = str(path.relative_to(Path.home())) if str(path).startswith(str(Path.home())) else str(path)
                    return {"name": project_name, "path": project_path}

            # Fallback to directory name
            return {"name": path.name, "path": str(path.relative_to(Path.home())) if str(path).startswith(str(Path.home())) else str(path)}

        except Exception:
            return {"name": "unknown", "path": working_directory or "unknown"}

    def save_registry(self):
        """Save current process registry to disk"""
        registry_data = {}

        for pid, proc in self.discovered_processes.items():
            registry_data[str(pid)] = {
                "session_id": proc.session_id,
                "terminal": proc.terminal,
                "start_time": proc.start_time,
                "working_directory": proc.working_directory,
                "cmdline": proc.cmdline,
                "instrumented": proc.logger_instance is not None
            }

        try:
            with open(self.registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def load_registry(self) -> Dict:
        """Load existing process registry"""
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")

        return {}

    def monitor_loop(self, interval: int = 30):
        """Main monitoring loop"""
        logger.info("Starting global Claude Code observer...")
        self.running = True

        # Load existing registry
        existing_registry = self.load_registry()

        while self.running:
            try:
                # Discover current processes
                current_processes = self.discover_claude_processes()

                # Track new processes
                current_pids = {proc.pid for proc in current_processes}

                # Remove dead processes
                dead_pids = set(self.discovered_processes.keys()) - current_pids
                for pid in dead_pids:
                    logger.info(f"Claude process {pid} terminated")
                    if self.discovered_processes[pid].logger_instance:
                        try:
                            self.discovered_processes[pid].logger_instance.end_session("Process terminated")
                        except:
                            pass
                    del self.discovered_processes[pid]

                # Add new processes
                for proc in current_processes:
                    if proc.pid not in self.discovered_processes:
                        logger.info(f"Discovered new Claude process: PID {proc.pid}, Terminal {proc.terminal}")

                        # Instrument the process
                        if self.instrument_process(proc):
                            self.discovered_processes[proc.pid] = proc

                # Save updated registry
                self.save_registry()

                # Log status
                active_sessions = len([p for p in self.discovered_processes.values() if p.logger_instance])
                logger.info(f"Monitoring {len(self.discovered_processes)} Claude processes, {active_sessions} instrumented")

                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)

        self.cleanup()

    def cleanup(self):
        """Cleanup all instrumented processes"""
        logger.info("Cleaning up instrumented processes...")

        for proc in self.discovered_processes.values():
            if proc.logger_instance:
                try:
                    proc.logger_instance.end_session("Observer shutdown")
                except Exception as e:
                    logger.error(f"Error ending session for PID {proc.pid}: {e}")

        self.running = False
        logger.info("Global observer shutdown complete")

    def status(self) -> Dict:
        """Get current status of all monitored processes"""
        # Discover current processes for status command
        if not self.discovered_processes:
            current_processes = self.discover_claude_processes()
            for proc in current_processes:
                self.discovered_processes[proc.pid] = proc

        status = {
            "total_processes": len(self.discovered_processes),
            "instrumented_processes": len([p for p in self.discovered_processes.values() if p.logger_instance]),
            "processes": []
        }

        for proc in self.discovered_processes.values():
            proc_status = {
                "pid": proc.pid,
                "terminal": proc.terminal,
                "session_id": proc.session_id,
                "working_directory": proc.working_directory,
                "start_time": datetime.fromtimestamp(proc.start_time).isoformat(),
                "instrumented": proc.logger_instance is not None,
                "trace_url": None
            }

            if proc.logger_instance:
                try:
                    proc_status["trace_url"] = proc.logger_instance.get_trace_url()
                except:
                    pass

            status["processes"].append(proc_status)

        return status

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    if hasattr(signal_handler, 'observer'):
        signal_handler.observer.running = False

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Global Claude Code LangFuse Observer")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval in seconds")
    parser.add_argument("--status", action="store_true", help="Show current status and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")

    args = parser.parse_args()

    observer = GlobalClaudeObserver()

    if args.status:
        # Show status and exit
        status = observer.status()
        print(json.dumps(status, indent=2))
        return

    # Set up signal handlers
    signal_handler.observer = observer
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.daemon:
        # Run as daemon process
        import daemon
        with daemon.DaemonContext():
            observer.monitor_loop(args.interval)
    else:
        # Run in foreground
        observer.monitor_loop(args.interval)

if __name__ == "__main__":
    main()