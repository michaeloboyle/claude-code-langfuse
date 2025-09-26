# Universal Claude Code LangFuse Observer

> 🔍 **Automatic observability for ALL Claude Code sessions** - Zero configuration required!

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Overview

**Universal observability system** that automatically discovers and tracks ALL Claude Code sessions across your entire system with local LangFuse observability. This tool provides complete visibility into:

- 💬 **All conversations** with Claude (automatic discovery)
- 🔧 **Complete tool usage** (Bash, Read, Write, Edit, etc.)
- 📊 **Performance metrics** and quality scores
- 🎯 **Session grouping** with project-aware naming
- 📈 **Real-time analytics** across all terminals
- 🏷️ **Smart session naming**: `claude_{project}_{terminal}_{timestamp}_{pid}`

## ✨ Key Features

- **🎪 Universal Discovery**: Automatically finds ALL Claude Code processes
- **🔒 100% Local**: All data stays on your machine
- **🚀 Zero Configuration**: Works immediately after setup
- **📊 Complete Session Tracking**: All traces properly grouped under sessions
- **🎨 Beautiful Dashboard**: LangFuse web UI at http://localhost:3001
- **🔄 Real-time Monitoring**: 30-second discovery intervals
- **🏗️ Production Ready**: System service with auto-restart

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Claude Code installed

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/claude-code-langfuse.git
cd claude-code-langfuse
```

### 2. Start LangFuse

```bash
docker compose up -d
```

Wait 30 seconds for services to initialize, then visit http://localhost:3001

Default login: `admin@example.com` / `admin123`

### 3. Deploy Universal Observer (One-Time Setup)

```bash
# Install dependencies and deploy as system service
./setup_global_observer.sh
```

**That's it!** 🎉 The system now automatically:
- **Discovers** all running Claude Code processes
- **Instruments** them with LangFuse observability
- **Groups** all traces under proper sessions
- **Names** sessions with project context
- **Monitors** for new Claude processes every 30 seconds

### 4. Verify It's Working

```bash
# Check status of all monitored Claude processes
python3 global_observer.py --status

# View sessions in LangFuse dashboard
open http://localhost:3001/project/pkm-eval-project/sessions
```

All your existing and future Claude Code sessions will automatically appear in LangFuse!

## 📖 How It Works

### 🔍 Universal Process Discovery

The Global Observer automatically:

```bash
# Every 30 seconds, scans for Claude Code processes
psutil.process_iter() → discovers claude processes
↓
# Extracts context from each process
working_directory → project name extraction
terminal_session → terminal identification
↓
# Instruments with LangFuse observability
ClaudeCodeLogger(session_id=generated_name)
↓
# Smart session naming
claude_{project}_{terminal}_{timestamp}_{pid}
```

### 🏷️ Session Naming Examples

```bash
claude_pkm_ttys019_20250926_120010_12345
claude_agentic-radar_ttys017_20250926_120052_12346
claude_my-project_ttys020_20250926_120100_12347
```

### 📊 Session Grouping

All traces are properly associated with sessions:
- **Session start**: `claude_code_session` trace
- **Interactions**: `claude_interaction` traces
- **Tool usage**: `tool_*` traces (Bash, Read, Write, etc.)
- **Session end**: `session_end` trace

### 🛠️ Manual Usage (Optional)

For advanced use cases, you can still use manual logging:

```python
from claude_logger import ClaudeCodeLogger

# Manual session with custom naming
logger = ClaudeCodeLogger(session_id='my_custom_session')
logger.start_session({'project_name': 'my-project'})
logger.log_interaction("prompt", "response", tools_used=[...])
logger.end_session()
```

## 📊 What Gets Tracked

### 🎯 Automatic Session Discovery
- **All Claude Code processes** across your entire system
- **Working directory context** for project identification
- **Terminal session mapping** for multi-session workflows
- **Process lifecycle** (start/end/termination)

### 💬 Complete Interaction Data
- User prompts and Claude responses
- Timestamp and duration for each interaction
- Session context and metadata
- **Proper session grouping** (all traces under sessions)

### 🔧 Comprehensive Tool Usage
- Tool name and parameters (Bash, Read, Write, Edit, etc.)
- Complete input/output data
- Success/failure status and error handling
- Execution time and performance metrics
- **Tool traces grouped under sessions**

### 📈 Smart Quality Metrics
- Response quality scores (0-1) with heuristic analysis
- Tool usage efficiency tracking
- Session productivity metrics
- Task completion rates
- **Cross-session analytics**

## 🎨 Dashboard Views

Access the LangFuse dashboard at http://localhost:3001 to see:

- **🎯 Sessions**: All Claude Code sessions with smart naming (`claude_{project}_{terminal}_{timestamp}_{pid}`)
- **📊 Traces**: Complete conversation flows grouped under sessions
- **🔧 Spans**: Individual interactions and tool calls properly associated
- **⭐ Scores**: Quality metrics and performance analytics
- **📈 Analytics**: Cross-session insights and productivity trends

### 🎪 Session View Example

```
Sessions (http://localhost:3001/project/pkm-eval-project/sessions)
├── claude_pkm_ttys019_20250926_120010_12345
│   ├── claude_code_session (session start)
│   ├── claude_interaction (user prompt 1)
│   ├── tool_bash (bash command execution)
│   ├── claude_interaction (user prompt 2)
│   └── session_end (session complete)
├── claude_agentic-radar_ttys017_20250926_120052_12346
│   ├── claude_code_session (session start)
│   ├── claude_interaction (user prompt 1)
│   └── tool_read (file reading)
```

## 📁 Project Structure

```
claude-code-langfuse/
├── README.md                    # This comprehensive guide
├── docker-compose.yml           # LangFuse stack configuration
├── .env                         # Environment variables (LangFuse credentials)
├── setup_global_observer.sh     # 🚀 ONE-CLICK DEPLOYMENT SCRIPT
├── global_observer.py           # 🔍 Universal process discovery & instrumentation
├── claude_logger.py             # 📊 Core LangFuse logging functionality
├── claude_session_manager.py    # 🎯 Embeddable session management
└── examples/                    # Usage examples and testing
    ├── test_session_creation.py
    ├── manual_logging_example.py
    └── advanced_scoring.py
```

### 🔧 Core Components

- **`global_observer.py`**: The heart of the system - discovers and instruments ALL Claude Code processes
- **`claude_logger.py`**: LangFuse integration with proper session association and trace grouping
- **`setup_global_observer.sh`**: Production deployment script with system service creation
- **`claude_session_manager.py`**: Optional embeddable component for manual integration

## 🔧 Configuration

### Environment Variables (Auto-Configured)

The `.env` file is automatically configured during setup:

```bash
# LangFuse Configuration (automatically set)
LANGFUSE_HOST=http://localhost:3001
LANGFUSE_PUBLIC_KEY=pk-lf-2cb584c49e54723969b21603f83a8ab3
LANGFUSE_SECRET_KEY=sk-lf-439355cf3807997d7efe31ee4c663b5a
LANGFUSE_PROJECT_ID=pkm-eval-project

# Claude Observer Settings
CLAUDE_LANGFUSE_AUTO=true
CLAUDE_USER_ID=michaeloboyle@claude-observer
CLAUDE_OBSERVER_INTERVAL=30
```

### 🎛️ Observer Configuration

```bash
# Monitor status and configuration
python3 global_observer.py --status

# Manual start (if not running as service)
python3 global_observer.py --interval 30

# Run in daemon mode
python3 global_observer.py --daemon --interval 30
```

### 🎯 Custom Session Management

For advanced use cases, customize session handling:

```python
from claude_logger import ClaudeCodeLogger

# Custom session with project metadata
logger = ClaudeCodeLogger(
    user_id="custom-user@example.com",
    session_id="custom_session_name"
)

metadata = {
    "project_name": "my-custom-project",
    "project_path": "/path/to/project",
    "tags": ["custom", "manual", "advanced"]
}

logger.start_session(metadata)
```

## 🐳 Docker Services

The stack includes:

- **LangFuse Web**: Dashboard UI (port 3001)
- **PostgreSQL**: Trace storage (port 5432)
- **Redis**: Caching layer (port 6379)

### Managing Services

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Reset data
docker compose down -v
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangFuse](https://langfuse.com/) - Open source LLM observability
- [Anthropic](https://www.anthropic.com/) - Creator of Claude
- Community contributors

## 🐛 Troubleshooting

### 🚨 LangFuse won't start
- Ensure Docker is running: `docker --version`
- Check port 3001 is not in use: `lsof -i :3001`
- Run `docker compose logs -f` for detailed errors
- Try: `docker compose down -v && docker compose up -d`

### 🔍 No sessions appearing
- Check Global Observer status: `python3 global_observer.py --status`
- Verify Claude Code processes: `ps aux | grep claude`
- Check LangFuse API: `curl -u "pk-lf-...:sk-lf-..." http://localhost:3001/api/public/sessions`
- Restart observer: `python3 global_observer.py`

### 🔌 Connection errors
- Confirm LangFuse is running: `curl http://localhost:3001`
- Check credentials in `.env` file
- Verify project ID matches in dashboard URL
- Test authentication: `curl -u "public_key:secret_key" http://localhost:3001/api/public/sessions`

### 📊 Sessions not grouped properly
- **Fixed in latest version** - all traces now properly associated with sessions
- Update to latest code and restart Global Observer
- Old sessions may still appear as separate traces

## 📚 Resources

- [Documentation](docs/)
- [Examples](examples/)
- [API Reference](docs/api.md)
- [FAQ](docs/faq.md)

## 🧪 Testing

This project includes comprehensive test coverage to ensure reliability.

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run specific test files
pytest tests/test_claude_logger.py
pytest tests/test_track.py

# Run tests in verbose mode
pytest -v
```

### Test Structure

- **`tests/test_claude_logger.py`**: Comprehensive tests for the `ClaudeCodeLogger` class
  - Mock-based testing to avoid actual LangFuse API calls
  - Tests for initialization, session management, interaction logging
  - Error handling and edge case coverage
  - Integration test scenarios

- **`tests/test_track.py`**: Tests for the main tracking script
  - Command-line interface testing
  - Interactive and background mode functionality
  - Input validation and error handling
  - Environment variable configuration

### Coverage Reports

After running tests with coverage, open `htmlcov/index.html` to view detailed coverage reports.

### Continuous Integration

This project uses GitHub Actions for automated testing:
- Tests run on Python 3.9, 3.10, 3.11, and 3.12
- Code quality checks with flake8, black, and isort
- Coverage reporting with Codecov integration

## 🚦 System Status

![Universal Discovery](https://img.shields.io/badge/universal_discovery-active-brightgreen)
![Session Grouping](https://img.shields.io/badge/session_grouping-fixed-brightgreen)
![Auto Instrumentation](https://img.shields.io/badge/auto_instrumentation-enabled-brightgreen)
![Production Ready](https://img.shields.io/badge/production_ready-yes-brightgreen)

### 🎯 What's New

- ✅ **Universal Process Discovery** - Automatically finds ALL Claude Code sessions
- ✅ **Smart Session Naming** - Project-aware session names (`claude_{project}_{terminal}_{timestamp}_{pid}`)
- ✅ **Complete Session Grouping** - All traces properly associated under sessions
- ✅ **Zero Configuration** - Works immediately after deployment
- ✅ **Production Ready** - System service with auto-restart capability

---

🎉 **Universal Claude Code LangFuse Observability** - Made with ❤️ for comprehensive AI development visibility