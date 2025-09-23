# rag/urls.py
from django.urls import path
from .views import QnAPage, ConfigureLLM, ClearChat, UploadPDF, QnAPage_admin, ConfigureLLM_admin, ClearChat_admin, QnAPage2,QnAPagePhi,ClearChat2,ClearChatPhi, QnAPagePhi_admin, ClearChatPhiAdmin
from api import views
urlpatterns = [

    path("qna/", QnAPage.as_view(), name="rag_qna_page"),
    path("configure-llm/", ConfigureLLM.as_view(), name="configure_llm"),
    path("configure-llm/admin", ConfigureLLM_admin.as_view(), name="configure_llm_admin"),
    path("clear-chat/", ClearChat.as_view(), name="clear_chat"),
    path("clear-chat/admin", ClearChat_admin.as_view(), name="clear_chat_admin"),
    path("clear-chat2/", ClearChat2.as_view(), name="clear_chat2"),
    path("clear-chat/phi", ClearChatPhi.as_view(), name="clear_chatphi"),
    path("clear-chat/phi/admin", ClearChatPhiAdmin.as_view(), name="clear_chatphi_admin"),
    path("upload-pdf/", UploadPDF.as_view(), name="upload_pdf"),
    path("qna/admin/", QnAPage_admin.as_view(), name = "rag_qna_page_admin"),
    path("qna2/", QnAPage2.as_view(), name="rag_qna_page2"),
    path("qna/phi", QnAPagePhi.as_view(), name="rag_qna_page_phi"),
    path("qna/phi/admin", QnAPagePhi_admin.as_view(), name="rag_qna_page_phi_admin"),





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
   

