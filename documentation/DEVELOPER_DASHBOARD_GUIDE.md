# Developer Dashboard - Token Tracking & Cost Analysis

## 🎯 Overview

The Developer Dashboard provides comprehensive tracking of:
- **Token usage** per query (prompt + completion tokens)
- **Cost calculation** in USD based on Azure OpenAI pricing
- **Query analytics** (SQL/RAG/Hybrid breakdown)
- **Performance metrics** (response time, success rate)
- **Data source statistics**

---

## 📦 Setup

### 1. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This adds new fields to `QueryAnalytics` model:
- `prompt_tokens`
- `completion_tokens`
- `total_cost_usd`

### 2. Restart Server

```bash
python manage.py runserver
```

---

## 🔌 API Endpoints

### 1. **Complete Developer Dashboard**

```bash
GET /api/dashboard/
```

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 7)

**Response:**
```json
{
  "token_usage": {
    "total_tokens": 15234,
    "total_prompt_tokens": 10123,
    "total_completion_tokens": 5111,
    "total_cost_usd": "0.045678",
    "avg_tokens_per_query": 254.57,
    "avg_cost_per_query": "0.000762",
    "queries_count": 60
  },
  "total_queries": 60,
  "successful_queries": 58,
  "failed_queries": 2,
  "success_rate": 96.67,
  "avg_response_time_ms": 1234.56,
  "avg_confidence_score": 0.85,
  "sql_queries_count": 25,
  "rag_queries_count": 20,
  "hybrid_queries_count": 15,
  "total_data_sources": 5,
  "csv_tables": 2,
  "documents": 3,
  "total_sessions": 12,
  "active_sessions_24h": 3
}
```

### 2. **Token Usage Statistics**

```bash
GET /api/dashboard/tokens/?days=30
```

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 7)
- `session_id` (optional): Filter by specific session

**Response:**
```json
{
  "total_tokens": 25450,
  "total_prompt_tokens": 17200,
  "total_completion_tokens": 8250,
  "total_cost_usd": "0.076350",
  "avg_tokens_per_query": 282.78,
  "avg_cost_per_query": "0.000848",
  "queries_count": 90
}
```

### 3. **Query Cost Breakdown**

```bash
GET /api/dashboard/costs/?limit=10&order=cost
```

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 7)
- `limit` (optional): Max queries to return (default: 50)
- `order` (optional): `cost` or `date` (default: cost)

**Response:**
```json
{
  "queries": [
    {
      "query_id": 123,
      "query_text": "bachelor degree courses and course fees",
      "prompt_tokens": 450,
      "completion_tokens": 320,
      "total_tokens": 770,
      "cost_usd": "0.001540",
      "query_type": "hybrid",
      "created_at": "2025-10-04T20:35:04Z"
    }
  ],
  "total_queries": 10
}
```

---

## 💰 Cost Calculation

### Pricing (Azure OpenAI - 2025)

| Model | Prompt Tokens | Completion Tokens |
|-------|---------------|-------------------|
| **GPT-4 Turbo** | $0.01 / 1K | $0.03 / 1K |
| **GPT-4** | $0.03 / 1K | $0.06 / 1K |
| **GPT-3.5 Turbo** | $0.0015 / 1K | $0.002 / 1K |
| **text-embedding-3-large** | $0.13 / 1M | - |

### Example Calculation

For a query with:
- 450 prompt tokens
- 320 completion tokens
- Using GPT-4 Turbo

**Cost:**
```
Prompt cost    = (450 / 1000) × $0.01 = $0.0045
Completion cost = (320 / 1000) × $0.03 = $0.0096
Total cost     = $0.0141
```

---

## 📊 Existing Analytics Endpoints

### Query Analytics
```bash
GET /api/analytics/queries/?days=7
```

Returns query type breakdown, success rates, performance metrics.

### Data Source Stats
```bash
GET /api/analytics/sources/
```

Returns information about loaded CSV tables and documents.

### System Report
```bash
GET /api/reports/system/
```

Complete system health and metrics report.

---

## 🎨 Frontend Integration

### Sample React Component

```javascript
import React, { useEffect, useState } from 'react';

function DeveloperDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [days, setDays] = useState(7);

  useEffect(() => {
    fetch(`http://localhost:8000/api/dashboard/?days=${days}`)
      .then(res => res.json())
      .then(data => setDashboard(data));
  }, [days]);

  if (!dashboard) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      <h1>Developer Dashboard</h1>

      {/* Token Usage Card */}
      <div className="card">
        <h2>Token Usage (Last {days} days)</h2>
        <div className="metrics">
          <div className="metric">
            <label>Total Tokens</label>
            <value>{dashboard.token_usage.total_tokens.toLocaleString()}</value>
          </div>
          <div className="metric">
            <label>Total Cost</label>
            <value>${dashboard.token_usage.total_cost_usd}</value>
          </div>
          <div className="metric">
            <label>Avg Cost/Query</label>
            <value>${dashboard.token_usage.avg_cost_per_query}</value>
          </div>
        </div>
      </div>

      {/* Query Types Card */}
      <div className="card">
        <h2>Query Distribution</h2>
        <div className="chart">
          <div>SQL Queries: {dashboard.sql_queries_count}</div>
          <div>RAG Queries: {dashboard.rag_queries_count}</div>
          <div>Hybrid Queries: {dashboard.hybrid_queries_count}</div>
        </div>
      </div>

      {/* Performance Card */}
      <div className="card">
        <h2>Performance</h2>
        <div className="metrics">
          <div className="metric">
            <label>Success Rate</label>
            <value>{dashboard.success_rate}%</value>
          </div>
          <div className="metric">
            <label>Avg Response Time</label>
            <value>{dashboard.avg_response_time_ms}ms</value>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DeveloperDashboard;
```

### Sample Vanilla JavaScript

```javascript
// Fetch dashboard data
async function loadDashboard() {
  const response = await fetch('http://localhost:8000/api/dashboard/?days=7');
  const data = await response.json();

  // Update DOM
  document.getElementById('total-tokens').textContent =
    data.token_usage.total_tokens.toLocaleString();
  document.getElementById('total-cost').textContent =
    `$${data.token_usage.total_cost_usd}`;
  document.getElementById('avg-cost-per-query').textContent =
    `$${data.token_usage.avg_cost_per_query}`;
  document.getElementById('success-rate').textContent =
    `${data.success_rate}%`;
}

// Load on page load
window.addEventListener('load', loadDashboard);

// Refresh every 30 seconds
setInterval(loadDashboard, 30000);
```

---

## 🧪 Testing

### 1. Make Some Queries

```bash
# Query 1: RAG query
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What is CRM?", "session_id": "test-1"}'

# Query 2: SQL query
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all providers with fees over 1000", "session_id": "test-1"}'

# Query 3: Hybrid query
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "bachelor degree courses and fees", "session_id": "test-1"}'
```

### 2. Check Dashboard

```bash
curl http://localhost:8000/api/dashboard/
```

### 3. Check Token Usage

```bash
curl http://localhost:8000/api/dashboard/tokens/
```

### 4. Check Cost Breakdown

```bash
curl "http://localhost:8000/api/dashboard/costs/?limit=5&order=cost"
```

---

## 📈 Metrics Tracked

| Metric | Description | Endpoint |
|--------|-------------|----------|
| **Total Tokens** | Sum of all tokens used | `/api/dashboard/tokens/` |
| **Prompt Tokens** | Tokens in user prompts | `/api/dashboard/tokens/` |
| **Completion Tokens** | Tokens in AI responses | `/api/dashboard/tokens/` |
| **Total Cost** | Cumulative cost in USD | `/api/dashboard/tokens/` |
| **Avg Tokens/Query** | Average tokens per query | `/api/dashboard/` |
| **Avg Cost/Query** | Average cost per query | `/api/dashboard/` |
| **Success Rate** | % of successful queries | `/api/dashboard/` |
| **Response Time** | Average response time (ms) | `/api/dashboard/` |
| **Query Types** | SQL/RAG/Hybrid breakdown | `/api/dashboard/` |

---

## ⚠️ Important Notes

1. **Token tracking is automatic** - Every query processed through `/api/query/` is tracked

2. **Costs are calculated** using Azure OpenAI pricing (see `token_tracker.py` for rates)

3. **Historical data** - Analytics are filterable by days (7, 30, 90, etc.)

4. **Session filtering** - Can filter token usage by specific session

5. **Real-time updates** - Frontend can poll dashboard endpoints every 30-60 seconds

6. **Database storage** - All metrics stored in `QueryAnalytics` model

---

## 🔧 Customization

### Update Pricing

Edit `api/token_tracker.py`:

```python
PRICING = {
    'gpt-4-turbo': {
        'prompt': 0.00001,  # Update price here
        'completion': 0.00003
    }
}
```

### Add New Metrics

1. Add field to `QueryAnalytics` model
2. Run migrations
3. Update `DeveloperDashboardView` to include new metric
4. Update serializer

---

## 📋 Checklist

- [x] Add token fields to QueryAnalytics model
- [x] Create token tracking utility
- [x] Create dashboard API endpoints
- [x] Add URL routes
- [ ] Run database migrations
- [ ] Test endpoints
- [ ] Update frontend to display metrics
- [ ] Add real-time polling
- [ ] Create dashboard UI components

---

## 🆘 Troubleshooting

### "Migrations needed"
```bash
python manage.py makemigrations
python manage.py migrate
```

### "No data showing"
- Make sure queries have been processed
- Check that `QueryAnalytics` records exist
- Verify date filter (`days` parameter)

### "Costs are 0"
- Token tracking happens during query processing
- Check if `master_orchestrator` is being used (not old `rag_agent`)
- Verify OpenAI responses include token usage

---

## 📚 Related Files

- [api/models.py](api/models.py:129) - QueryAnalytics model
- [api/token_tracker.py](api/token_tracker.py) - Cost calculation
- [api/views_dashboard.py](api/views_dashboard.py) - Dashboard endpoints
- [api/urls.py](api/urls.py) - URL routing
