# Django models for RAG backend
from django.db import models
from django.utils import timezone
from django.db.models import JSONField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class ChatMessage(models.Model):
    """Individual chat message in a conversation"""
    
    class MessageRole(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'
        SYSTEM = 'system', 'System'
    
    role = models.CharField(
        max_length=20,
        choices=MessageRole.choices,
        default=MessageRole.USER
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    session = models.ForeignKey(
        'ConversationSession',
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class ConversationSession(models.Model):
    """Conversation session with memory context"""
    session_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sessions')
    total_tokens = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Session {self.session_id}"


class QueryRequest(models.Model):
    """Request model for query processing"""
    query = models.TextField()
    session_id = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='queries')
    use_web_search = models.BooleanField(default=True)
    enhance_formatting = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Query: {self.query[:50]}..."


class QueryResponse(models.Model):
    """Response model for query processing"""
    answer = models.TextField()
    sources = JSONField(default=list, blank=True)
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    web_search_used = models.BooleanField(default=False)
    session_id = models.CharField(max_length=255)
    query_request = models.OneToOneField(
        QueryRequest,
        on_delete=models.CASCADE,
        related_name='response',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Response: {self.answer[:50]}..."


class DocumentUpload(models.Model):
    """Model for text document upload"""
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    metadata = JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Document: {self.content[:50]}..."


class SystemMetrics(models.Model):
    """System performance metrics"""
    queries_processed = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)
    kb_hits = models.IntegerField(default=0)
    web_searches = models.IntegerField(default=0)
    errors = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Metrics: {self.queries_processed} queries"


class KnowledgeBaseStatus(models.Model):
    """Knowledge base status and statistics"""
    status = models.CharField(max_length=50, default='active')
    parent_chunks = models.IntegerField(default=0)
    child_chunks = models.IntegerField(default=0)
    total_documents = models.IntegerField(default=0)
    knowledge_base_path = models.CharField(max_length=500)
    data_source = models.CharField(max_length=200)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"KB Status: {self.total_documents} documents"


class QueryAnalytics(models.Model):
    """Analytics for query processing"""

    class QueryTypeChoices(models.TextChoices):
        STRUCTURED_SQL = 'structured_sql', 'Structured SQL'
        SEMANTIC_RAG = 'semantic_rag', 'Semantic RAG'
        HYBRID = 'hybrid', 'Hybrid'
        UNKNOWN = 'unknown', 'Unknown'

    session_id = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='analytics')
    query_text = models.TextField()
    query_type = models.CharField(
        max_length=20,
        choices=QueryTypeChoices.choices,
        default=QueryTypeChoices.UNKNOWN
    )
    classification_method = models.CharField(max_length=20, default='keyword')  # keyword or llm

    # Performance metrics
    response_time_ms = models.IntegerField(default=0)

    # Token usage metrics
    tokens_used = models.IntegerField(default=0)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)

    # Tool usage
    tools_used = JSONField(default=list, blank=True)  # List of tool names
    sql_used = models.BooleanField(default=False)
    rag_used = models.BooleanField(default=False)
    web_search_used = models.BooleanField(default=False)

    # Results
    sources_count = models.IntegerField(default=0)
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.5
    )
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['query_type', 'created_at']),
            models.Index(fields=['session_id', 'created_at']),
        ]

    def __str__(self):
        return f"{self.query_type} query at {self.created_at}"


class DataSourceStats(models.Model):
    """Statistics about data sources (CSV tables and document collections)"""

    class SourceTypeChoices(models.TextChoices):
        CSV_TABLE = 'csv_table', 'CSV Table'
        PDF_DOCUMENT = 'pdf_document', 'PDF Document'
        DOCX_DOCUMENT = 'docx_document', 'DOCX Document'
        TEXT_DOCUMENT = 'text_document', 'Text Document'
        VECTOR_STORE = 'vector_store', 'Vector Store'

    source_name = models.CharField(max_length=255, unique=True)
    source_type = models.CharField(
        max_length=20,
        choices=SourceTypeChoices.choices
    )

    # Size metrics
    row_count = models.IntegerField(default=0)  # For CSV tables
    chunk_count = models.IntegerField(default=0)  # For documents
    file_size_kb = models.IntegerField(default=0)

    # Usage metrics
    query_count = models.IntegerField(default=0)
    last_queried_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    columns = JSONField(default=list, blank=True)  # For CSV: list of column names
    metadata = JSONField(default=dict, blank=True)  # Additional metadata

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['source_name']
        verbose_name_plural = 'Data source stats'

    def __str__(self):
        return f"{self.source_name} ({self.source_type})"


class CSVUpload(models.Model):
    """Track CSV file uploads"""
    original_filename = models.CharField(max_length=255)
    table_name = models.CharField(max_length=255, unique=True)
    file_size_bytes = models.IntegerField(default=0)
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    columns = JSONField(default=list, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='csv_uploads')
    uploaded_by = models.CharField(max_length=255, blank=True, null=True)  # Legacy field
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_filename} → {self.table_name}"


class AgentInteraction(models.Model):
    """Track agent interactions and tool usage"""
    session_id = models.CharField(max_length=255, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='interactions')
    query = models.TextField()

    # Agent response
    response = models.TextField()
    response_time_ms = models.IntegerField(default=0)

    # Classification
    query_classification = JSONField(default=dict, blank=True)

    # Enhancement
    query_enhancement = JSONField(default=dict, blank=True)

    # Tool execution details
    intermediate_steps = JSONField(default=list, blank=True)  # List of tool calls and results

    # Final metrics
    total_tokens = models.IntegerField(default=0)
    success = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Interaction at {self.created_at}"