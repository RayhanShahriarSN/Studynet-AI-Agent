// RAG AI Agent Frontend JavaScript
class RAGAgent {
  constructor() {
    this.apiBase = "/api";
    this.sessionId = this.generateSessionId();
    this.isLoading = false;
    this.recentQueries = JSON.parse(
      localStorage.getItem("recentQueries") || "[]"
    );

    this.initializeElements();
    this.bindEvents();
    this.loadSystemStatus();
    this.updateRecentQueries();
    this.updateSessionDisplay();
  }

  initializeElements() {
    this.elements = {
      chatMessages: document.getElementById("chatMessages"),
      queryInput: document.getElementById("queryInput"),
      sendButton: document.getElementById("sendButton"),
      useWebSearch: document.getElementById("useWebSearch"),
      enhanceFormatting: document.getElementById("enhanceFormatting"),
      clearChat: document.getElementById("clearChat"),
      uploadDoc: document.getElementById("uploadDoc"),
      uploadModal: document.getElementById("uploadModal"),
      closeModal: document.getElementById("closeModal"),
      fileInput: document.getElementById("fileInput"),
      uploadArea: document.getElementById("uploadArea"),
      uploadProgress: document.getElementById("uploadProgress"),
      loadingOverlay: document.getElementById("loadingOverlay"),
      apiStatus: document.getElementById("apiStatus"),
      kbStatus: document.getElementById("kbStatus"),
      sessionCount: document.getElementById("sessionCount"),
      sessionId: document.getElementById("sessionId"),
      responseTime: document.getElementById("responseTime"),
      recentQueries: document.getElementById("recentQueries"),
      // Developer dashboard elements
      developerToggle: document.getElementById("developerToggle"),
      developerMode: document.getElementById("developerMode"),
      closeDeveloperMode: document.getElementById("closeDeveloperMode"),
      // Navigation
      navButtons: document.querySelectorAll(".nav-btn"),
      dashboardSections: document.querySelectorAll(".dashboard-section"),
      // Overview section
      getMainDashboard: document.getElementById("getMainDashboard"),
      mainDashboardOutput: document.getElementById("mainDashboardOutput"),
      getTokenUsage: document.getElementById("getTokenUsage"),
      tokenDays: document.getElementById("tokenDays"),
      tokenSessionId: document.getElementById("tokenSessionId"),
      tokenUsageOutput: document.getElementById("tokenUsageOutput"),
      getCostBreakdown: document.getElementById("getCostBreakdown"),
      costLimit: document.getElementById("costLimit"),
      costOrder: document.getElementById("costOrder"),
      costBreakdownOutput: document.getElementById("costBreakdownOutput"),
      // Analytics section
      getQueryAnalytics: document.getElementById("getQueryAnalytics"),
      queryDays: document.getElementById("queryDays"),
      queryAnalyticsOutput: document.getElementById("queryAnalyticsOutput"),
      getDataSourceStats: document.getElementById("getDataSourceStats"),
      dataSourceOutput: document.getElementById("dataSourceOutput"),
      // Reports section
      getSystemReport: document.getElementById("getSystemReport"),
      systemReportOutput: document.getElementById("systemReportOutput"),
      getUsageReport: document.getElementById("getUsageReport"),
      usageReportOutput: document.getElementById("usageReportOutput"),
      // Data management section
      csvUpload: document.getElementById("csvUpload"),
      docUpload: document.getElementById("docUpload"),
      uploadOutput: document.getElementById("uploadOutput"),
      exportSql: document.getElementById("exportSql"),
      sqlQuery: document.getElementById("sqlQuery"),
      sqlExportOutput: document.getElementById("sqlExportOutput"),
      // Monitoring section
      getHealthCheck: document.getElementById("getHealthCheck"),
      healthOutput: document.getElementById("healthOutput"),
      getSystemMetrics: document.getElementById("getSystemMetrics"),
      resetSystemMetrics: document.getElementById("resetSystemMetrics"),
      systemMetricsOutput: document.getElementById("systemMetricsOutput"),
      getKbStatus: document.getElementById("getKbStatus"),
      reloadKb: document.getElementById("reloadKb"),
      clearVectorStore: document.getElementById("clearVectorStore"),
      kbOutput: document.getElementById("kbOutput"),
      // Memory section
      devSessionId: document.getElementById("devSessionId"),
      getMemory: document.getElementById("getMemory"),
      clearMemory: document.getElementById("clearMemory"),
      listSessions: document.getElementById("listSessions"),
      memoryOutput: document.getElementById("memoryOutput"),
      processQuery: document.getElementById("processQuery"),
      testQuery: document.getElementById("testQuery"),
      querySessionId: document.getElementById("querySessionId"),
      queryOutput: document.getElementById("queryOutput"),
      // Debug info
      connectionStatus: document.getElementById("connectionStatus"),
      lastRequest: document.getElementById("lastRequest"),
      errorCount: document.getElementById("errorCount"),
    };

    // Initialize developer mode state
    this.developerModeActive = false;
    this.errorCount = 0;
    this.lastRequestTime = null;
    this.charts = {};
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

    // Upload document
    this.elements.uploadDoc.addEventListener("click", () =>
      this.showUploadModal()
    );
    this.elements.closeModal.addEventListener("click", () =>
      this.hideUploadModal()
    );
    this.elements.uploadArea.addEventListener("click", () =>
      this.elements.fileInput.click()
    );
    this.elements.fileInput.addEventListener("change", (e) =>
      this.handleFileUpload(e)
    );

    // Close modal on outside click
    this.elements.uploadModal.addEventListener("click", (e) => {
      if (e.target === this.elements.uploadModal) {
        this.hideUploadModal();
      }
    });

    // Auto-resize input
    this.elements.queryInput.addEventListener("input", () => {
      this.elements.queryInput.style.height = "auto";
      this.elements.queryInput.style.height =
        this.elements.queryInput.scrollHeight + "px";
    });

    // Developer dashboard events
    this.elements.developerToggle.addEventListener("click", () =>
      this.toggleDeveloperMode()
    );
    this.elements.closeDeveloperMode.addEventListener("click", () =>
      this.toggleDeveloperMode()
    );

    // Navigation events
    this.elements.navButtons.forEach((btn) => {
      btn.addEventListener("click", (e) =>
        this.switchDashboardSection(e.target.dataset.section)
      );
    });

    // Overview section events
    this.elements.getMainDashboard?.addEventListener("click", () =>
      this.getMainDashboard()
    );
    this.elements.getTokenUsage?.addEventListener("click", () =>
      this.getTokenUsage()
    );
    this.elements.getCostBreakdown?.addEventListener("click", () =>
      this.getCostBreakdown()
    );

    // Analytics section events
    this.elements.getQueryAnalytics?.addEventListener("click", () =>
      this.getQueryAnalytics()
    );
    this.elements.getDataSourceStats?.addEventListener("click", () =>
      this.getDataSourceStats()
    );

    // Reports section events
    this.elements.getSystemReport?.addEventListener("click", () =>
      this.getSystemReport()
    );
    this.elements.getUsageReport?.addEventListener("click", () =>
      this.getUsageReport()
    );

    // Data management section events
    this.elements.csvUpload?.addEventListener("change", (e) =>
      this.handleCsvUpload(e)
    );
    this.elements.docUpload?.addEventListener("change", (e) =>
      this.handleDocUpload(e)
    );
    this.elements.exportSql?.addEventListener("click", () =>
      this.exportSqlQuery()
    );

    // Monitoring section events
    this.elements.getHealthCheck?.addEventListener("click", () =>
      this.getHealthCheck()
    );
    this.elements.getSystemMetrics?.addEventListener("click", () =>
      this.getSystemMetrics()
    );
    this.elements.resetSystemMetrics?.addEventListener("click", () =>
      this.resetSystemMetrics()
    );
    this.elements.getKbStatus?.addEventListener("click", () =>
      this.getKnowledgeBaseStatus()
    );
    this.elements.reloadKb?.addEventListener("click", () =>
      this.reloadKnowledgeBase()
    );
    this.elements.clearVectorStore?.addEventListener("click", () =>
      this.clearVectorStore()
    );

    // Memory section events
    this.elements.getMemory?.addEventListener("click", () =>
      this.getMemoryForSession()
    );
    this.elements.clearMemory?.addEventListener("click", () =>
      this.clearSessionMemory()
    );
    this.elements.listSessions?.addEventListener("click", () =>
      this.listAllSessions()
    );
    this.elements.processQuery?.addEventListener("click", () =>
      this.processTestQuery()
    );
  }

  generateSessionId() {
    return (
      "session_" + Math.random().toString(36).substr(2, 9) + "_" + Date.now()
    );
  }

  async sendMessage() {
    const query = this.elements.queryInput.value.trim();
    if (!query || this.isLoading) return;

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
        this.updateResponseTime(responseTime);
      } else {
        const error = await response.json();
        this.addMessage(
          "assistant",
          `Error: ${error.error || "Something went wrong"}`
        );
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
    this.elements.uploadModal.style.display = "block";
    this.elements.uploadProgress.style.display = "none";
  }

  hideUploadModal() {
    this.elements.uploadModal.style.display = "none";
  }

  async handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    this.elements.uploadProgress.style.display = "block";
    this.elements.uploadArea.style.display = "none";

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await this.makeRequest("/upload/document/", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        this.showNotification(
          `Document uploaded successfully! ${data.chunks_created} chunks created.`,
          "success"
        );
        this.hideUploadModal();
      } else {
        const error = await response.json();
        this.showNotification(`Upload failed: ${error.error}`, "error");
      }
    } catch (error) {
      this.showNotification(`Upload failed: ${error.message}`, "error");
    } finally {
      this.elements.uploadProgress.style.display = "none";
      this.elements.uploadArea.style.display = "block";
      this.elements.fileInput.value = "";
    }
  }

  async loadSystemStatus() {
    try {
      // Check API status
      const apiResponse = await this.makeRequest("/health/");
      if (apiResponse.ok && this.elements.apiStatus) {
        this.elements.apiStatus.textContent = "Online";
        this.elements.apiStatus.className = "status-value online";
      } else {
        throw new Error("API not responding");
      }

      // Check knowledge base status
      const kbResponse = await this.makeRequest("/knowledge-base/status/");
      if (kbResponse.ok) {
        const kbData = await kbResponse.json();
        this.elements.kbStatus.textContent = `${kbData.total_documents} documents`;
        this.elements.kbStatus.className = "status-value online";
      }

      // Get session count
      const sessionsResponse = await this.makeRequest("/sessions/");
      if (sessionsResponse.ok) {
        const sessionsData = await sessionsResponse.json();
        this.elements.sessionCount.textContent = sessionsData.count;
      }
    } catch (error) {
      console.error("Error loading system status:", error);
      this.elements.apiStatus.textContent = "Offline";
      this.elements.apiStatus.className = "status-value offline";
      this.elements.kbStatus.textContent = "Unknown";
      this.elements.kbStatus.className = "status-value offline";
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
    localStorage.setItem("recentQueries", JSON.stringify(this.recentQueries));
    this.updateRecentQueries();
  }

  updateRecentQueries() {
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

  async makeRequest(endpoint, options = {}) {
    const url = this.apiBase + endpoint;

    // Don't set Content-Type for FormData (browser will set it with boundary)
    const defaultOptions = {};
    if (!(options.body instanceof FormData)) {
      defaultOptions.headers = {
        "Content-Type": "application/json",
      };
    }

    // Update debug info
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

  // Dashboard Navigation
  switchDashboardSection(sectionName) {
    // Update navigation buttons
    this.elements.navButtons.forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.section === sectionName);
    });

    // Show/hide sections
    this.elements.dashboardSections.forEach((section) => {
      section.classList.toggle(
        "active",
        section.id === `${sectionName}-section`
      );
    });
  }

  // Developer Dashboard Methods
  toggleDeveloperMode() {
    this.developerModeActive = !this.developerModeActive;
    this.elements.developerMode.classList.toggle(
      "active",
      this.developerModeActive
    );

    if (this.developerModeActive) {
      this.elements.developerToggle.innerHTML = '<i class="fas fa-times"></i>';
      this.elements.developerToggle.title = "Close Developer Dashboard";
    } else {
      this.elements.developerToggle.innerHTML =
        '<i class="fas fa-chart-line"></i>';
      this.elements.developerToggle.title = "Developer Dashboard";
    }
  }

  // Overview Section Methods
  async getMainDashboard() {
    try {
      const response = await this.makeRequest("/dashboard/");
      const data = await response.json();

      this.elements.mainDashboardOutput.style.display = "block";
      this.elements.mainDashboardOutput.textContent = JSON.stringify(
        data,
        null,
        2
      );

      // Create dashboard chart
      this.createMainDashboardChart(data);

      this.showNotification("Complete dashboard loaded!", "success");
    } catch (error) {
      this.elements.mainDashboardOutput.style.display = "block";
      this.elements.mainDashboardOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to load dashboard", "error");
    }
  }

  async getTokenUsage() {
    try {
      const days = this.elements.tokenDays?.value || 30;
      const sessionId = this.elements.tokenSessionId?.value || "";
      const params = new URLSearchParams({ days });
      if (sessionId) params.append("session_id", sessionId);

      const response = await this.makeRequest(`/dashboard/tokens/?${params}`);
      const data = await response.json();

      this.elements.tokenUsageOutput.style.display = "block";
      this.elements.tokenUsageOutput.textContent = JSON.stringify(
        data,
        null,
        2
      );

      // Create token usage chart
      this.createTokenUsageChart(data);

      this.showNotification("Token usage retrieved!", "success");
    } catch (error) {
      this.elements.tokenUsageOutput.style.display = "block";
      this.elements.tokenUsageOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to get token usage", "error");
    }
  }

  async getCostBreakdown() {
    try {
      const limit = this.elements.costLimit?.value || 10;
      const order = this.elements.costOrder?.value || "cost";
      const params = new URLSearchParams({ limit, order });

      const response = await this.makeRequest(`/dashboard/costs/?${params}`);
      const data = await response.json();

      this.elements.costBreakdownOutput.style.display = "block";
      this.elements.costBreakdownOutput.textContent = JSON.stringify(
        data,
        null,
        2
      );
      this.showNotification("Cost breakdown retrieved!", "success");
    } catch (error) {
      this.elements.costBreakdownOutput.style.display = "block";
      this.elements.costBreakdownOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to get cost breakdown", "error");
    }
  }

  // Analytics Section Methods
  async getQueryAnalytics() {
    try {
      const days = this.elements.queryDays?.value || 7;
      const params = new URLSearchParams({ days });

      const response = await this.makeRequest(`/analytics/queries/?${params}`);
      const data = await response.json();

      this.elements.queryAnalyticsOutput.style.display = "block";
      this.elements.queryAnalyticsOutput.textContent = JSON.stringify(
        data,
        null,
        2
      );

      // Create query analytics chart
      this.createQueryAnalyticsChart(data);

      this.showNotification("Query analytics retrieved!", "success");
    } catch (error) {
      this.elements.queryAnalyticsOutput.style.display = "block";
      this.elements.queryAnalyticsOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to get query analytics", "error");
    }
  }

  async getDataSourceStats() {
    try {
      const response = await this.makeRequest("/analytics/sources/");
      const data = await response.json();

      this.elements.dataSourceOutput.style.display = "block";
      this.elements.dataSourceOutput.textContent = JSON.stringify(
        data,
        null,
        2
      );
      this.showNotification("Data source stats retrieved!", "success");
    } catch (error) {
      this.elements.dataSourceOutput.style.display = "block";
      this.elements.dataSourceOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to get data source stats", "error");
    }
  }

  // Reports Section Methods
  async getSystemReport() {
    try {
      const response = await this.makeRequest("/reports/system/");
      const data = await response.json();

      this.elements.systemReportOutput.style.display = "block";
      this.elements.systemReportOutput.textContent = JSON.stringify(
        data,
        null,
        2
      );
      this.showNotification("System report retrieved!", "success");
    } catch (error) {
      this.elements.systemReportOutput.style.display = "block";
      this.elements.systemReportOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to get system report", "error");
    }
  }

  async getUsageReport() {
    try {
      const response = await this.makeRequest("/reports/usage/");
      const data = await response.json();

      this.elements.usageReportOutput.style.display = "block";
      this.elements.usageReportOutput.textContent = JSON.stringify(
        data,
        null,
        2
      );
      this.showNotification("Usage report retrieved!", "success");
    } catch (error) {
      this.elements.usageReportOutput.style.display = "block";
      this.elements.usageReportOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to get usage report", "error");
    }
  }

  // Data Management Section Methods
  async handleCsvUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await this.makeRequest("/upload/csv/", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      this.elements.uploadOutput.style.display = "block";
      this.elements.uploadOutput.textContent = JSON.stringify(data, null, 2);
      this.showNotification("CSV uploaded successfully!", "success");
    } catch (error) {
      this.elements.uploadOutput.style.display = "block";
      this.elements.uploadOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to upload CSV", "error");
    }
  }

  async handleDocUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await this.makeRequest("/upload/document/", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      this.elements.uploadOutput.style.display = "block";
      this.elements.uploadOutput.textContent = JSON.stringify(data, null, 2);
      this.showNotification("Document uploaded successfully!", "success");
    } catch (error) {
      this.elements.uploadOutput.style.display = "block";
      this.elements.uploadOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to upload document", "error");
    }
  }

  async exportSqlQuery() {
    const query = this.elements.sqlQuery?.value;
    if (!query) {
      this.showNotification("Please enter a SQL query", "error");
      return;
    }

    try {
      const response = await this.makeRequest("/export/sql/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await response.json();

      this.elements.sqlExportOutput.style.display = "block";
      this.elements.sqlExportOutput.textContent = JSON.stringify(data, null, 2);
      this.showNotification("SQL export completed!", "success");
    } catch (error) {
      this.elements.sqlExportOutput.style.display = "block";
      this.elements.sqlExportOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to export SQL", "error");
    }
  }

  // Monitoring Section Methods
  async getHealthCheck() {
    try {
      const response = await this.makeRequest("/health/");
      const data = await response.json();

      this.elements.healthOutput.style.display = "block";
      this.elements.healthOutput.textContent = JSON.stringify(data, null, 2);
      this.showNotification("Health check completed!", "success");
    } catch (error) {
      this.elements.healthOutput.style.display = "block";
      this.elements.healthOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Health check failed", "error");
    }
  }

  async processTestQuery() {
    const query = this.elements.testQuery?.value;
    const sessionId = this.elements.querySessionId?.value || this.sessionId;

    if (!query) {
      this.showNotification("Please enter a query", "error");
      return;
    }

    try {
      const response = await this.makeRequest("/query/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          session_id: sessionId,
          use_web_search: true,
          enhance_formatting: true,
        }),
      });
      const data = await response.json();

      this.elements.queryOutput.style.display = "block";
      this.elements.queryOutput.textContent = JSON.stringify(data, null, 2);
      this.showNotification("Query processed successfully!", "success");
    } catch (error) {
      this.elements.queryOutput.style.display = "block";
      this.elements.queryOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Query processing failed", "error");
    }
  }

  // Chart Creation Methods
  createMainDashboardChart(data) {
    const ctx = document.getElementById("mainDashboardChart");
    if (!ctx) return;

    // Destroy existing chart
    if (this.charts.mainDashboard) {
      this.charts.mainDashboard.destroy();
    }

    // Extract data for visualization
    const labels = ["Total Queries", "Successful Queries", "Failed Queries"];
    const values = [
      data.total_queries || 0,
      data.successful_queries || 0,
      (data.total_queries || 0) - (data.successful_queries || 0),
    ];

    this.charts.mainDashboard = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            backgroundColor: ["#667eea", "#38a169", "#e53e3e"],
            borderWidth: 2,
            borderColor: "#2d3748",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: "#e2e8f0",
              font: {
                size: 12,
              },
            },
          },
        },
      },
    });
  }

  createTokenUsageChart(data) {
    const ctx = document.getElementById("tokenUsageChart");
    if (!ctx) return;

    // Destroy existing chart
    if (this.charts.tokenUsage) {
      this.charts.tokenUsage.destroy();
    }

    // Extract token data
    const labels = ["Prompt Tokens", "Completion Tokens", "Total Tokens"];
    const values = [
      data.prompt_tokens || 0,
      data.completion_tokens || 0,
      data.total_tokens || 0,
    ];

    this.charts.tokenUsage = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Token Count",
            data: values,
            backgroundColor: ["#667eea", "#764ba2", "#38a169"],
            borderColor: "#4a5568",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              color: "#a0aec0",
            },
            grid: {
              color: "#4a5568",
            },
          },
          x: {
            ticks: {
              color: "#a0aec0",
            },
            grid: {
              color: "#4a5568",
            },
          },
        },
        plugins: {
          legend: {
            labels: {
              color: "#e2e8f0",
              font: {
                size: 12,
              },
            },
          },
        },
      },
    });
  }

  createQueryAnalyticsChart(data) {
    const ctx = document.getElementById("queryAnalyticsChart");
    if (!ctx) return;

    // Destroy existing chart
    if (this.charts.queryAnalytics) {
      this.charts.queryAnalytics.destroy();
    }

    // Extract query type data
    const labels = ["SQL Queries", "RAG Queries", "Hybrid Queries"];
    const values = [
      data.sql_queries || 0,
      data.rag_queries || 0,
      data.hybrid_queries || 0,
    ];

    this.charts.queryAnalytics = new Chart(ctx, {
      type: "pie",
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            backgroundColor: ["#667eea", "#38a169", "#d69e2e"],
            borderWidth: 2,
            borderColor: "#2d3748",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: "#e2e8f0",
              font: {
                size: 12,
              },
            },
          },
        },
      },
    });
  }

  updateDebugInfo() {
    this.elements.lastRequest.textContent = `Last Request: ${
      this.lastRequestTime || "None"
    }`;
    this.elements.errorCount.textContent = `Errors: ${this.errorCount}`;

    // Update connection status
    this.elements.connectionStatus.innerHTML = `
            <i class="fas fa-circle ${
              this.errorCount > 0 ? "offline" : "online"
            }"></i>
            <span>Connection: ${this.errorCount > 0 ? "Issues" : "OK"}</span>
        `;
  }

  async getMemoryForSession() {
    const sessionId = this.elements.devSessionId.value || this.sessionId;
    try {
      const response = await this.makeRequest(`/memory/${sessionId}/`);
      const data = await response.json();

      this.elements.memoryOutput.style.display = "block";
      this.elements.memoryOutput.textContent = JSON.stringify(data, null, 2);
      this.showNotification("Memory retrieved successfully!", "success");
    } catch (error) {
      this.elements.memoryOutput.style.display = "block";
      this.elements.memoryOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to get memory", "error");
    }
  }

  async clearSessionMemory() {
    const sessionId = this.elements.devSessionId.value || this.sessionId;
    if (
      !confirm(
        `Are you sure you want to clear memory for session: ${sessionId}?`
      )
    ) {
      return;
    }

    try {
      const response = await this.makeRequest(`/memory/${sessionId}/`, {
        method: "DELETE",
      });
      if (response.ok) {
        this.elements.memoryOutput.style.display = "block";
        this.elements.memoryOutput.textContent = "Memory cleared successfully!";
        this.showNotification("Memory cleared successfully!", "success");
      } else {
        throw new Error("Failed to clear memory");
      }
    } catch (error) {
      this.elements.memoryOutput.style.display = "block";
      this.elements.memoryOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to clear memory", "error");
    }
  }

  async listAllSessions() {
    try {
      const response = await this.makeRequest("/sessions/");
      const data = await response.json();

      this.elements.memoryOutput.style.display = "block";
      this.elements.memoryOutput.textContent = JSON.stringify(data, null, 2);
      this.showNotification("Sessions retrieved successfully!", "success");
    } catch (error) {
      this.elements.memoryOutput.style.display = "block";
      this.elements.memoryOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to get sessions", "error");
    }
  }

  async getKnowledgeBaseStatus() {
    try {
      const response = await this.makeRequest("/knowledge-base/status/");
      const data = await response.json();

      this.elements.kbOutput.style.display = "block";
      this.elements.kbOutput.textContent = JSON.stringify(data, null, 2);
      this.showNotification("Knowledge base status retrieved!", "success");
    } catch (error) {
      this.elements.kbOutput.style.display = "block";
      this.elements.kbOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to get KB status", "error");
    }
  }

  async reloadKnowledgeBase() {
    if (
      !confirm(
        "Are you sure you want to reload the knowledge base? This may take a while."
      )
    ) {
      return;
    }

    try {
      this.elements.reloadKb.classList.add("loading");
      this.elements.reloadKb.disabled = true;

      const response = await this.makeRequest("/knowledge-base/reload/", {
        method: "POST",
      });
      const data = await response.json();

      this.elements.kbOutput.style.display = "block";
      this.elements.kbOutput.textContent = JSON.stringify(data, null, 2);
      this.showNotification("Knowledge base reloaded successfully!", "success");

      // Refresh system status
      this.loadSystemStatus();
    } catch (error) {
      this.elements.kbOutput.style.display = "block";
      this.elements.kbOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to reload knowledge base", "error");
    } finally {
      this.elements.reloadKb.classList.remove("loading");
      this.elements.reloadKb.disabled = false;
    }
  }

  async clearVectorStore() {
    if (
      !confirm(
        "Are you sure you want to clear the vector store? This will delete ALL document data!"
      )
    ) {
      return;
    }

    try {
      this.elements.clearVectorStore.classList.add("loading");
      this.elements.clearVectorStore.disabled = true;

      const response = await this.makeRequest("/vectorstore/clear/", {
        method: "DELETE",
      });
      const data = await response.json();

      this.elements.kbOutput.style.display = "block";
      this.elements.kbOutput.textContent = JSON.stringify(data, null, 2);
      this.showNotification("Vector store cleared successfully!", "success");

      // Refresh system status
      this.loadSystemStatus();
    } catch (error) {
      this.elements.kbOutput.style.display = "block";
      this.elements.kbOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to clear vector store", "error");
    } finally {
      this.elements.clearVectorStore.classList.remove("loading");
      this.elements.clearVectorStore.disabled = false;
    }
  }

  async getSystemMetrics() {
    try {
      const response = await this.makeRequest("/metrics/");
      const data = await response.json();

      this.elements.systemMetricsOutput.style.display = "block";
      this.elements.systemMetricsOutput.textContent = JSON.stringify(
        data,
        null,
        2
      );
      this.showNotification("Metrics retrieved successfully!", "success");
    } catch (error) {
      this.elements.systemMetricsOutput.style.display = "block";
      this.elements.systemMetricsOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to get metrics", "error");
    }
  }

  async resetSystemMetrics() {
    if (!confirm("Are you sure you want to reset all system metrics?")) {
      return;
    }

    try {
      const response = await this.makeRequest("/metrics/", { method: "POST" });
      const data = await response.json();

      this.elements.systemMetricsOutput.style.display = "block";
      this.elements.systemMetricsOutput.textContent = JSON.stringify(
        data,
        null,
        2
      );
      this.showNotification("Metrics reset successfully!", "success");
    } catch (error) {
      this.elements.systemMetricsOutput.style.display = "block";
      this.elements.systemMetricsOutput.textContent = `Error: ${error.message}`;
      this.showNotification("Failed to reset metrics", "error");
    }
  }

  async testApiEndpoint() {
    const endpoint = this.elements.testEndpoint.value.trim();
    if (!endpoint) {
      this.showNotification("Please enter an endpoint", "error");
      return;
    }

    try {
      const response = await this.makeRequest(endpoint);
      const data = await response.json();

      this.elements.apiTestOutput.style.display = "block";
      this.elements.apiTestOutput.textContent = `Status: ${
        response.status
      }\n\n${JSON.stringify(data, null, 2)}`;
      this.showNotification("API test completed!", "success");
    } catch (error) {
      this.elements.apiTestOutput.style.display = "block";
      this.elements.apiTestOutput.textContent = `Error: ${error.message}`;
      this.showNotification("API test failed", "error");
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
