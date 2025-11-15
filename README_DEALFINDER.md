# 🛒 DealFinder AI - Web Research Agent

A sophisticated AI-powered deal-finding and price comparison agent built with **CopilotKit**, **LangGraph**, and **Tavily** web research capabilities.

## 🚀 Features

- **🔍 Smart Deal Search**: Search for products and deals across major e-commerce platforms
- **💰 Price Comparison**: Compare prices across Amazon, eBay, Walmart, Target, Best Buy, Costco
- **📊 Product Analysis**: Extract detailed product information and specifications
- **🌐 Web Crawling**: Comprehensive store catalog exploration
- **💬 Conversational Interface**: Natural language interaction with CopilotKit
- **🎨 Dynamic UI**: Real-time updates with generative UI components
- **📱 Responsive Design**: Beautiful, modern interface with Tailwind CSS

## 🏗️ Architecture

### Frontend (Next.js + CopilotKit)
- **React 19** with Next.js 16 (Turbopack)
- **CopilotKit** for AI agent integration and MCP support
- **Tailwind CSS** for styling
- **Real-time state management** with CopilotKit shared state

### Backend Agent (Python + LangGraph + Tavily)
- **LangGraph** ReAct agent implementation
- **Tavily API** for web search, extraction, and crawling
- **OpenAI GPT-4** for intelligent reasoning
- **FastAPI** server with LangSmith integration

### MCP Integration
- **Model Context Protocol (MCP)** support via CopilotKit
- Configured MCP server for enhanced AI capabilities
- Seamless frontend-backend communication

## 🛠️ Setup & Installation

### Prerequisites
- Node.js 18+
- Python 3.8+
- OpenAI API Key
- Tavily API Key (optional, for full web research features)

### 1. Install Dependencies

```bash
# Install Node.js dependencies
npm install

# This will also automatically install Python dependencies via postinstall script
```

### 2. Environment Configuration

Create environment files for API keys:

```bash
# Create agent environment file
echo 'OPENAI_API_KEY=your-openai-api-key-here' > agent/.env
echo 'TAVILY_API_KEY=your-tavily-api-key-here' >> agent/.env
echo 'LANGSMITH_API_KEY=your-langsmith-api-key-here' >> agent/.env
```

**Getting API Keys:**
- **OpenAI**: Get your API key from [OpenAI Platform](https://platform.openai.com/)
- **Tavily**: Sign up at [app.tavily.com](https://app.tavily.com/home/) for web research capabilities
- **LangSmith**: Optional, get from [LangSmith](https://smith.langchain.com/) for debugging

### 3. Start Development Server

```bash
npm run dev
```

This starts both:
- **UI Server**: http://localhost:3000
- **Agent Server**: http://localhost:8123

## 🎯 Usage Examples

### Basic Deal Searching
```
"Find deals on iPhone 15"
"Search for gaming laptops under $1000"
"Compare prices for MacBook Air M2"
```

### Advanced Product Research
```
"Extract product details from this Amazon link: [URL]"
"Crawl Best Buy's laptop section for gaming computers"
"Find the best deals on wireless headphones this week"
```

### UI Customization
```
"Set the theme to orange"
"Change the color scheme to purple"
```

## 🧩 Architecture Deep Dive

### Agent Tools

1. **`search_for_deals(query, max_price?, category?)`**
   - Searches across major e-commerce platforms
   - Filters by price and category
   - Returns formatted deal results

2. **`extract_product_details(url)`**
   - Extracts detailed product information
   - Includes prices, specifications, reviews
   - Works with major retailer URLs

3. **`crawl_store_catalog(store_url, product_category?)`**
   - Explores entire store sections
   - Discovers product catalogs
   - Configurable depth and breadth

4. **`compare_prices(product_name)`**
   - Cross-platform price comparison
   - Finds best deals across stores
   - Identifies savings opportunities

### Frontend Actions

- **`addDeal`**: Adds discovered deals to the UI
- **`addPriceComparison`**: Displays price comparisons
- **`show_deal_card`**: Renders interactive deal cards
- **`setThemeColor`**: Dynamic theme customization

### State Management

```typescript
type AgentState = {
  proverbs: string[];           // Shopping wisdom
  deals_found: Deal[];          // Discovered deals
  search_results: SearchResult[]; // Search history
  price_comparisons: PriceComparison[]; // Price data
}
```

## 🌐 MCP Integration

The project includes Model Context Protocol (MCP) support:

```json
{
  "servers": {
    "CopilotKit MCP": {
      "url": "https://mcp.copilotkit.ai/sse"
    }
  }
}
```

This enables:
- Enhanced AI capabilities
- Seamless tool integration
- Real-time communication between frontend and agent

## 🔧 Development Scripts

```bash
# Development (both servers)
npm run dev

# Development with debug logging
npm run dev:debug

# UI only
npm run dev:ui

# Agent only
npm run dev:agent

# Production build
npm run build

# Start production server
npm run start

# Linting
npm run lint

# Install agent dependencies
npm run install:agent
```

## 🐛 Troubleshooting

### Common Issues

1. **Agent Connection Issues**
   ```bash
   # Check if agent is running on port 8123
   curl http://localhost:8123/docs
   ```

2. **Missing API Keys**
   ```bash
   # Verify environment variables
   cd agent && python -c "import os; print('OPENAI_API_KEY:', bool(os.getenv('OPENAI_API_KEY'))); print('TAVILY_API_KEY:', bool(os.getenv('TAVILY_API_KEY')))"
   ```

3. **Python Dependencies**
   ```bash
   # Reinstall agent dependencies
   npm run install:agent
   ```

4. **Port Conflicts**
   ```bash
   # Kill processes on ports 3000 and 8123
   lsof -ti:3000 | xargs kill
   lsof -ti:8123 | xargs kill
   ```

### Without Tavily API Key

The agent gracefully handles missing Tavily API keys:
- Web research tools return informative messages
- Basic functionality remains available
- Can still demonstrate conversational AI capabilities

## 📚 API Documentation

- **Agent API Docs**: http://localhost:8123/docs
- **LangSmith Studio**: https://smith.langchain.com/studio/?baseUrl=http://localhost:8123

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **CopilotKit** for the amazing AI integration framework
- **LangGraph** for the powerful agent orchestration
- **Tavily** for comprehensive web research capabilities
- **OpenAI** for the intelligent reasoning capabilities

---

**Happy Deal Hunting! 🛒✨**
