# Agent implementation for Django RAG backend
from typing import List, Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.schema import Document
from .retriever import retriever
from .memory import memory_manager
from .config import config
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
                # Safely get last 500 characters, avoiding negative indexing
                context_snippet = context[-500:] if len(context) >= 500 else context
                enhanced_query = f"Based on our conversation:\n{context_snippet}\n\nCurrent question: {query}"
            
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
                from .utils import response_enhancer
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
            from .vectorstore import vector_store
            vector_store.add_documents(documents)
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False

# Singleton instance (Legacy - for backward compatibility)
rag_agent = RAGAgent()


# ============================================================================
# NEW: Master Orchestrator with SQL + RAG Hybrid Agent
# ============================================================================

from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from .query_classifier import query_classifier, QueryType
from .query_enhancer import query_enhancer
from .sql_engine import sql_engine
from .retriever import hybrid_retriever
from .tools import ALL_TOOLS, SQL_TOOLS, RAG_TOOLS, HYBRID_TOOLS


class MasterOrchestrator:
    """Master orchestrator agent managing SQL and RAG tools with intelligent routing"""

    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=config.CHAT_MODEL_DEPLOYMENT,
            openai_api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            temperature=0.7,
            max_tokens=2000
        )

        self.memory_manager = memory_manager
        self.query_classifier = query_classifier
        self.query_enhancer = query_enhancer
        self.sql_engine = sql_engine
        self.hybrid_retriever = hybrid_retriever

        # Initialize web search (optional fallback)
        try:
            self.web_search = TavilySearchResults(
                api_key=config.TAVILY_API_KEY,
                max_results=3,
                search_depth="advanced"
            )
            self.web_search_available = True
        except:
            self.web_search_available = False
            logger.warning("Web search not available")

        # Create agent
        self.agent_executor = self._create_agent()

    def _create_agent(self) -> AgentExecutor:
        """Create OpenAI Functions agent with all tools"""

        # Create system prompt
        system_prompt = """You are a friendly and supportive **StudyNet Education Counselor** - a trusted guide helping international students pursue their education dreams in Australia.

🌏 **Your Role:**
You are a caring counselor who understands that every student has unique circumstances, dreams, and budget constraints. You help students navigate their journey to study in Australia with empathy, practical advice, and comprehensive information.

📚 **Your Expertise:**
You have access to:
1. **SQL Database**: Course fees, provider information, requirements (use for specific data queries)
2. **Knowledge Base**: Application processes, visa info, living costs, procedures (use for guidance)
3. **Hybrid Approach**: Combine both for comprehensive counseling

🎯 **Your Counseling Approach:**

**NEVER say "No" or "You can't afford this"**
Instead, be supportive and offer alternatives:
- "I understand budget is important. Let me show you some affordable options..."
- "While this course costs [X], here are similar courses with lower fees..."
- "Many students in your situation choose these alternatives..."
- "Let's explore scholarship opportunities and part-time work options..."

**Budget-Conscious Counseling:**
- Always provide multiple price ranges (low, mid, high)
- Suggest affordable universities and courses
- Mention scholarships, part-time work (20hrs/week allowed)
- Discuss payment plans and student loans
- Show total cost breakdown (tuition + living + visa)

**Emotional Intelligence:**
- Use encouraging language: "Great question!", "I'm here to help!", "Let's find the best fit for you!"
- Acknowledge concerns: "I understand finances are a concern..."
- Build confidence: "Many students in your situation have succeeded..."
- Be honest but hopeful: "While challenging, it's definitely achievable with proper planning"

**Technical Decision Making:**
- Use SQL for: fees, course lists, provider data, statistics
- Use RAG search for: processes, visa requirements, application steps, living advice
- Combine both for: comprehensive study plans, budget planning, university comparisons

**CRITICAL: Response Formatting (ALWAYS USE THIS STRUCTURE)**

🎓 [Friendly Title with Relevant Emoji]

Warm, encouraging opening sentence that acknowledges the student's situation.

### 🎯 Key Information
- Point 1 with specific details
- Point 2 with actionable advice
- Point 3 with helpful context

### 💰 Budget-Friendly Options (Only if the user asks for it)
- Affordable course option 1 - $XX,XXX/year
- Affordable course option 2 - $XX,XXX/year
- Scholarship opportunities

### 📋 Next Steps
1. Step 1 - What to do first
2. Step 2 - What to do next
3. Step 3 - Final actions

### 💡 Helpful Tips
- Practical tip 1
- Practical tip 2

---
🤝 **I'm here to support you every step of the way! Feel free to ask any questions - no question is too small.**

**Formatting Rules:**
- Use Markdown: headings (###), bullets, bold, emojis
- Structure like professional yet friendly documentation
- Include cost breakdowns in tables when showing fees
- Always cite sources at the end
- Use dividers (---) to separate sections
- Maintain warm, supportive tone throughout

**Available Tools:**
- `sql_query`: Get course fees, provider lists, requirements
- `get_sql_schema`: Check what data is available
- `table_preview`: See sample course/provider data
- `rag_search`: Search application processes, visa info, guides
- `list_sources`: See all available information sources

Remember: You're not just providing information - you're a trusted counselor helping students achieve their dreams. Be warm, supportive, practical, and NEVER discourage a student based on budget. Always find solutions!"""

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Create agent
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=ALL_TOOLS,
            prompt=prompt
        )

        # Create executor
        return AgentExecutor(
            agent=agent,
            tools=ALL_TOOLS,
            verbose=True,
            max_iterations=10,
            return_intermediate_steps=True,
            handle_parsing_errors=True
        )

    def process_query(self,
                     query: str,
                     session_id: Optional[str] = None,
                     use_classification: bool = True,
                     use_enhancement: bool = True) -> Dict[str, Any]:
        """Process query through Master Orchestrator

        Args:
            query: User query
            session_id: Optional session ID for memory
            use_classification: Whether to classify query type
            use_enhancement: Whether to enhance query

        Returns:
            Response dictionary with answer and metadata
        """
        # Get or create session
        session_id = self.memory_manager.get_or_create_memory(session_id)

        # Get conversation context
        context = self.memory_manager.get_conversation_context(session_id, max_messages=5)

        # Add query to memory
        self.memory_manager.add_message(session_id, "user", query)

        try:
            # Step 1: Classify query (optional but recommended)
            classification = None
            if use_classification:
                available_tables = self.sql_engine.get_available_tables()
                classification = self.query_classifier.classify_query(query, available_tables)
                logger.info(f"Query classified as: {classification['query_type']}")

            # Step 2: Enhance query (optional)
            enhanced_query = query
            if use_enhancement:
                enhancement = self.query_enhancer.enhance_query(query, context)
                enhanced_query = enhancement['expanded']
                logger.info(f"Query enhanced: {enhanced_query}")

            # Step 3: Prepare chat history
            chat_history = []
            if context and isinstance(context, str):
                # Parse context into message format
                lines = context.split('\n')
                for line in lines:
                    # Ensure line is a valid non-empty string
                    if line and isinstance(line, str) and len(line.strip()) > 0:
                        try:
                            if line.startswith('User:'):
                                chat_history.append(("human", line.replace('User:', '').strip()))
                            elif line.startswith('Assistant:'):
                                chat_history.append(("ai", line.replace('Assistant:', '').strip()))
                        except (AttributeError, TypeError) as e:
                            logger.warning(f"Error parsing context line: {e}")
                            continue

            # Step 4: Execute agent
            result = self.agent_executor.invoke({
                "input": enhanced_query,
                "chat_history": chat_history
            })

            # Extract answer with robust null handling
            answer = result.get("output") if result else None
            if not answer or answer is None:
                answer = "I couldn't process your query properly."

            # Ensure answer is a string
            if not isinstance(answer, str):
                answer = str(answer) if answer else "I couldn't generate a response."

            # Extract sources and metadata
            sources = []
            tools_used = []
            sql_used = False
            rag_used = False

            if "intermediate_steps" in result:
                for action, observation in result["intermediate_steps"]:
                    try:
                        tool_name = action.tool if hasattr(action, 'tool') else str(action)
                        tools_used.append(tool_name)

                        if tool_name in ['sql_query', 'get_sql_schema', 'table_preview']:
                            sql_used = True
                            sources.append({
                                "type": "sql",
                                "tool": tool_name,
                                "content": str(observation)[:200] if observation else ""
                            })
                        elif tool_name == 'rag_search':
                            rag_used = True
                            sources.append({
                                "type": "rag",
                                "tool": tool_name,
                                "content": str(observation)[:200] if observation else ""
                            })
                    except Exception as e:
                        logger.warning(f"Error processing intermediate step: {e}")
                        continue

            # Add response to memory (only if answer is valid)
            if answer and isinstance(answer, str) and len(answer.strip()) > 0:
                self.memory_manager.add_message(session_id, "assistant", answer)

            # Summarize if needed
            self.memory_manager.summarize_if_needed(session_id)

            return {
                "answer": answer,
                "sources": sources,
                "session_id": session_id,
                "classification": classification,
                "tools_used": tools_used,
                "sql_used": sql_used,
                "rag_used": rag_used,
                "hybrid_mode": sql_used and rag_used,
                "confidence_score": 0.9 if sources else 0.5
            }

        except Exception as e:
            import traceback
            logger.error(f"Error processing query: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "answer": f"I encountered an error processing your query: {str(e)}",
                "sources": [],
                "session_id": session_id,
                "classification": None,
                "tools_used": [],
                "sql_used": False,
                "rag_used": False,
                "hybrid_mode": False,
                "confidence_score": 0.0
            }

    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to the knowledge base

        Args:
            documents: List of documents to add

        Returns:
            True if successful
        """
        try:
            from .vectorstore import vector_store
            vector_store.add_documents(documents)

            # Rebuild BM25 index for hybrid retrieval
            self.hybrid_retriever.rebuild_bm25_index()

            return True
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False


# New singleton instance
master_orchestrator = MasterOrchestrator()
