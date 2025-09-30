# StudyNet AI Counselor - Development Instructions

**Last Updated:** 2025-10-01
**Status:** Phase 2 Complete (70%), Foundation + Query Intelligence + Tool System Complete
**Next Phase:** Implement Hybrid Retrieval (Phase 3)

## 🎯 Quick Start - Continue Development

**To test what's been built:**
```bash
# Test Phase 1 (Query Intelligence)
python test_phase1.py

# Test Phase 2 (Tool System)
python test_phase2.py

# Reload CSV data if needed
python load_csv_data.py
```

**Progress Summary:**
- ✅ **Foundation (30%):** DuckDB storage + CSV loading - COMPLETE
- ✅ **Phase 1 (20%):** Query classification + entity extraction + SQL building - COMPLETE
- ✅ **Phase 2 (20%):** Tool system for LangChain agent - COMPLETE
- ❌ **Phase 3 (15%):** Hybrid retrieval with reranking - PENDING
- ❌ **Phase 4 (20%):** Enhanced agent with routing - PENDING
- ❌ **Phase 5 (10%):** API integration - PENDING
- ❌ **Phase 6 (15%):** Testing & docs - PENDING

**Total Progress: 70%**

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [What's Been Completed](#whats-been-completed)
3. [What Remains To Be Built](#what-remains-to-be-built)
4. [Architecture Overview](#architecture-overview)
5. [How To Continue Development](#how-to-continue-development)
6. [Testing Guide](#testing-guide)
7. [Troubleshooting](#troubleshooting)

---

## 1. Project Overview

### Problem Statement
StudyNet helps students find universities in Australia. The system has:
- **Structured Data:** 5 CSV files with 21,875 total rows (providers, courses, fees, locations, intakes)
- **Unstructured Data:** PDF guidance documents (application guides, visa info, etc.)

**Challenge:** Students ask complex questions requiring BOTH data types:
- "Show me IT courses under $20k in Sydney" → Needs structured filtering
- "How do I apply for a student visa?" → Needs semantic search of PDFs
- "Best IT courses with scholarships in Melbourne" → Needs HYBRID (both)

### Solution Architecture
**Dual-Pipeline RAG System:**
- **Structured Pipeline:** DuckDB → SQL queries for filtering/comparing courses
- **Semantic Pipeline:** ChromaDB → Vector search for guidance documents
- **Hybrid Merger:** Intelligently combine both results with reranking

---

## 2. What's Been Completed ✅

### 2.1 Architecture Design (100%)
**File:** [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md)

**Completed:**
- ✅ Full system design documented
- ✅ Data flow diagrams
- ✅ Database schema design for all 5 CSV files
- ✅ Query classification strategy
- ✅ Tool system design
- ✅ Hybrid retrieval pattern

### 2.2 Structured Storage Layer (100%)
**Files:**
- `api/storage/schema.py` - Database schemas
- `api/storage/duckdb_store.py` - DuckDB implementation
- `api/storage/__init__.py`

**Schemas Created:**
```sql
providers          (97 rows)     - Universities/Colleges
campus_locations   (499 rows)    - City/State for location filtering
courses            (9,999 rows)  - Course catalog (main table)
fees               (4,281 rows)  - Course pricing
intakes            (6,999 rows)  - Application deadlines
```

**Features:**
- ✅ Proper foreign key relationships
- ✅ Indexes on searchable columns (city, state, fee, field_of_study)
- ✅ Pre-built query methods:
  - `search_courses()` - Multi-filter course search
  - `compare_providers()` - University comparison
  - `get_provider_details()` - Full provider info
  - `get_courses_by_budget()` - Price range search
  - `get_scholarships()` - Find scholarship opportunities
  - `get_upcoming_intakes()` - Application deadlines

### 2.3 Data Loading System (100%)
**Files:**
- `api/loaders/csv_loader.py` - CSV to DuckDB loader
- `api/loaders/__init__.py`
- `load_csv_data.py` - Standalone loading script

**Features:**
- ✅ Multi-encoding support (UTF-8, Latin-1, ISO-8859-1, CP1252)
- ✅ Automatic column mapping from CSV headers to database columns
- ✅ Data validation (filters invalid rows)
- ✅ Type conversion (booleans, numerics, dates)
- ✅ Data cleaning (handles "N/A", "Not specified", empty values)

**Successfully Loaded:**
```
providers:         97 rows (filtered 105 invalid from 202)
campus_locations:  499 rows
courses:           9,999 rows
fees:              4,281 rows
intakes:           6,999 rows
TOTAL:             21,875 rows
```

### 2.4 Query Intelligence Layer (100%) - **NEW!**
**Files:**
- `api/query/classifier.py` - Query classification with LLM
- `api/query/entity_extractor.py` - Extract entities from natural language
- `api/query/sql_builder.py` - Build SQL from extracted entities
- `test_phase1.py` - Test script for Phase 1

**Features:**
- ✅ **Query Classification:** Classifies queries as STRUCTURED, SEMANTIC, HYBRID, or COMPARISON
- ✅ **Intent Detection:** Identifies user intent (SEARCH_COURSES, GET_GUIDANCE, etc.)
- ✅ **Entity Extraction:** Extracts 8+ entity types:
  - Field of Study: Maps 'IT' → ['Information Technology', 'Computing']
  - Price Range: Extracts "under $20k" → {min: 0, max: 20000}
  - Location: Maps 'Sydney' → {city: 'Sydney', state: 'NSW'}
  - Provider: Maps 'UNSW' → 'University of New South Wales'
  - Study Level: Maps 'bachelor' → 'Bachelor Degree'
  - Booleans: has_scholarship, has_internship
  - Ranking: top N universities
- ✅ **Dynamic SQL Building:** Constructs WHERE clauses based on extracted filters
- ✅ **Tested:** All 12 test queries pass successfully

**Test Results:**
```
✅ IT courses under $20k          → 10 results (hybrid query)
✅ Business courses in Sydney     → 10 results (structured)
✅ Bachelor in Melbourne <$25k    → 0 results (no matches in data)
✅ Engineering with scholarships  → 10 results (structured)
✅ Courses in Brisbane            → 10 results (location filter)
✅ Universities in NSW            → 55 results (provider search)
✅ Courses $15k-$30k             → 10 results (price range)
✅ Cheapest courses              → 10 results (sorted by price)
✅ Student visa application      → Semantic query detected
✅ What documents needed?        → Semantic query detected
✅ Best IT with scholarships     → 10 results (multi-filter)
✅ Affordable Business programs  → 10 results (field filter)
```

### 2.5 Tool System (100%) - **NEW!**
**Files:**
- `api/tools/structured_tools.py` - 6 LangChain tools for structured data
- `api/tools/semantic_tools.py` - 2 LangChain tools for PDF search
- `test_phase2.py` - Test script for Phase 2

**Structured Tools (6 total):**
1. ✅ **search_courses** - Search courses with multiple filters (field, price, location, level, scholarship)
2. ✅ **compare_providers** - Compare 2-4 universities side-by-side
3. ✅ **get_provider_details** - Full details about a specific university
4. ✅ **get_scholarships** - Find providers offering scholarships
5. ✅ **get_intakes** - Get upcoming intake/application deadlines
6. ✅ **get_budget_options** - Find courses within budget, sorted by price

**Semantic Tools (2 total):**
1. ✅ **search_guidance** - Search PDF guidance documents (visa, application, procedures)
2. ✅ **search_provider_info** - Search university facilities, culture, research info from PDFs

**Tool Features:**
- ✅ Proper Pydantic input schemas for type safety
- ✅ Descriptive tool descriptions for LLM agent
- ✅ Error handling and user-friendly error messages
- ✅ Formatted output (tables, bullet points, numbered lists)
- ✅ All tools tested and working

**Test Results:**
```
✅ search_courses (IT under $20k)        → 5 results
✅ search_courses (Business in Sydney)   → 5 results
✅ compare_providers (2 universities)    → Formatted comparison table
✅ get_provider_details (UNSW)           → Full university profile
✅ get_scholarships (IT field)           → 5 universities
✅ get_intakes                          → 10 upcoming intakes
✅ get_budget_options (under $25k)       → 5 courses
✅ search_guidance (student visa)        → PDF guidance results
✅ search_provider_info (facilities)     → PDF university info
```

### 2.6 Directory Structure
```
api/
├── storage/           ✅ Storage layer (DuckDB + Vector)
│   ├── __init__.py
│   ├── schema.py      ✅ Database schemas
│   ├── duckdb_store.py ✅ Structured data storage (updated with limit params)
│   └── vectorstore.py  ✅ Hierarchical vector store for PDFs
├── loaders/           ✅ Data loading
│   ├── __init__.py
│   └── csv_loader.py   ✅ CSV loader
├── query/             ✅ Query Intelligence - PHASE 1 COMPLETE
│   ├── __init__.py
│   ├── classifier.py   ✅ Query classification + intent detection
│   ├── entity_extractor.py ✅ Entity extraction (fields, prices, locations)
│   └── sql_builder.py  ✅ Dynamic SQL query building
├── tools/             ✅ Tool System - PHASE 2 COMPLETE
│   ├── __init__.py
│   ├── structured_tools.py ✅ 6 structured data tools
│   └── semantic_tools.py   ✅ 2 semantic search tools
├── retrieval/         ❌ Created (empty - needs implementation)
│   └── __init__.py
└── embeddings.py      ✅ UPGRADED - Removed unused similarity_search()
```

### 2.7 Dependencies Installed
```bash
✅ duckdb==1.4.0          # Structured data storage
✅ pandas==2.3.3          # Data processing
✅ numpy (already had)     # Numeric operations
✅ django (already had)    # Web framework
✅ langchain (already had) # LLM framework
✅ chromadb (already had)  # Vector database
```

### 2.8 Code Improvements
**File:** `api/embeddings.py`
- ✅ **REMOVED:** Unused `similarity_search()` method (was confusing, never called)
- ✅ **CLEANED:** Now purely handles embedding generation
- ✅ **SIMPLIFIED:** 49 lines → 29 lines

---

## 3. What Remains To Be Built ❌

### ~~Phase 1: Query Intelligence Layer~~ ✅ COMPLETED

**Status:** Phase 1 is fully implemented and tested. See section 2.4 for details.

**Test Command:**
```bash
python test_phase1.py  # Tests all classification, extraction, and SQL building
```

---

### ~~Phase 2: Tool System~~ ✅ COMPLETED

**Status:** Phase 2 is fully implemented and tested. See section 2.5 for details.

**Components Built:**
- ✅ 6 structured data tools (search_courses, compare_providers, get_provider_details, get_scholarships, get_intakes, get_budget_options)
- ✅ 2 semantic search tools (search_guidance, search_provider_info)
- ✅ Proper Pydantic schemas for all tools
- ✅ Error handling and formatted output
- ✅ All tools tested and working

**Test Command:**
```bash
python test_phase2.py  # Tests all 8 tools
```

---

### Phase 3: Hybrid Retrieval System (15% of work)

#### 3.1 Hybrid Retriever
**File to create:** `api/retrieval/hybrid_retriever.py`

**Purpose:** Merge structured + semantic results with reranking

```python
class HybridRetriever:
    def retrieve(parsed_query: ParsedQuery) -> List[HybridResult]:
        # 1. Get structured results (courses from SQL)
        # 2. Get semantic results (guidance from vector DB)
        # 3. Enrich courses with provider context from PDFs
        # 4. Merge both result types
        # 5. Rerank by relevance using LLM
        # 6. Return top 10
```

**Reranking Methods:**
- Cross-encoder (LLM-based)
- Relevance scoring
- Diversity filtering

---

### Phase 4: Enhanced Agent (20% of work)

#### 4.1 New Agent with Routing
**File to create:** `api/agent_v2.py`

**Purpose:** Route queries to appropriate pipeline

```python
class StudyNetCounselorAgent:
    def process_query(query: str, session_id: str) -> Dict:
        # 1. Classify query
        parsed = classifier.classify(query)

        # 2. Route to handler
        if parsed.type == STRUCTURED:
            return handle_structured(parsed)
        elif parsed.type == SEMANTIC:
            return handle_semantic(parsed)
        else:  # HYBRID
            return handle_hybrid(parsed)
```

**Handlers:**
- `handle_structured()` - Use SQL tools directly
- `handle_semantic()` - Use vector search
- `handle_hybrid()` - Use hybrid retriever

---

### Phase 5: API Integration (10% of work)

#### 5.1 Update Views
**File to modify:** `api/views.py`

**Changes Needed:**
```python
# Update QueryProcessView to use agent_v2
from .agent_v2 import StudyNetCounselorAgent

class QueryProcessView(APIView):
    def post(self, request):
        # Use new agent instead of old one
        result = StudyNetCounselorAgent().process_query(
            query=request.data['query'],
            session_id=request.data.get('session_id')
        )
```

---

### Phase 6: Testing & Documentation (15% of work)

#### 6.1 Test Queries
**Create:** `test_queries.py`

**Test Cases:**
```python
# Structured
"Show me IT courses under $20k in Sydney"
"Find Business courses between 15k and 25k"
"Compare Macquarie and UNSW for Engineering"

# Semantic
"How do I apply for a student visa?"
"What documents do I need for application?"

# Hybrid
"Best AI courses with scholarships in Melbourne"
"Cheap IT courses with good job prospects"
```

#### 6.2 Performance Testing
- Query response time
- Database query optimization
- Vector search speed
- Memory usage

---

## 4. Architecture Overview

### Current State

```
┌──────────────────────────────────────────┐
│         STUDENT QUERY                     │
│    "IT courses under $20k in Sydney"      │
└──────────────────┬───────────────────────┘
                   │
            ┌──────▼──────┐
            │ OLD AGENT   │  ← Still using this
            │ (agent.py)  │
            └──────┬──────┘
                   │
      ┌────────────▼────────────┐
      │   Vector Search Only     │
      │   (treats CSV as text)   │  ❌ PROBLEM
      └─────────────────────────┘
```

### Target State (50% Complete - Phase 1 Done)

```
┌──────────────────────────────────────────┐
│         STUDENT QUERY                     │
│    "IT courses under $20k in Sydney"      │
└──────────────────┬───────────────────────┘
                   │
          ┌────────▼─────────┐
          │ Query Classifier  │  ✅ DONE (Phase 1)
          │ (classifier.py)   │
          └────────┬─────────┘
                   │
       ┌───────────▼───────────┐
       │   Intent: STRUCTURED   │  ✅ DONE
       │   Entities:            │  ✅ DONE
       │    - Field: IT         │
       │    - MaxPrice: 20000   │
       │    - Location: Sydney  │
       └───────────┬───────────┘
                   │
    ┌──────────────▼──────────────┐
    │   SQL Query Builder          │  ✅ DONE (Phase 1)
    │   (sql_builder.py)           │
    └──────────────┬──────────────┘
                   │
    ┌──────────────▼──────────────┐
    │   DuckDB Store               │  ✅ DONE (Foundation)
    │   (duckdb_store.py)          │
    │   - search_courses()         │
    │   - filter_by_budget()       │
    │   - compare_providers()      │
    └──────────────┬──────────────┘
                   │
              [5 IT courses]
                   │
    ┌──────────────▼──────────────┐
    │   Agent V2 + Tools           │  ❌ TO BUILD (Phase 2-4)
    │   Response Formatter         │
    └─────────────────────────────┘
```

### Data Relationships

```
Providers (97)
    │
    ├──┐ provider_id
    │  │
    │  ├─→ Campus_Locations (499)  ← Has CITY/STATE for filtering
    │  │
    │  ├─→ Courses (9,999)         ← Main search target
    │  │       │
    │  │       └─→ Fees (4,281)    ← Price filtering
    │  │
    │  └─→ Intakes (6,999)         ← Application deadlines
```

---

## 5. How To Continue Development

### Step 1: Set Up Environment

```bash
# Navigate to project
cd "Studynet-AI-Agent"

# Activate virtual environment
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Verify data is loaded
python -c "from api.storage.duckdb_store import get_duckdb_store; print(get_duckdb_store().get_table_stats())"
```

**Expected Output:**
```
{'providers': 97, 'campus_locations': 499, 'courses': 9999, 'fees': 4281, 'intakes': 6999}
```

### Step 2: Build Query Classifier (Start Here!)

**File:** `api/query/classifier.py`

```python
# Template to start with:
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from langchain_openai import AzureChatOpenAI
from ..config import config

class QueryType(Enum):
    STRUCTURED = "structured"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    COMPARISON = "comparison"

class Intent(Enum):
    SEARCH_COURSES = "search_courses"
    GET_GUIDANCE = "get_guidance"
    COMPARE_PROVIDERS = "compare_providers"

class Entity(BaseModel):
    type: str  # field_of_study, price_range, location, etc.
    value: str
    normalized_value: any
    confidence: float

class ParsedQuery(BaseModel):
    original_query: str
    query_type: QueryType
    intent: Intent
    entities: List[Entity]
    filters: dict

class QueryClassifier:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=config.CHAT_MODEL_DEPLOYMENT,
            # ... config
        )

    def classify(self, query: str) -> ParsedQuery:
        # TODO: Implement
        # 1. Use LLM to detect intent
        # 2. Extract entities
        # 3. Determine query type
        # 4. Build filters dict
        pass
```

**Test It:**
```python
# test_classifier.py
from api.query.classifier import QueryClassifier

classifier = QueryClassifier()
result = classifier.classify("Show me IT courses under $20k in Sydney")

print(f"Type: {result.query_type}")
print(f"Intent: {result.intent}")
print(f"Entities: {result.entities}")
print(f"Filters: {result.filters}")
```

### Step 3: Build Entity Extractor

**File:** `api/query/entity_extractor.py`

**Start with Price Extraction (Easiest):**
```python
import re
from typing import Optional

class PriceExtractor:
    PATTERNS = [
        r'under \$?(\d+)k?',
        r'less than \$?(\d+)k?',
        r'below \$?(\d+)k?',
    ]

    def extract(self, query: str) -> Optional[dict]:
        for pattern in self.PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                value = self._parse_value(match.group(1))
                return {'min': 0, 'max': value}
        return None

    def _parse_value(self, value: str) -> float:
        if value.endswith('k'):
            return float(value[:-1]) * 1000
        return float(value)
```

**Test It:**
```python
extractor = PriceExtractor()
print(extractor.extract("courses under $20k"))
# Output: {'min': 0, 'max': 20000.0}
```

### Step 4: Build Structured Tools

**File:** `api/tools/structured_tools.py`

```python
from langchain.tools import Tool
from ..storage.duckdb_store import get_duckdb_store
import json

def create_structured_tools():
    db = get_duckdb_store()

    def search_courses_tool(input_json: str) -> str:
        filters = json.loads(input_json)
        results = db.search_courses(**filters)

        # Format results as string
        output = f"Found {len(results)} courses:\n\n"
        for i, course in enumerate(results[:5], 1):
            output += f"{i}. {course['course_name']}\n"
            output += f"   Provider: {course['provider_name']}\n"
            output += f"   Fee: ${course['total_annual_fee']:,.2f}\n\n"
        return output

    return [
        Tool(
            name="search_courses",
            func=search_courses_tool,
            description="Search for courses with filters"
        )
    ]
```

### Step 5: Build Hybrid Retriever

**File:** `api/retrieval/hybrid_retriever.py`

```python
from ..storage.duckdb_store import get_duckdb_store
from ..vectorstore import vector_store

class HybridRetriever:
    def __init__(self):
        self.db = get_duckdb_store()
        self.vector_store = vector_store

    def retrieve(self, parsed_query):
        if parsed_query.query_type == QueryType.STRUCTURED:
            return self._structured_only(parsed_query)
        elif parsed_query.query_type == QueryType.SEMANTIC:
            return self._semantic_only(parsed_query)
        else:
            return self._hybrid(parsed_query)
```

### Step 6: Build New Agent

**File:** `api/agent_v2.py`

```python
from .query.classifier import QueryClassifier
from .retrieval.hybrid_retriever import HybridRetriever

class StudyNetCounselorAgent:
    def __init__(self):
        self.classifier = QueryClassifier()
        self.retriever = HybridRetriever()

    def process_query(self, query: str, session_id: str = None):
        # 1. Classify
        parsed = self.classifier.classify(query)

        # 2. Retrieve
        results = self.retriever.retrieve(parsed)

        # 3. Format response
        return self._format_response(results, parsed)
```

### Step 7: Update API Views

**File:** `api/views.py`

```python
# Add import at top
from .agent_v2 import StudyNetCounselorAgent

# In QueryProcessView.post():
# REPLACE:
result = rag_agent.process_query(...)

# WITH:
agent_v2 = StudyNetCounselorAgent()
result = agent_v2.process_query(
    query=serializer.validated_data['query'],
    session_id=serializer.validated_data.get('session_id')
)
```

### Step 8: Test End-to-End

```bash
# Start server
python manage.py runserver

# Test query
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me IT courses under $20k in Sydney"}'
```

---

## 6. Testing Guide

### Test Data Loading

```bash
# Reload data (if needed)
python load_csv_data.py

# Verify counts
python -c "
from api.storage.duckdb_store import get_duckdb_store
db = get_duckdb_store()
print(db.get_table_stats())
"
```

### Test Database Queries

```python
from api.storage.duckdb_store import get_duckdb_store

db = get_duckdb_store()

# Test 1: Search by budget
results = db.get_courses_by_budget(0, 25000, limit=5)
print(f"Found {len(results)} courses under $25k")

# Test 2: Compare providers
results = db.compare_providers([
    'Macquarie University',
    'Charles Sturt University'
])
for provider in results:
    print(f"{provider['provider_name']}: {provider['total_courses']} courses")

# Test 3: Get scholarships
results = db.get_scholarships()
print(f"Found {len(results)} providers with scholarships")
```

### Test Vector Store (Existing)

```python
from api.vectorstore import vector_store

# Should still work for PDFs
results = vector_store.similarity_search_with_score(
    "how to apply for visa",
    k=3
)
print(f"Found {len(results)} guidance documents")
```

---

## 7. Troubleshooting

### Issue: Data not loading

```bash
# Clear database and reload
rm -f data/studynet.duckdb
python load_csv_data.py
```

### Issue: Import errors

```bash
# Ensure you're in virtual environment
venv\Scripts\activate

# Reinstall if needed
pip install duckdb pandas
```

### Issue: Unicode errors in Windows CMD

**Solution:** The data loads fine, just the checkmark emojis don't display. Use PowerShell instead:
```powershell
python load_csv_data.py
```

### Issue: Query returns no results

**Check:**
1. Is data loaded? `python -c "from api.storage.duckdb_store import get_duckdb_store; print(get_duckdb_store().get_table_stats())"`
2. Are filters too strict? Try broader search
3. Check available cities/fields in database (see Step 1 test queries)

---

## 8. Key Files Reference

### Completed Files
```
api/storage/schema.py          - Database schemas ✅
api/storage/duckdb_store.py    - Structured data layer ✅
api/loaders/csv_loader.py      - CSV loader ✅
load_csv_data.py               - Loading script ✅
ARCHITECTURE_V2.md             - Full architecture ✅
INSTRUCTIONS.md                - This file ✅
```

### Files To Create
```
api/query/classifier.py        - Query classification ❌
api/query/entity_extractor.py - Entity extraction ❌
api/query/sql_builder.py       - SQL generation ❌
api/tools/structured_tools.py  - Course search tools ❌
api/tools/semantic_tools.py    - Guidance search tools ❌
api/retrieval/hybrid_retriever.py - Hybrid merger ❌
api/agent_v2.py                - New routing agent ❌
test_queries.py                - Test suite ❌
```

### Files To Modify
```
api/views.py                   - Switch to agent_v2 ❌
api/vectorstore.py            - Filter to PDFs only ❌
```

---

## 9. Development Workflow

### Daily Workflow

1. **Morning:** Review previous day's work
2. **Focus:** Pick ONE component from "Files To Create"
3. **Build:** Implement with tests
4. **Test:** Verify it works in isolation
5. **Integrate:** Connect to existing system
6. **Commit:** Save progress

### Recommended Order

1. **Week 1:** Query Intelligence Layer
   - Day 1-2: QueryClassifier
   - Day 3-4: EntityExtractor
   - Day 5: SQLBuilder

2. **Week 2:** Tool System
   - Day 1-3: Structured tools
   - Day 4-5: Semantic tools

3. **Week 3:** Integration
   - Day 1-2: HybridRetriever
   - Day 3-4: Agent v2
   - Day 5: Update views

4. **Week 4:** Testing & Polish
   - Day 1-3: End-to-end testing
   - Day 4-5: Performance optimization

---

## 10. Success Criteria

### Phase Complete When:

✅ **Foundation (DONE):**
- [x] Database schema created
- [x] 21,875 rows loaded
- [x] SQL queries working
- [x] Architecture documented

⬜ **Intelligence Layer:**
- [ ] Classifier correctly identifies query types
- [ ] Entity extractor pulls out fields, prices, locations
- [ ] SQL builder generates valid queries

⬜ **Tool System:**
- [ ] 6+ structured tools implemented
- [ ] Tools return formatted results
- [ ] Agent can call tools

⬜ **Integration:**
- [ ] Hybrid retriever merges results
- [ ] Agent v2 routes queries correctly
- [ ] API endpoints use new system

⬜ **Testing:**
- [ ] 10+ test queries pass
- [ ] Response time < 3 seconds
- [ ] No errors in logs

---

## 11. Questions & Support

### Common Questions

**Q: Where is the database file?**
A: `./data/studynet.duckdb` (created when you run `load_csv_data.py`)

**Q: How do I reload data?**
A: `rm data/studynet.duckdb && python load_csv_data.py`

**Q: Can I use the old agent while building new one?**
A: Yes! The old system still works. Build new system in parallel.

**Q: What if I want to add a new CSV column?**
A:
1. Update `api/storage/schema.py` (add column to table)
2. Update `api/storage/schema.py` (add to column map)
3. Delete database: `rm data/studynet.duckdb`
4. Reload: `python load_csv_data.py`

**Q: How do I debug SQL queries?**
A:
```python
from api.storage.duckdb_store import get_duckdb_store
db = get_duckdb_store()

# Your query
sql = "SELECT * FROM courses WHERE course_name LIKE ?"
results = db.execute(sql, ['%Bachelor%'])
print(results)
```

---

## 12. Next Steps After Completion

### Future Enhancements

1. **Advanced Features:**
   - Course recommendations based on student profile
   - Scholarship eligibility calculator
   - Application deadline notifications
   - Course comparison side-by-side

2. **Performance:**
   - Cache frequent queries
   - Pre-compute popular searches
   - Add full-text search indexes

3. **Data:**
   - Add more CSVs (English requirements, prerequisites)
   - Update data automatically from CRM
   - Add historical trend data

4. **UI/UX:**
   - Interactive course filtering
   - Map view of campuses
   - Cost calculator
   - Application checklist generator

---

## Contact & Resources

**Architecture Document:** [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md)

**Database Location:** `./data/studynet.duckdb`

**Test Data:** `./pdfs/*.csv`

**Vector Store:** `./vector_store/` (existing, for PDFs)

---

**Remember:** You have a solid foundation. The structured data layer is DONE and WORKING. Now build the intelligence layer on top of it, one component at a time. Start with the QueryClassifier and work your way up!

Good luck! 🚀
