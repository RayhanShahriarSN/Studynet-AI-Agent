# Memory management
from typing import Dict, List, Optional
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import AzureChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from models import MemoryContext, ChatMessage, MessageRole
from config import config
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
        self.contexts: Dict[str, MemoryContext] = {}
        
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
            
            self.contexts[session_id] = MemoryContext(
                session_id=session_id,
                messages=[]
            )
        
        return session_id
    
    def add_message(self, session_id: str, role: MessageRole, content: str):
        """Add a message to the conversation memory"""
        session_id = self.get_or_create_memory(session_id)
        
        # Add to context
        message = ChatMessage(role=role, content=content)
        self.contexts[session_id].messages.append(message)
        
        # Add to LangChain memory
        if role == MessageRole.USER:
            self.memories[session_id].chat_memory.add_user_message(content)
        elif role == MessageRole.ASSISTANT:
            self.memories[session_id].chat_memory.add_ai_message(content)
        
        # Update token count
        self.contexts[session_id].total_tokens = self._count_tokens(session_id)
        self.contexts[session_id].updated_at = datetime.now()
        
    def get_conversation_context(self, session_id: str, 
                                 max_messages: Optional[int] = None) -> str:
        """Get formatted conversation context"""
        if session_id not in self.contexts:
            return ""
        
        messages = self.contexts[session_id].messages
        if max_messages:
            messages = messages[-max_messages:]
        
        # Format messages for context
        context_parts = []
        for msg in messages:
            role_label = "User" if msg.role == MessageRole.USER else "Assistant"
            context_parts.append(f"{role_label}: {msg.content}")
        
        return "\n".join(context_parts)
    
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
        if session_id not in self.contexts:
            return 0
        
        total_text = " ".join([msg.content for msg in self.contexts[session_id].messages])
        return len(self.encoding.encode(total_text))
    
    def clear_session(self, session_id: str):
        """Clear memory for a specific session"""
        if session_id in self.memories:
            self.memories[session_id].clear()
            del self.memories[session_id]
        
        if session_id in self.contexts:
            del self.contexts[session_id]
    
    def get_all_sessions(self) -> List[str]:
        """Get all active session IDs"""
        return list(self.memories.keys())

# Singleton instance
memory_manager = ConversationMemoryManager()