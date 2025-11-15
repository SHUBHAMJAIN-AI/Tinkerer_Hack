# 🛒 DealFinder AI - Web Research Agent

A sophisticated AI-powered deal-finding and price comparison agent built with **CopilotKit**, **LangGraph**, and **Tavily** web research capabilities.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure API keys:**
   ```bash
   ./setup.sh  # Interactive setup
   # OR manually create agent/.env with your API keys
   ```

3. **Start the servers:**
   ```bash
   npm run dev
   ```

4. **Open the app:**
   ```
   http://localhost:3000
   ```

## ✨ Features

- **🔍 Smart Deal Search**: Find products and deals across major e-commerce platforms
- **💰 Price Comparison**: Compare prices across Amazon, eBay, Walmart, Target, Best Buy, Costco
- **📊 Product Analysis**: Extract detailed product information and specifications
- **🌐 Web Crawling**: Comprehensive store catalog exploration
- **💬 Conversational Interface**: Natural language interaction with CopilotKit
- **🎨 Dynamic UI**: Real-time updates with generative UI components

## 🗣️ Try These Commands

```
"Find deals on iPhone 15"
"Compare prices for MacBook Air"
"Search for gaming laptops under $1000"
"Extract product details from this Amazon link"
"Set the theme to orange"
```

## 🏗️ Architecture

- **Frontend**: Next.js 16 + CopilotKit + React 19
- **Backend**: Python + LangGraph + Tavily API
- **AI Model**: OpenAI GPT-4o
- **MCP Support**: Model Context Protocol integration

## 📚 Documentation

- **[Complete Setup Guide](README_DEALFINDER.md)** - Detailed installation and configuration
- **[Testing Guide](TESTING_GUIDE.md)** - Comprehensive testing scenarios and benchmarks
- **[Original CopilotKit Starter](README_ORIGINAL.md)** - Original starter template documentation

## 🛠️ Development

```bash
# Development (both servers)
npm run dev

# UI only
npm run dev:ui

# Agent only  
npm run dev:agent

# Debug mode
npm run dev:debug
```

## 📖 API Keys Required

- **OpenAI API Key** (required): Get from [OpenAI Platform](https://platform.openai.com/)
- **Tavily API Key** (optional): Get from [Tavily](https://app.tavily.com/home/) for web research
- **LangSmith API Key** (optional): Get from [LangSmith](https://smith.langchain.com/) for debugging

## Prerequisites

- Node.js 18+ 
- Python 3.8+
- Any of the following package managers:
  - [pnpm](https://pnpm.io/installation) (recommended)
  - npm
  - [yarn](https://classic.yarnpkg.com/lang/en/docs/install/#mac-stable)
  - [bun](https://bun.sh/)
- OpenAI API Key (for the LangGraph agent)

> **Note:** This repository ignores lock files (package-lock.json, yarn.lock, pnpm-lock.yaml, bun.lockb) to avoid conflicts between different package managers. Each developer should generate their own lock file using their preferred package manager. After that, make sure to delete it from the .gitignore.

## Getting Started

1. Install dependencies using your preferred package manager:
```bash
# Using pnpm (recommended)
pnpm install

# Using npm
npm install

# Using yarn
yarn install

# Using bun
bun install
```

> **Note:** Installing the package dependencies will also install the agent's python dependencies via the `install:agent` script.


2. Set up your OpenAI API key:
```bash
echo 'OPENAI_API_KEY=your-openai-api-key-here' > agent/.env
```

3. Start the development server:
```bash
# Using pnpm
pnpm dev

# Using npm
npm run dev

# Using yarn
yarn dev

# Using bun
bun run dev
```

This will start both the UI and agent servers concurrently.

## Available Scripts
The following scripts can also be run using your preferred package manager:
- `dev` - Starts both UI and agent servers in development mode
- `dev:debug` - Starts development servers with debug logging enabled
- `dev:ui` - Starts only the Next.js UI server
- `dev:agent` - Starts only the LangGraph agent server
- `build` - Builds the Next.js application for production
- `start` - Starts the production server
- `lint` - Runs ESLint for code linting
- `install:agent` - Installs Python dependencies for the agent

## Documentation

The main UI component is in `src/app/page.tsx`. You can:
- Modify the theme colors and styling
- Add new frontend actions
- Customize the CopilotKit sidebar appearance

## 📚 Documentation

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) - Learn more about LangGraph and its features
- [CopilotKit Documentation](https://docs.copilotkit.ai) - Explore CopilotKit's capabilities
- [Next.js Documentation](https://nextjs.org/docs) - Learn about Next.js features and API
- [YFinance Documentation](https://pypi.org/project/yfinance/) - Financial data tools

## Contributing

Feel free to submit issues and enhancement requests! This starter is designed to be easily extensible.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Agent Connection Issues
If you see "I'm having trouble connecting to my tools", make sure:
1. The LangGraph agent is running on port 8000
2. Your OpenAI API key is set correctly
3. Both servers started successfully

### Python Dependencies
If you encounter Python import errors:
```bash
npm install:agent
```