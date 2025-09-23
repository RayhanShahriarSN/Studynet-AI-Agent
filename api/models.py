# Django models for RAG backend
from django.db import models
from django.utils import timezone
from django.db.models import JSONField
from django.core.validators import MinValueValidator, MaxValueValidator


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