# Anonymous Chat Endpoint

## Overview

A dedicated endpoint has been created for anonymous users to chat without authentication. This allows visitors to try the system before registering.

## Endpoint Details

### **POST /api/chat/**
- **Purpose**: Anonymous chat without authentication
- **Authentication**: None required
- **Content-Type**: application/json

### Request Format
```json
{
  "query": "What universities are available in Australia?",
  "session_id": "anonymous_session_123"
}
```

### Response Format
```json
{
  "answer": "Here are the universities available in Australia...",
  "sources": [
    {
      "source": "document.pdf",
      "score": 0.85
    }
  ],
  "confidence_score": 0.9,
  "web_search_used": false,
  "session_id": "anonymous_session_123",
  "query_type": "semantic_rag",
  "user_type": "anonymous",
  "message": "This is a free anonymous chat. For full features, please register an account."
}
```

## Key Features

### ✅ **What Anonymous Users Get**
- Full RAG query processing (SQL + RAG + Hybrid)
- Access to knowledge base
- Session-based conversation memory
- Query analytics tracking (without user association)
- Same AI capabilities as authenticated users

### ❌ **What Anonymous Users Cannot Do**
- Upload documents
- Upload CSV files
- View personal statistics
- Access admin features
- View system metrics
- Access analytics dashboard

## Implementation Details

### **Backend Changes**
1. **New View**: `AnonymousChatView` in `api/views.py`
2. **URL Pattern**: Added `path('chat/', views.AnonymousChatView.as_view())`
3. **Permission**: `permission_classes = [AllowAny]`
4. **User Association**: `user=None` in analytics records

### **Analytics Tracking**
- Anonymous queries are tracked in `QueryAnalytics` with `user=None`
- Session IDs are prefixed with `anonymous_` for easy identification
- All metrics (tokens, costs, response times) are still recorded

### **Response Differences**
- Includes `user_type: "anonymous"` field
- Includes promotional message about registration
- Same technical capabilities as authenticated endpoint

## Frontend Integration

### **Anonymous User Flow**
```javascript
// Anonymous chat - no authentication required
const response = await fetch('/api/chat/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'What universities are in Sydney?',
    session_id: 'anonymous_session_123'
  })
});

const data = await response.json();
// data.user_type will be "anonymous"
// data.message will contain registration prompt
```

### **UI Considerations**
- Show "Try for free" or "Chat anonymously" option
- Display registration prompts after responses
- Hide upload/analytics features for anonymous users
- Show "Register for full features" messages

## Security Considerations

### **Rate Limiting**
- Consider implementing rate limiting for anonymous users
- Monitor for abuse of the free endpoint
- Track usage patterns to prevent spam

### **Resource Management**
- Anonymous users consume the same resources as authenticated users
- Monitor costs and usage patterns
- Consider implementing usage limits

## Testing

### **Manual Testing**
```bash
# Test anonymous chat
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What universities are in Australia?", "session_id": "test"}'

# Test authenticated query (should require auth)
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What universities are in Australia?", "session_id": "test"}'
```

### **Automated Testing**
Run the test script:
```bash
python test_anonymous_chat.py
```

## Benefits

### **For Users**
- Try before registering
- No barriers to entry
- Full AI capabilities for testing
- Easy conversion to registered users

### **For Business**
- Lower barrier to entry
- Higher conversion rates
- Better user experience
- Reduced friction in onboarding

## Migration Notes

### **Existing Code**
- No breaking changes to existing endpoints
- `/api/query/` still works for authenticated users
- All existing functionality preserved

### **Frontend Updates**
- Add anonymous chat option to UI
- Update authentication flows
- Add registration prompts
- Implement role-based UI controls

## Monitoring

### **Analytics**
- Track anonymous vs authenticated usage
- Monitor conversion rates
- Measure engagement metrics
- Cost analysis for anonymous users

### **Metrics to Track**
- Anonymous query volume
- Conversion rate (anonymous → registered)
- Average session length for anonymous users
- Most popular anonymous queries

---

**Endpoint Added**: 2025-10-08  
**Total Endpoints**: 32 (was 31)  
**Authentication**: None required for `/api/chat/`  
**Compatibility**: Full backward compatibility maintained
