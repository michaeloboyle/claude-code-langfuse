#!/bin/bash

# Claude Code LangFuse Observer - Quick Setup Script

set -e

echo "🚀 Claude Code LangFuse Observer - Setup"
echo "========================================"
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker found"

# Check for Docker Compose
if ! docker compose version &> /dev/null && ! docker-compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

echo "✅ Docker Compose found"

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file..."
    cp .env.example .env

    # Generate secure keys
    NEXTAUTH_SECRET=$(openssl rand -hex 32)
    SALT=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(openssl rand -hex 32)

    # Update .env with generated keys
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-key-change-me-in-production/$NEXTAUTH_SECRET/" .env
        sed -i '' "s/your-salt-change-me-in-production/$SALT/" .env
        sed -i '' "s/0000000000000000000000000000000000000000000000000000000000000000/$ENCRYPTION_KEY/" .env
    else
        # Linux
        sed -i "s/your-secret-key-change-me-in-production/$NEXTAUTH_SECRET/" .env
        sed -i "s/your-salt-change-me-in-production/$SALT/" .env
        sed -i "s/0000000000000000000000000000000000000000000000000000000000000000/$ENCRYPTION_KEY/" .env
    fi

    echo "✅ Generated secure keys in .env"
else
    echo "✅ .env file exists"
fi

# Generate API keys
echo ""
echo "📝 Generating API keys..."
PUBLIC_KEY="pk-lf-$(openssl rand -hex 20)"
SECRET_KEY="sk-lf-$(openssl rand -hex 20)"

# Update .env with API keys
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/pk-lf-1234567890/$PUBLIC_KEY/" .env
    sed -i '' "s/sk-lf-0987654321/$SECRET_KEY/" .env
else
    sed -i "s/pk-lf-1234567890/$PUBLIC_KEY/" .env
    sed -i "s/sk-lf-0987654321/$SECRET_KEY/" .env
fi

echo "✅ Generated API keys"

# Start Docker services
echo ""
echo "🐳 Starting Docker services..."
docker compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to initialize..."
sleep 5

# Check if services are running
if docker compose ps | grep -q "langfuse-web.*running"; then
    echo "✅ LangFuse is running"
else
    echo "⚠️  LangFuse may not have started correctly"
    echo "   Check logs with: docker compose logs langfuse-web"
fi

# Create Python virtual environment
echo ""
echo "🐍 Setting up Python environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Created virtual environment"
else
    echo "✅ Virtual environment exists"
fi

# Activate and install dependencies
source venv/bin/activate
pip install -q -r requirements.txt
echo "✅ Installed Python dependencies"

# Test the setup
echo ""
echo "🧪 Testing setup..."
python track.py --test

echo ""
echo "========================================"
echo "✨ Setup complete!"
echo ""
echo "📊 LangFuse Dashboard: http://localhost:3001"
echo "   Login: admin@example.com / admin123"
echo ""
echo "📚 Your API Keys (saved in .env):"
echo "   Public Key:  $PUBLIC_KEY"
echo "   Secret Key:  $SECRET_KEY"
echo ""
echo "🚀 Start tracking:"
echo "   source venv/bin/activate"
echo "   python track.py"
echo ""
echo "📖 See README.md for detailed usage"
echo "========================================="