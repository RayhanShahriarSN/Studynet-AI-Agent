# Quick Start Guide

## 🚀 First Time Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Load knowledge base** (PDFs and CSVs from `pdfs/` folder)
   ```bash
   python load_kb.py
   ```
   ⏱️ Takes 2-5 minutes depending on file count

4. **Start server**
   ```bash
   python manage.py runserver
   ```
   ⚡ Starts in ~2-3 seconds

---

## 📂 Data Management

### Hard Knowledge Base (`pdfs/` folder)

Place your files here:
- **Documents**: `.pdf`, `.docx`, `.doc`, `.txt`, `.html`
- **CSVs**: `.csv` files (will be loaded as SQL tables)

Then run:
```bash
python load_kb.py
```

### User Uploads (`uploaded_docs/` folder)

Files uploaded via the frontend `/api/upload/document/` or `/api/upload/csv/` endpoints are automatically:
- Saved to `uploaded_docs/` folder
- Loaded to vector store (documents) or SQL engine (CSVs)
- Tracked in database

**No manual loading needed for user uploads!**

---

## 🔄 Re-loading Data

### Smart Loading (Skip Already Loaded Files)
```bash
python load_kb.py
```
Only loads new/changed files.

### Force Reload Everything
```bash
python load_kb.py --force
```
Reloads ALL files, ignoring tracking.

### Load Specific Folders
```bash
# Only load pdfs/ folder
python load_kb.py --hard-kb-only

# Only load uploaded_docs/ folder
python load_kb.py --uploads-only
```

---

## 📊 Check Status

### Knowledge Base Status
```bash
curl http://localhost:8000/api/knowledge-base/status/
```

### Available SQL Tables
```bash
curl http://localhost:8000/api/analytics/sources/
```

---

## 🧪 Test Queries

### RAG Query (Document Search)
```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is CRM?",
    "session_id": "test-session-1"
  }'
```

### SQL Query (Structured Data)
```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me top 5 providers by fee amount",
    "session_id": "test-session-1"
  }'
```

### Hybrid Query (Both RAG + SQL)
```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the requirements for providers with fees over $1000?",
    "session_id": "test-session-1"
  }'
```

---

## 📁 Folder Structure

```
Studynet-AI-Agent/
├── pdfs/                       # Hard knowledge base (put your files here)
│   ├── *.pdf                   # Will be embedded to vector store
│   ├── *.docx                  # Will be embedded to vector store
│   └── *.csv                   # Will be loaded as SQL tables
│
├── uploaded_docs/              # User uploads (auto-created)
│   ├── *.pdf                   # From /api/upload/document/
│   ├── *.docx                  # From /api/upload/document/
│   └── *.csv                   # From /api/upload/csv/
│
├── vector_store/               # ChromaDB vector database (auto-created)
│
├── load_kb.py                  # Manual data loader script
│
└── manage.py                   # Django management
```

---

## ⚠️ Important Notes

1. **Manual Loading Required**: Knowledge base is NOT auto-loaded on server startup. You must run `python load_kb.py` first.

2. **Smart Tracking**: The script tracks all loaded files in the database. It won't re-process the same files unless you use `--force`.

3. **User Uploads Auto-Load**: Files uploaded via API endpoints are automatically loaded (no manual script needed).

4. **Fast Server Start**: Since data is pre-loaded, server starts in ~2-3 seconds (not 2-5 minutes).

---

## 🆘 Troubleshooting

### "No documents found"
- Check that files are in `pdfs/` folder
- Run `python load_kb.py --force` to force reload

### "Table already exists"
- Normal if you run `load_kb.py` multiple times
- Use `python load_kb.py --force` to force reload

### "Django not set up"
- Make sure you run migrations first:
  ```bash
  python manage.py migrate
  ```

### Check what's loaded
```bash
curl http://localhost:8000/api/analytics/sources/
```
