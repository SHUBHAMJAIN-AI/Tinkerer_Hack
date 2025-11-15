#!/bin/bash

# DealFinder AI - Quick Setup Script
echo "🛒 Welcome to DealFinder AI Setup!"
echo "=================================="
echo

# Check if agent/.env exists
if [ -f "agent/.env" ]; then
    echo "⚠️  Environment file already exists at agent/.env"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Existing configuration preserved."
        exit 0
    fi
fi

echo "Please provide your API keys:"
echo

# OpenAI API Key
read -p "OpenAI API Key (required): " openai_key
if [ -z "$openai_key" ]; then
    echo "❌ OpenAI API Key is required!"
    exit 1
fi

# Tavily API Key
echo
echo "Tavily API Key (optional - for web research features):"
echo "Get it from: https://app.tavily.com/home/"
read -p "Tavily API Key (press Enter to skip): " tavily_key

# LangSmith API Key
echo
echo "LangSmith API Key (optional - for debugging):"
echo "Get it from: https://smith.langchain.com/"
read -p "LangSmith API Key (press Enter to skip): " langsmith_key

# Create the .env file
echo "Creating agent/.env file..."
cat > agent/.env << EOF
# OpenAI API Key for LLM
OPENAI_API_KEY=$openai_key

# Tavily API Key for web research
TAVILY_API_KEY=$tavily_key

# LangSmith API Key (optional, for debugging)
LANGSMITH_API_KEY=$langsmith_key
EOF

echo
echo "✅ Configuration saved to agent/.env"
echo

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
else
    echo "📦 Dependencies already installed"
fi

echo
echo "🚀 Setup complete! Run the following to start DealFinder AI:"
echo "   npm run dev"
echo
echo "🌐 Then open: http://localhost:3000"
echo
echo "💡 Pro tips:"
echo "   - Ask: 'Find deals on iPhone 15'"
echo "   - Try: 'Compare prices for MacBook Air'"
echo "   - Use: 'Set the theme to orange'"
echo
