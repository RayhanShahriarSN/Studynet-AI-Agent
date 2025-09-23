// RAG AI Agent Frontend JavaScript
class RAGAgent {
    constructor() {
        this.apiBase = '/api';
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
            recentQueries: document.getElementById('recentQueries')
        };
    }

    bindEvents() {
        // Send message
        this.elements.sendButton.addEventListener('click', () => this.sendMessage());
        this.elements.queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Clear chat
        this.elements.clearChat.addEventListener('click', () => this.clearChat());

        // Upload document
        this.elements.uploadDoc.addEventListener('click', () => this.showUploadModal());
        this.elements.closeModal.addEventListener('click', () => this.hideUploadModal());
        this.elements.uploadArea.addEventListener('click', () => this.elements.fileInput.click());
        this.elements.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));

        // Close modal on outside click
        this.elements.uploadModal.addEventListener('click', (e) => {
            if (e.target === this.elements.uploadModal) {
                this.hideUploadModal();
            }
        });

        // Auto-resize input
        this.elements.queryInput.addEventListener('input', () => {
            this.elements.queryInput.style.height = 'auto';
            this.elements.queryInput.style.height = this.elements.queryInput.scrollHeight + 'px';
        });
    }

    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }

    async sendMessage() {
        const query = this.elements.queryInput.value.trim();
        if (!query || this.isLoading) return;

        this.isLoading = true;
        this.elements.sendButton.disabled = true;
        this.elements.queryInput.disabled = true;

        // Add user message to chat
        this.addMessage('user', query);
        this.elements.queryInput.value = '';
        this.elements.queryInput.style.height = 'auto';

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
                },
                body: JSON.stringify({
                    query: query,
                    session_id: this.sessionId,
                    use_web_search: this.elements.useWebSearch.checked,
                    enhance_formatting: this.elements.enhanceFormatting.checked
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
            this.elements.sendButton.disabled = false;
            this.elements.queryInput.disabled = false;
            this.elements.queryInput.focus();
        }
    }

    addMessage(role, content, sources = [], confidence = null, webSearchUsed = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role} fade-in`;

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
        this.scrollToBottom();
    }

    formatMessage(content) {
        // Content is already HTML from the backend, so return as-is
        // The backend now converts markdown to HTML before sending
        return content;
    }

    showTypingIndicator() {
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
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    clearChat() {
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
        this.elements.uploadModal.style.display = 'block';
        this.elements.uploadProgress.style.display = 'none';
    }

    hideUploadModal() {
        this.elements.uploadModal.style.display = 'none';
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        this.elements.uploadProgress.style.display = 'block';
        this.elements.uploadArea.style.display = 'none';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await this.makeRequest('/upload/document/', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification(`Document uploaded successfully! ${data.chunks_created} chunks created.`, 'success');
                this.hideUploadModal();
            } else {
                const error = await response.json();
                this.showNotification(`Upload failed: ${error.error}`, 'error');
            }
        } catch (error) {
            this.showNotification(`Upload failed: ${error.message}`, 'error');
        } finally {
            this.elements.uploadProgress.style.display = 'none';
            this.elements.uploadArea.style.display = 'block';
            this.elements.fileInput.value = '';
        }
    }

    async loadSystemStatus() {
        try {
            // Check API status
            const apiResponse = await this.makeRequest('/health/');
            if (apiResponse.ok) {
                this.elements.apiStatus.textContent = 'Online';
                this.elements.apiStatus.className = 'status-value online';
            } else {
                throw new Error('API not responding');
            }

            // Check knowledge base status
            const kbResponse = await this.makeRequest('/knowledge-base/status/');
            if (kbResponse.ok) {
                const kbData = await kbResponse.json();
                this.elements.kbStatus.textContent = `${kbData.total_documents} documents`;
                this.elements.kbStatus.className = 'status-value online';
            }

            // Get session count
            const sessionsResponse = await this.makeRequest('/sessions/');
            if (sessionsResponse.ok) {
                const sessionsData = await sessionsResponse.json();
                this.elements.sessionCount.textContent = sessionsData.count;
            }
        } catch (error) {
            this.elements.apiStatus.textContent = 'Offline';
            this.elements.apiStatus.className = 'status-value offline';
            this.elements.kbStatus.textContent = 'Unknown';
            this.elements.kbStatus.className = 'status-value offline';
        }
    }

    updateSessionDisplay() {
        this.elements.sessionId.value = this.sessionId;
    }

    updateResponseTime(time) {
        this.elements.responseTime.textContent = `${time.toFixed(2)}s`;
    }

    addToRecentQueries(query) {
        this.recentQueries.unshift(query);
        this.recentQueries = this.recentQueries.slice(0, 10); // Keep only last 10
        localStorage.setItem('recentQueries', JSON.stringify(this.recentQueries));
        this.updateRecentQueries();
    }

    updateRecentQueries() {
        if (this.recentQueries.length === 0) {
            this.elements.recentQueries.innerHTML = '<p class="no-queries">No recent queries</p>';
            return;
        }

        this.elements.recentQueries.innerHTML = this.recentQueries
            .map(query => `<div class="recent-query" onclick="ragAgent.loadQuery('${query.replace(/'/g, "\\'")}')">${query}</div>`)
            .join('');
    }

    loadQuery(query) {
        this.elements.queryInput.value = query;
        this.elements.queryInput.focus();
    }

    showNotification(message, type = 'info') {
        // Create notification element
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

        // Remove after 3 seconds
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

        return fetch(url, { ...defaultOptions, ...options });
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
`;
document.head.appendChild(style);
