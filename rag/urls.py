# rag/urls.py
from django.urls import path
from rag.views import *

urlpatterns = [
    
 
    
    
    path("clear-chat/admin", ClearChat_admin.as_view(), name="clear_chat_admin"),
  
    path("clear-chat/phi", ClearChatPhi.as_view(), name="clear_chatphi"),
    path("clear-chat/phi/admin", ClearChatPhiAdmin.as_view(), name="clear_chatphi_admin"),
    path("upload-pdf/", UploadPDF.as_view(), name="upload_pdf"),
   
    
    path("qna/phi", QnAPagePhi.as_view(), name="rag_qna_page_phi"),
    path("qna/phi/admin", QnAPagePhi_admin.as_view(), name="rag_qna_page_phi_admin"),
    path("clear-chat/api/", ClearChatAPI.as_view(), name="clear_chat_api"),
  


    # Frontend
    path('', index_view, name='frontend'),
   
    
    # Health check
    path('health/', HealthCheckView.as_view(), name='health_check'),
    
    # Core query processing
    path('query/', QueryProcessView.as_view(), name='query_process'),
    
    # Document management
    path('upload/document/', DocumentUploadView.as_view(), name='document_upload'),
    path('upload/text/', TextUploadView.as_view(), name='text_upload'),
    
    # Memory management
    path('memory/<str:session_id>/', MemoryView.as_view(), name='memory_detail'),
    path('sessions/', SessionsListView.as_view(), name='sessions_list'),
    
    # System monitoring
    path('metrics/', MetricsView.as_view(), name='metrics'),
    
    # Knowledge base management
    path('knowledge-base/status/', KnowledgeBaseStatusView.as_view(), name='kb_status'),
    path('knowledge-base/reload/', KnowledgeBaseReloadView.as_view(), name='kb_reload'),
    path('vectorstore/clear/', VectorStoreClearView.as_view(), name='vectorstore_clear'),

]