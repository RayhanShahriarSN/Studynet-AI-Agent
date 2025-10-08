# Data Loading Guide

## 📁 Two Ways to Load Data

### 1. **Hard Knowledge Base** (Manual - One-time Setup)
   - Location: `pdfs/` folder
   - When: Initial setup or when adding new reference documents
   - Method: Run `load_kb.py` script

### 2. **User Uploads** (Automatic - Via API)
   - Location: `uploaded_docs/` folder
   - When: Users upload from frontend
   - Method: Automatic via API endpoints

---

## 🚀 Method 1: Hard Knowledge Base (Manual Loading)

### Step 1: Place Your Files

Put your files in the `pdfs/` folder:

```
Studynet-AI-Agent/
└── pdfs/
    ├── CRM_Overview.pdf
    ├── User_Guide.docx
    ├── FAQ.txt
    ├── Provider_Data.csv
    └── Fees.csv
```

**Supported formats:**
- **Documents**: `.pdf`, `.docx`, `.doc`, `.txt`, `.html`
- **CSV files**: `.csv`

### Step 2: Run the Loader Script

```bash
# Load everything (documents + CSVs)
python load_kb.py
```

**What happens:**
- ✅ PDFs/DOCX/TXT/HTML → Embedded to vector store
- ✅ CSVs → Loaded as SQL tables
- ✅ Tracked in database (won't reload on next run)

### Advanced Loading Options

```bash
# Load only CSV files
python load_kb.py --csv-only

# Load only documents (skip CSVs)
python load_kb.py --docs-only

# Load only from pdfs/ folder
python load_kb.py --hard-kb-only

# Force reload all files (ignore tracking)
python load_kb.py --force

# Combine options
python load_kb.py --hard-kb-only --csv-only
python load_kb.py --csv-only --force
```

### Example Output

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
   📥 User_Guide.docx                        [LOADING...]
      ✅ Embedded 38 chunks
   📥 FAQ.txt                                [LOADING...]
      ✅ Embedded 12 chunks

   Summary: 3 loaded, 0 skipped

📊 Found 2 CSV file(s)
   📥 Provider_Data.csv                      [LOADING...]
      ✅ Created table 'provider_data' with 150 rows
   📥 Fees.csv                               [LOADING...]
      ✅ Created table 'fees' with 89 rows

   Summary: 2 loaded, 0 skipped

📊 Hard KB Summary: 3 documents, 2 CSVs

======================================================================
FINAL STATISTICS
======================================================================

📊 VECTOR STORE:
   Parent chunks: 95
   Child chunks:  285
   Documents:     3

📊 SQL ENGINE:
   Tables:        2
   Table names:   provider_data, fees

📊 SOURCE BREAKDOWN:
   Hard KB:       3 documents, 2 CSVs
   User uploads:  0 documents, 0 CSVs
======================================================================
✅ LOADING COMPLETE!
======================================================================
```

---

## 🌐 Method 2: User Uploads (Automatic via API)

### Upload Documents (PDF, DOCX, TXT, HTML)

**Endpoint:** `POST /api/upload/document/`

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/upload/document/ \
  -F "file=@/path/to/document.pdf"
```

**Example (JavaScript - Frontend):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/upload/document/', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('Upload successful:', data);
  // Response: { status: "success", chunks_created: 45, file_path: "..." }
});
```

**What happens automatically:**
1. File saved to `uploaded_docs/document.pdf`
2. Processed with Docling (advanced PDF processing)
3. Embedded to vector store
4. Tracked in database
5. **Immediately queryable** - no restart needed

---

### Upload CSV Files

**Endpoint:** `POST /api/upload/csv/`

**Parameters:**
- `file` (required): CSV file
- `table_name` (optional): Custom table name
- `uploaded_by` (optional): Username

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/upload/csv/ \
  -F "file=@/path/to/data.csv" \
  -F "table_name=custom_table_name" \
  -F "uploaded_by=john_doe"
```

**Example (JavaScript - Frontend):**
```javascript
const formData = new FormData();
formData.append('file', csvFileInput.files[0]);
formData.append('table_name', 'sales_data');
formData.append('uploaded_by', 'john_doe');

fetch('http://localhost:8000/api/upload/csv/', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('CSV uploaded:', data);
  // Response: { status: "success", table_name: "sales_data", row_count: 150, ... }
});
```

**What happens automatically:**
1. File saved to `uploaded_docs/data.csv`
2. Loaded as SQL table
3. Tracked in database (CSVUpload + DataSourceStats models)
4. **Immediately queryable via SQL** - no restart needed

---

## 🔄 Smart Tracking System

The system tracks all loaded files in the database to prevent duplicate processing.

### Check What's Already Loaded

```bash
curl http://localhost:8000/api/analytics/sources/
```

**Response:**
```json
{
  "total_sources": 5,
  "sources": [
    {
      "source_name": "CRM_Overview.pdf",
      "source_type": "pdf_document",
      "chunk_count": 45,
      "file_size_kb": 1024
    },
    {
      "source_name": "provider_data",
      "source_type": "csv_table",
      "row_count": 150,
      "columns": ["id", "name", "fee"]
    }
  ]
}
```

### Re-running the Loader

```bash
# Run again - will skip already loaded files
python load_kb.py
```

**Output:**
```
📄 Found 3 document(s)
   ⏭️  CRM_Overview.pdf                       [SKIPPED - already loaded]
   ⏭️  User_Guide.docx                        [SKIPPED - already loaded]
   📥 New_Document.pdf                        [LOADING...]
      ✅ Embedded 28 chunks

   Summary: 1 loaded, 2 skipped
```

### Force Reload All Files

```bash
python load_kb.py --force
```

**Use case:** Database corrupted, vector store cleared, need fresh start

---

## 📊 Folder Structure

```
Studynet-AI-Agent/
├── pdfs/                          # Hard knowledge base (put files here manually)
│   ├── CRM_Overview.pdf           → Embedded to vector store
│   ├── User_Guide.docx            → Embedded to vector store
│   ├── FAQ.txt                    → Embedded to vector store
│   ├── Provider_Data.csv          → Loaded as SQL table 'provider_data'
│   └── Fees.csv                   → Loaded as SQL table 'fees'
│
├── uploaded_docs/                 # User uploads (auto-created via API)
│   ├── report_2024.pdf            → Embedded to vector store (auto)
│   ├── sales_data.csv             → Loaded as SQL table (auto)
│   └── ...
│
├── vector_store/                  # ChromaDB database (auto-managed)
│   ├── parent_store/
│   └── child_store/
│
├── load_kb.py                     # Manual loader script
└── manage.py
```

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Load everything from `pdfs/` | `python load_kb.py` |
| Load only CSVs | `python load_kb.py --csv-only` |
| Load only documents | `python load_kb.py --docs-only` |
| Force reload all | `python load_kb.py --force` |
| Upload via API (document) | `POST /api/upload/document/` |
| Upload via API (CSV) | `POST /api/upload/csv/` |
| Check loaded files | `GET /api/analytics/sources/` |

---

## ⚠️ Important Notes

1. **Hard KB files persist forever** - Place permanent reference docs in `pdfs/`
2. **User uploads persist forever** - Saved to `uploaded_docs/`, survive restarts
3. **No need to reload on restart** - All data is saved in vector store and SQL engine
4. **API uploads are instant** - No manual script needed for frontend uploads
5. **Smart tracking prevents duplicates** - Won't reload same files twice (unless `--force`)

---

## 🧪 Testing Your Setup

### 1. Load Hard KB
```bash
python load_kb.py
```

### 2. Check Status
```bash
curl http://localhost:8000/api/knowledge-base/status/
```

### 3. Test RAG Query
```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What is in the CRM overview?", "session_id": "test-1"}'
```

### 4. Test SQL Query
```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me top 5 providers", "session_id": "test-1"}'
```

### 5. Upload Test File
```bash
curl -X POST http://localhost:8000/api/upload/document/ \
  -F "file=@test.pdf"
```

---

## 🆘 Troubleshooting

### "No documents found"
- ✅ Check files are in `pdfs/` folder
- ✅ Verify file extensions (`.pdf`, `.docx`, `.csv`)

### "Table already exists"
- ℹ️ Normal if running `load_kb.py` multiple times
- ℹ️ Use `--force` to reload

### "Django not setup"
- ✅ Run migrations first: `python manage.py migrate`

### Files not loading via API
- ✅ Check endpoint URL is correct
- ✅ Verify file is attached in `FormData`
- ✅ Check server logs for errors

### Want to clear everything and restart
```bash
# Delete vector store
rm -rf vector_store/

# Clear database tracking
python manage.py shell
>>> from api.models import DataSourceStats, CSVUpload
>>> DataSourceStats.objects.all().delete()
>>> CSVUpload.objects.all().delete()
>>> exit()

# Reload everything
python load_kb.py --force
```
