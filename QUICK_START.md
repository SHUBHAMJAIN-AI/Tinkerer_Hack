# 🚀 24-Hour Deal Freshness - Quick Start Guide

## ✅ **STATUS: FULLY OPERATIONAL**

The 24-hour deal freshness system is **LIVE** and running on your LangGraph server!

---

## 🎯 What It Does

**Prevents showing outdated deals** by enforcing a 24-hour maximum age policy with category-specific refresh windows.

---

## 🔥 Try It Now

### 1. **Test Fresh Electronics Deal**
```bash
# Query for iPhone deals
curl -X POST http://localhost:8123/multi_agent/stream \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "user", "content": "Find me the best iPhone 15 deals"}]}}'
```

**Expected Behavior:**
- First search: Fetches fresh deals from Tavily API
- Second search (within 4h): Uses cached results ✅
- Search after 4h: Automatically refreshes (electronics TTL exceeded) 🔄
- Search after 24h: Forces refresh with warning ⚠️

---

### 2. **Test Price-Sensitive Search**
```bash
# Price-sensitive query (4-hour TTL)
curl -X POST http://localhost:8123/multi_agent/stream \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "user", "content": "Find cheapest MacBook Pro"}]}}'
```

**Expected Behavior:**
- Keyword "cheapest" triggers 4-hour TTL (price-sensitive)
- Cache expires after 4 hours instead of 24

---

### 3. **Test Category Detection**
```bash
# Gaming query (8-hour TTL)
curl -X POST http://localhost:8123/multi_agent/stream \
  -H "Content-Type: application/json" \
  -d '{"input": {"messages": [{"role": "user", "content": "Nintendo Switch deals"}]}}'
```

**Expected Behavior:**
- Auto-detects "gaming" category
- Applies 8-hour TTL
- Refreshes after 8 hours

---

## 📊 Category TTLs

| Category | TTL | Why? |
|----------|-----|------|
| Electronics | 4h | Prices change frequently |
| Gaming | 8h | Moderate price changes |
| Fashion | 12h | Relatively stable |
| Software | 6h | License deals fluctuate |
| Home | 16h | Slower price changes |
| Sports | 12h | Moderate changes |
| Books | 24h | Very stable pricing |
| **Price-Sensitive** | **4h** | **Overrides all** |

---

## 🔍 Monitor Freshness

### Check Redis Cache Status
```bash
cd agent
source ../env/bin/activate
python cache_dashboard.py
```

### Verify Deal Ages
```bash
python verify_deal_freshness.py
```

### Demo Freshness System
```bash
python demo_deal_freshness.py
```

---

## 🎯 How It Works Behind The Scenes

### Cache Check Flow:
```
1. User searches for "iPhone 15 deals"
   ↓
2. System checks Redis cache
   ↓
3. DealFreshnessManager validates age
   ↓
4a. IF < 4h → "✅ FRESH - Use cache"
4b. IF 4-12h → "✅ GOOD - Use cache"
4c. IF 12-24h → "⚠️ STALE - Use but warn"
4d. IF > 24h → "🔄 EXPIRED - Force refresh"
   ↓
5. Return results with freshness indicator
```

---

## 🛠️ Fix Blocking Warnings (Optional)

Your server shows warnings about blocking Redis calls. To eliminate:

### Option 1: Allow Blocking (Quick Fix)
```bash
# Stop current server (Ctrl+C)
langgraph dev --allow-blocking
```

### Option 2: Set Environment Variable
```bash
export BG_JOB_ISOLATED_LOOPS=true
langgraph dev
```

**Note:** These warnings don't affect functionality, only performance at scale.

---

## 📈 Monitor Cache Performance

### Redis Cloud Dashboard
- URL: https://app.redislabs.com
- Keys: 21 cached (as of last check)
- Memory: ~1.2M

### Local Monitoring
```bash
# Watch Redis keys in real-time
cd agent
source ../env/bin/activate
python -c "
from utils.redis_client import get_redis_client
redis = get_redis_client()
keys = redis.keys('search:*')
print(f'🔑 Total cached searches: {len(keys)}')
for key in keys[:5]:
    ttl = redis.ttl(key)
    print(f'  {key}: {ttl//3600}h {(ttl%3600)//60}m remaining')
"
```

---

## 🎮 Interactive Test

### Test All Features:
```bash
cd agent
source ../env/bin/activate
python test_deal_freshness_system.py
```

**Tests:**
- ✅ Category detection
- ✅ Price-sensitive keyword detection
- ✅ Optimal TTL calculation
- ✅ Freshness validation
- ✅ 24-hour expiration
- ✅ Cache invalidation

---

## 🔧 Customize Thresholds

Edit `agent/utils/deal_freshness.py`:

```python
class DealFreshnessManager:
    # Modify these values:
    MAX_DEAL_AGE = 24  # Change max age (hours)
    
    CATEGORY_THRESHOLDS = {
        "electronics": 4,  # Customize per category
        "gaming": 8,
        # ... add more categories
    }
    
    PRICE_SENSITIVE_KEYWORDS = [
        "cheapest",        # Add more keywords
        "best deal",
        # ...
    ]
```

---

## 📊 Real-World Examples

### Example 1: Electronics Shopper
```
User: "Find iPhone 15 deals"
System: 
  - Category: electronics (4h TTL)
  - First search: Fresh API call
  - 2h later: Cache hit (fresh)
  - 5h later: Refresh (threshold exceeded)
  - 25h later: Force refresh + warning
```

### Example 2: Budget Hunter
```
User: "Cheapest laptop under $500"
System:
  - Price-sensitive: YES (4h TTL)
  - Category: electronics (4h TTL)
  - Refresh every 4 hours max
  - Always fresh prices
```

### Example 3: Book Buyer
```
User: "Programming books on sale"
System:
  - Category: books (24h TTL)
  - Cache lasts full 24 hours
  - Book prices rarely change
  - Optimal cache efficiency
```

---

## ✅ Success Checklist

- [x] DealFreshnessManager loaded
- [x] Integrated into search_agent.py
- [x] 24-hour policy enforced
- [x] Category detection working
- [x] Price-sensitive detection active
- [x] Redis Cloud connected
- [x] LangGraph server running
- [x] Multi-agent pipeline operational

---

## 🎉 **SYSTEM IS LIVE!**

Your DealFinder AI now has **intelligent 24-hour deal freshness validation** preventing outdated, unavailable, or price-changed deals from being shown to users.

**Test it now:** Open http://localhost:3000 and search for deals!

---

## 📞 Quick Reference

**Frontend:** http://localhost:3000  
**Backend:** http://localhost:8123  
**Redis Dashboard:** https://app.redislabs.com  
**Docs:** See `IMPLEMENTATION_SUCCESS.md`

**Questions?** Check the full documentation in:
- `DEAL_FRESHNESS_IMPLEMENTATION.md`
- `DEAL_FRESHNESS_QUICK_REFERENCE.md`
- `REDIS_CACHE_UTILIZATION_PLAN.md`
