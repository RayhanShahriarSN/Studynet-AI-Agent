"""
Enhanced StudyNet AI Counselor Agent (V2)

Integrates all components:
- Query classification and entity extraction
- Tool-based execution for structured queries
- Hybrid retrieval for complex queries
- LangChain agent with intelligent routing
"""

import logging
from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory

from .query.classifier import get_classifier, QueryType, Intent
from .retrieval.hybrid_retriever import get_hybrid_retriever
from .tools.structured_tools import get_structured_tools
from .tools.semantic_tools import get_semantic_tools
from .llm import llm
from .memory import get_memory

logger = logging.getLogger(__name__)


class StudyNetCounselorAgentV2:
    """
    Enhanced AI agent for StudyNet with intelligent query routing

    Architecture:
    1. Classify incoming query (STRUCTURED/SEMANTIC/HYBRID/COMPARISON)
    2. Route to appropriate handler:
       - STRUCTURED → Use tools directly
       - SEMANTIC → Use semantic tools
       - HYBRID → Use hybrid retriever + tools
       - COMPARISON → Use comparison tools
    3. Generate natural language response
    """

    def __init__(self):
        self.classifier = get_classifier()
        self.hybrid_retriever = get_hybrid_retriever()

        # Get all tools
        self.structured_tools = get_structured_tools()
        self.semantic_tools = get_semantic_tools()
        self.all_tools = self.structured_tools + self.semantic_tools

        # Create agent prompt
        self.prompt = self._create_prompt()

        # Create ReAct agent
        self.agent = create_react_agent(
            llm=llm,
            tools=self.all_tools,
            prompt=self.prompt
        )

    def _create_prompt(self) -> PromptTemplate:
        """Create the agent prompt template"""

        template = """You are an AI counselor for StudyNet, helping international students find universities and courses in Australia.

You have access to the following tools:

{tools}

Tool Names: {tool_names}

IMPORTANT GUIDELINES:
1. Always be helpful, friendly, and professional
2. For course searches, use search_courses tool with appropriate filters
3. For university comparisons, use compare_providers tool
4. For guidance questions (visa, applications), use search_guidance tool
5. Always cite specific course names, fees, and provider names from your search results
6. If you don't find results, suggest the student broaden their search criteria
7. Format responses with clear sections and bullet points when helpful

Previous conversation:
{chat_history}

Student Question: {input}

Think step-by-step:
{agent_scratchpad}"""

        return PromptTemplate(
            input_variables=["input", "chat_history", "agent_scratchpad", "tools", "tool_names"],
            template=template
        )

    def process_query(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Main entry point for processing queries

        Args:
            query: Student's question
            session_id: Session identifier for conversation history

        Returns:
            Dict with response, sources, and metadata
        """

        logger.info(f"Processing query: {query[:100]}...")

        try:
            # 1. Classify the query
            parsed_query = self.classifier.classify(query)
            logger.info(f"Query classified as: {parsed_query.query_type.value}, Intent: {parsed_query.intent.value}")

            # 2. Get conversation memory
            memory = get_memory(session_id)

            # 3. Route to appropriate handler
            if parsed_query.query_type == QueryType.STRUCTURED:
                response = self._handle_structured(query, parsed_query, memory)

            elif parsed_query.query_type == QueryType.SEMANTIC:
                response = self._handle_semantic(query, parsed_query, memory)

            elif parsed_query.query_type == QueryType.HYBRID:
                response = self._handle_hybrid(query, parsed_query, memory)

            elif parsed_query.query_type == QueryType.COMPARISON:
                response = self._handle_comparison(query, parsed_query, memory)

            else:
                # Fallback to agent
                response = self._handle_with_agent(query, memory)

            # 4. Update memory
            memory.save_context(
                {"input": query},
                {"output": response['answer']}
            )

            # 5. Add metadata
            response['metadata'] = {
                'query_type': parsed_query.query_type.value,
                'intent': parsed_query.intent.value,
                'entities_found': len(parsed_query.entities),
                'session_id': session_id
            }

            return response

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                'answer': f"I apologize, but I encountered an error processing your request. Please try rephrasing your question or contact support if the issue persists.",
                'sources': [],
                'metadata': {'error': str(e)}
            }

    def _handle_structured(self, query: str, parsed_query, memory) -> Dict[str, Any]:
        """Handle structured queries using direct tool calls"""

        logger.info("Handling structured query with tools")

        # For structured queries, we can use the tools directly
        # Or let the agent decide which tool to use

        return self._handle_with_agent(query, memory)

    def _handle_semantic(self, query: str, parsed_query, memory) -> Dict[str, Any]:
        """Handle semantic queries using guidance search"""

        logger.info("Handling semantic query")

        # Use search_guidance tool directly
        from .tools.semantic_tools import SearchGuidanceTool

        guidance_tool = SearchGuidanceTool()
        result = guidance_tool._run(query=query, k=5)

        # Format response
        return {
            'answer': result,
            'sources': ['PDF Guidance Documents'],
            'query_type': 'semantic'
        }

    def _handle_hybrid(self, query: str, parsed_query, memory) -> Dict[str, Any]:
        """Handle hybrid queries using hybrid retriever"""

        logger.info("Handling hybrid query with retriever")

        # Use hybrid retriever to get both structured and semantic results
        hybrid_result = self.hybrid_retriever.retrieve(parsed_query, k=10)

        # Use the agent to synthesize a response from the hybrid results
        context = self._format_hybrid_context(hybrid_result)

        # Create enhanced query with context
        enhanced_query = f"""Based on the following information, answer the student's question:

{context}

Student Question: {query}

Please provide a comprehensive answer."""

        return self._handle_with_agent(enhanced_query, memory, include_sources=True)

    def _handle_comparison(self, query: str, parsed_query, memory) -> Dict[str, Any]:
        """Handle comparison queries"""

        logger.info("Handling comparison query")

        # Use the agent with compare_providers tool
        return self._handle_with_agent(query, memory)

    def _handle_with_agent(self, query: str, memory, include_sources: bool = False) -> Dict[str, Any]:
        """Let the ReAct agent handle the query"""

        logger.info("Delegating to ReAct agent")

        try:
            # Create agent executor
            agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.all_tools,
                verbose=True,
                max_iterations=5,
                handle_parsing_errors=True,
                return_intermediate_steps=include_sources
            )

            # Get chat history
            chat_history = memory.load_memory_variables({}).get('history', '')

            # Execute agent
            result = agent_executor.invoke({
                "input": query,
                "chat_history": chat_history
            })

            # Extract sources if available
            sources = []
            if include_sources and 'intermediate_steps' in result:
                for step in result['intermediate_steps']:
                    tool_name = step[0].tool
                    sources.append(tool_name)

            return {
                'answer': result['output'],
                'sources': sources,
                'query_type': 'agent'
            }

        except Exception as e:
            logger.error(f"Agent execution error: {e}")

            # Fallback to simple response
            return {
                'answer': "I apologize, but I'm having trouble processing that request right now. Could you please rephrase your question or be more specific about what you're looking for?",
                'sources': [],
                'query_type': 'error'
            }

    def _format_hybrid_context(self, hybrid_result) -> str:
        """Format hybrid retrieval results as context for LLM"""

        context = ""

        # Add structured data
        if hybrid_result.structured_data:
            context += "## Course Information:\n\n"
            for i, course in enumerate(hybrid_result.structured_data[:5], 1):
                context += f"{i}. **{course.get('course_name', 'N/A')}**\n"
                context += f"   - Provider: {course.get('provider_name', 'N/A')}\n"
                context += f"   - Level: {course.get('study_level', 'N/A')}\n"
                if course.get('total_annual_fee'):
                    context += f"   - Annual Fee: ${course['total_annual_fee']:,.2f}\n"
                if course.get('address_city'):
                    context += f"   - Location: {course['address_city']}, {course.get('address_state', '')}\n"
                context += "\n"

        # Add semantic data
        if hybrid_result.semantic_data:
            context += "\n## Additional Context:\n\n"
            for i, doc in enumerate(hybrid_result.semantic_data[:3], 1):
                content = doc.get('content', '')[:200]  # Truncate
                context += f"{i}. {content}...\n\n"

        return context


# Singleton instance
_agent_instance = None

def get_agent_v2() -> StudyNetCounselorAgentV2:
    """Get singleton instance of StudyNetCounselorAgentV2"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = StudyNetCounselorAgentV2()
    return _agent_instance
