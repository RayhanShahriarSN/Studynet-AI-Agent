# Memory management for Django RAG backend
from typing import Dict, List, Optional
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import AzureChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from .models import ConversationSession, ChatMessage
from .config import config
import tiktoken
import uuid
from datetime import datetime

class ConversationMemoryManager:
    """Manages conversation memory with token-based summarization"""
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=config.CHAT_MODEL_DEPLOYMENT,
            openai_api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            temperature=0.3,
            max_tokens=500
        )
        
        # Store memories for different sessions
        self.memories: Dict[str, ConversationSummaryBufferMemory] = {}
        
        # Token counter
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
    def get_or_create_memory(self, session_id: Optional[str] = None) -> str:
        """Get existing memory or create new one for session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.memories:
            self.memories[session_id] = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=config.MAX_MEMORY_TOKENS,
                return_messages=True,
                memory_key="chat_history",
                input_key="input",
                output_key="output"
            )
            
            # Create or get Django session
            session, created = ConversationSession.objects.get_or_create(
                session_id=session_id,
                defaults={'total_tokens': 0}
            )
        
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the conversation memory"""
        session_id = self.get_or_create_memory(session_id)
        
        # Get or create Django session
        session, created = ConversationSession.objects.get_or_create(
            session_id=session_id,
            defaults={'total_tokens': 0}
        )
        
        # Add to Django model
        ChatMessage.objects.create(
            session=session,
            role=role,
            content=content
        )
        
        # Add to LangChain memory
        if role == "user":
            self.memories[session_id].chat_memory.add_user_message(content)
        elif role == "assistant":
            self.memories[session_id].chat_memory.add_ai_message(content)
        
        # Update token count
        session.total_tokens = self._count_tokens(session_id)
        session.save()
        
    def get_conversation_context(self, session_id: str, 
                                 max_messages: Optional[int] = None) -> str:
        """Get formatted conversation context"""
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            messages = session.messages.all()
            
            if max_messages and len(messages) > max_messages:
                messages = messages[-max_messages:]
            
            # Format messages for context
            context_parts = []
            for msg in messages:
                role_label = "User" if msg.role == "user" else "Assistant"
                context_parts.append(f"{role_label}: {msg.content}")
            
            return "\n".join(context_parts)
        except ConversationSession.DoesNotExist:
            return ""
    
    def get_memory_variables(self, session_id: str) -> Dict:
        """Get memory variables for LangChain"""
        if session_id not in self.memories:
            return {"chat_history": []}
        
        return self.memories[session_id].load_memory_variables({})
    
    def summarize_if_needed(self, session_id: str):
        """Summarize conversation if token limit exceeded"""
        if session_id not in self.memories:
            return
        
        current_tokens = self._count_tokens(session_id)
        if current_tokens > config.MAX_MEMORY_TOKENS:
            # Memory will automatically summarize older messages
            self.memories[session_id].prune()
    
    def _count_tokens(self, session_id: str) -> int:
        """Count tokens in conversation"""
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            messages = session.messages.all()
            total_text = " ".join([msg.content for msg in messages])
            return len(self.encoding.encode(total_text))
        except ConversationSession.DoesNotExist:
            return 0
    
    def clear_session(self, session_id: str):
        """Clear memory for a specific session"""
        if session_id in self.memories:
            self.memories[session_id].clear()
            del self.memories[session_id]
        
        # Clear Django session
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            session.messages.all().delete()
            session.delete()
        except ConversationSession.DoesNotExist:
            pass
    
    def get_all_sessions(self) -> List[str]:
        """Get all active session IDs"""
        return list(ConversationSession.objects.values_list('session_id', flat=True))

# Singleton instance
memory_manager = ConversationMemoryManager()