# 🧪 DealFinder AI - Testing Guide

## Quick Test Commands

### 1. Basic Deal Search
```
Find deals on wireless headphones
Search for gaming laptops under $800
Look for iPhone 15 deals and discounts
```

### 2. Price Comparison
```
Compare prices for MacBook Air M2
Show me price comparison for Nintendo Switch
Find the best price for AirPods Pro
```

### 3. Product Research
```
Extract details from this Amazon link: https://amazon.com/...
Get product information for Sony WH-1000XM5
Research specifications for Dell XPS 13
```

### 4. Store Catalog Exploration
```
Crawl Best Buy's laptop section
Explore Target's electronics department
Browse Amazon's gaming accessories
```

### 5. UI Customization
```
Set the theme to orange
Change color to purple
Make the interface dark blue
```

## Expected Behaviors

### With Tavily API Key
- ✅ Full web search capabilities
- ✅ Real product data extraction
- ✅ Live price comparisons
- ✅ Store catalog crawling

### Without Tavily API Key
- ✅ Conversational interface works
- ✅ Theme changes work
- ✅ UI state management works
- ⚠️ Web research tools return helpful messages about missing API key

## Testing Scenarios

### Scenario 1: Mobile Phone Deal Search
```
User: "I'm looking for the best deals on iPhone 15"
Expected: Agent searches multiple platforms, compares prices, shows deals in organized cards
```

### Scenario 2: Laptop Price Comparison
```
User: "Compare prices for MacBook Air M2 across different stores"
Expected: Agent creates price comparison table with best deals highlighted
```

### Scenario 3: Product Deep Dive
```
User: "Extract all details about this product: [Amazon URL]"
Expected: Agent extracts comprehensive product information including specs, reviews, pricing
```

### Scenario 4: Budget Shopping
```
User: "Find gaming laptops under $1000 with good reviews"
Expected: Agent searches with price filter, evaluates deals, recommends best options
```

### Scenario 5: Theme Customization
```
User: "Set the theme to a nice green color"
Expected: UI immediately updates with new color scheme, all components reflect change
```

## Performance Benchmarks

### Response Times
- Theme changes: < 100ms
- Deal searches: 2-5 seconds (depends on Tavily API)
- Price comparisons: 3-7 seconds
- Product extraction: 2-4 seconds

### Accuracy Metrics
- Deal relevance: High (powered by Tavily's semantic search)
- Price accuracy: Real-time (depends on source freshness)
- Product details: Comprehensive (includes specs, reviews, pricing)

## Error Handling Tests

### Test Missing API Keys
1. Remove TAVILY_API_KEY from agent/.env
2. Restart agent: `npm run dev:agent`
3. Try web search commands
4. Expected: Graceful error messages, not crashes

### Test Invalid URLs
1. Ask agent to extract from invalid URL
2. Expected: Helpful error message, suggestions for valid URLs

### Test Network Issues
1. Disconnect internet during search
2. Expected: Timeout handling, retry suggestions

## User Experience Tests

### Conversation Flow
```
User: "Hi, I need a new laptop"
Agent: Responds with helpful questions about budget, use case, preferences

User: "Gaming laptop, budget $1200"
Agent: Searches for gaming laptops under $1200, shows options

User: "Tell me more about the first one"
Agent: Extracts detailed information about selected laptop

User: "Compare it with similar options"
Agent: Creates comparison table with alternatives
```

### Mobile Responsiveness
- Test on different screen sizes
- Verify deal cards adapt to mobile layout
- Check sidebar usability on mobile

### Accessibility
- Test keyboard navigation
- Verify screen reader compatibility
- Check color contrast ratios

## Integration Tests

### CopilotKit Integration
- Verify agent state updates in real-time
- Test frontend action calls
- Confirm MCP communication

### LangGraph Agent
- Test tool routing logic
- Verify ReAct pattern execution
- Check error propagation

### Tavily API Integration
- Test search parameters
- Verify extraction quality
- Check crawl depth limits

## Debugging Tips

### Check Agent Status
```bash
curl http://localhost:8123/docs
```

### View Agent Logs
```bash
# In the terminal where npm run dev is running
# Look for [agent] prefixed messages
```

### Test Individual Tools
```python
# In Python environment
from agent import search_for_deals
result = search_for_deals("test product")
print(result)
```

### Monitor Network Requests
- Open browser dev tools
- Monitor API calls to localhost:8123
- Check for errors in Network tab

## Known Limitations

1. **Rate Limits**: Tavily API has usage limits
2. **Data Freshness**: Product data depends on source update frequency
3. **Geographic Limits**: Some stores may be region-specific
4. **Language Support**: Currently optimized for English

## Troubleshooting Common Issues

### Agent Not Responding
```bash
# Restart the agent server
npm run dev:agent
```

### UI Not Loading
```bash
# Clear Next.js cache
rm -rf .next
npm run dev:ui
```

### API Key Issues
```bash
# Verify environment variables
cd agent && python -c "import os; print(os.environ.get('OPENAI_API_KEY', 'NOT SET')[:10] + '...')"
```

### Port Conflicts
```bash
# Check what's running on ports
lsof -i :3000
lsof -i :8123
```

## Success Metrics

### Functional Tests ✅
- [ ] Agent responds to queries
- [ ] Deal searches return results
- [ ] Price comparisons display correctly
- [ ] Theme changes work
- [ ] Error handling is graceful

### Performance Tests ✅
- [ ] Response times under 10 seconds
- [ ] UI updates are smooth
- [ ] No memory leaks during extended use
- [ ] Concurrent user support

### User Experience Tests ✅
- [ ] Intuitive conversation flow
- [ ] Clear deal presentation
- [ ] Helpful error messages
- [ ] Responsive design works

---

**Ready to test your DealFinder AI! 🚀**
