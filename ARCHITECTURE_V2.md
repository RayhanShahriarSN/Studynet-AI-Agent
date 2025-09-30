# StudyNet AI Counselor - Architecture V2

## Overview
Enhanced RAG architecture for StudyNet counselor AI agent that handles both structured data (CSV) and unstructured data (PDF) with intelligent query routing.

## Data Sources

### CSV Data (Structured - 5 files)
1. **Providers** (1,029 rows) - Universities/Colleges
2. **Campus Locations** (701 rows) - **CRITICAL: Contains city/state for location filtering**
3. **Courses** (44,634 rows) - **MAIN TABLE: Course catalog**
4. **Fees** (4,291 rows) - Course pricing information
5. **Intakes** (7,000 rows) - Application deadlines and intake dates

### PDF Data (Unstructured)
- Application guides
- CRM documentation
- Lead management guides

## Key Relationships

```
Providers (PROVIDERID)
    ↓
    ├── Campus_Locations (address_city, address_state) → Location filtering
    ├── Courses (course details, requirements)
    ├── Fees (pricing)
    └── Intakes (deadlines)

Courses (COURSEID)
    ↓
    └── Fees (pricing per course)
```

## Architecture Components

### 1. Dual Storage Layer
- **DuckDB**: Structured CSV data with SQL querying
- **ChromaDB**: Vector embeddings for PDF guidance documents

### 2. Query Classification
- **STRUCTURED**: "courses under $20k", "IT programs in Sydney"
- **SEMANTIC**: "how to apply?", "visa requirements"
- **HYBRID**: "best IT courses with scholarships in Melbourne"

### 3. Entity Extraction
Extracts from student queries:
- Field of study → Maps to area_of_study_broad/narrow
- Location (city/state) → Joins with campus_locations
- Price range → Filters on total_annual_fee
- Provider name → Exact match from providers table
- Study level (Bachelor, Master, etc.)

### 4. Intelligent Routing
```
Student Query
    ↓
Query Classifier
    ↓
┌─────────┴─────────┐
│                   │
Structured          Semantic
Query Engine        Search (Vector)
(SQL on DuckDB)     (ChromaDB)
│                   │
└─────────┬─────────┘
          ↓
    Hybrid Merger
          ↓
    Response Generator
```

### 5. Tools for Agent
- **search_courses**: Filter courses by criteria
- **filter_by_budget**: Find courses in price range
- **compare_providers**: Side-by-side university comparison
- **get_provider_details**: Full university information
- **search_by_location**: Find courses in specific cities
- **get_scholarships**: Find scholarship opportunities
- **search_guidance**: Query PDF documents for procedures

## Critical Filters Supported

### By Location (via campus_locations JOIN)
- City: Sydney, Melbourne, Brisbane, etc.
- State: NSW, VIC, QLD, etc.

### By Price (via fees table)
- Annual fee range
- Total course fee range
- Budget comparisons

### By Study Area (via courses table)
- Broad: IT, Business, Engineering, etc.
- Narrow: Software Engineering, Accounting, etc.
- Detailed: AI, Cybersecurity, etc.

### By Provider (via providers table)
- University name
- Ranking (Australian/Global)
- Public/Private
- Facilities

### By Requirements
- IELTS scores
- TOEFL scores
- Duolingo scores
- Has scholarship
- Has internship

## Example Query Flows

### Example 1: "Show me IT courses under $20k in Sydney"
1. **Classify**: HYBRID (structured + semantic)
2. **Extract Entities**:
   - field: "Information Technology"
   - max_price: 20000
   - location: "Sydney"
3. **SQL Query**:
   ```sql
   SELECT c.*, f.total_annual_fee, l.address_city
   FROM courses c
   JOIN fees f ON c.course_id = f.course_id
   JOIN campus_locations l ON c.provider_id = l.provider_id
   WHERE c.area_of_study_broad LIKE '%Information Technology%'
   AND f.total_annual_fee <= 20000
   AND l.address_city = 'Sydney'
   AND c.is_active = TRUE
   ORDER BY f.total_annual_fee ASC
   ```
4. **Enrich** with provider details and guidance docs
5. **Format** as student-friendly response

### Example 2: "Compare Macquarie and UNSW for Business courses"
1. **Classify**: COMPARISON
2. **Extract**: providers = ["Macquarie University", "UNSW"]
3. **SQL**: Compare course counts, fees, rankings
4. **Response**: Side-by-side table

### Example 3: "How do I apply for a student visa?"
1. **Classify**: SEMANTIC
2. **Vector Search**: PDF guidance documents
3. **Response**: Procedural information from PDFs

## Implementation Files

```
api/
├── storage/
│   ├── duckdb_store.py         # SQL database for CSVs
│   ├── vectorstore.py          # ChromaDB (existing, modified)
│   └── schema.py               # Database schemas
├── query/
│   ├── classifier.py           # Query type classification
│   ├── entity_extractor.py    # Extract entities from queries
│   └── sql_builder.py          # Build SQL from entities
├── tools/
│   ├── structured_tools.py     # Tools for SQL queries
│   └── semantic_tools.py       # Tools for vector search
├── retrieval/
│   └── hybrid_retriever.py     # Merge structured + semantic
├── loaders/
│   └── csv_loader.py           # Load CSVs into DuckDB
└── agent_v2.py                 # Enhanced agent with routing
```

## Migration Path
1. Keep existing PDF vector store
2. Add DuckDB for CSV data
3. Add query classification layer
4. Add structured query tools
5. Update agent to use both systems
6. Gradually deprecate old CSV embedding approach
