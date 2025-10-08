# Frontend Integration Guide

Complete guide for frontend developers to integrate with the RAG AI Agent Backend.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Backend Setup](#backend-setup)
3. [API Architecture Overview](#api-architecture-overview)
4. [Core Integration Flow](#core-integration-flow)
5. [Authentication & CORS](#authentication--cors)
6. [API Integration Examples](#api-integration-examples)
7. [State Management](#state-management)
8. [Error Handling](#error-handling)
9. [Best Practices](#best-practices)
10. [Example Implementations](#example-implementations)
11. [Testing Your Integration](#testing-your-integration)
12. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### What You Need

- Backend running at `http://localhost:8000` (or your deployed URL)
- Modern browser with JavaScript ES6+ support
- Basic knowledge of REST APIs and async/await

### 5-Minute Integration

```javascript
// 1. Test backend connection
fetch('http://localhost:8000/api/health/')
  .then(res => res.json())
  .then(data => console.log('Backend online:', data));

// 2. Send your first query
fetch('http://localhost:8000/api/query/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'What universities are in Sydney?',
    session_id: 'test_session_' + Date.now()
  })
})
  .then(res => res.json())
  .then(data => console.log('Response:', data));
```

---

## 🔧 Backend Setup

### 1. Prerequisites

Ensure the backend is installed and running:

```bash
cd Studynet-AI-Agent

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create .env file with:
# AZURE_OPENAI_API_KEY=your_key
# AZURE_OPENAI_ENDPOINT=your_endpoint
# AZURE_OPENAI_CHAT_DEPLOYMENT=chat-heavy
# AZURE_OPENAI_EMBED_DEPLOYMENT=embed-large
# AZURE_OPENAI_API_VERSION=2025-01-01-preview

# Run migrations
python manage.py migrate

# Load knowledge base (optional)
python load_kb.py

# Start server
python manage.py runserver 0.0.0.0:8000
```

### 2. Verify Backend

Open: `http://localhost:8000/api/health/`

Expected response:
```json
{
  "status": "healthy",
  "service": "RAG Pipeline API",
  "version": "1.0.0"
}
```

---

## 🏗️ API Architecture Overview

### Base URL

```
Development: http://localhost:8000/api
Production: https://your-domain.com/api
```

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND APPLICATION                     │
│  (React / Vue / Angular / Vanilla JS / Mobile App)          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/REST API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  DJANGO REST API BACKEND                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Query      │  │  Document    │  │   Memory     │     │
│  │  Processing  │  │  Management  │  │  Management  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Analytics   │  │  Knowledge   │  │   System     │     │
│  │   & Reports  │  │     Base     │  │  Monitoring  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Azure      │  │   Vector     │  │   SQLite     │
│   OpenAI     │  │   Store      │  │   Database   │
│   (GPT-4)    │  │  (ChromaDB)  │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

### API Categories

1. **Query Processing** - Core chat/Q&A functionality
2. **Document Management** - Upload and process documents
3. **Memory Management** - Session and conversation tracking
4. **Analytics** - Usage statistics and insights
5. **System Monitoring** - Health checks and metrics
6. **Knowledge Base** - Document repository management

---

## 🔄 Core Integration Flow

### User Query Flow

```
User Types Question
        │
        ▼
Frontend: Validate & Format Request
        │
        ▼
API Call: POST /api/query/
        │
        ├─► Backend: Classify Query Type
        │           (SQL / RAG / Hybrid)
        │
        ├─► Backend: Retrieve Relevant Documents
        │           (Vector Search + BM25)
        │
        ├─► Backend: Generate Response
        │           (Azure OpenAI GPT-4)
        │
        ▼
Response: JSON with answer, sources, metadata
        │
        ▼
Frontend: Display Response
        │
        ├─► Show answer text
        ├─► Display sources
        ├─► Show metadata (tokens, cost, confidence)
        └─► Update conversation history
```

### Document Upload Flow

```
User Selects File
        │
        ▼
Frontend: Validate File Type & Size
        │
        ▼
API Call: POST /api/upload/document/
        │
        ├─► Backend: Parse Document
        │           (PDF/DOCX/TXT)
        │
        ├─► Backend: Chunk Content
        │           (Parent + Child chunks)
        │
        ├─► Backend: Generate Embeddings
        │           (Azure OpenAI Embeddings)
        │
        ├─► Backend: Store in Vector DB
        │
        ▼
Response: Success + metadata
        │
        ▼
Frontend: Show success message
        └─► Refresh knowledge base status
```

---

## 🔐 Authentication & CORS

### Current Setup

The backend currently has **no authentication** (AllowAny) and **allows all CORS origins**.

**Important:** This is for development only. For production, implement authentication.

### CORS Configuration

Located in `config/settings.py`:

```python
CORS_ALLOW_ALL_ORIGINS = True  # Development only
CORS_ALLOW_CREDENTIALS = True

# For production, use:
# CORS_ALLOWED_ORIGINS = [
#     "https://your-frontend-domain.com",
#     "https://app.your-domain.com"
# ]
```

### Adding Authentication (Future)

To add JWT authentication:

1. Install: `pip install djangorestframework-simplejwt`
2. Add to `settings.py`:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
```
3. Update views: Change `AllowAny` to `IsAuthenticated`
4. Frontend: Add Authorization header
```javascript
headers: {
  'Authorization': `Bearer ${accessToken}`
}
```

---

## 💻 API Integration Examples

### 1. Basic Query (JavaScript/Fetch)

```javascript
async function sendQuery(userMessage, sessionId) {
  try {
    const response = await fetch('http://localhost:8000/api/query/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: userMessage,
        session_id: sessionId,
        use_web_search: true,
        enhance_formatting: true
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Query failed:', error);
    throw error;
  }
}

// Usage
const result = await sendQuery(
  'What is the tuition fee for Sydney University?',
  'session_12345'
);

console.log('Answer:', result.response);
console.log('Sources:', result.sources);
console.log('Confidence:', result.confidence_score);
```

### 2. React Integration

```jsx
import { useState, useEffect } from 'react';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);

  const API_BASE = 'http://localhost:8000/api';

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/query/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: input,
          session_id: sessionId,
          use_web_search: true,
          enhance_formatting: true
        })
      });

      const data = await response.json();

      const assistantMessage = {
        role: 'assistant',
        content: data.response,
        sources: data.sources,
        metadata: {
          confidence: data.confidence_score,
          tokens: data.metadata?.tokens_used,
          cost: data.metadata?.cost_usd
        }
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="content">{msg.content}</div>
            {msg.sources && (
              <div className="sources">
                <strong>Sources:</strong>
                {msg.sources.map((src, i) => (
                  <span key={i}>{src.source} ({src.score})</span>
                ))}
              </div>
            )}
            {msg.metadata && (
              <div className="metadata">
                Confidence: {msg.metadata.confidence} |
                Tokens: {msg.metadata.tokens} |
                Cost: ${msg.metadata.cost}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="loading">Thinking...</div>}
      </div>

      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask a question..."
        />
        <button onClick={sendMessage} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
```

### 3. Vue.js Integration

```vue
<template>
  <div class="chat-app">
    <div class="messages" ref="messagesContainer">
      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="['message', message.role]"
      >
        <div class="content" v-html="message.content"></div>
        <div v-if="message.sources" class="sources">
          <strong>Sources:</strong>
          <span v-for="(source, i) in message.sources" :key="i">
            {{ source.source }} ({{ source.score }})
          </span>
        </div>
      </div>
      <div v-if="loading" class="loading">AI is thinking...</div>
    </div>

    <div class="input-area">
      <input
        v-model="userInput"
        @keyup.enter="sendMessage"
        placeholder="Type your question..."
        :disabled="loading"
      />
      <button @click="sendMessage" :disabled="loading || !userInput.trim()">
        Send
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChatApp',
  data() {
    return {
      messages: [],
      userInput: '',
      loading: false,
      sessionId: `session_${Date.now()}`,
      apiBase: 'http://localhost:8000/api'
    };
  },
  methods: {
    async sendMessage() {
      if (!this.userInput.trim() || this.loading) return;

      // Add user message
      this.messages.push({
        role: 'user',
        content: this.userInput
      });

      const query = this.userInput;
      this.userInput = '';
      this.loading = true;

      try {
        const response = await fetch(`${this.apiBase}/query/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: query,
            session_id: this.sessionId,
            use_web_search: true,
            enhance_formatting: true
          })
        });

        const data = await response.json();

        // Add assistant response
        this.messages.push({
          role: 'assistant',
          content: data.response,
          sources: data.sources,
          confidence: data.confidence_score
        });

        this.scrollToBottom();
      } catch (error) {
        console.error('Error sending message:', error);
        this.messages.push({
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          error: true
        });
      } finally {
        this.loading = false;
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer;
        container.scrollTop = container.scrollHeight;
      });
    }
  }
};
</script>
```

### 4. Angular Integration

```typescript
// chat.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface QueryRequest {
  query: string;
  session_id: string;
  use_web_search?: boolean;
  enhance_formatting?: boolean;
}

export interface QueryResponse {
  response: string;
  session_id: string;
  query_type: string;
  confidence_score: number;
  sources: Array<{source: string, score: number}>;
  processing_time_ms: number;
  metadata: {
    tokens_used: number;
    cost_usd: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = 'http://localhost:8000/api';
  private sessionId = `session_${Date.now()}`;

  constructor(private http: HttpClient) {}

  sendQuery(query: string): Observable<QueryResponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    const body: QueryRequest = {
      query: query,
      session_id: this.sessionId,
      use_web_search: true,
      enhance_formatting: true
    };

    return this.http.post<QueryResponse>(
      `${this.apiUrl}/query/`,
      body,
      { headers }
    );
  }

  getSessionMemory(): Observable<any> {
    return this.http.get(`${this.apiUrl}/memory/${this.sessionId}/`);
  }

  clearSession(): Observable<any> {
    return this.http.delete(`${this.apiUrl}/memory/${this.sessionId}/`);
  }

  getSessionId(): string {
    return this.sessionId;
  }
}

// chat.component.ts
import { Component } from '@angular/core';
import { ChatService, QueryResponse } from './chat.service';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{source: string, score: number}>;
  metadata?: any;
}

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent {
  messages: Message[] = [];
  userInput: string = '';
  loading: boolean = false;

  constructor(private chatService: ChatService) {}

  sendMessage(): void {
    if (!this.userInput.trim() || this.loading) return;

    // Add user message
    this.messages.push({
      role: 'user',
      content: this.userInput
    });

    const query = this.userInput;
    this.userInput = '';
    this.loading = true;

    this.chatService.sendQuery(query).subscribe({
      next: (response: QueryResponse) => {
        this.messages.push({
          role: 'assistant',
          content: response.response,
          sources: response.sources,
          metadata: {
            confidence: response.confidence_score,
            tokens: response.metadata.tokens_used,
            cost: response.metadata.cost_usd
          }
        });
        this.loading = false;
      },
      error: (error) => {
        console.error('Error:', error);
        this.messages.push({
          role: 'assistant',
          content: 'Sorry, something went wrong. Please try again.'
        });
        this.loading = false;
      }
    });
  }
}
```

### 5. File Upload (Any Framework)

```javascript
async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('http://localhost:8000/api/upload/document/', {
      method: 'POST',
      body: formData // Don't set Content-Type header, browser will set it
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }

    const data = await response.json();
    console.log('Upload successful:', data);
    return data;
  } catch (error) {
    console.error('Upload error:', error);
    throw error;
  }
}

// HTML
// <input type="file" id="fileInput" accept=".pdf,.docx,.txt,.html">

// Usage
document.getElementById('fileInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (file) {
    try {
      const result = await uploadDocument(file);
      alert(`Uploaded! ${result.chunks_created} chunks created.`);
    } catch (error) {
      alert('Upload failed: ' + error.message);
    }
  }
});
```

### 6. System Monitoring

```javascript
class SystemMonitor {
  constructor(apiBase = 'http://localhost:8000/api') {
    this.apiBase = apiBase;
  }

  async checkHealth() {
    const response = await fetch(`${this.apiBase}/health/`);
    return response.json();
  }

  async getKnowledgeBaseStatus() {
    const response = await fetch(`${this.apiBase}/knowledge-base/status/`);
    return response.json();
  }

  async getSessions() {
    const response = await fetch(`${this.apiBase}/sessions/`);
    return response.json();
  }

  async getMetrics() {
    const response = await fetch(`${this.apiBase}/metrics/`);
    return response.json();
  }

  async getDashboard(days = 7) {
    const response = await fetch(`${this.apiBase}/dashboard/?days=${days}`);
    return response.json();
  }
}

// Usage
const monitor = new SystemMonitor();

// Display system status
async function updateSystemStatus() {
  const [health, kb, sessions] = await Promise.all([
    monitor.checkHealth(),
    monitor.getKnowledgeBaseStatus(),
    monitor.getSessions()
  ]);

  console.log('API Status:', health.status);
  console.log('Knowledge Base:', kb.total_documents, 'documents');
  console.log('Active Sessions:', sessions.count);
}

updateSystemStatus();
```

---

## 📊 State Management

### Session Management

Each user conversation should have a unique `session_id`:

```javascript
// Generate session ID
function generateSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Store in localStorage
function getOrCreateSession() {
  let sessionId = localStorage.getItem('chat_session_id');
  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem('chat_session_id', sessionId);
  }
  return sessionId;
}

// Use in API calls
const sessionId = getOrCreateSession();
```

### Conversation History

The backend tracks conversation history automatically per session:

```javascript
async function getConversationHistory(sessionId) {
  const response = await fetch(
    `http://localhost:8000/api/memory/${sessionId}/`
  );
  const data = await response.json();
  return data.context; // Returns formatted conversation string
}

async function clearConversation(sessionId) {
  await fetch(`http://localhost:8000/api/memory/${sessionId}/`, {
    method: 'DELETE'
  });
  // Also clear local storage
  localStorage.removeItem('chat_session_id');
}
```

### Global State (React Context Example)

```jsx
import React, { createContext, useState, useContext } from 'react';

const ChatContext = createContext();

export function ChatProvider({ children }) {
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiBase] = useState('http://localhost:8000/api');

  const sendQuery = async (query) => {
    setLoading(true);
    try {
      const response = await fetch(`${apiBase}/query/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          session_id: sessionId,
          use_web_search: true,
          enhance_formatting: true
        })
      });
      const data = await response.json();
      setMessages(prev => [...prev, {
        role: 'user',
        content: query
      }, {
        role: 'assistant',
        content: data.response,
        sources: data.sources
      }]);
      return data;
    } finally {
      setLoading(false);
    }
  };

  const clearMessages = () => setMessages([]);

  return (
    <ChatContext.Provider value={{
      sessionId,
      messages,
      loading,
      apiBase,
      sendQuery,
      clearMessages
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = () => useContext(ChatContext);
```

---

## ⚠️ Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "error": "Error message",
  "details": "Additional details (optional)"
}
```

### Comprehensive Error Handler

```javascript
class APIError extends Error {
  constructor(message, status, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

async function apiRequest(endpoint, options = {}) {
  const baseUrl = 'http://localhost:8000/api';

  try {
    const response = await fetch(`${baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    // Handle HTTP errors
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(
        errorData.error || 'Request failed',
        response.status,
        errorData.details
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    // Network errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new APIError(
        'Cannot connect to server. Please check if backend is running.',
        0,
        error.message
      );
    }

    // Unknown errors
    throw new APIError(
      'An unexpected error occurred',
      500,
      error.message
    );
  }
}

// Usage with error handling
try {
  const result = await apiRequest('/query/', {
    method: 'POST',
    body: JSON.stringify({
      query: 'Test query',
      session_id: 'test'
    })
  });
  console.log('Success:', result);
} catch (error) {
  if (error.status === 400) {
    console.error('Bad request:', error.message);
  } else if (error.status === 500) {
    console.error('Server error:', error.message);
  } else if (error.status === 0) {
    console.error('Network error:', error.message);
  } else {
    console.error('Error:', error.message);
  }
}
```

### User-Friendly Error Messages

```javascript
function getUserFriendlyError(error) {
  const errorMessages = {
    0: 'Cannot connect to server. Please check your internet connection.',
    400: 'Invalid request. Please check your input and try again.',
    404: 'Resource not found. Please refresh the page.',
    429: 'Too many requests. Please wait a moment and try again.',
    500: 'Server error. Our team has been notified.',
    503: 'Service temporarily unavailable. Please try again later.'
  };

  return errorMessages[error.status] || 'Something went wrong. Please try again.';
}

// Usage in UI
catch (error) {
  const userMessage = getUserFriendlyError(error);
  showNotification(userMessage, 'error');
  console.error('Detailed error:', error); // For debugging
}
```

---

## ✅ Best Practices

### 1. Environment Configuration

```javascript
// config.js
const CONFIG = {
  development: {
    API_BASE: 'http://localhost:8000/api',
    WS_BASE: 'ws://localhost:8000/ws',
    TIMEOUT: 30000
  },
  production: {
    API_BASE: 'https://api.yourdomain.com/api',
    WS_BASE: 'wss://api.yourdomain.com/ws',
    TIMEOUT: 60000
  }
};

export const getConfig = () => {
  const env = process.env.NODE_ENV || 'development';
  return CONFIG[env];
};

// Usage
import { getConfig } from './config';
const { API_BASE } = getConfig();
```

### 2. Request Timeout

```javascript
async function fetchWithTimeout(url, options = {}, timeout = 30000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout');
    }
    throw error;
  }
}
```

### 3. Request Debouncing

```javascript
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Usage for search-as-you-type
const debouncedSearch = debounce(async (query) => {
  const results = await apiRequest('/query/', {
    method: 'POST',
    body: JSON.stringify({ query, session_id: sessionId })
  });
  displayResults(results);
}, 500);
```

### 4. Request Caching

```javascript
class APICache {
  constructor(ttl = 300000) { // 5 minutes default
    this.cache = new Map();
    this.ttl = ttl;
  }

  set(key, value) {
    this.cache.set(key, {
      value,
      timestamp: Date.now()
    });
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.value;
  }

  clear() {
    this.cache.clear();
  }
}

// Usage
const cache = new APICache();

async function getCachedKBStatus() {
  const cacheKey = 'kb_status';
  let data = cache.get(cacheKey);

  if (!data) {
    const response = await fetch('http://localhost:8000/api/knowledge-base/status/');
    data = await response.json();
    cache.set(cacheKey, data);
  }

  return data;
}
```

### 5. Loading States

```javascript
class LoadingManager {
  constructor() {
    this.loadingStates = new Map();
    this.listeners = new Set();
  }

  setLoading(key, isLoading) {
    this.loadingStates.set(key, isLoading);
    this.notifyListeners();
  }

  isLoading(key) {
    return this.loadingStates.get(key) || false;
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notifyListeners() {
    this.listeners.forEach(listener => listener(this.loadingStates));
  }
}

// Usage
const loadingManager = new LoadingManager();

async function sendQuery(query) {
  loadingManager.setLoading('query', true);
  try {
    const response = await apiRequest('/query/', {
      method: 'POST',
      body: JSON.stringify({ query })
    });
    return response;
  } finally {
    loadingManager.setLoading('query', false);
  }
}
```

---

## 🎨 Example Implementations

### Complete Vanilla JS Chat App

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>RAG Chat</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }
    .chat-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      max-width: 800px;
      margin: 0 auto;
      width: 100%;
      padding: 20px;
    }
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      background: #f5f5f5;
      border-radius: 10px;
      margin-bottom: 20px;
    }
    .message {
      margin-bottom: 15px;
      padding: 12px;
      border-radius: 8px;
      max-width: 80%;
    }
    .message.user {
      background: #007bff;
      color: white;
      margin-left: auto;
    }
    .message.assistant {
      background: white;
      border: 1px solid #ddd;
    }
    .message .sources {
      margin-top: 8px;
      font-size: 0.85em;
      opacity: 0.8;
    }
    .input-area {
      display: flex;
      gap: 10px;
    }
    .input-area input {
      flex: 1;
      padding: 12px;
      border: 1px solid #ddd;
      border-radius: 8px;
      font-size: 14px;
    }
    .input-area button {
      padding: 12px 24px;
      background: #007bff;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
    }
    .input-area button:disabled {
      background: #ccc;
      cursor: not-allowed;
    }
    .loading {
      text-align: center;
      padding: 12px;
      color: #666;
      font-style: italic;
    }
  </style>
</head>
<body>
  <div class="chat-container">
    <div class="messages" id="messages"></div>
    <div class="input-area">
      <input
        type="text"
        id="queryInput"
        placeholder="Ask a question..."
        autocomplete="off"
      >
      <button id="sendButton">Send</button>
    </div>
  </div>

  <script>
    const API_BASE = 'http://localhost:8000/api';
    const sessionId = `session_${Date.now()}`;

    const messagesContainer = document.getElementById('messages');
    const queryInput = document.getElementById('queryInput');
    const sendButton = document.getElementById('sendButton');

    function addMessage(role, content, sources = null) {
      const messageDiv = document.createElement('div');
      messageDiv.className = `message ${role}`;

      const contentDiv = document.createElement('div');
      contentDiv.textContent = content;
      messageDiv.appendChild(contentDiv);

      if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';
        sourcesDiv.innerHTML = '<strong>Sources:</strong> ' +
          sources.map(s => `${s.source} (${s.score.toFixed(2)})`).join(', ');
        messageDiv.appendChild(sourcesDiv);
      }

      messagesContainer.appendChild(messageDiv);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function showLoading(show) {
      const existingLoading = document.querySelector('.loading');
      if (show && !existingLoading) {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.textContent = 'AI is thinking...';
        messagesContainer.appendChild(loadingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      } else if (!show && existingLoading) {
        existingLoading.remove();
      }
    }

    async function sendQuery() {
      const query = queryInput.value.trim();
      if (!query) return;

      // Add user message
      addMessage('user', query);
      queryInput.value = '';
      sendButton.disabled = true;
      showLoading(true);

      try {
        const response = await fetch(`${API_BASE}/query/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: query,
            session_id: sessionId,
            use_web_search: true,
            enhance_formatting: true
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        addMessage('assistant', data.response, data.sources);
      } catch (error) {
        console.error('Error:', error);
        addMessage('assistant', 'Sorry, something went wrong. Please try again.');
      } finally {
        showLoading(false);
        sendButton.disabled = false;
        queryInput.focus();
      }
    }

    sendButton.addEventListener('click', sendQuery);
    queryInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendQuery();
    });

    // Initial message
    addMessage('assistant', 'Hello! How can I help you today?');
  </script>
</body>
</html>
```

### TypeScript API Client

```typescript
// api-client.ts
export interface QueryRequest {
  query: string;
  session_id: string;
  use_web_search?: boolean;
  enhance_formatting?: boolean;
}

export interface QueryResponse {
  response: string;
  session_id: string;
  query_type: string;
  confidence_score: number;
  sources: Source[];
  processing_time_ms: number;
  metadata: {
    tokens_used: number;
    cost_usd: number;
  };
}

export interface Source {
  source: string;
  score: number;
}

export interface UploadResponse {
  message: string;
  filename: string;
  chunks_created: number;
  file_size_kb: number;
  document_id: string;
}

export class RAGAPIClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = 'http://localhost:8000/api', timeout: number = 30000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.error || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  }

  async sendQuery(request: QueryRequest): Promise<QueryResponse> {
    return this.request<QueryResponse>('/query/', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<UploadResponse>('/upload/document/', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  }

  async getHealth(): Promise<any> {
    return this.request('/health/');
  }

  async getKnowledgeBaseStatus(): Promise<any> {
    return this.request('/knowledge-base/status/');
  }

  async getSessionMemory(sessionId: string): Promise<any> {
    return this.request(`/memory/${sessionId}/`);
  }

  async clearSessionMemory(sessionId: string): Promise<any> {
    return this.request(`/memory/${sessionId}/`, { method: 'DELETE' });
  }

  async getSessions(): Promise<any> {
    return this.request('/sessions/');
  }

  async getDashboard(days: number = 7): Promise<any> {
    return this.request(`/dashboard/?days=${days}`);
  }
}

// Usage
const client = new RAGAPIClient();

// Send query
const response = await client.sendQuery({
  query: 'What is the tuition fee?',
  session_id: 'test_session',
  use_web_search: true,
});

console.log(response.response);
```

---

## 🧪 Testing Your Integration

### 1. Manual Testing Checklist

```
□ Backend Health Check
  - GET /api/health/ returns 200
  - Response contains "status": "healthy"

□ Basic Query
  - POST /api/query/ with valid data returns 200
  - Response contains "response" field
  - session_id is preserved

□ File Upload
  - POST /api/upload/document/ with PDF returns 200
  - chunks_created > 0
  - Knowledge base updated

□ Session Memory
  - GET /api/memory/{session_id}/ returns conversation
  - DELETE /api/memory/{session_id}/ clears memory

□ Error Handling
  - Invalid requests return 400
  - Missing required fields return error message
  - Network errors handled gracefully

□ Performance
  - Queries complete in < 5 seconds
  - UI remains responsive during loading
  - No memory leaks on repeated queries
```

### 2. Automated Tests (Jest Example)

```javascript
// api.test.js
const API_BASE = 'http://localhost:8000/api';

describe('RAG API Integration', () => {
  let sessionId;

  beforeAll(() => {
    sessionId = `test_session_${Date.now()}`;
  });

  test('Health check returns healthy status', async () => {
    const response = await fetch(`${API_BASE}/health/`);
    const data = await response.json();

    expect(response.ok).toBe(true);
    expect(data.status).toBe('healthy');
  });

  test('Query processing returns valid response', async () => {
    const response = await fetch(`${API_BASE}/query/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: 'Test query',
        session_id: sessionId,
      }),
    });
    const data = await response.json();

    expect(response.ok).toBe(true);
    expect(data).toHaveProperty('response');
    expect(data).toHaveProperty('session_id');
    expect(data.session_id).toBe(sessionId);
  });

  test('Invalid request returns error', async () => {
    const response = await fetch(`${API_BASE}/query/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}), // Missing required fields
    });
    const data = await response.json();

    expect(response.ok).toBe(false);
    expect(data).toHaveProperty('error');
  });

  afterAll(async () => {
    // Clean up test session
    await fetch(`${API_BASE}/memory/${sessionId}/`, {
      method: 'DELETE',
    });
  });
});
```

### 3. Performance Testing Script

```javascript
// performance-test.js
async function measureQueryPerformance(numQueries = 10) {
  const API_BASE = 'http://localhost:8000/api';
  const sessionId = `perf_test_${Date.now()}`;
  const times = [];

  console.log(`Running ${numQueries} queries...`);

  for (let i = 0; i < numQueries; i++) {
    const start = Date.now();

    await fetch(`${API_BASE}/query/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: `Test query ${i}`,
        session_id: sessionId,
      }),
    });

    const duration = Date.now() - start;
    times.push(duration);
    console.log(`Query ${i + 1}: ${duration}ms`);
  }

  const avg = times.reduce((a, b) => a + b, 0) / times.length;
  const min = Math.min(...times);
  const max = Math.max(...times);

  console.log('\nPerformance Summary:');
  console.log(`Average: ${avg.toFixed(2)}ms`);
  console.log(`Min: ${min}ms`);
  console.log(`Max: ${max}ms`);
}

measureQueryPerformance();
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. CORS Errors

**Problem:** `Access-Control-Allow-Origin` error in browser console

**Solution:**
```python
# In config/settings.py
CORS_ALLOW_ALL_ORIGINS = True  # Development
# Or for production:
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-frontend-domain.com"
]
```

#### 2. Backend Not Reachable

**Problem:** `Failed to fetch` or connection refused

**Solutions:**
- Check backend is running: `http://localhost:8000/api/health/`
- Verify port 8000 is open
- Check firewall settings
- Ensure correct URL (http vs https)

#### 3. Slow Response Times

**Problem:** Queries take >10 seconds

**Solutions:**
- Check Azure OpenAI quota/rate limits
- Verify vector database has sufficient memory
- Monitor backend logs for errors
- Consider adding request timeout

#### 4. Session Not Persisting

**Problem:** Conversation context lost between queries

**Solutions:**
- Ensure same `session_id` used across requests
- Check session isn't being cleared unintentionally
- Verify backend session storage

#### 5. File Upload Fails

**Problem:** Document upload returns error

**Solutions:**
- Check file size (backend may have limits)
- Verify file type is supported (PDF, DOCX, TXT, HTML)
- Ensure `Content-Type: multipart/form-data`
- Don't set Content-Type manually, let browser handle it

### Debug Mode

Enable detailed logging:

```javascript
class DebugAPIClient {
  constructor(apiBase) {
    this.apiBase = apiBase;
    this.logRequests = true;
  }

  async request(endpoint, options = {}) {
    const url = `${this.apiBase}${endpoint}`;

    if (this.logRequests) {
      console.group('API Request');
      console.log('URL:', url);
      console.log('Method:', options.method || 'GET');
      console.log('Headers:', options.headers);
      console.log('Body:', options.body);
      console.groupEnd();
    }

    const start = Date.now();

    try {
      const response = await fetch(url, options);
      const duration = Date.now() - start;
      const data = await response.json();

      if (this.logRequests) {
        console.group('API Response');
        console.log('Status:', response.status);
        console.log('Duration:', duration + 'ms');
        console.log('Data:', data);
        console.groupEnd();
      }

      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }
}
```

---

## 📚 Additional Resources

- **Full API Documentation:** See `ENDPOINTS.md`
- **Backend README:** See `README.md`
- **Example Frontend:** Check `/static/` directory
- **Postman Collection:** Import endpoints from `ENDPOINTS.md`

---

## 🤝 Support

For issues or questions:
1. Check `ENDPOINTS.md` for API reference
2. Review backend logs: `Studynet-AI-Agent/server.log`
3. Test endpoints with Postman
4. Check browser console for errors

---

**Last Updated:** 2025-10-06
**API Version:** 1.0.0
