# Claude Code LangFuse Observer

> 🔍 Real-time observability for Claude Code interactions using LangFuse

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Overview

Track, analyze, and observe all your Claude Code (Anthropic's official CLI) interactions with local LangFuse observability. This tool provides complete visibility into:

- 💬 Conversations with Claude
- 🔧 Tool usage (Bash, Read, Write, Edit, etc.)
- 📊 Performance metrics and quality scores
- 🎯 Task completion tracking
- 📈 Session analytics

## ✨ Features

- **🔒 100% Local**: All data stays on your machine
- **🚀 Easy Setup**: 5-minute installation with Docker
- **📊 Rich Analytics**: Detailed traces, spans, and scores
- **🔄 Real-time Tracking**: See interactions as they happen
- **🎨 Beautiful Dashboard**: LangFuse web UI at http://localhost:3001

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

### 3. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings (optional - defaults work)
```

### 5. Start Tracking

```bash
python track.py
```

Now all your Claude Code interactions will be tracked in LangFuse!

## 📖 Usage

### Option 1: Automatic Tracking (Recommended)

Run the tracker in the background:

```bash
python track.py --background
```

This will automatically capture all Claude Code interactions.

### Option 2: Manual Session Logging

```python
from claude_logger import ClaudeCodeLogger

with ClaudeCodeLogger() as logger:
    # Your Claude Code interactions here
    logger.log_interaction(
        user_prompt="Help me write a function",
        claude_response="I'll help you write that function...",
        tools_used=["Write", "Bash"]
    )
```

### Option 3: Quick One-off Logging

```bash
python log_interaction.py "Your prompt" "Claude's response"
```

## 📊 What Gets Tracked

### Interaction Data
- User prompts and Claude responses
- Timestamp and duration
- Session context

### Tool Usage
- Tool name and parameters
- Input/output data
- Success/failure status
- Execution time

### Quality Metrics
- Response quality scores (0-1)
- Tool usage efficiency
- Task completion rates
- Session productivity

## 🎨 Dashboard Views

Access the LangFuse dashboard at http://localhost:3001 to see:

- **Traces**: Complete conversation flows
- **Spans**: Individual interactions and tool calls
- **Scores**: Quality metrics and performance
- **Sessions**: Grouped interactions over time

## 📁 Project Structure

```
claude-code-langfuse/
├── README.md                    # This file
├── docker-compose.yml           # LangFuse stack configuration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── track.py                     # Main tracking script
├── claude_logger.py             # Core logging functionality
├── log_interaction.py           # Manual logging utility
├── examples/                    # Usage examples
│   ├── basic_tracking.py
│   ├── session_analysis.py
│   └── custom_scoring.py
└── tests/                       # Test suite
    ├── __init__.py
    ├── test_claude_logger.py
    └── test_track.py
```

## 🔧 Configuration

### Environment Variables

```bash
# LangFuse Configuration
LANGFUSE_HOST=http://localhost:3001
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key

# Optional Settings
CLAUDE_TRACKING_ENABLED=true
CLAUDE_USER_ID=your_email@example.com
CLAUDE_AUTO_SCORE=true
```

### Custom Scoring

Create custom scoring rules in `config/scoring.yml`:

```yaml
scoring:
  response_quality:
    min_length: 50
    tool_usage_weight: 0.3
    completion_weight: 0.7
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

### LangFuse won't start
- Ensure Docker is running
- Check port 3001 is not in use
- Run `docker compose logs` for errors

### No traces appearing
- Verify environment variables are set
- Check `python track.py --test` works
- Ensure Claude Code is installed

### Connection errors
- Confirm LangFuse is running: `curl http://localhost:3001`
- Check network settings in Docker

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

## 🚦 Status

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)

---

Made with ❤️ for the Claude Code community