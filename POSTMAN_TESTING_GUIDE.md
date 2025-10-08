# Postman Testing Guide for StudyNet Counselor RAG API

## Overview

This guide provides comprehensive instructions for testing all API endpoints using Postman with JWT authentication. The API uses JWT tokens for authentication, with most endpoints requiring a valid access token.

## Base Configuration

### Environment Variables
Create a Postman environment with these variables:

```
BASE_URL: http://localhost:8000/api
ACCESS_TOKEN: (will be set automatically after login)
REFRESH_TOKEN: (will be set automatically after login)
```

### Base URL
```
http://localhost:8000/api
```

---

## 1. Authentication Endpoints (No Auth Required)

### 1.1 Health Check
**Method:** `GET`  
**URL:** `{{BASE_URL}}/health/`  
**Headers:** None required  
**Body:** None  

**Expected Response (200):**
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

### 1.2 User Registration
**Method:** `POST`  
**URL:** `{{BASE_URL}}/auth/register/`  
**Headers:** `Content-Type: application/json`  
**Body (JSON):**
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "Test",
  "last_name": "User"
}
```

**Expected Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Test Script (to save tokens):**
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("ACCESS_TOKEN", response.tokens.access);
    pm.environment.set("REFRESH_TOKEN", response.tokens.refresh);
}
```

### 1.3 User Login
**Method:** `POST`  
**URL:** `{{BASE_URL}}/auth/login/`  
**Headers:** `Content-Type: application/json`  
**Body (JSON):**
```json
{
  "username": "testuser",
  "password": "SecurePass123!"
}
```

**Expected Response (200):**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Test Script (to save tokens):**
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("ACCESS_TOKEN", response.tokens.access);
    pm.environment.set("REFRESH_TOKEN", response.tokens.refresh);
}
```

### 1.4 Token Refresh
**Method:** `POST`  
**URL:** `{{BASE_URL}}/auth/token/refresh/`  
**Headers:** `Content-Type: application/json`  
**Body (JSON):**
```json
{
  "refresh": "{{REFRESH_TOKEN}}"
}
```

**Expected Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Test Script (to save new access token):**
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("ACCESS_TOKEN", response.access);
}
```

---

## 2. Authenticated Endpoints (Require JWT Token)

### Common Headers for All Authenticated Endpoints
```
Authorization: Bearer {{ACCESS_TOKEN}}
Content-Type: application/json
```

### 2.1 User Profile Management

#### Get User Profile
**Method:** `GET`  
**URL:** `{{BASE_URL}}/auth/profile/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

**Expected Response (200):**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "first_name": "Test",
  "last_name": "User",
  "is_active": true,
  "is_staff": false,
  "date_joined": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z"
}
```

#### Update User Profile
**Method:** `PUT` or `PATCH`  
**URL:** `{{BASE_URL}}/auth/profile/update/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`, `Content-Type: application/json`  
**Body (JSON):**
```json
{
  "email": "newemail@example.com",
  "first_name": "Updated",
  "last_name": "Name"
}
```

#### Change Password
**Method:** `POST`  
**URL:** `{{BASE_URL}}/auth/password/change/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`, `Content-Type: application/json`  
**Body (JSON):**
```json
{
  "old_password": "SecurePass123!",
  "new_password": "NewSecurePass456!",
  "new_password_confirm": "NewSecurePass456!"
}
```

#### Logout
**Method:** `POST`  
**URL:** `{{BASE_URL}}/auth/logout/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`, `Content-Type: application/json`  
**Body (JSON):**
```json
{
  "refresh": "{{REFRESH_TOKEN}}"
}
```

### 2.2 Core Query Processing

#### Process Query
**Method:** `POST`  
**URL:** `{{BASE_URL}}/query/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`, `Content-Type: application/json`  
**Body (JSON):**
```json
{
  "query": "What are the application requirements?",
  "session_id": "test-session-123"
}
```

**Expected Response (200):**
```json
{
  "answer": "Based on the available information...",
  "sources": [
    {
      "title": "Application Management.pdf",
      "content": "Relevant content...",
      "page": 1
    }
  ],
  "confidence_score": 0.85,
  "web_search_used": false,
  "session_id": "test-session-123",
  "query_type": "semantic_rag",
  "tokens_used": 150,
  "cost_usd": "0.0003"
}
```

### 2.3 Document Management

#### Upload Document
**Method:** `POST`  
**URL:** `{{BASE_URL}}/upload/document/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  
**Body (form-data):**
- Key: `file`, Type: File, Value: [Select a PDF/DOC file]

**Expected Response (200):**
```json
{
  "status": "success",
  "message": "Document filename.pdf uploaded and embedded successfully",
  "chunks_created": 15,
  "file_path": "./uploaded_docs/filename.pdf"
}
```

#### Upload Text Content
**Method:** `POST`  
**URL:** `{{BASE_URL}}/upload/text/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`, `Content-Type: application/json`  
**Body (JSON):**
```json
{
  "content": "This is some text content to be processed.",
  "metadata": {
    "title": "Custom Text Document",
    "source": "manual_input"
  }
}
```

#### Upload CSV File
**Method:** `POST`  
**URL:** `{{BASE_URL}}/upload/csv/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  
**Body (form-data):**
- Key: `file`, Type: File, Value: [Select a CSV file]
- Key: `table_name`, Type: Text, Value: `custom_table`
- Key: `uploaded_by`, Type: Text, Value: `testuser`

**Expected Response (200):**
```json
{
  "status": "success",
  "message": "CSV uploaded and available as table 'custom_table'",
  "table_name": "custom_table",
  "row_count": 100,
  "column_count": 5,
  "columns": ["id", "name", "email", "phone", "address"],
  "file_path": "./uploaded_docs/data.csv"
}
```

### 2.4 Memory & Sessions

#### Get Session Memory
**Method:** `GET`  
**URL:** `{{BASE_URL}}/memory/{{session_id}}/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

**Expected Response (200):**
```json
{
  "session_id": "test-session-123",
  "context": "Previous conversation context...",
  "memory": {
    "user_preferences": {},
    "conversation_history": []
  }
}
```

#### Clear Session Memory
**Method:** `DELETE`  
**URL:** `{{BASE_URL}}/memory/{{session_id}}/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

#### List All Sessions
**Method:** `GET`  
**URL:** `{{BASE_URL}}/sessions/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

**Expected Response (200):**
```json
{
  "sessions": [
    "test-session-123",
    "another-session-456"
  ],
  "count": 2
}
```

### 2.5 System Monitoring

#### Get System Metrics
**Method:** `GET`  
**URL:** `{{BASE_URL}}/metrics/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

**Expected Response (200):**
```json
{
  "total_queries": 150,
  "successful_queries": 145,
  "failed_queries": 5,
  "avg_response_time": 2.5,
  "success_rate": 96.67
}
```

#### Reset System Metrics
**Method:** `POST`  
**URL:** `{{BASE_URL}}/metrics/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

#### Get Knowledge Base Status
**Method:** `GET`  
**URL:** `{{BASE_URL}}/knowledge-base/status/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

**Expected Response (200):**
```json
{
  "status": "active",
  "parent_chunks": 500,
  "child_chunks": 1200,
  "total_documents": 1700,
  "knowledge_base_path": "./pdfs/",
  "data_source": "PDFs folder (./pdfs/)"
}
```

#### Reload Knowledge Base
**Method:** `POST`  
**URL:** `{{BASE_URL}}/knowledge-base/reload/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

#### Clear Vector Store
**Method:** `DELETE`  
**URL:** `{{BASE_URL}}/vectorstore/clear/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

### 2.6 Analytics Endpoints

#### Get Query Analytics
**Method:** `GET`  
**URL:** `{{BASE_URL}}/analytics/queries/?days=7`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

**Expected Response (200):**
```json
{
  "total_queries": 50,
  "sql_queries": 15,
  "rag_queries": 25,
  "hybrid_queries": 10,
  "avg_response_time_ms": 2500.5,
  "avg_confidence_score": 0.85,
  "success_rate": 96.0,
  "total_tools_used": 45
}
```

#### Get Data Source Statistics
**Method:** `GET`  
**URL:** `{{BASE_URL}}/analytics/sources/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

### 2.7 Reporting Endpoints

#### Get System Report
**Method:** `GET`  
**URL:** `{{BASE_URL}}/reports/system/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

#### Get Usage Report
**Method:** `GET`  
**URL:** `{{BASE_URL}}/reports/usage/?days=7`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

### 2.8 SQL Export

#### Export SQL Results
**Method:** `POST`  
**URL:** `{{BASE_URL}}/export/sql/`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`, `Content-Type: application/json`  
**Body (JSON):**
```json
{
  "query": "SELECT * FROM users LIMIT 10",
  "format": "csv",
  "filename": "user_export"
}
```

### 2.9 Developer Dashboard

#### Get Developer Dashboard
**Method:** `GET`  
**URL:** `{{BASE_URL}}/dashboard/?days=7`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

#### Get Token Usage
**Method:** `GET`  
**URL:** `{{BASE_URL}}/dashboard/tokens/?days=7&session_id=test-session-123`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

#### Get Cost Breakdown
**Method:** `GET`  
**URL:** `{{BASE_URL}}/dashboard/costs/?days=7&limit=50&order=cost`  
**Headers:** `Authorization: Bearer {{ACCESS_TOKEN}}`  

---

## 3. Testing Workflow

### Step 1: Setup Environment
1. Create a new Postman environment
2. Set the `BASE_URL` variable to `http://localhost:8000/api`
3. Leave `ACCESS_TOKEN` and `REFRESH_TOKEN` empty initially

### Step 2: Test Authentication Flow
1. **Health Check** - Verify API is running
2. **Register** - Create a new user account
3. **Login** - Authenticate and get tokens
4. **Profile** - Test authenticated endpoint access

### Step 3: Test Core Functionality
1. **Query Processing** - Test the main RAG functionality
2. **Document Upload** - Test file upload capabilities
3. **Memory Management** - Test session handling

### Step 4: Test Advanced Features
1. **Analytics** - Test reporting endpoints
2. **System Management** - Test admin functions
3. **Token Refresh** - Test token renewal

### Step 5: Test Error Scenarios
1. **Invalid Token** - Test with expired/invalid tokens
2. **Missing Authentication** - Test without Authorization header
3. **Invalid Data** - Test with malformed requests

---

## 4. Common Test Scripts

### Auto Token Refresh Script
Add this to the **Pre-request Script** tab of your collection:

```javascript
// Check if access token is expired (basic check)
const accessToken = pm.environment.get("ACCESS_TOKEN");
if (accessToken) {
    try {
        const payload = JSON.parse(atob(accessToken.split('.')[1]));
        const now = Math.floor(Date.now() / 1000);
        if (payload.exp < now) {
            // Token expired, refresh it
            pm.sendRequest({
                url: pm.environment.get("BASE_URL") + "/auth/token/refresh/",
                method: 'POST',
                header: {
                    'Content-Type': 'application/json'
                },
                body: {
                    mode: 'raw',
                    raw: JSON.stringify({
                        refresh: pm.environment.get("REFRESH_TOKEN")
                    })
                }
            }, function (err, response) {
                if (response.code === 200) {
                    const newToken = response.json().access;
                    pm.environment.set("ACCESS_TOKEN", newToken);
                }
            });
        }
    } catch (e) {
        console.log("Token validation error:", e);
    }
}
```

### Response Validation Script
Add this to the **Tests** tab of requests:

```javascript
// Basic response validation
pm.test("Status code is successful", function () {
    pm.expect(pm.response.code).to.be.oneOf([200, 201, 204]);
});

pm.test("Response time is reasonable", function () {
    pm.expect(pm.response.responseTime).to.be.below(5000);
});

pm.test("Response has valid JSON", function () {
    pm.response.to.be.json;
});
```

---

## 5. Error Testing Scenarios

### 5.1 Authentication Errors

#### Test with Invalid Token
**Headers:** `Authorization: Bearer invalid_token_here`  
**Expected Response (401):**
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "token_type": "access",
      "message": "Token is invalid or expired"
    }
  ]
}
```

#### Test without Authorization Header
**Headers:** None  
**Expected Response (401):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 5.2 Validation Errors

#### Test Invalid Registration Data
**Body:**
```json
{
  "username": "",
  "email": "invalid-email",
  "password": "123",
  "password_confirm": "456"
}
```

**Expected Response (400):**
```json
{
  "error": ["Username, email, and password are required"]
}
```

---

## 6. Collection Organization

### Recommended Folder Structure:
```
StudyNet RAG API Tests/
├── 1. Authentication/
│   ├── Health Check
│   ├── Register User
│   ├── Login User
│   ├── Refresh Token
│   └── Logout User
├── 2. User Management/
│   ├── Get Profile
│   ├── Update Profile
│   └── Change Password
├── 3. Core Features/
│   ├── Process Query
│   ├── Upload Document
│   ├── Upload Text
│   └── Upload CSV
├── 4. Memory & Sessions/
│   ├── Get Session Memory
│   ├── Clear Session Memory
│   └── List Sessions
├── 5. System Monitoring/
│   ├── Get Metrics
│   ├── Reset Metrics
│   ├── Knowledge Base Status
│   └── Reload Knowledge Base
├── 6. Analytics/
│   ├── Query Analytics
│   └── Source Statistics
├── 7. Reports/
│   ├── System Report
│   └── Usage Report
└── 8. Developer Tools/
    ├── Developer Dashboard
    ├── Token Usage
    ├── Cost Breakdown
    └── SQL Export
```

---

## 7. Environment Variables Summary

| Variable | Description | Example |
|----------|-------------|---------|
| `BASE_URL` | API base URL | `http://localhost:8000/api` |
| `ACCESS_TOKEN` | JWT access token | `eyJ0eXAiOiJKV1QiLCJhbGc...` |
| `REFRESH_TOKEN` | JWT refresh token | `eyJ0eXAiOiJKV1QiLCJhbGc...` |
| `SESSION_ID` | Test session ID | `test-session-123` |

---

## 8. Troubleshooting

### Common Issues:

1. **401 Unauthorized**: Check if token is valid and not expired
2. **403 Forbidden**: User doesn't have required permissions
3. **400 Bad Request**: Check request body format and required fields
4. **500 Internal Server Error**: Check server logs for detailed error

### Token Management:
- Access tokens expire in 1 hour
- Refresh tokens expire in 7 days
- Use refresh endpoint to get new access tokens
- Store tokens securely in environment variables

### File Upload Issues:
- Ensure files are not too large
- Check file format is supported
- Verify multipart/form-data content type

---

This guide provides comprehensive testing instructions for all API endpoints. Follow the workflow steps to systematically test your JWT implementation and ensure all functionality works correctly.
