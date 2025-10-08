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


# ============================================================================
# NEW: Serializers for Analytics, CSV Upload, and Reporting
# ============================================================================

from .models import QueryAnalytics, DataSourceStats, CSVUpload, AgentInteraction


class QueryAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for query analytics"""

    class Meta:
        model = QueryAnalytics
        fields = '__all__'
        read_only_fields = ['created_at']


class DataSourceStatsSerializer(serializers.ModelSerializer):
    """Serializer for data source statistics"""

    class Meta:
        model = DataSourceStats
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CSVUploadSerializer(serializers.ModelSerializer):
    """Serializer for CSV uploads"""

    class Meta:
        model = CSVUpload
        fields = '__all__'
        read_only_fields = ['uploaded_at']


class AgentInteractionSerializer(serializers.ModelSerializer):
    """Serializer for agent interactions"""

    class Meta:
        model = AgentInteraction
        fields = '__all__'
        read_only_fields = ['created_at']


# Input/Output Serializers for new endpoints

class CSVUploadInputSerializer(serializers.Serializer):
    """Input serializer for CSV upload"""
    file = serializers.FileField()
    table_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    uploaded_by = serializers.CharField(max_length=255, required=False, allow_blank=True)


class CSVUploadResponseSerializer(serializers.Serializer):
    """Response serializer for CSV upload"""
    status = serializers.CharField()
    message = serializers.CharField()
    table_name = serializers.CharField()
    row_count = serializers.IntegerField()
    column_count = serializers.IntegerField()
    columns = serializers.ListField(child=serializers.CharField())


class AnalyticsQueryStatsSerializer(serializers.Serializer):
    """Serializer for query analytics statistics"""
    total_queries = serializers.IntegerField()
    sql_queries = serializers.IntegerField()
    rag_queries = serializers.IntegerField()
    hybrid_queries = serializers.IntegerField()
    avg_response_time_ms = serializers.FloatField()
    avg_confidence_score = serializers.FloatField()
    success_rate = serializers.FloatField()
    total_tools_used = serializers.IntegerField()


class AnalyticsSourceStatsSerializer(serializers.Serializer):
    """Serializer for data source analytics"""
    total_sources = serializers.IntegerField()
    csv_tables = serializers.IntegerField()
    documents = serializers.IntegerField()
    total_rows = serializers.IntegerField()
    total_chunks = serializers.IntegerField()
    sources = serializers.ListField(child=DataSourceStatsSerializer())


class SystemReportSerializer(serializers.Serializer):
    """Serializer for system health report"""
    system_status = serializers.CharField()
    uptime_info = serializers.DictField()
    database_stats = serializers.DictField()
    vector_store_stats = serializers.DictField()
    sql_engine_stats = serializers.DictField()
    memory_usage = serializers.DictField()
    recent_errors = serializers.ListField()


class UsageReportSerializer(serializers.Serializer):
    """Serializer for usage report"""
    time_period = serializers.CharField()
    total_queries = serializers.IntegerField()
    unique_sessions = serializers.IntegerField()
    query_breakdown = serializers.DictField()
    tool_usage = serializers.DictField()
    top_queries = serializers.ListField()
    performance_metrics = serializers.DictField()


class SQLExportInputSerializer(serializers.Serializer):
    """Input serializer for SQL export"""
    query = serializers.CharField()
    format = serializers.ChoiceField(choices=['csv', 'json'], default='csv')
    filename = serializers.CharField(max_length=255, required=False, allow_blank=True)


class SQLExportResponseSerializer(serializers.Serializer):
    """Response serializer for SQL export"""
    status = serializers.CharField()
    filename = serializers.CharField()
    row_count = serializers.IntegerField()
    download_url = serializers.CharField(required=False)
