#!/bin/bash
set -e

echo "🔥 Setting up Habit Streak Bot..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create data directory
mkdir -p data

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Please copy .env.example to .env and add your BOT_TOKEN"
    cp .env.example .env
    echo "Created .env from template. Please edit it!"
else
    echo "✅ .env file found"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your BOT_TOKEN from @BotFather"
echo "2. Run: python run.py"
echo ""
echo "Or use Docker:"
echo "docker-compose up -d"
