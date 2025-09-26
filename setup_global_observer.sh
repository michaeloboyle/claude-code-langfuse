#!/bin/bash
# Setup Global Claude Code LangFuse Observer
# Installs and configures automatic observability for all Claude Code sessions

set -e

echo "🔍 Setting up Global Claude Code LangFuse Observer..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install psutil python-daemon

# Create Claude configuration directory
CLAUDE_DIR="$HOME/.claude"
mkdir -p "$CLAUDE_DIR"

# Install global observer script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/global_observer.py" "$CLAUDE_DIR/"
cp "$SCRIPT_DIR/claude_session_manager.py" "$CLAUDE_DIR/"
cp "$SCRIPT_DIR/claude_logger.py" "$CLAUDE_DIR/"

# Make scripts executable
chmod +x "$CLAUDE_DIR/global_observer.py"
chmod +x "$CLAUDE_DIR/claude_session_manager.py"

# Create systemd service (if systemd is available)
if command -v systemctl &> /dev/null; then
    echo "Creating systemd service..."

    cat > "$HOME/.config/systemd/user/claude-observer.service" << EOF
[Unit]
Description=Claude Code LangFuse Global Observer
After=network.target

[Service]
Type=simple
ExecStart=$CLAUDE_DIR/global_observer.py --interval 30
Restart=always
RestartSec=10
Environment=PYTHONPATH=$CLAUDE_DIR
Environment=CLAUDE_LANGFUSE_AUTO=true

[Install]
WantedBy=default.target
EOF

    # Create systemd user directory if it doesn't exist
    mkdir -p "$HOME/.config/systemd/user"

    # Reload and enable service
    systemctl --user daemon-reload
    systemctl --user enable claude-observer.service

    echo "✅ Systemd service created. Start with: systemctl --user start claude-observer"
else
    echo "⚠️  Systemd not available. Manual startup required."
fi

# Create launchd plist for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Creating macOS launchd service..."

    PLIST_FILE="$HOME/Library/LaunchAgents/com.oboyle.claude-observer.plist"

    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.oboyle.claude-observer</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$CLAUDE_DIR/global_observer.py</string>
        <string>--interval</string>
        <string>30</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>$CLAUDE_DIR</string>
        <key>CLAUDE_LANGFUSE_AUTO</key>
        <string>true</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$CLAUDE_DIR/observer.log</string>
    <key>StandardErrorPath</key>
    <string>$CLAUDE_DIR/observer.error.log</string>
</dict>
</plist>
EOF

    # Load the service
    launchctl load "$PLIST_FILE"

    echo "✅ macOS launchd service created and loaded"
fi

# Create environment configuration
echo "Creating environment configuration..."

ENV_FILE="$CLAUDE_DIR/langfuse.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << EOF
# LangFuse Configuration for Claude Code Observer
LANGFUSE_HOST=http://localhost:3001
LANGFUSE_PUBLIC_KEY=pk-lf-2cb584c49e54723969b21603f83a8ab3
LANGFUSE_SECRET_KEY=sk-lf-8b5f1c2d9e3a4b6c8d1f2a5b7c9e4d6f
LANGFUSE_PROJECT_ID=claude-code-obs

# Claude Observer Settings
CLAUDE_LANGFUSE_AUTO=true
CLAUDE_USER_ID=${USER}@$(hostname)
CLAUDE_OBSERVER_INTERVAL=30
EOF
    echo "📝 Created environment file: $ENV_FILE"
    echo "   Please update LangFuse credentials as needed"
else
    echo "📄 Environment file already exists: $ENV_FILE"
fi

# Create convenience scripts
echo "Creating convenience scripts..."

# Status script
cat > "$CLAUDE_DIR/observer-status.sh" << 'EOF'
#!/bin/bash
# Show Claude Observer status
cd "$HOME/.claude"
python3 global_observer.py --status
EOF
chmod +x "$CLAUDE_DIR/observer-status.sh"

# Start script
cat > "$CLAUDE_DIR/observer-start.sh" << 'EOF'
#!/bin/bash
# Start Claude Observer manually
cd "$HOME/.claude"
source langfuse.env 2>/dev/null || true
python3 global_observer.py
EOF
chmod +x "$CLAUDE_DIR/observer-start.sh"

# Add shell aliases
SHELL_RC=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
    if ! grep -q "claude-observer" "$SHELL_RC"; then
        echo "" >> "$SHELL_RC"
        echo "# Claude Code LangFuse Observer aliases" >> "$SHELL_RC"
        echo "alias claude-observer-status='$CLAUDE_DIR/observer-status.sh'" >> "$SHELL_RC"
        echo "alias claude-observer-start='$CLAUDE_DIR/observer-start.sh'" >> "$SHELL_RC"
        echo "alias claude-traces='open http://localhost:3001'" >> "$SHELL_RC"
        echo "📝 Added shell aliases to $SHELL_RC"
    fi
fi

# Test the installation
echo "🧪 Testing installation..."
cd "$CLAUDE_DIR"
source langfuse.env 2>/dev/null || true

if python3 -c "import psutil, claude_logger; print('✅ Dependencies OK')"; then
    echo "✅ Installation successful!"
else
    echo "❌ Installation test failed. Check dependencies."
    exit 1
fi

# Summary
echo ""
echo "🎉 Global Claude Code LangFuse Observer Setup Complete!"
echo ""
echo "📋 What was installed:"
echo "   • Global observer script: $CLAUDE_DIR/global_observer.py"
echo "   • Session manager: $CLAUDE_DIR/claude_session_manager.py"
echo "   • Environment config: $CLAUDE_DIR/langfuse.env"
echo "   • Convenience scripts: observer-status.sh, observer-start.sh"

if command -v systemctl &> /dev/null; then
    echo "   • Systemd service: claude-observer.service"
    echo ""
    echo "🚀 To start automatic observability:"
    echo "   systemctl --user start claude-observer"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   • macOS launchd service: loaded automatically"
    echo ""
    echo "🚀 Automatic observability is now active!"
else
    echo ""
    echo "🚀 To start manual observability:"
    echo "   $CLAUDE_DIR/observer-start.sh"
fi

echo ""
echo "📊 Check status anytime with:"
echo "   claude-observer-status"
echo ""
echo "🌐 View traces at:"
echo "   http://localhost:3001"
echo ""
echo "⚠️  Note: Make sure LangFuse is running (docker compose up -d)"