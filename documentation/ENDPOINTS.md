# API Endpoints Documentation

Complete documentation of all API endpoints with JWT authentication and Postman test examples.

**Base URL:** `http://localhost:8000/api`

**Total Endpoints:** 32

---

## Table of Contents

1. [Frontend Views](#frontend-views)
2. [Health & Status](#health--status)
3. [Authentication Pages](#authentication-pages)
4. [Authentication Endpoints](#authentication-endpoints)
5. [User Management](#user-management)
6. [Query Processing](#query-processing)
7. [Document Management](#document-management)
8. [Memory Management](#memory-management)
9. [System Monitoring](#system-monitoring)
10. [Knowledge Base Management](#knowledge-base-management)
11. [Analytics](#analytics)
12. [Reports](#reports)
13. [Data Export](#data-export)
14. [Developer Dashboard](#developer-dashboard)

---

## Frontend Views

### 1. Main Frontend Interface
**Endpoint:** `GET /api/`
**Description:** Serves the main chat interface HTML page
**Auth:** None

**Postman Test:**
```
GET http://localhost:8000/api/
```

**Expected Response:** HTML page

---

### 2. Developer Dashboard Page
**Endpoint:** `GET /api/developer/`
**Description:** Serves the developer dashboard HTML page
**Auth:** None

**Postman Test:**
```
GET http://localhost:8000/api/developer/
```

**Expected Response:** HTML page

---

## Health & Status

### 3. Health Check
**Endpoint:** `GET /api/health/`
**Description:** Check API health status
**Auth:** None

**Postman Test:**
```
GET http://localhost:8000/api/health/
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "RAG Pipeline API",
  "version": "1.0.0",
  "data_source": "PDFs folder (./pdfs/)",
  "features": {
    "knowledge_base": "Active",
    "web_search": "Active",
    "data_location": "pdfs/ folder"
  }
}
```

---

## Authentication Pages

### 3. Login Page
**Endpoint:** `GET /api/auth/login-page/`
**Description:** Serves the login HTML page
**Auth:** None

**Postman Test:**
```
GET http://localhost:8000/api/auth/login-page/
```

**Expected Response:** HTML login page

---

### 4. Register Page
**Endpoint:** `GET /api/auth/register-page/`
**Description:** Serves the registration HTML page
**Auth:** None

**Postman Test:**
```
GET http://localhost:8000/api/auth/register-page/
```

**Expected Response:** HTML registration page

---

## Authentication Endpoints

### 5. User Registration
**Endpoint:** `POST /api/auth/register/`
**Description:** Register a new user account
**Auth:** None
**Content-Type:** application/json

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Postman Test:**
```
POST http://localhost:8000/api/auth/register/
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "TestPass123!",
  "password_confirm": "TestPass123!",
  "first_name": "Test",
  "last_name": "User"
}
```

**Expected Response:**
```json
{
  "message": "User registered successfully",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_admin": false
  }
}
```

---

### 6. User Login
**Endpoint:** `POST /api/auth/login/`
**Description:** Login user and return JWT tokens
**Auth:** None
**Content-Type:** application/json

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Postman Test:**
```
POST http://localhost:8000/api/auth/login/
Content-Type: application/json

{
  "username": "testuser",
  "password": "TestPass123!"
}
```

**Expected Response:**
```json
{
  "message": "Login successful",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  }
}
```

---

### 7. Token Refresh
**Endpoint:** `POST /api/auth/token/refresh/`
**Description:** Refresh access token using refresh token
**Auth:** None
**Content-Type:** application/json

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Postman Test:**
```
POST http://localhost:8000/api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Expected Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 8. User Logout
**Endpoint:** `POST /api/auth/logout/`
**Description:** Logout user by blacklisting refresh token
**Auth:** Required (Bearer Token)
**Content-Type:** application/json

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Postman Test:**
```
POST http://localhost:8000/api/auth/logout/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Expected Response:**
```json
{
  "message": "Logout successful"
}
```

---

### 9. Get User Profile
**Endpoint:** `GET /api/auth/profile/`
**Description:** Get current user profile
**Auth:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Postman Test:**
```
GET http://localhost:8000/api/auth/profile/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Expected Response:**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "first_name": "Test",
  "last_name": "User",
  "is_active": true,
  "is_admin": false,
  "date_joined": "2025-10-08T10:30:00Z",
  "last_login": "2025-10-08T12:30:00Z"
}
```

---

### 10. Update User Profile
**Endpoint:** `PUT/PATCH /api/auth/profile/update/`
**Description:** Update current user profile
**Auth:** Required (Bearer Token)
**Content-Type:** application/json

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (all fields optional):**
```json
{
  "email": "newemail@example.com",
  "first_name": "Johnny",
  "last_name": "Doe"
}
```

**Postman Test:**
```
PUT http://localhost:8000/api/auth/profile/update/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "email": "newemail@example.com",
  "first_name": "Johnny"
}
```

**Expected Response:**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "newemail@example.com",
    "first_name": "Johnny",
    "last_name": "User"
  }
}
```

---

### 11. Change Password
**Endpoint:** `POST /api/auth/password/change/`
**Description:** Change user password
**Auth:** Required (Bearer Token)
**Content-Type:** application/json

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass456!",
  "new_password_confirm": "NewPass456!"
}
```

**Postman Test:**
```
POST http://localhost:8000/api/auth/password/change/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "old_password": "TestPass123!",
  "new_password": "NewTestPass456!",
  "new_password_confirm": "NewTestPass456!"
}
```

**Expected Response:**
```json
{
  "message": "Password changed successfully"
}
```

---

## User Management

### 12. User Statistics
**Endpoint:** `GET /api/users/me/stats/`
**Description:** Get user statistics (students can only view their own stats)
**Auth:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Postman Test:**
```
GET http://localhost:8000/api/users/me/stats/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Expected Response:**
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "full_name": "Test User"
  },
  "statistics": {
    "total_queries": 25,
    "total_tokens": 12500,
    "total_cost_usd": 0.625,
    "avg_response_time_ms": 850.5,
    "avg_confidence_score": 0.87,
    "query_types": {
      "sql": 10,
      "rag": 12,
      "hybrid": 3
    },
    "sessions_count": 5,
    "csv_uploads": 2,
    "document_uploads": 3
  }
}
```

---

## Query Processing

### 13. Anonymous Chat
**Endpoint:** `POST /api/chat/`
**Description:** Dedicated endpoint for anonymous users to chat without authentication
**Auth:** None (Anonymous access only)
**Content-Type:** application/json

**Request Body:**
```json
{
  "query": "What is the student visa process?",
  "session_id": "anonymous_session_123"
}
```

**Parameters:**
- `query` (string, required): User's question
- `session_id` (string, optional): Session identifier for conversation context

**Postman Test:**
```
POST http://localhost:8000/api/chat/
Content-Type: application/json

{
  "query": "List top 5 universities in Australia",
  "session_id": "anonymous_test_session"
}
```

**Expected Response:**
```json
{
  "answer": "Here are the top 5 universities in Australia...",
  "sources": [
    {
      "source": "document.pdf",
      "score": 0.85
    }
  ],
  "confidence_score": 0.9,
  "web_search_used": false,
  "session_id": "anonymous_test_session",
  "query_type": "semantic_rag",
  "user_type": "anonymous",
  "message": "This is a free anonymous chat. For full features, please register an account."
}
```

**Note:** This endpoint is specifically designed for anonymous users. It provides basic chat functionality without requiring authentication.

---

### 14. Process Query (Authenticated)
**Endpoint:** `POST /api/query/`
**Description:** Process a user query through RAG pipeline (for authenticated users)
**Auth:** Required (Bearer Token)
**Content-Type:** application/json

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "query": "What is the student visa process?",
  "session_id": "test_session_123",
  "use_web_search": true,
  "enhance_formatting": true
}
```

**Parameters:**
- `query` (string, required): User's question
- `session_id` (string, optional): Session identifier for conversation context
- `use_web_search` (boolean, optional): Enable web search, default: false
- `enhance_formatting` (boolean, optional): Enable enhanced response formatting, default: true

**Postman Test:**
```
POST http://localhost:8000/api/query/
Content-Type: application/json

{
  "query": "List top 5 universities in Australia",
  "session_id": "postman_test_session",
  "use_web_search": false,
  "enhance_formatting": true
}
```

**Expected Response:**
```json
{
  "response": "Here are the top 5 universities...",
  "session_id": "postman_test_session",
  "query_type": "structured_sql",
  "confidence_score": 0.9,
  "sources": [
    {
      "source": "document.pdf",
      "score": 0.85
    }
  ],
  "processing_time_ms": 1234,
  "metadata": {
    "tokens_used": 500,
    "cost_usd": 0.00025
  }
}
```

---

## Document Management

### 14. Upload Document
**Endpoint:** `POST /api/upload/document/`
**Description:** Upload and process PDF, DOCX, TXT, or HTML files
**Auth:** Required (Bearer Token)
**Content-Type:** multipart/form-data

**Headers:**
```
Authorization: Bearer <access_token>
```

**Form Data:**
- `file` (file, required): Document file to upload

**Postman Test:**
```
POST http://localhost:8000/api/upload/document/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: multipart/form-data

Body:
- file: [Select File] (test_document.pdf)
```

**Expected Response:**
```json
{
  "message": "Document uploaded and processed successfully",
  "filename": "test_document.pdf",
  "chunks_created": 45,
  "file_size_kb": 1024,
  "document_id": "doc_abc123"
}
```

---

### 15. Upload Text
**Endpoint:** `POST /api/upload/text/`
**Description:** Upload raw text content
**Auth:** Required (Bearer Token)
**Content-Type:** application/json

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "text": "This is sample text content to be indexed",
  "filename": "sample_text.txt",
  "metadata": {
    "source": "manual_upload",
    "category": "test"
  }
}
```

**Parameters:**
- `text` (string, required): Raw text content
- `filename` (string, optional): Filename for reference
- `metadata` (object, optional): Additional metadata

**Postman Test:**
```
POST http://localhost:8000/api/upload/text/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "text": "The student visa application requires proof of funds, English proficiency test scores, and a valid offer letter from an Australian university.",
  "filename": "visa_info.txt",
  "metadata": {
    "category": "visa_information"
  }
}
```

**Expected Response:**
```json
{
  "message": "Text uploaded and processed successfully",
  "filename": "visa_info.txt",
  "chunks_created": 1,
  "text_length": 145
}
```

---

### 16. Upload CSV
**Endpoint:** `POST /api/upload/csv/`
**Description:** Upload CSV file for SQL queries
**Auth:** Required (Bearer Token)
**Content-Type:** multipart/form-data

**Headers:**
```
Authorization: Bearer <access_token>
```

**Form Data:**
- `file` (file, required): CSV file to upload

**Postman Test:**
```
POST http://localhost:8000/api/upload/csv/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: multipart/form-data

Body:
- file: [Select File] (universities.csv)
```

**Expected Response:**
```json
{
  "message": "CSV uploaded successfully",
  "table_name": "universities",
  "row_count": 150,
  "column_count": 12,
  "columns": ["name", "location", "tuition_fee", "ranking"],
  "sample_data": [
    {
      "name": "University of Sydney",
      "location": "Sydney",
      "tuition_fee": 45000,
      "ranking": 1
    }
  ]
}
```

---

## Memory Management

### 17. Get Session Memory
**Endpoint:** `GET /api/memory/<session_id>/`
**Description:** Retrieve conversation memory for a specific session
**Auth:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Postman Test:**
```
GET http://localhost:8000/api/memory/postman_test_session/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Expected Response:**
```json
{
  "session_id": "postman_test_session",
  "message_count": 5,
  "context": "User: What is the visa process?\nAssistant: The visa process involves...\n",
  "total_tokens": 1200
}
```

---

### 18. Clear Session Memory
**Endpoint:** `DELETE /api/memory/<session_id>/`
**Description:** Clear conversation memory for a specific session
**Auth:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Postman Test:**
```
DELETE http://localhost:8000/api/memory/postman_test_session/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Expected Response:**
```json
{
  "message": "Memory cleared successfully",
  "session_id": "postman_test_session"
}
```

---

### 19. List All Sessions
**Endpoint:** `GET /api/sessions/`
**Description:** List all active sessions
**Auth:** None (Anonymous access allowed)

**Postman Test:**
```
GET http://localhost:8000/api/sessions/
```

**Expected Response:**
```json
{
  "sessions": [
    "session_abc123_1234567890",
    "session_def456_0987654321",
    "postman_test_session"
  ],
  "count": 3
}
```

---

## System Monitoring

### 20. Get System Metrics
**Endpoint:** `GET /api/metrics/`
**Description:** Retrieve system performance metrics
**Auth:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Postman Test:**
```
GET http://localhost:8000/api/metrics/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Expected Response:**
```json
{
  "total_queries": 1234,
  "successful_queries": 1200,
  "failed_queries": 34,
  "avg_response_time_ms": 850,
  "total_tokens_used": 500000,
  "total_cost_usd": 25.50,
  "uptime_seconds": 86400,
  "last_query_timestamp": "2025-10-06T12:30:45Z"
}
```

---

### 21. Reset System Metrics
**Endpoint:** `POST /api/metrics/`
**Description:** Reset system metrics to zero
**Auth:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Postman Test:**
```
POST http://localhost:8000/api/metrics/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Expected Response:**
```json
{
  "message": "Metrics reset successfully",
  "timestamp": "2025-10-06T12:30:45Z"
}
```

---

## Knowledge Base Management

### 22. Knowledge Base Status
**Endpoint:** `GET /api/knowledge-base/status/`
**Description:** Get knowledge base statistics
**Auth:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Postman Test:**
```
GET http://localhost:8000/api/knowledge-base/status/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Expected Response:**
```json
{
  "status": "active",
  "parent_chunks": 259,
  "child_chunks": 952,
  "total_documents": 1211,
  "knowledge_base_path": "./pdfs",
  "data_source": "PDFs folder (./pdfs/)"
}
```

---

### 23. Reload Knowledge Base
**Endpoint:** `POST /api/knowledge-base/reload/`
**Description:** Reload knowledge base from PDFs folder
**Auth:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Postman Test:**
```
POST http://localhost:8000/api/knowledge-base/reload/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Expected Response:**
```json
{
  "message": "Knowledge base reloaded successfully",
  "documents_processed": 45,
  "chunks_created": 1211,
  "processing_time_seconds": 120.5
}
```

**Note:** This operation may take several minutes depending on the number of documents.

---

### 24. Clear Vector Store
**Endpoint:** `DELETE /api/vectorstore/clear/`
**Description:** Clear entire vector store (use with caution!)
**Auth:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Postman Test:**
```
DELETE http://localhost:8000/api/vectorstore/clear/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Expected Response:**
```json
{
  "message": "Vector store cleared successfully",
  "documents_deleted": 1211
}
```

**Warning:** This will delete ALL document data from the vector store!

---

## Analytics

### 25. Query Analytics
**Endpoint:** `GET /api/analytics/queries/`
**Description:** Get query analytics and statistics
**Auth:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `days` (integer, optional): Number of days to analyze, default: 7

**Postman Test:**
```
GET http://localhost:8000/api/analytics/queries/?days=30
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Expected Response:**
```json
{
  "time_period_days": 30,
  "total_queries": 500,
  "query_types": {
    "structured_sql": 200,
    "semantic_rag": 250,
    "hybrid": 50
  },
  "avg_confidence_score": 0.85,
  "avg_response_time_ms": 850,
  "success_rate": 96.5,
  "top_queries": [
    {
      "query": "List universities in Sydney",
      "count": 25,
      "avg_confidence": 0.92
    }
  ]
}
```

---

### 26. Data Source Statistics
**Endpoint:** `GET /api/analytics/sources/`
**Description:** Get statistics for all data sources
**Auth:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Postman Test:**
```
GET http://localhost:8000/api/analytics/sources/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Expected Response:**
```json
{
  "total_sources": 15,
  "sources": [
    {
      "source_name": "universities.csv",
      "source_type": "csv_table",
      "row_count": 150,
      "column_count": 12,
      "file_size_kb": 256,
      "columns": ["name", "location", "tuition_fee"],
      "chunk_count": 0,
      "created_at": "2025-10-05T10:30:00Z"
    },
    {
      "source_name": "visa_guide.pdf",
      "source_type": "pdf_document",
      "chunk_count": 45,
      "file_size_kb": 1024,
      "columns": [],
      "row_count": 0,
      "created_at": "2025-10-04T15:20:00Z"
    }
  ]
}
```

---

## Reports

### 27. System Report
**Endpoint:** `GET /api/reports/system/`
**Description:** Generate comprehensive system health report
**Auth:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Postman Test:**
```
GET http://localhost:8000/api/reports/system/
```

**Expected Response:**
```json
{
  "timestamp": "2025-10-06T12:30:45Z",
  "database": {
    "csv_uploads": 5,
    "data_sources": 15,
    "query_analytics": 500,
    "conversation_sessions": 71,
    "conversation_messages": 1234
  },
  "vector_store": {
    "parent_chunks": 259,
    "child_chunks": 952,
    "total_documents": 1211
  },
  "performance": {
    "avg_query_time_ms": 850,
    "total_queries": 500,
    "success_rate": 96.5
  },
  "health": "healthy"
}
```

---

### 19. Usage Report
**Endpoint:** `GET /api/reports/usage/`
**Description:** Generate usage statistics report
**Auth:** None

**Query Parameters:**
- `days` (integer, optional): Number of days to analyze, default: 7

**Postman Test:**
```
GET http://localhost:8000/api/reports/usage/?days=30
```

**Expected Response:**
```json
{
  "time_period_days": 30,
  "start_date": "2025-09-06",
  "end_date": "2025-10-06",
  "queries": {
    "total": 500,
    "successful": 482,
    "failed": 18,
    "sql_queries": 200,
    "rag_queries": 250,
    "hybrid_queries": 50
  },
  "tokens": {
    "total_tokens": 250000,
    "prompt_tokens": 100000,
    "completion_tokens": 150000,
    "total_cost_usd": 12.50,
    "avg_tokens_per_query": 500,
    "avg_cost_per_query_usd": 0.025
  },
  "sessions": {
    "total_sessions": 71,
    "active_sessions_24h": 15,
    "avg_messages_per_session": 8.5
  },
  "data_sources": {
    "csv_files": 5,
    "documents": 10,
    "total_chunks": 1211
  },
  "performance": {
    "avg_response_time_ms": 850,
    "min_response_time_ms": 200,
    "max_response_time_ms": 5000,
    "avg_confidence_score": 0.85
  }
}
```

---

## Data Export

### 20. SQL Export
**Endpoint:** `POST /api/export/sql/`
**Description:** Export SQL query results to CSV or JSON
**Auth:** None
**Content-Type:** application/json

**Request Body:**
```json
{
  "query": "SELECT * FROM universities WHERE location = 'Sydney' LIMIT 10",
  "format": "csv"
}
```

**Parameters:**
- `query` (string, required): SQL query to execute
- `format` (string, optional): Export format - "csv" or "json", default: "csv"

**Postman Test:**
```
POST http://localhost:8000/api/export/sql/
Content-Type: application/json

{
  "query": "SELECT name, location, tuition_fee FROM universities WHERE ranking <= 10",
  "format": "json"
}
```

**Expected Response (JSON format):**
```json
{
  "format": "json",
  "row_count": 10,
  "data": [
    {
      "name": "University of Sydney",
      "location": "Sydney",
      "tuition_fee": 45000
    },
    {
      "name": "University of Melbourne",
      "location": "Melbourne",
      "tuition_fee": 46000
    }
  ],
  "query": "SELECT name, location, tuition_fee FROM universities WHERE ranking <= 10"
}
```

**Expected Response (CSV format):**
```json
{
  "format": "csv",
  "row_count": 10,
  "csv_data": "name,location,tuition_fee\nUniversity of Sydney,Sydney,45000\nUniversity of Melbourne,Melbourne,46000",
  "query": "SELECT name, location, tuition_fee FROM universities WHERE ranking <= 10"
}
```

---

## Developer Dashboard

### 21. Developer Dashboard (Main)
**Endpoint:** `GET /api/dashboard/`
**Description:** Get comprehensive dashboard data
**Auth:** None

**Query Parameters:**
- `days` (integer, optional): Number of days to analyze, default: 7

**Postman Test:**
```
GET http://localhost:8000/api/dashboard/?days=30
```

**Expected Response:**
```json
{
  "time_period_days": 30,
  "total_queries": 500,
  "successful_queries": 482,
  "failed_queries": 18,
  "success_rate": 96.4,
  "sql_queries_count": 200,
  "rag_queries_count": 250,
  "hybrid_queries_count": 50,
  "avg_response_time_ms": 850,
  "avg_confidence_score": 0.85,
  "token_usage": {
    "total_tokens": 250000,
    "total_prompt_tokens": 100000,
    "total_completion_tokens": 150000,
    "total_cost_usd": 12.50,
    "avg_tokens_per_query": 500,
    "avg_cost_per_query": 0.025
  },
  "active_sessions_24h": 15,
  "total_data_sources": 15,
  "vector_store_stats": {
    "parent_chunks": 259,
    "child_chunks": 952,
    "total_documents": 1211
  }
}
```

---

### 22. Token Usage Statistics
**Endpoint:** `GET /api/dashboard/tokens/`
**Description:** Get detailed token usage and cost statistics
**Auth:** None

**Query Parameters:**
- `days` (integer, optional): Number of days to analyze, default: 30
- `session_id` (string, optional): Filter by specific session

**Postman Test:**
```
GET http://localhost:8000/api/dashboard/tokens/?days=30
```

**Expected Response:**
```json
{
  "time_period_days": 30,
  "session_id": null,
  "total_queries": 500,
  "token_stats": {
    "total_tokens": 250000,
    "total_prompt_tokens": 100000,
    "total_completion_tokens": 150000,
    "avg_tokens_per_query": 500,
    "min_tokens": 50,
    "max_tokens": 2000
  },
  "cost_stats": {
    "total_cost_usd": 12.50,
    "avg_cost_per_query": 0.025,
    "min_cost_usd": 0.001,
    "max_cost_usd": 0.15
  },
  "by_query_type": {
    "structured_sql": {
      "queries": 200,
      "total_tokens": 80000,
      "total_cost_usd": 4.00,
      "avg_tokens": 400
    },
    "semantic_rag": {
      "queries": 250,
      "total_tokens": 150000,
      "total_cost_usd": 7.50,
      "avg_tokens": 600
    },
    "hybrid": {
      "queries": 50,
      "total_tokens": 20000,
      "total_cost_usd": 1.00,
      "avg_tokens": 400
    }
  },
  "daily_breakdown": [
    {
      "date": "2025-10-06",
      "queries": 25,
      "tokens": 12500,
      "cost_usd": 0.625
    }
  ]
}
```

---

### 23. Query Cost Breakdown
**Endpoint:** `GET /api/dashboard/costs/`
**Description:** Get cost breakdown for individual queries
**Auth:** None

**Query Parameters:**
- `days` (integer, optional): Number of days to analyze, default: 7
- `limit` (integer, optional): Number of queries to return, default: 10
- `order` (string, optional): Sort order - "cost" (highest cost first) or "date" (most recent first), default: "cost"

**Postman Test:**
```
GET http://localhost:8000/api/dashboard/costs/?days=30&limit=10&order=cost
```

**Expected Response:**
```json
{
  "time_period_days": 30,
  "limit": 10,
  "order": "cost",
  "total_queries": 500,
  "queries": [
    {
      "query_text": "Provide detailed analysis of top universities in Australia with admission requirements",
      "timestamp": "2025-10-06T10:30:00Z",
      "query_type": "hybrid",
      "total_tokens": 2000,
      "prompt_tokens": 800,
      "completion_tokens": 1200,
      "cost_usd": 0.15,
      "response_time_ms": 2500,
      "confidence_score": 0.92,
      "success": true
    },
    {
      "query_text": "Compare tuition fees across all Australian universities",
      "timestamp": "2025-10-05T15:20:00Z",
      "query_type": "structured_sql",
      "total_tokens": 1500,
      "prompt_tokens": 600,
      "completion_tokens": 900,
      "cost_usd": 0.10,
      "response_time_ms": 1800,
      "confidence_score": 0.95,
      "success": true
    }
  ]
}
```

---

## Common Response Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Error Response Format

All endpoints return errors in this format:

```json
{
  "error": "Error message description",
  "details": "Additional error details (if available)"
}
```

---

## Postman Collection Setup

### Environment Variables
Create a Postman environment with:
- `base_url`: `http://localhost:8000`
- `session_id`: `postman_test_session`

### Pre-request Script (Global)
```javascript
// Generate session ID if not exists
if (!pm.environment.get("session_id")) {
    pm.environment.set("session_id", "session_" + Date.now());
}
```

### Tests Script (Global)
```javascript
// Test status code
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test response time
pm.test("Response time is less than 5000ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(5000);
});

// Test JSON response
pm.test("Response is JSON", function () {
    pm.response.to.be.json;
});
```

---

## Testing Workflow

### 1. Basic Flow Test
1. Health Check → Verify API is running
2. Knowledge Base Status → Check data loaded
3. Process Query → Test basic functionality
4. Get Session Memory → Verify conversation tracking

### 2. Document Upload Flow
1. Upload Document → Add new PDF
2. Knowledge Base Status → Verify document indexed
3. Process Query → Query the uploaded document
4. Analytics Sources → Check document stats

### 3. CSV Data Flow
1. Upload CSV → Add structured data
2. Analytics Sources → Verify CSV loaded
3. Process Query (SQL) → Query CSV data
4. SQL Export → Export query results

### 4. Monitoring Flow
1. System Report → Overall health
2. Usage Report → Usage statistics
3. Token Usage → Cost analysis
4. Cost Breakdown → Expensive queries

### 5. Cleanup Flow
1. Clear Session Memory → Remove test session
2. (Optional) Clear Vector Store → Reset all data

---

## Notes

- All endpoints accept JSON request bodies unless specified otherwise
- File uploads use `multipart/form-data`
- Session IDs are automatically generated if not provided
- Token costs are calculated using OpenAI pricing
- Response times may vary based on query complexity
- Vector store operations may take time with large datasets
- Always test DELETE operations on non-production data

---

**Last Updated:** 2025-10-06
**API Version:** 1.0.0
