// RAG AI Agent Frontend JavaScript - Complete Fixed Version
class RAGAgent {
    constructor() {
        this.apiBase = '/rag';
        this.sessionId = this.generateSessionId();
        this.isLoading = false;
        this.recentQueries = JSON.parse(localStorage.getItem('recentQueries') || '[]');
        
        this.initializeElements();
        this.bindEvents();
        this.loadSystemStatus();
        this.updateRecentQueries();
        this.updateSessionDisplay();
    }

    initializeElements() {
        this.elements = {
            chatMessages: document.getElementById('chatMessages'),
            queryInput: document.getElementById('queryInput'),
            sendButton: document.getElementById('sendButton'),
            useWebSearch: document.getElementById('useWebSearch'),
            enhanceFormatting: document.getElementById('enhanceFormatting'),
            clearChat: document.getElementById('clearChat'),
            uploadDoc: document.getElementById('uploadDoc'),
            uploadModal: document.getElementById('uploadModal'),
            closeModal: document.getElementById('closeModal'),
            fileInput: document.getElementById('fileInput'),
            uploadArea: document.getElementById('uploadArea'),
            uploadProgress: document.getElementById('uploadProgress'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            apiStatus: document.getElementById('apiStatus'),
            kbStatus: document.getElementById('kbStatus'),
            sessionCount: document.getElementById('sessionCount'),
            sessionId: document.getElementById('sessionId'),
            responseTime: document.getElementById('responseTime'),
            recentQueries: document.getElementById('recentQueries'),
            // Developer mode elements
            developerToggle: document.getElementById('developerToggle'),
            developerMode: document.getElementById('developerMode'),
            closeDeveloperMode: document.getElementById('closeDeveloperMode'),
            devSessionId: document.getElementById('devSessionId'),
            getMemory: document.getElementById('getMemory'),
            clearMemory: document.getElementById('clearMemory'),
            listSessions: document.getElementById('listSessions'),
            memoryOutput: document.getElementById('memoryOutput'),
            getKbStatus: document.getElementById('getKbStatus'),
            reloadKb: document.getElementById('reloadKb'),
            clearVectorStore: document.getElementById('clearVectorStore'),
            kbOutput: document.getElementById('kbOutput'),
            getMetrics: document.getElementById('getMetrics'),
            resetMetrics: document.getElementById('resetMetrics'),
            metricsOutput: document.getElementById('metricsOutput'),
            testEndpoint: document.getElementById('testEndpoint'),
            testApi: document.getElementById('testApi'),
            apiTestOutput: document.getElementById('apiTestOutput'),
            connectionStatus: document.getElementById('connectionStatus'),
            lastRequest: document.getElementById('lastRequest'),
            errorCount: document.getElementById('errorCount')
        };
        
        this.developerModeActive = false;
        this.errorCount = 0;
        this.lastRequestTime = null;
    }

    bindEvents() {
        // Send message
        if (this.elements.sendButton) {
            this.elements.sendButton.addEventListener('click', () => this.sendMessage());
        }
        if (this.elements.queryInput) {
            this.elements.queryInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        // Clear chat
        if (this.elements.clearChat) {
            this.elements.clearChat.addEventListener('click', () => this.clearChat());
        }

        // Upload document
        if (this.elements.uploadDoc) {
            this.elements.uploadDoc.addEventListener('click', () => this.showUploadModal());
        }
        if (this.elements.closeModal) {
            this.elements.closeModal.addEventListener('click', () => this.hideUploadModal());
        }
        if (this.elements.uploadArea) {
            this.elements.uploadArea.addEventListener('click', () => this.elements.fileInput.click());
        }
        if (this.elements.fileInput) {
            this.elements.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }

        // Close modal on outside click
        if (this.elements.uploadModal) {
            this.elements.uploadModal.addEventListener('click', (e) => {
                if (e.target === this.elements.uploadModal) {
                    this.hideUploadModal();
                }
            });
        }

        // Auto-resize input
        if (this.elements.queryInput) {
            this.elements.queryInput.addEventListener('input', () => {
                this.elements.queryInput.style.height = 'auto';
                this.elements.queryInput.style.height = this.elements.queryInput.scrollHeight + 'px';
            });
        }

        // Developer mode events
        if (this.elements.developerToggle) {
            this.elements.developerToggle.addEventListener('click', () => this.toggleDeveloperMode());
        }
        if (this.elements.closeDeveloperMode) {
            this.elements.closeDeveloperMode.addEventListener('click', () => this.toggleDeveloperMode());
        }
        if (this.elements.getMemory) {
            this.elements.getMemory.addEventListener('click', () => this.getMemoryForSession());
        }
        if (this.elements.clearMemory) {
            this.elements.clearMemory.addEventListener('click', () => this.clearSessionMemory());
        }
        if (this.elements.listSessions) {
            this.elements.listSessions.addEventListener('click', () => this.listAllSessions());
        }
        if (this.elements.getKbStatus) {
            this.elements.getKbStatus.addEventListener('click', () => this.getKnowledgeBaseStatus());
        }
        if (this.elements.reloadKb) {
            this.elements.reloadKb.addEventListener('click', () => this.reloadKnowledgeBase());
        }
        if (this.elements.clearVectorStore) {
            this.elements.clearVectorStore.addEventListener('click', () => this.clearVectorStore());
        }
        if (this.elements.getMetrics) {
            this.elements.getMetrics.addEventListener('click', () => this.getSystemMetrics());
        }
        if (this.elements.resetMetrics) {
            this.elements.resetMetrics.addEventListener('click', () => this.resetSystemMetrics());
        }
        if (this.elements.testApi) {
            this.elements.testApi.addEventListener('click', () => this.testApiEndpoint());
        }
    }

    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }

    async sendMessage() {
        const query = this.elements.queryInput?.value.trim();
        if (!query || this.isLoading) return;

        this.isLoading = true;
        if (this.elements.sendButton) this.elements.sendButton.disabled = true;
        if (this.elements.queryInput) this.elements.queryInput.disabled = true;

        // Add user message to chat
        this.addMessage('user', query);
        if (this.elements.queryInput) {
            this.elements.queryInput.value = '';
            this.elements.queryInput.style.height = 'auto';
        }

        // Add to recent queries
        this.addToRecentQueries(query);

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const startTime = Date.now();
            const response = await this.makeRequest('/query/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: JSON.stringify({
                    query: query,
                    session_id: this.sessionId,
                    use_web_search: this.elements.useWebSearch?.checked || true,
                    enhance_formatting: this.elements.enhanceFormatting?.checked || true
                })
            });

            const endTime = Date.now();
            const responseTime = (endTime - startTime) / 1000;

            this.hideTypingIndicator();

            if (response.ok) {
                const data = await response.json();
                this.addMessage('assistant', data.answer, data.sources, data.confidence_score, data.web_search_used);
                this.updateResponseTime(responseTime);
            } else {
                const error = await response.json();
                this.addMessage('assistant', `Error: ${error.error || 'Something went wrong'}`);
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('assistant', `Error: ${error.message}`);
        } finally {
            this.isLoading = false;
            if (this.elements.sendButton) this.elements.sendButton.disabled = false;
            if (this.elements.queryInput) {
                this.elements.queryInput.disabled = false;
                this.elements.queryInput.focus();
            }
        }
    }

    // Get CSRF token from Django
    getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        const csrfMeta = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfMeta ? csrfMeta.value : '';
    }

    addMessage(role, content, sources = [], confidence = null, webSearchUsed = false) {
        if (!this.elements.chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = this.formatMessage(content);

        contentDiv.appendChild(bubble);

        // Add sources if available
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            sourcesDiv.innerHTML = '<h4><i class="fas fa-link"></i> Sources</h4>';
            
            sources.forEach((source, index) => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.innerHTML = `<strong>${source.type}:</strong> ${source.content}`;
                sourcesDiv.appendChild(sourceItem);
            });
            
            contentDiv.appendChild(sourcesDiv);
        }

        // Add metadata
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        metaDiv.innerHTML = `
            <span><i class="fas fa-clock"></i> ${new Date().toLocaleTimeString()}</span>
            ${confidence ? `<span><i class="fas fa-chart-line"></i> Confidence: ${(confidence * 100).toFixed(1)}%</span>` : ''}
            ${webSearchUsed ? '<span><i class="fas fa-globe"></i> Web Search Used</span>' : ''}
        `;
        contentDiv.appendChild(metaDiv);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);

        // Remove welcome message if it exists
        const welcomeMessage = this.elements.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        this.elements.chatMessages.appendChild(messageDiv);
        
        setTimeout(() => {
            messageDiv.classList.add('fade-in');
        }, 50);
        
        this.scrollToBottom();
    }

    formatMessage(content) {
        return content;
    }

    showTypingIndicator() {
        if (!this.elements.chatMessages) return;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant fade-in typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    <div class="typing-indicator">
                        <span>AI is thinking</span>
                        <div class="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        this.elements.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        if (this.elements.chatMessages) {
            this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        }
    }

    clearChat() {
        if (!this.elements.chatMessages) return;

        this.elements.chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">
                    <i class="fas fa-robot"></i>
                </div>
                <h2>Welcome to RAG AI Agent</h2>
                <p>Ask me anything about your documents or get help with Studynet CRM processes.</p>
                <div class="feature-highlights">
                    <div class="feature">
                        <i class="fas fa-search"></i>
                        <span>Document Search</span>
                    </div>
                    <div class="feature">
                        <i class="fas fa-globe"></i>
                        <span>Web Search</span>
                    </div>
                    <div class="feature">
                        <i class="fas fa-memory"></i>
                        <span>Memory Context</span>
                    </div>
                </div>
            </div>
        `;
        this.sessionId = this.generateSessionId();
        this.updateSessionDisplay();
    }

    showUploadModal() {
        if (this.elements.uploadModal) {
            this.elements.uploadModal.style.display = 'block';
        }
        if (this.elements.uploadProgress) {
            this.elements.uploadProgress.style.display = 'none';
        }
    }

    hideUploadModal() {
        if (this.elements.uploadModal) {
            this.elements.uploadModal.style.display = 'none';
        }
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (this.elements.uploadProgress) {
            this.elements.uploadProgress.style.display = 'block';
        }
        if (this.elements.uploadArea) {
            this.elements.uploadArea.style.display = 'none';
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await this.makeRequest('/upload/document/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification(`Document uploaded successfully! ${data.chunks_created} chunks created.`, 'success');
                this.hideUploadModal();
                this.loadSystemStatus();
            } else {
                const error = await response.json();
                this.showNotification(`Upload failed: ${error.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Upload failed: ${error.message}`, 'error');
        } finally {
            if (this.elements.uploadProgress) {
                this.elements.uploadProgress.style.display = 'none';
            }
            if (this.elements.uploadArea) {
                this.elements.uploadArea.style.display = 'block';
            }
            if (this.elements.fileInput) {
                this.elements.fileInput.value = '';
            }
        }
    }

    async loadSystemStatus() {
        try {
            // Check API status
            const apiResponse = await this.makeRequest('/health/');
            if (apiResponse.ok) {
                if (this.elements.apiStatus) {
                    this.elements.apiStatus.textContent = 'Online';
                    this.elements.apiStatus.className = 'status-value online';
                }
            } else {
                throw new Error('API not responding');
            }

            // Check knowledge base status
            const kbResponse = await this.makeRequest('/knowledge-base/status/');
            if (kbResponse.ok) {
                const kbData = await kbResponse.json();
                if (this.elements.kbStatus) {
                    this.elements.kbStatus.textContent = `${kbData.total_documents} documents`;
                    this.elements.kbStatus.className = 'status-value online';
                }
            }

            // Get session count
            const sessionsResponse = await this.makeRequest('/sessions/');
            if (sessionsResponse.ok) {
                const sessionsData = await sessionsResponse.json();
                if (this.elements.sessionCount) {
                    this.elements.sessionCount.textContent = sessionsData.count;
                }
            }
        } catch (error) {
            console.error('System status error:', error);
            if (this.elements.apiStatus) {
                this.elements.apiStatus.textContent = 'Offline';
                this.elements.apiStatus.className = 'status-value offline';
            }
            if (this.elements.kbStatus) {
                this.elements.kbStatus.textContent = 'Unknown';
                this.elements.kbStatus.className = 'status-value offline';
            }
        }
    }

    updateSessionDisplay() {
        if (this.elements.sessionId) {
            this.elements.sessionId.value = this.sessionId;
        }
    }

    updateResponseTime(time) {
        if (this.elements.responseTime) {
            this.elements.responseTime.textContent = `${time.toFixed(2)}s`;
        }
    }

    addToRecentQueries(query) {
        this.recentQueries.unshift(query);
        this.recentQueries = this.recentQueries.slice(0, 10);
        localStorage.setItem('recentQueries', JSON.stringify(this.recentQueries));
        this.updateRecentQueries();
    }

    updateRecentQueries() {
        if (!this.elements.recentQueries) return;

        if (this.recentQueries.length === 0) {
            this.elements.recentQueries.innerHTML = '<p class="no-queries">No recent queries</p>';
            return;
        }

        this.elements.recentQueries.innerHTML = this.recentQueries
            .map(query => `<div class="recent-query" onclick="ragAgent.loadQuery('${query.replace(/'/g, "\\'")}')">${query}</div>`)
            .join('');
    }

    loadQuery(query) {
        if (this.elements.queryInput) {
            this.elements.queryInput.value = query;
            this.elements.queryInput.focus();
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 3000;
            animation: slideInRight 0.3s ease;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        `;

        const colors = {
            success: '#38a169',
            error: '#e53e3e',
            info: '#3182ce',
            warning: '#d69e2e'
        };

        notification.style.backgroundColor = colors[type] || colors.info;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    async makeRequest(endpoint, options = {}) {
        const url = this.apiBase + endpoint;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        this.lastRequestTime = new Date().toLocaleTimeString();
        this.updateDebugInfo();

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            return response;
        } catch (error) {
            this.errorCount++;
            this.updateDebugInfo();
            throw error;
        }
    }

    // Developer Mode Methods
    toggleDeveloperMode() {
        this.developerModeActive = !this.developerModeActive;
        if (this.elements.developerMode) {
            this.elements.developerMode.classList.toggle('active', this.developerModeActive);
        }
        
        if (this.elements.developerToggle) {
            if (this.developerModeActive) {
                this.elements.developerToggle.innerHTML = '<i class="fas fa-times"></i>';
                this.elements.developerToggle.title = 'Close Developer Mode';
            } else {
                this.elements.developerToggle.innerHTML = '<i class="fas fa-code"></i>';
                this.elements.developerToggle.title = 'Developer Mode';
            }
        }
    }

    updateDebugInfo() {
        if (this.elements.lastRequest) {
            this.elements.lastRequest.innerHTML = `<i class="fas fa-clock"></i><span>Last Request: ${this.lastRequestTime || 'None'}</span>`;
        }
        if (this.elements.errorCount) {
            this.elements.errorCount.innerHTML = `<i class="fas fa-exclamation-triangle"></i><span>Errors: ${this.errorCount}</span>`;
        }
        
        if (this.elements.connectionStatus) {
            this.elements.connectionStatus.innerHTML = `
                <i class="fas fa-circle ${this.errorCount > 0 ? 'offline' : 'online'}"></i>
                <span>Connection: ${this.errorCount > 0 ? 'Issues' : 'OK'}</span>
            `;
        }
    }

    async getMemoryForSession() {
        const sessionId = this.elements.devSessionId?.value || this.sessionId;
        try {
            const response = await this.makeRequest(`/memory/${sessionId}/`);
            const data = await response.json();
            
            if (this.elements.memoryOutput) {
                this.elements.memoryOutput.style.display = 'block';
                this.elements.memoryOutput.textContent = JSON.stringify(data, null, 2);
            }
            this.showNotification('Memory retrieved successfully!', 'success');
        } catch (error) {
            if (this.elements.memoryOutput) {
                this.elements.memoryOutput.style.display = 'block';
                this.elements.memoryOutput.textContent = `Error: ${error.message}`;
            }
            this.showNotification('Failed to get memory', 'error');
        }
    }

    async clearSessionMemory() {
        const sessionId = this.elements.devSessionId?.value || this.sessionId;
        if (!confirm(`Are you sure you want to clear memory for session: ${sessionId}?`)) {
            return;
        }
        
        try {
            const response = await this.makeRequest(`/memory/${sessionId}/`, { 
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                }
            });
            if (response.ok) {
                if (this.elements.memoryOutput) {
                    this.elements.memoryOutput.style.display = 'block';
                    this.elements.memoryOutput.textContent = 'Memory cleared successfully!';
                }
                this.showNotification('Memory cleared successfully!', 'success');
            } else {
                throw new Error('Failed to clear memory');
            }
        } catch (error) {
            if (this.elements.memoryOutput) {
                this.elements.memoryOutput.style.display = 'block';
                this.elements.memoryOutput.textContent = `Error: ${error.message}`;
            }
            this.showNotification('Failed to clear memory', 'error');
        }
    }

    async listAllSessions() {
        try {
            const response = await this.makeRequest('/sessions/');
            const data = await response.json();
            
            if (this.elements.memoryOutput) {
                this.elements.memoryOutput.style.display = 'block';
                this.elements.memoryOutput.textContent = JSON.stringify(data, null, 2);
            }
            this.showNotification('Sessions retrieved successfully!', 'success');
        } catch (error) {
            if (this.elements.memoryOutput) {
                this.elements.memoryOutput.style.display = 'block';
                this.elements.memoryOutput.textContent = `Error: ${error.message}`;
            }
            this.showNotification('Failed to get sessions', 'error');
        }
    }

    async getKnowledgeBaseStatus() {
        try {
            const response = await this.makeRequest('/knowledge-base/status/');
            const data = await response.json();
            
            if (this.elements.kbOutput) {
                this.elements.kbOutput.style.display = 'block';
                this.elements.kbOutput.textContent = JSON.stringify(data, null, 2);
            }
            this.showNotification('Knowledge base status retrieved!', 'success');
        } catch (error) {
            if (this.elements.kbOutput) {
                this.elements.kbOutput.style.display = 'block';
                this.elements.kbOutput.textContent = `Error: ${error.message}`;
            }
            this.showNotification('Failed to get KB status', 'error');
        }
    }

    async reloadKnowledgeBase() {
        if (!confirm('Are you sure you want to reload the knowledge base? This may take a while.')) {
            return;
        }
        
        try {
            if (this.elements.reloadKb) {
                this.elements.reloadKb.classList.add('loading');
                this.elements.reloadKb.disabled = true;
            }
            
            const response = await this.makeRequest('/knowledge-base/reload/', { 
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                }
            });
            const data = await response.json();
            
            if (this.elements.kbOutput) {
                this.elements.kbOutput.style.display = 'block';
                this.elements.kbOutput.textContent = JSON.stringify(data, null, 2);
            }
            this.showNotification('Knowledge base reloaded successfully!', 'success');
            
            this.loadSystemStatus();
        } catch (error) {
            if (this.elements.kbOutput) {
                this.elements.kbOutput.style.display = 'block';
                this.elements.kbOutput.textContent = `Error: ${error.message}`;
            }
            this.showNotification('Failed to reload knowledge base', 'error');
        } finally {
            if (this.elements.reloadKb) {
                this.elements.reloadKb.classList.remove('loading');
                this.elements.reloadKb.disabled = false;
            }
        }
    }

    async clearVectorStore() {
        if (!confirm('Are you sure you want to clear the vector store? This will delete ALL document data!')) {
            return;
        }
        
        try {
            if (this.elements.clearVectorStore) {
                this.elements.clearVectorStore.classList.add('loading');
                this.elements.clearVectorStore.disabled = true;
            }
            
            const response = await this.makeRequest('/vectorstore/clear/', { 
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                }
            });
            const data = await response.json();
            
            if (this.elements.kbOutput) {
                this.elements.kbOutput.style.display = 'block';
                this.elements.kbOutput.textContent = JSON.stringify(data, null, 2);
            }
            this.showNotification('Vector store cleared successfully!', 'success');
            
            this.loadSystemStatus();
        } catch (error) {
            if (this.elements.kbOutput) {
                this.elements.kbOutput.style.display = 'block';
                this.elements.kbOutput.textContent = `Error: ${error.message}`;
            }
            this.showNotification('Failed to clear vector store', 'error');
        } finally {
            if (this.elements.clearVectorStore) {
                this.elements.clearVectorStore.classList.remove('loading');
                this.elements.clearVectorStore.disabled = false;
            }
        }
    }

    async getSystemMetrics() {
        try {
            const response = await this.makeRequest('/metrics/');
            const data = await response.json();
            
            if (this.elements.metricsOutput) {
                this.elements.metricsOutput.style.display = 'block';
                this.elements.metricsOutput.textContent = JSON.stringify(data, null, 2);
            }
            this.showNotification('Metrics reset successfully!', 'success');
        } catch (error) {
            if (this.elements.metricsOutput) {
                this.elements.metricsOutput.style.display = 'block';
                this.elements.metricsOutput.textContent = `Error: ${error.message}`;
            }
            this.showNotification('Failed to reset metrics', 'error');
        }
    }

    async testApiEndpoint() {
        const endpoint = this.elements.testEndpoint?.value.trim();
        if (!endpoint) {
            this.showNotification('Please enter an endpoint', 'error');
            return;
        }
        
        try {
            const response = await this.makeRequest(endpoint);
            const data = await response.json();
            
            if (this.elements.apiTestOutput) {
                this.elements.apiTestOutput.style.display = 'block';
                this.elements.apiTestOutput.textContent = `Status: ${response.status}\n\n${JSON.stringify(data, null, 2)}`;
            }
            this.showNotification('API test completed!', 'success');
        } catch (error) {
            if (this.elements.apiTestOutput) {
                this.elements.apiTestOutput.style.display = 'block';
                this.elements.apiTestOutput.textContent = `Error: ${error.message}`;
            }
            this.showNotification('API test failed', 'error');
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ragAgent = new RAGAgent();
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .fade-in {
        animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .typing-dots {
        display: inline-flex;
        gap: 4px;
        margin-left: 8px;
    }

    .typing-dots span {
        width: 6px;
        height: 6px;
        background: currentColor;
        border-radius: 50%;
        animation: typing 1.5s infinite ease-in-out;
    }

    .typing-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }

    .typing-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }

    @keyframes typing {
        0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.3;
        }
        30% {
            transform: translateY(-10px);
            opacity: 1;
        }
    }

    .status-value.online {
        color: #38a169 !important;
    }

    .status-value.offline {
        color: #e53e3e !important;
    }

    .dev-status i.online {
        color: #38a169;
    }

    .dev-status i.offline {
        color: #e53e3e;
    }
`;
document.head.appendChild(style); 'block';