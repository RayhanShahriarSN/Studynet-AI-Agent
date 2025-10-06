# Migration and Testing Guide

## 🎯 Pre-Migration Checklist

- [ ] All your PDF/DOC files are in `pdfs/` folder
- [ ] All your CSV files are in `pdfs/` folder
- [ ] Dependencies updated in requirements.txt
- [ ] `.env` file configured with Azure OpenAI keys

---

## 📦 Step 1: Install Dependencies

```bash
cd Studynet-AI-Agent
pip install -r requirements.txt
```

**New packages being installed:**
- `docling==2.9.2` - Better document processing
- `rank-bm25==0.2.2` - Keyword search
- `sentence-transformers==3.3.1` - Cross-encoder reranking
- `pandasql==0.7.3` - SQL on DataFrames

---

## 🗄️ Step 2: Create Database Migrations

```bash
python manage.py makemigrations
```

**Expected output:**
```
Migrations for 'api':
  api/migrations/0002_queryanalytics_datasourcestats_csvupload_agentinteraction.py
    - Create model QueryAnalytics
    - Create model DataSourceStats
    - Create model CSVUpload
    - Create model AgentInteraction
```

---

## 🔄 Step 3: Run Migrations

```bash
python manage.py migrate
```

**Expected output:**
```
Running migrations:
  Applying api.0002_queryanalytics_datasourcestats... OK
```

---

## 📚 Step 4: Load Knowledge Base

**IMPORTANT:** Knowledge base must be loaded manually using the `load_kb.py` script.

```bash
python load_kb.py
```

**What happens:**
```
======================================================================
KNOWLEDGE BASE LOADER
======================================================================

======================================================================
HARD KNOWLEDGE BASE (pdfs/)
======================================================================

📄 Found 3 document(s)
   📥 CRM_Overview.pdf                       [LOADING...]
      ✅ Embedded 45 chunks
   📥 Application_Management.pdf             [LOADING...]
      ✅ Embedded 38 chunks
   📥 Leads_Management_Guide.pdf             [LOADING...]
      ✅ Embedded 29 chunks

   Summary: 3 loaded, 0 skipped

📊 Found 2 CSV file(s)
   📥 01_SN_Provider_Data.csv                [LOADING...]
      ✅ Created table 'sn_provider_data' with 150 rows
   📥 05_SN_Fees.csv                         [LOADING...]
      ✅ Created table 'sn_fees' with 89 rows

   Summary: 2 loaded, 0 skipped

📊 Hard KB Summary: 3 documents, 2 CSVs

======================================================================
USER UPLOADS (uploaded_docs/)
======================================================================
ℹ️  No uploads folder found
   Creating folder for future uploads...

======================================================================
FINAL STATISTICS
======================================================================

📊 VECTOR STORE:
   Parent chunks: 112
   Child chunks:  336
   Documents:     3

📊 SQL ENGINE:
   Tables:        2
   Table names:   sn_provider_data, sn_fees

📊 SOURCE BREAKDOWN:
   Hard KB:       3 documents, 2 CSVs
   User uploads:  0 documents, 0 CSVs
======================================================================
✅ LOADING COMPLETE!
======================================================================
```

**This process takes 2-5 minutes depending on file count.**

### Additional Loading Options

```bash
# Load only hard knowledge base (pdfs/ folder)
python load_kb.py --hard-kb-only

# Load only user uploads (uploaded_docs/ folder)
python load_kb.py --uploads-only

# Force reload all files (ignore tracking)
python load_kb.py --force
```

**⚡ Smart Tracking:** The script tracks all loaded files in the database. On subsequent runs, it will skip already-loaded files unless you use `--force`.

---

## 🚀 Step 5: Start the Server

Now you can start the Django server (it will start quickly):

```bash
python manage.py runserver
```

Server should start in ~2-3 seconds since knowledge base is already loaded.

---

## ✅ Step 6: Verify Initialization

### 6.1 Check Vector Store
```bash
curl http://localhost:8000/api/knowledge-base/status/
```

**Expected:**
```json
{
  "status": "active",
  "parent_chunks": 112,
  "child_chunks": 336,
  "total_documents": 448
}
```

### 5.2 Check SQL Tables
```bash
curl http://localhost:8000/api/analytics/sources/
```

**Expected:**
```json
{
  "total_sources": 5,
  "csv_tables": 2,
  "documents": 3,
  "sources": [...]
}
```

---

## 🧪 Step 6: Test Core Functionality

### Test 1: RAG Query (Document Search)
```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I add a lead in the CRM?"
  }'
```

**Expected Response:**
```json
{
  "answer": "To add a lead in the CRM: 1. Go to **Add Leads** section...",
  "sources": [...],
  "classification": {
    "query_type": "semantic_rag",
    "requires_rag": true
  },
  "rag_used": true,
  "sql_used": false
}
```

---

### Test 2: SQL Query (Data Retrieval)
```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many providers are in the database?"
  }'
```

**Expected Response:**
```json
{
  "answer": "There are 150 providers in the database.",
  "classification": {
    "query_type": "structured_sql",
    "requires_sql": true
  },
  "sql_used": true,
  "rag_used": false,
  "tools_used": ["sql_query"]
}
```

---

### Test 3: Hybrid Query (SQL + RAG)
```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all providers and explain how to contact them"
  }'
```

**Expected Response:**
```json
{
  "answer": "Here are the providers: [SQL results]... To contact them: [RAG answer]...",
  "classification": {
    "query_type": "hybrid"
  },
  "sql_used": true,
  "rag_used": true,
  "hybrid_mode": true,
  "tools_used": ["sql_query", "rag_search"]
}
```

---

### Test 4: CSV Upload
```bash
curl -X POST http://localhost:8000/api/upload/csv/ \
  -F "file=@test_data.csv" \
  -F "table_name=test_table" \
  -F "uploaded_by=admin"
```

**Expected Response:**
```json
{
  "status": "success",
  "table_name": "test_table",
  "row_count": 25,
  "column_count": 5,
  "columns": ["id", "name", "email", "city", "status"]
}
```

**Verification:**
- File saved to `uploaded_docs/test_data.csv`
- Table available in SQL: `SELECT * FROM test_table`
- Tracked in DataSourceStats model

---

### Test 5: Document Upload
```bash
curl -X POST http://localhost:8000/api/upload/document/ \
  -F "file=@my_manual.pdf"
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Document my_manual.pdf processed successfully",
  "chunks_created": 15
}
```

**Verification:**
- File saved to `uploaded_docs/my_manual.pdf` (for permanent storage)
- Embeddings added to vector store
- Immediately searchable via RAG queries

---

## 🔄 Step 7: Test Server Restart Persistence

```bash
# Stop server (Ctrl+C)
# Restart server
python manage.py runserver
```

**Expected on restart:**
```
[INFO] Django app ready - initializing knowledge base...
============================================================
STARTING KNOWLEDGE BASE INITIALIZATION
============================================================
✓ Directories verified

[HARD KNOWLEDGE BASE]
✓ Hard KB already initialized (skipping)

📊 KNOWLEDGE BASE STATS:
   Vector Store: 112 parent chunks, 336 child chunks
   SQL Tables: 3 tables (sn_provider_data, sn_fees, test_table)
============================================================
INITIALIZATION COMPLETE
============================================================
```

**Notice:**
- ✅ Initialization is INSTANT (skipped)
- ✅ All data still available
- ✅ User uploads included (test_table)

---

## 📊 Step 8: Test Analytics Endpoints

### Query Analytics
```bash
curl "http://localhost:8000/api/analytics/queries/?days=7"
```

### Source Statistics
```bash
curl http://localhost:8000/api/analytics/sources/
```

### System Report
```bash
curl http://localhost:8000/api/reports/system/
```

### Usage Report
```bash
curl "http://localhost:8000/api/reports/usage/?days=7"
```

---

## 🔍 Step 9: SQL Export Test

```bash
curl -X POST http://localhost:8000/api/export/sql/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM sn_provider_data LIMIT 10",
    "format": "csv",
    "filename": "providers_export"
  }' \
  --output providers_export.csv
```

---

## ⚠️ Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'docling'"
**Solution:**
```bash
pip install docling==2.9.2 docling-core==2.6.3
```

### Issue: "Vector store is empty"
**Solution:**
```bash
# Force reload
curl -X POST http://localhost:8000/api/knowledge-base/reload/
```

### Issue: "SQL table not found"
**Solution:**
1. Check file is in `pdfs/` or `uploaded_docs/`
2. Restart server to trigger initialization
3. Check logs for loading errors

### Issue: "Initialization takes too long"
**Normal:** First load takes 2-5 minutes for:
- 3-5 PDFs: ~2 minutes
- 10+ PDFs: ~5 minutes
- Subsequent starts: Instant (skipped)

---

## ✅ Success Criteria

You'll know everything is working when:

- [x] First startup shows initialization log
- [x] Subsequent startups skip initialization (instant)
- [x] RAG queries return document-based answers
- [x] SQL queries execute on CSV data
- [x] Hybrid queries use both SQL + RAG
- [x] Uploads work and survive restart
- [x] Analytics endpoints return data
- [x] Export endpoint downloads files

---

## 🎯 Next Steps

1. **Test with your actual data**
   - Put your PDFs in `pdfs/`
   - Put your CSVs in `pdfs/`
   - Run first startup

2. **Test frontend integration**
   - Upload CSV from frontend
   - Upload PDF from frontend
   - Query both types

3. **Monitor analytics**
   - Check query types
   - Review tool usage
   - Monitor performance

---

## 📞 Support

If you encounter issues:
1. Check Django logs for errors
2. Verify `.env` configuration
3. Ensure all files in `pdfs/` are readable
4. Check database migrations are applied
5. Verify vector_store/ folder permissions

**The system is designed to:**
- ✅ Load once, use forever
- ✅ Survive server restarts
- ✅ Auto-handle user uploads
- ✅ Never re-process same files
