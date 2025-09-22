# Agent implementation
from typing import List, Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.schema import Document
from retriever import retriever
from memory import memory_manager
from config import config
import logging

logger = logging.getLogger(__name__)

class RAGAgent:
    """Main RAG agent with knowledge base and web search fallback"""
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=config.CHAT_MODEL_DEPLOYMENT,
            openai_api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            temperature=0.7,
            max_tokens=2000
        )
        
        self.retriever = retriever
        self.memory_manager = memory_manager
        
        # Initialize Tavily web search
        self.web_search = TavilySearchResults(
            api_key=config.TAVILY_API_KEY,
            max_results=3,
            search_depth="advanced"
        )
        
        # Create tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent_executor = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent"""
        
        def search_knowledge_base(query: str) -> str:
             """Search internal knowledge base (data from PDFs folder)"""
             docs = self.retriever.retrieve(query, k=config.RETRIEVER_K)
             if not docs:
                 return "No relevant information found in knowledge base (PDFs folder)."
             
             # Format results
             results = []
             for i, doc in enumerate(docs, 1):
                 content = doc.page_content
                 if 'parent_context' in doc.metadata:
                     content = f"{content}\n\nContext: {doc.metadata['parent_context'][:500]}"
                 
                 # Add source file information
                 source_file = doc.metadata.get('source_file', 'Unknown')
                 results.append(f"[{i}] From {source_file}: {content[:500]}...")
             
             return "\n\n".join(results)
        
        def search_web(query: str) -> str:
            """Search the web for information"""
            try:
                results = self.web_search.run(query)
                if isinstance(results, list) and results:
                    formatted = []
                    for r in results[:3]:
                        formatted.append(f"Title: {r.get('title', 'N/A')}\n{r.get('content', '')[:500]}")
                    return "\n\n".join(formatted)
                return str(results)
            except Exception as e:
                logger.error(f"Web search failed: {e}")
                return "Web search failed. Please try again."
        
        return [
             Tool(
                 name="search_knowledge_base",
                 func=search_knowledge_base,
                 description="Search the internal knowledge base (PDFs folder) for information. Use this FIRST before web search."
             ),
             Tool(
                 name="search_web",
                 func=search_web,
                 description="Search the web for current information. Use only if knowledge base (PDFs folder) doesn't have the answer."
             )
         ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the ReAct agent with enhanced formatting"""
        
        prompt = PromptTemplate(
            input_variables=["input", "tools", "tool_names", "agent_scratchpad", "chat_history"],
            template="""You are an intelligent AI assistant with access to a knowledge base and web search.

You must use the following format:

Thought: I need to think about what to do
Action: search_knowledge_base
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

RESPONSE FORMATTING GUIDELINES:
- Always use the correct format: Thought: ... Action: ... Action Input: ... Observation: ...
- ALWAYS search the knowledge base FIRST for any information
-  If the knowledge base doesn't have sufficient information, then search the web
- Use clear structure with headers and bullet points
- Highlight key information with **bold text**
- Break complex processes into numbered steps
- Include relevant details and context
- End with a helpful follow-up question
- Use professional but friendly tone
- Format lists clearly with proper indentation

Previous conversation:
{chat_history}

Available tools:
{tools}

Tool names: {tool_names}

Question: {input}

Begin!

{agent_scratchpad}

Remember:
- Always follow the Thought/Action/Action Input/Observation format
- Always check knowledge base first
- Provide well-structured, detailed answers with proper formatting
- Include helpful follow-up questions
- Be thorough and accurate
- If uncertain, acknowledge it
"""
        )
        
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors="Check your output and make sure it conforms to the expected format! Use the correct format: Thought: ... Action: ... Action Input: ...",
            return_intermediate_steps=True,
            early_stopping_method="generate"
        )
    
    def process_query(self, 
                     query: str, 
                     session_id: Optional[str] = None,
                     use_web_search: bool = True,
                     enhance_formatting: bool = True) -> Dict[str, Any]:
        """Process a user query through the RAG pipeline"""
        
        # Get or create session
        session_id = self.memory_manager.get_or_create_memory(session_id)
        
        # Get conversation context
        context = self.memory_manager.get_conversation_context(session_id, max_messages=5)
        
        # Add query to memory
        self.memory_manager.add_message(session_id, "user", query)
        
        try:
            # First, try to retrieve from knowledge base
            kb_docs = self.retriever.retrieve(
                query, 
                k=config.RETRIEVER_K,
                context=context
            )
            
            # Check if we have good results from knowledge base
            has_good_kb_results = (
                len(kb_docs) > 0 and 
                any(doc.metadata.get('retrieval_score', 0) > config.SIMILARITY_THRESHOLD 
                    for doc in kb_docs)
            )
            
            # Prepare the enhanced query with context
            enhanced_query = query
            if context:
                enhanced_query = f"Based on our conversation:\n{context[-500:]}\n\nCurrent question: {query}"
            
            # Decide whether to use agent with tools or just LLM
            if has_good_kb_results and not use_web_search:
                # Just use LLM with retrieved context
                context_docs = "\n\n".join([doc.page_content for doc in kb_docs[:3]])
                
                prompt = f"""Answer the question using the following information.
                 
 Information:
 {context_docs}
 
 Question: {enhanced_query}
 
 Provide a direct, comprehensive answer. If the information doesn't fully answer the question, acknowledge what's missing."""
                
                response = self.llm.invoke(prompt)
                answer = response.content
                sources = [{"type": "knowledge_base", "content": doc.page_content[:200]} 
                          for doc in kb_docs[:3]]
                web_search_used = False
                
            else:
                # Use agent with tools
                try:
                    result = self.agent_executor.invoke({
                        "input": enhanced_query,
                        "chat_history": context,
                        "tools": self.tools,
                        "tool_names": [tool.name for tool in self.tools]
                    })
                    
                    answer = result.get("output", "I couldn't process your query properly.")
                    
                    # Extract sources from intermediate steps
                    sources = []
                    web_search_used = False
                    
                    if "intermediate_steps" in result:
                        for action, observation in result["intermediate_steps"]:
                            if action.tool == "search_knowledge_base":
                                sources.append({"type": "knowledge_base", "content": str(observation)[:200]})
                            elif action.tool == "search_web":
                                sources.append({"type": "web", "content": str(observation)[:200]})
                                web_search_used = True
                    
                    # If no sources found but we have KB docs, use them
                    if not sources and kb_docs:
                        sources = [{"type": "knowledge_base", "content": doc.page_content[:200]} 
                                  for doc in kb_docs[:3]]
                        
                except Exception as agent_error:
                    logger.warning(f"Agent execution failed: {agent_error}")
                    # Fallback to simple LLM response with KB context
                    if kb_docs:
                        context_docs = "\n\n".join([doc.page_content for doc in kb_docs[:3]])
                        fallback_prompt = f"""Answer the question using the following information.
                        
Information:
{context_docs}

Question: {enhanced_query}

Provide a direct, comprehensive answer. If the information doesn't fully answer the question, acknowledge what's missing."""
                        
                        response = self.llm.invoke(fallback_prompt)
                        answer = response.content
                        sources = [{"type": "knowledge_base", "content": doc.page_content[:200]} 
                                  for doc in kb_docs[:3]]
                        web_search_used = False
                    else:
                        answer = "I encountered an issue processing your query. Please try again."
                        sources = []
                        web_search_used = False
            
            # Enhance response formatting if requested
            if enhance_formatting:
                # Import here to avoid circular imports
                from utils import response_enhancer
                answer = response_enhancer.enhance_response(answer, query, sources)
            
            # Add response to memory
            self.memory_manager.add_message(session_id, "assistant", answer)
            
            # Summarize if needed
            self.memory_manager.summarize_if_needed(session_id)
            
            return {
                "answer": answer,
                "sources": sources,
                "session_id": session_id,
                "web_search_used": web_search_used,
                "confidence_score": min(max([doc.metadata.get('retrieval_score', 0.5) 
                                           for doc in kb_docs]) if kb_docs else 0.5, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "answer": f"I encountered an error processing your query: {str(e)}",
                "sources": [],
                "session_id": session_id,
                "web_search_used": False,
                "confidence_score": 0.0
            }
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to the knowledge base"""
        try:
            from vectorstore import vector_store
            vector_store.add_documents(documents)
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False

# Singleton instance
rag_agent = RAGAgent()