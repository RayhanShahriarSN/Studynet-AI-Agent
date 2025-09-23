# URL configuration for RAG backend API
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Frontend
    path('', views.index_view, name='frontend'),
    
    # Health check
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
    
    # Core query processing
    path('query/', views.QueryProcessView.as_view(), name='query_process'),
    
    # Document management
    path('upload/document/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('upload/text/', views.TextUploadView.as_view(), name='text_upload'),
    
    # Memory management
    path('memory/<str:session_id>/', views.MemoryView.as_view(), name='memory_detail'),
    path('sessions/', views.SessionsListView.as_view(), name='sessions_list'),
    
    # System monitoring
    path('metrics/', views.MetricsView.as_view(), name='metrics'),
    
    # Knowledge base management
    path('knowledge-base/status/', views.KnowledgeBaseStatusView.as_view(), name='kb_status'),
    path('knowledge-base/reload/', views.KnowledgeBaseReloadView.as_view(), name='kb_reload'),
    path('vectorstore/clear/', views.VectorStoreClearView.as_view(), name='vectorstore_clear'),
]
