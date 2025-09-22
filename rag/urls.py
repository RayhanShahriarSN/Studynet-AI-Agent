# rag/urls.py
from django.urls import path
from .views import QnAPage, ConfigureLLM, ClearChat, UploadPDF, QnAPage_admin, ConfigureLLM_admin, ClearChat_admin, QnAPage2,QnAPagePhi,ClearChat2,ClearChatPhi, QnAPagePhi_admin

urlpatterns = [

    path("qna/", QnAPage.as_view(), name="rag_qna_page"),
    path("configure-llm/", ConfigureLLM.as_view(), name="configure_llm"),
    path("configure-llm/admin", ConfigureLLM_admin.as_view(), name="configure_llm_admin"),
    path("clear-chat/", ClearChat.as_view(), name="clear_chat"),
    path("clear-chat/admin", ClearChat_admin.as_view(), name="clear_chat_admin"),
    path("clear-chat2/", ClearChat2.as_view(), name="clear_chat2"),
    path("clear-chat/phi", ClearChatPhi.as_view(), name="clear_chatphi"),
    path("upload-pdf/", UploadPDF.as_view(), name="upload_pdf"),
    path("qna/admin/", QnAPage_admin.as_view(), name = "rag_qna_page_admin"),
    path("qna2/", QnAPage2.as_view(), name="rag_qna_page2"),
    path("qna/phi", QnAPagePhi.as_view(), name="rag_qna_page_phi"),
    path("qna/phi/admin", QnAPagePhi_admin.as_view(), name="rag_qna_page_phi_admin")
   
]
