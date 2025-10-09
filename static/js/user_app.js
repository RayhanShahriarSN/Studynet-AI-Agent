// RAG AI Agent Frontend JavaScript - SIMPLIFIED VERSION
class RAGAgent {
  constructor() {
    this.apiBase = "/api";
    this.sessionId = this.generateSessionId();
    this.isLoading = false;
    
    // Store recent queries in memory instead of localStorage
    this.recentQueries = [];

    this.initializeElements();
    this.bindEvents();
    
    // ✅ FIX: Initialize token after DOM is ready
    this.initializeToken();
    
    this.updateRecentQueries();
    
    // ✅ FIX: Prevent BFCache - Force page reload on back/forward
    this.preventBFCache();
  }

  // ✅ NEW: Initialize token and load system status
  initializeToken() {
    // Try multiple ways to get the token from the template
    this.authToken = window.token || token || "";
    
    console.log("Token initialized:", this.authToken ? "✅ Token found" : "❌ No token");
    console.log("Token value:", this.authToken);
    
    // Validate token
    if (!this.authToken || this.authToken === "None" || this.authToken.trim() === "") {
      console.warn("No valid token available");
      this.authToken = "";
    }
  }

  // ✅ FIX: Prevent Browser Forward/Backward Cache
  preventBFCache() {
    // Disable BFCache by adding pageshow event listener
    window.addEventListener('pageshow', (event) => {
      // Check if page was loaded from cache (persisted)
      if (event.persisted || (window.performance && window.performance.navigation.type === 2)) {
        console.log('Page loaded from cache - forcing reload');
        window.location.reload();
      }
    });

    // Also prevent caching with unload event
    window.addEventListener('unload', () => {
      // This ensures browser doesn't cache the page
    });

    // Additional cache prevention
    window.addEventListener('pagehide', (event) => {
      if (event.persisted) {
        window.location.reload();
      }
    });
  }

  initializeElements() {
    this.elements = {
      chatMessages: document.getElementById("chatMessages"),
      queryInput: document.getElementById("queryInput"),
      sendButton: document.getElementById("sendButton"),
      useWebSearch: document.getElementById("useWebSearch"),
      enhanceFormatting: document.getElementById("enhanceFormatting"),
      clearChat: document.getElementById("clearChat"),
      loadingOverlay: document.getElementById("loadingOverlay"),
      recentQueries: document.getElementById("recentQueries"),
    };
  }

  bindEvents() {
    // Send message
    this.elements.sendButton.addEventListener("click", () =>
      this.sendMessage()
    );
    this.elements.queryInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Clear chat
    this.elements.clearChat.addEventListener("click", () => this.clearChat());

    // ✅ Logout button handler
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleLogout();
      });
    }

    // Auto-resize input
    this.elements.queryInput.addEventListener("input", () => {
      this.elements.queryInput.style.height = "auto";
      this.elements.queryInput.style.height =
        this.elements.queryInput.scrollHeight + "px";
    });
  }

  generateSessionId() {
    return (
      "session_" + Math.random().toString(36).substr(2, 9) + "_" + Date.now()
    );
  }

  // ✅ FIXED: Added token authentication
  async sendMessage() {
    const query = this.elements.queryInput.value.trim();
    if (!query || this.isLoading) return;

    // ✅ Check token before sending
    if (!this.authToken || this.authToken === "None" || this.authToken.trim() === "") {
      this.showNotification("Authentication required. Please login.", "error");
      setTimeout(() => {
        window.location.href = "/login/";
      }, 2000);
      return;
    }

    this.isLoading = true;
    this.elements.sendButton.disabled = true;
    this.elements.queryInput.disabled = true;

    // Add user message to chat
    this.addMessage("user", query);
    this.elements.queryInput.value = "";
    this.elements.queryInput.style.height = "auto";

    // Add to recent queries
    this.addToRecentQueries(query);

    // Show typing indicator
    this.showTypingIndicator();

    try {
      const startTime = Date.now();

      const response = await this.makeRequest("/query/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${this.authToken}`,
        },
        body: JSON.stringify({
          query: query,
          session_id: this.sessionId,
          use_web_search: this.elements.useWebSearch.checked,
          enhance_formatting: this.elements.enhanceFormatting.checked,
        }),
      });

      const endTime = Date.now();
      const responseTime = (endTime - startTime) / 1000;

      this.hideTypingIndicator();

      if (response.ok) {
        const data = await response.json();
        this.addMessage(
          "assistant",
          data.answer,
          data.sources,
          data.confidence_score,
          data.web_search_used
        );
      } else {
        let errorMsg = "Something went wrong";
        try {
          const errorData = await response.json();
          errorMsg = errorData.error || errorData.detail || errorMsg;
        } catch {}
        
        // ✅ Handle authentication errors
        if (response.status === 401 || response.status === 403) {
          this.showNotification("Session expired. Please login again.", "error");
          setTimeout(() => {
            window.location.href = "/login/";
          }, 2000);
          return;
        }
        
        this.addMessage("assistant", `Error: ${errorMsg}`);
      }

    } catch (error) {
      this.hideTypingIndicator();
      this.addMessage("assistant", `Error: ${error.message}`);
    } finally {
      this.isLoading = false;
      this.elements.sendButton.disabled = false;
      this.elements.queryInput.disabled = false;
      this.elements.queryInput.focus();
    }
  }

  addMessage(
    role,
    content,
    sources = [],
    confidence = null,
    webSearchUsed = false
  ) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.innerHTML =
      role === "user"
        ? '<i class="fas fa-user"></i>'
        : '<i class="fas fa-robot"></i>';

    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.innerHTML = this.formatMessage(content);

    contentDiv.appendChild(bubble);

    // Add sources if available
    if (sources && sources.length > 0) {
      const sourcesDiv = document.createElement("div");
      sourcesDiv.className = "message-sources";
      sourcesDiv.innerHTML = '<h4><i class="fas fa-link"></i> Sources</h4>';

      sources.forEach((source, index) => {
        const sourceItem = document.createElement("div");
        sourceItem.className = "source-item";
        sourceItem.innerHTML = `<strong>${source.type}:</strong> ${source.content}`;
        sourcesDiv.appendChild(sourceItem);
      });

      contentDiv.appendChild(sourcesDiv);
    }

    // Add metadata
    const metaDiv = document.createElement("div");
    metaDiv.className = "message-meta";
    metaDiv.innerHTML = `
            <span><i class="fas fa-clock"></i> ${new Date().toLocaleTimeString()}</span>
            ${
              confidence
                ? `<span><i class="fas fa-chart-line"></i> Confidence: ${(
                    confidence * 100
                  ).toFixed(1)}%</span>`
                : ""
            }
            ${
              webSearchUsed
                ? '<span><i class="fas fa-globe"></i> Web Search Used</span>'
                : ""
            }
        `;
    contentDiv.appendChild(metaDiv);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    // Remove welcome message if it exists
    const welcomeMessage =
      this.elements.chatMessages.querySelector(".welcome-message");
    if (welcomeMessage) {
      welcomeMessage.remove();
    }

    this.elements.chatMessages.appendChild(messageDiv);

    // Add animation after a brief delay
    setTimeout(() => {
      messageDiv.classList.add("fade-in");
    }, 50);

    this.scrollToBottom();
  }

  formatMessage(content) {
    // Convert markdown to readable HTML formatting
    if (!content) return "";

    // Convert other markdown elements first
    let formatted = content
      // Convert headers to HTML
      .replace(/^### (.*$)/gim, "<h3>$1</h3>")
      .replace(/^## (.*$)/gim, "<h2>$1</h2>")
      .replace(/^# (.*$)/gim, "<h1>$1</h1>")
      // Convert bold text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      // Convert italic text
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      // Convert code blocks
      .replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
      // Convert inline code
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      // Convert horizontal rules
      .replace(/^---$/gim, "<hr>")
      .replace(/^___$/gim, "<hr>")
      .replace(/^\*\*\*$/gim, "<hr>")
      // Convert lists to HTML
      .replace(/^\* (.*$)/gim, "<li>$1</li>")
      .replace(/^- (.*$)/gim, "<li>$1</li>")
      .replace(/^\d+\. (.*$)/gim, "<li>$1</li>")
      // Convert links
      .replace(
        /\[([^\]]+)\]\(([^)]+)\)/g,
        '<a href="$2" target="_blank">$1</a>'
      )
      // Clean up multiple line breaks
      .replace(/\n{3,}/g, "\n\n")
      // Remove extra spaces
      .replace(/[ \t]+/g, " ")
      .trim();

    // Then handle tables after other processing
    formatted = this.convertTables(formatted);

    // Handle list items by wrapping consecutive <li> elements in <ul>
    formatted = formatted.replace(
      /(<li>.*?<\/li>(?:\s*<li>.*?<\/li>)*)/g,
      (match) => {
        if (!match.includes("<ul>") && !match.includes("<ol>")) {
          return "<ul>" + match + "</ul>";
        }
        return match;
      }
    );

    // Convert line breaks to HTML breaks and wrap in paragraph
    formatted = formatted.replace(/\n\n/g, "</p><p>").replace(/\n/g, "<br>");

    // Wrap in paragraph if not already wrapped
    if (
      !formatted.includes("<p>") &&
      !formatted.includes("<h1>") &&
      !formatted.includes("<h2>") &&
      !formatted.includes("<h3>")
    ) {
      formatted = "<p>" + formatted + "</p>";
    }

    return formatted;
  }

  convertTables(content) {
    // Find and convert markdown tables to HTML tables
    const lines = content.split("\n");
    let result = [];
    let inTable = false;
    let tableRows = [];
    let isFirstRow = true;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // Check if this line is a table row
      if (line.includes("|") && line.split("|").filter(c => c.trim()).length >= 2) {
        // Check if it's a separator line (---|---|---)
        const isSeparator = /^\|?[\s\-:]+\|[\s\-:|]+\|?$/.test(line);

        if (isSeparator) {
          isFirstRow = false; // Next row will be tbody
          continue;
        }

        // Parse table row
        let cells = line.split("|")
          .map(cell => cell.trim())
          .filter(cell => cell.length > 0);

        // Remove leading/trailing empty cells if line starts/ends with |
        if (line.startsWith("|")) {
          cells = cells.slice(0);
        }

        if (cells.length >= 2) {
          if (!inTable) {
            inTable = true;
            isFirstRow = true;
            tableRows = [];
          }

          // Create table row
          const cellTag = isFirstRow ? 'th' : 'td';
          const rowHtml = '<tr>' + cells.map(cell =>
            `<${cellTag}>${cell}</${cellTag}>`
          ).join('') + '</tr>';

          tableRows.push(rowHtml);
        }
      } else {
        // Not a table line
        if (inTable) {
          // Close the table
          const tableHtml = '<table class="markdown-table"><tbody>' +
            tableRows.join('') + '</tbody></table>';
          result.push(tableHtml);
          tableRows = [];
          inTable = false;
          isFirstRow = true;
        }
        result.push(line);
      }
    }

    // Close table if we ended while in a table
    if (inTable && tableRows.length > 0) {
      const tableHtml = '<table class="markdown-table"><tbody>' +
        tableRows.join('') + '</tbody></table>';
      result.push(tableHtml);
    }

    return result.join("\n");
  }

  showTypingIndicator() {
    const typingDiv = document.createElement("div");
    typingDiv.className = "message assistant fade-in typing-indicator";
    typingDiv.id = "typingIndicator";
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
    const typingIndicator = document.getElementById("typingIndicator");
    if (typingIndicator) {
      typingIndicator.remove();
    }
  }

  scrollToBottom() {
    this.elements.chatMessages.scrollTop =
      this.elements.chatMessages.scrollHeight;
  }

  clearChat() {
    this.elements.chatMessages.innerHTML = `
            <div class="welcome-message">
              <h1>What can I help you with today?</h1>
              <p>Ask me anything and I'll provide detailed, helpful responses</p>
            </div>
        `;
    this.sessionId = this.generateSessionId();
  }

  addToRecentQueries(query) {
    this.recentQueries.unshift(query);
    this.recentQueries = this.recentQueries.slice(0, 10); // Keep only last 10
    this.updateRecentQueries();
  }

  updateRecentQueries() {
    if (!this.elements.recentQueries) return;
    
    if (this.recentQueries.length === 0) {
      this.elements.recentQueries.innerHTML =
        '<p class="no-queries">No recent queries</p>';
      return;
    }

    this.elements.recentQueries.innerHTML = this.recentQueries
      .map(
        (query) =>
          `<div class="recent-query" onclick="ragAgent.loadQuery('${query.replace(
            /'/g,
            "\\'"
          )}')">${query}</div>`
      )
      .join("");
  }

  loadQuery(query) {
    this.elements.queryInput.value = query;
    this.elements.queryInput.focus();
  }

  showNotification(message, type = "info") {
    // Create notification element
    const notification = document.createElement("div");
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
      success: "#38a169",
      error: "#e53e3e",
      info: "#3182ce",
      warning: "#d69e2e",
    };

    notification.style.backgroundColor = colors[type] || colors.info;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
      notification.style.animation = "slideOutRight 0.3s ease";
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  // ✅ FIXED: Now includes Authorization header by default
  async makeRequest(endpoint, options = {}) {
    const url = this.apiBase + endpoint;

    // Set default headers
    const defaultHeaders = {};
    
    // Add Authorization header if token exists
    if (this.authToken && this.authToken !== "None" && this.authToken.trim() !== "") {
      defaultHeaders["Authorization"] = `Bearer ${this.authToken}`;
    }

    // Don't set Content-Type for FormData (browser will set it with boundary)
    if (!(options.body instanceof FormData)) {
      defaultHeaders["Content-Type"] = "application/json";
    }

    // Merge headers
    const finalOptions = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {}),
      },
    };

    try {
      const response = await fetch(url, finalOptions);
      
      // Handle authentication errors globally
      if (response.status === 401 || response.status === 403) {
        this.showNotification("Session expired. Please login again.", "error");
        setTimeout(() => {
          window.location.href = "/login/";
        }, 2000);
      }
      
      return response;
    } catch (error) {
      throw error;
    }
  }

  // ✅ LOGOUT HANDLER - Using Django's session-based logout
  async handleLogout() {
    try {
      // Show loading notification
      this.showNotification("Logging out...", "info");

      // Clear token from memory
      this.authToken = "";
      
      // Redirect to Django's logout_page which handles everything
      // This calls logout_user(), clears session, and redirects to login
      setTimeout(() => {
        window.location.replace("/logout/");
      }, 500);

    } catch (error) {
      console.error("Logout error:", error);
      // Still redirect even if something fails
      window.location.replace("/logout/");
    }
  }
}

// Initialize the app when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.ragAgent = new RAGAgent();
});

// Add CSS animations
const style = document.createElement("style");
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