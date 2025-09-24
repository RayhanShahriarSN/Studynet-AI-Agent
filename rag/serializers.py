from rest_framework import serializers
# DRF serializers for RAG backend
from rest_framework import serializers
from .models import (
    ChatMessage, ConversationSession, QueryRequest, QueryResponse,
    DocumentUpload, SystemMetrics, KnowledgeBaseStatus
)

class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class ConversationSessionSerializer(serializers.ModelSerializer):
    """Serializer for conversation sessions"""
    messages = ChatMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ConversationSession
        fields = ['id', 'session_id', 'total_tokens', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'created_at', 'updated_at']


class QueryRequestSerializer(serializers.ModelSerializer):
    """Serializer for query requests"""
    
    class Meta:
        model = QueryRequest
        fields = ['id', 'query', 'session_id', 'use_web_search', 'enhance_formatting', 'created_at']
        read_only_fields = ['id', 'created_at']


class QueryResponseSerializer(serializers.ModelSerializer):
    """Serializer for query responses"""
    
    class Meta:
        model = QueryResponse
        fields = [
            'id', 'answer', 'sources', 'confidence_score', 'web_search_used',
            'session_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for document uploads"""
    
    class Meta:
        model = DocumentUpload
        fields = ['id', 'content', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']


class SystemMetricsSerializer(serializers.ModelSerializer):
    """Serializer for system metrics"""
    
    class Meta:
        model = SystemMetrics
        fields = [
            'id', 'queries_processed', 'avg_response_time', 'kb_hits',
            'web_searches', 'errors', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class KnowledgeBaseStatusSerializer(serializers.ModelSerializer):
    """Serializer for knowledge base status"""
    
    class Meta:
        model = KnowledgeBaseStatus
        fields = [
            'id', 'status', 'parent_chunks', 'child_chunks', 'total_documents',
            'knowledge_base_path', 'data_source', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Request/Response serializers for API endpoints
class QueryRequestInputSerializer(serializers.Serializer):
    """Input serializer for query processing endpoint"""
    query = serializers.CharField(max_length=2000)
    session_id = serializers.CharField(max_length=255, required=False, allow_null=True)
    use_web_search = serializers.BooleanField(default=True)
    enhance_formatting = serializers.BooleanField(default=True)


class QueryResponseOutputSerializer(serializers.Serializer):
    """Output serializer for query processing endpoint"""
    answer = serializers.CharField()
    sources = serializers.ListField(
        child=serializers.DictField(),
        default=list
    )
    confidence_score = serializers.FloatField(min_value=0.0, max_value=1.0)
    web_search_used = serializers.BooleanField()
    session_id = serializers.CharField()


class DocumentUploadInputSerializer(serializers.Serializer):
    """Input serializer for document upload endpoint"""
    content = serializers.CharField()
    metadata = serializers.DictField(required=False, default=dict)


class DocumentUploadResponseSerializer(serializers.Serializer):
    """Response serializer for document upload endpoint"""
    status = serializers.CharField()
    message = serializers.CharField()
    chunks_created = serializers.IntegerField(required=False)


class MemoryContextSerializer(serializers.Serializer):
    """Serializer for memory context"""
    session_id = serializers.CharField()
    context = serializers.CharField()
    memory = serializers.DictField()


class SessionsListSerializer(serializers.Serializer):
    """Serializer for sessions list"""
    sessions = serializers.ListField(child=serializers.CharField())
    count = serializers.IntegerField()


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check endpoint"""
    status = serializers.CharField()
    service = serializers.CharField()
    version = serializers.CharField()
    data_source = serializers.CharField()
    features = serializers.DictField()


class KnowledgeBaseReloadSerializer(serializers.Serializer):
    """Serializer for knowledge base reload response"""
    status = serializers.CharField()
    message = serializers.CharField()


class VectorStoreClearSerializer(serializers.Serializer):
    """Serializer for vector store clear response"""
    status = serializers.CharField()
    message = serializers.CharField()
