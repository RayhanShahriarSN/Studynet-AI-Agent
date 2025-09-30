# StudyNet AI Counselor - Development Instructions

**Last Updated:** 2025-10-01
**Status:** Foundation Complete (30%), Architecture Designed (100%)
**Next Phase:** Implement Query Intelligence Layer

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

### 2.4 Directory Structure Created
```
api/
├── storage/           ✅ Storage layer (DuckDB + Vector)
│   ├── __init__.py
│   ├── schema.py      ✅ Database schemas
│   ├── duckdb_store.py ✅ Structured data storage
│   └── vectorstore.py  ✅ Exists (needs modification for PDFs only)
├── loaders/           ✅ Data loading
│   ├── __init__.py
│   └── csv_loader.py   ✅ CSV loader
├── query/             ✅ Created (empty - needs implementation)
│   └── __init__.py
├── tools/             ✅ Created (empty - needs implementation)
│   └── __init__.py
├── retrieval/         ✅ Created (empty - needs implementation)
│   └── __init__.py
└── embeddings.py      ✅ UPGRADED - Removed unused similarity_search()
```

### 2.5 Dependencies Installed
```bash
✅ duckdb==1.4.0          # Structured data storage
✅ pandas==2.3.3          # Data processing
✅ numpy (already had)     # Numeric operations
✅ django (already had)    # Web framework
✅ langchain (already had) # LLM framework
✅ chromadb (already had)  # Vector database
```

### 2.6 Code Improvements
**File:** `api/embeddings.py`
- ✅ **REMOVED:** Unused `similarity_search()` method (was confusing, never called)
- ✅ **CLEANED:** Now purely handles embedding generation
- ✅ **SIMPLIFIED:** 49 lines → 29 lines

---

## 3. What Remains To Be Built ❌

### Phase 1: Query Intelligence Layer (Critical - 20% of work)

#### 3.1 Query Classifier
**File to create:** `api/query/classifier.py`

**Purpose:** Analyze student queries and classify them

**Required Components:**
```python
class QueryType(Enum):
    STRUCTURED  # "courses under $20k"
    SEMANTIC    # "how to apply?"
    HYBRID      # "best IT courses with scholarships"
    COMPARISON  # "compare Macquarie vs UNSW"

class QueryClassifier:
    def classify(query: str) -> ParsedQuery:
        # 1. Detect intent (search, compare, guidance)
        # 2. Extract entities (see 3.2)
        # 3. Determine query type
        # 4. Return structured ParsedQuery object
```

**Dependencies:**
- LLM for intent detection
- Pattern matching for query types

#### 3.2 Entity Extractor
**File to create:** `api/query/entity_extractor.py`

**Purpose:** Extract structured data from natural language queries

**Required Extractions:**
```python
class EntityExtractor:
    # 1. Field of Study
    #    Input: "IT courses" / "Business programs" / "AI"
    #    Output: ["Information Technology", "Computing"]

    # 2. Price Range
    #    Input: "under $20k" / "between 15k and 25k"
    #    Output: {min: 0, max: 20000}

    # 3. Location
    #    Input: "Sydney" / "Melbourne" / "NSW"
    #    Output: {city: "Sydney", state: "NSW"}

    # 4. Provider Name
    #    Input: "Macquarie" / "UNSW"
    #    Output: "Macquarie University"

    # 5. Study Level
    #    Input: "Bachelor" / "Master's"
    #    Output: "Bachelor Degree"

    # 6. Requirements
    #    Input: "with scholarships" / "has internship"
    #    Output: {has_scholarship: True}
```

**Field Mappings Needed:**
```python
FIELD_MAPPINGS = {
    'IT': ['Information Technology', 'Computer Science', 'Computing'],
    'AI': ['Artificial Intelligence', 'Data Science', 'Machine Learning'],
    'business': ['Business', 'Commerce', 'Accounting'],
    'engineering': ['Engineering', 'Civil Engineering', ...],
    # ... 50+ mappings
}

AUSTRALIAN_CITIES = [
    'Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide',
    'Canberra', 'Hobart', 'Darwin', 'Gold Coast', ...
]

PROVIDER_ALIASES = {
    'UNSW': 'University of New South Wales',
    'UTS': 'University of Technology Sydney',
    'Macquarie': 'Macquarie University',
    # ... all providers
}
```

#### 3.3 SQL Query Builder
**File to create:** `api/query/sql_builder.py`

**Purpose:** Convert extracted entities to SQL queries

```python
class SQLQueryBuilder:
    def build_course_search(entities: List[Entity]) -> (str, List):
        # Build SELECT with JOINs
        # Add WHERE filters dynamically
        # Return (sql, params)
```

### Phase 2: Tool System (20% of work)

#### 3.4 Structured Query Tools
**File to create:** `api/tools/structured_tools.py`

**Required Tools:**
```python
1. search_courses
   - Filters: field, price, location, provider, level, scholarship
   - Returns: List of courses with provider/location/fee info

2. filter_by_budget
   - Input: min_fee, max_fee, optional field
   - Returns: Courses sorted by price

3. compare_providers
   - Input: List of provider names
   - Returns: Side-by-side comparison table

4. get_provider_details
   - Input: Provider name
   - Returns: Full provider info + course count + locations

5. get_scholarships
   - Input: Optional field of study
   - Returns: Providers with scholarship URLs

6. get_upcoming_intakes
   - Input: Provider name, year
   - Returns: Application deadlines
```

#### 3.5 Semantic Search Tools (Enhanced)
**File to create:** `api/tools/semantic_tools.py`

**Modify Existing:** `api/vectorstore.py` to store ONLY PDFs

**Required Tools:**
```python
1. search_guidance
   - Input: Procedural question (how-to, visa, application)
   - Filters: doc_type="guidance_pdf"
   - Returns: Relevant PDF chunks

2. search_provider_info
   - Input: Question about university (facilities, culture, research)
   - Filters: doc_type="provider_profile"
   - Returns: Provider descriptions
```

### Phase 3: Hybrid Retrieval System (15% of work)

#### 3.6 Hybrid Retriever
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

### Phase 4: Enhanced Agent (20% of work)

#### 3.7 New Agent with Routing
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

### Phase 5: API Integration (10% of work)

#### 3.8 Update Views
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

### Phase 6: Testing & Documentation (15% of work)

#### 3.9 Test Queries
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

#### 3.10 Performance Testing
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

### Target State (After Completion)

```
┌──────────────────────────────────────────┐
│         STUDENT QUERY                     │
│    "IT courses under $20k in Sydney"      │
└──────────────────┬───────────────────────┘
                   │
          ┌────────▼─────────┐
          │ Query Classifier  │  ← TO BUILD
          │ (classifier.py)   │
          └────────┬─────────┘
                   │
       ┌───────────▼───────────┐
       │   Intent: STRUCTURED   │
       │   Entities:            │
       │    - Field: IT         │
       │    - MaxPrice: 20000   │
       │    - Location: Sydney  │
       └───────────┬───────────┘
                   │
    ┌──────────────▼──────────────┐
    │   SQL Query Builder          │  ← TO BUILD
    │   (sql_builder.py)           │
    └──────────────┬──────────────┘
                   │
    ┌──────────────▼──────────────┐
    │   DuckDB Store               │  ✅ DONE
    │   (duckdb_store.py)          │
    │   - search_courses()         │
    │   - filter_by_budget()       │
    │   - compare_providers()      │
    └──────────────┬──────────────┘
                   │
              [5 IT courses]
                   │
    ┌──────────────▼──────────────┐
    │   Response Formatter         │  ← TO BUILD
    │   (Format as student-        │
    │    friendly response)        │
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
