from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ChatMessage, ConversationSession, QueryRequest, QueryResponse,
    DocumentUpload, SystemMetrics, KnowledgeBaseStatus, QueryAnalytics,
    DataSourceStats, CSVUpload, AgentInteraction
)
from .user_profile import UserProfile


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['role', 'content_preview', 'session_link', 'timestamp']
    list_filter = ['role', 'timestamp']
    search_fields = ['content', 'session__session_id']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def session_link(self, obj):
        url = reverse('admin:api_conversationsession_change', args=[obj.session.id])
        return format_html('<a href="{}">{}</a>', url, obj.session.session_id)
    session_link.short_description = 'Session'


@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user_link', 'total_tokens', 'message_count', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'user']
    search_fields = ['session_id', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="/admin/auth/user/{}/change/">{}</a>', obj.user.id, obj.user.username)
        return '-'
    user_link.short_description = 'User'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Non-admin users only see their own sessions
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs


@admin.register(QueryRequest)
class QueryRequestAdmin(admin.ModelAdmin):
    list_display = ['query_preview', 'user_link', 'session_id', 'use_web_search', 'enhance_formatting', 'created_at']
    list_filter = ['use_web_search', 'enhance_formatting', 'created_at', 'user']
    search_fields = ['query', 'session_id', 'user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="/admin/auth/user/{}/change/">{}</a>', obj.user.id, obj.user.username)
        return 'Anonymous'
    user_link.short_description = 'User'

    def query_preview(self, obj):
        return obj.query[:100] + "..." if len(obj.query) > 100 else obj.query
    query_preview.short_description = 'Query Preview'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Non-admin users only see their own queries
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs


@admin.register(QueryResponse)
class QueryResponseAdmin(admin.ModelAdmin):
    list_display = ['answer_preview', 'confidence_score', 'web_search_used', 'session_id', 'created_at']
    list_filter = ['web_search_used', 'created_at']
    search_fields = ['answer', 'session_id']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def answer_preview(self, obj):
        return obj.answer[:100] + "..." if len(obj.answer) > 100 else obj.answer
    answer_preview.short_description = 'Answer Preview'


@admin.register(DocumentUpload)
class DocumentUploadAdmin(admin.ModelAdmin):
    list_display = ['content_preview', 'user_link', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['content', 'user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="/admin/auth/user/{}/change/">{}</a>', obj.user.id, obj.user.username)
        return 'Anonymous'
    user_link.short_description = 'User'

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Non-admin users only see their own documents
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = ['queries_processed', 'avg_response_time', 'kb_hits', 'web_searches', 'errors', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']


@admin.register(KnowledgeBaseStatus)
class KnowledgeBaseStatusAdmin(admin.ModelAdmin):
    list_display = ['status', 'total_documents', 'parent_chunks', 'child_chunks', 'data_source', 'updated_at']
    list_filter = ['status', 'data_source', 'created_at', 'updated_at']
    search_fields = ['knowledge_base_path', 'data_source']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']


@admin.register(QueryAnalytics)
class QueryAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'query_type', 'query_preview', 'user_link', 'response_time_ms', 'tokens_used',
        'total_cost_usd', 'success', 'created_at'
    ]
    list_filter = [
        'query_type', 'classification_method', 'sql_used', 'rag_used',
        'web_search_used', 'success', 'created_at', 'user'
    ]
    search_fields = ['query_text', 'session_id', 'user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="/admin/auth/user/{}/change/">{}</a>', obj.user.id, obj.user.username)
        return 'Anonymous'
    user_link.short_description = 'User'

    def query_preview(self, obj):
        return obj.query_text[:50] + "..." if len(obj.query_text) > 50 else obj.query_text
    query_preview.short_description = 'Query Preview'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Non-admin users only see their own analytics
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs


@admin.register(DataSourceStats)
class DataSourceStatsAdmin(admin.ModelAdmin):
    list_display = [
        'source_name', 'source_type', 'row_count', 'chunk_count', 
        'query_count', 'last_queried_at'
    ]
    list_filter = ['source_type', 'created_at', 'updated_at']
    search_fields = ['source_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['source_name']


@admin.register(CSVUpload)
class CSVUploadAdmin(admin.ModelAdmin):
    list_display = [
        'original_filename', 'table_name', 'user_link', 'row_count', 'column_count',
        'file_size_bytes', 'uploaded_at'
    ]
    list_filter = ['uploaded_at', 'user']
    search_fields = ['original_filename', 'table_name', 'uploaded_by', 'user__username']
    readonly_fields = ['uploaded_at']
    ordering = ['-uploaded_at']

    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="/admin/auth/user/{}/change/">{}</a>', obj.user.id, obj.user.username)
        return obj.uploaded_by or 'Unknown'
    user_link.short_description = 'User'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Non-admin users only see their own CSV uploads
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs


@admin.register(AgentInteraction)
class AgentInteractionAdmin(admin.ModelAdmin):
    list_display = [
        'session_id', 'user_link', 'query_preview', 'response_time_ms', 'total_tokens',
        'success', 'created_at'
    ]
    list_filter = ['success', 'created_at', 'user']
    search_fields = ['query', 'response', 'session_id', 'user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="/admin/auth/user/{}/change/">{}</a>', obj.user.id, obj.user.username)
        return 'Anonymous'
    user_link.short_description = 'User'

    def query_preview(self, obj):
        return obj.query[:50] + "..." if len(obj.query) > 50 else obj.query
    query_preview.short_description = 'Query Preview'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Non-admin users only see their own interactions
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs


# User Profile Inline
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile & Bearer Token'
    fields = ['bearer_token', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']


# Extend User Admin
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'get_bearer_token')

    def get_bearer_token(self, obj):
        if hasattr(obj, 'profile') and obj.profile.bearer_token:
            token_preview = obj.profile.bearer_token[:50] + '...' if len(obj.profile.bearer_token) > 50 else obj.profile.bearer_token
            return format_html('<code style="background:#f0f0f0;padding:2px 6px;border-radius:3px;">{}</code>', token_preview)
        return '-'
    get_bearer_token.short_description = 'Bearer Token'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# Customize admin site
admin.site.site_header = "StudyNet Counselor Admin"
admin.site.site_title = "StudyNet Admin"
admin.site.index_title = "Welcome to StudyNet Counselor Administration"
