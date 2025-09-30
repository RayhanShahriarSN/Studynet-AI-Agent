"""
Semantic Search Tools for StudyNet AI Counselor

LangChain tools that perform vector search on PDF guidance documents
for questions about procedures, visas, applications, etc.
"""

import logging
from typing import Optional, List, Dict
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ..vectorstore import HierarchicalVectorStore

logger = logging.getLogger(__name__)


# ============================================================================
# Tool Input Schemas
# ============================================================================

class SearchGuidanceInput(BaseModel):
    """Input schema for search_guidance_tool"""
    query: str = Field(..., description="The guidance question (e.g., 'How do I apply for a student visa?')")
    k: int = Field(5, description="Number of relevant documents to retrieve")


class SearchProviderInfoInput(BaseModel):
    """Input schema for search_provider_info_tool"""
    query: str = Field(..., description="Question about university facilities, culture, research areas")
    provider_name: Optional[str] = Field(None, description="Optional provider name to filter results")
    k: int = Field(5, description="Number of relevant documents to retrieve")


# ============================================================================
# Tool Implementations
# ============================================================================

class SearchGuidanceTool(BaseTool):
    """Search guidance documents for procedural questions"""

    name: str = "search_guidance"
    description: str = """
    Search PDF guidance documents to answer procedural questions about:
    - Student visa applications and requirements
    - Application procedures and documents needed
    - Admission requirements and eligibility
    - Living in Australia (accommodation, cost of living)
    - Working while studying
    - Post-study work rights
    - Health insurance (OSHC) requirements

    Use this for "how-to" questions and guidance needs:
    - "How do I apply for a student visa?"
    - "What documents do I need for application?"
    - "What are the English language requirements?"
    - "Can I work while studying in Australia?"

    DO NOT use this for:
    - Searching for specific courses (use search_courses instead)
    - Comparing universities (use compare_providers instead)
    """
    args_schema: type[BaseModel] = SearchGuidanceInput

    def _run(self, query: str, k: int = 5) -> str:
        """Search guidance documents"""
        try:
            vectorstore = HierarchicalVectorStore()

            # Perform similarity search
            # Note: Returns list of (Document, score) tuples
            results_with_scores = vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                threshold=0.5  # Lower threshold for guidance documents
            )

            # Extract just the documents
            results = [doc for doc, score in results_with_scores]

            if not results:
                return (
                    "I couldn't find specific guidance on that topic in our knowledge base. "
                    "For the most accurate information, please visit the official Australian "
                    "government immigration website or contact the university directly."
                )

            # Format results
            output = "Based on our guidance documents:\n\n"

            for i, doc in enumerate(results, 1):
                content = doc.page_content
                metadata = doc.metadata

                output += f"{i}. "
                if metadata.get('source'):
                    source_name = metadata['source'].split('/')[-1]
                    output += f"[From {source_name}]\n"

                output += f"{content}\n\n"

            output += "\n📌 Note: Always verify this information with official sources and the university."

            return output

        except Exception as e:
            logger.error(f"Error in search_guidance: {e}")
            return (
                f"I encountered an error while searching guidance documents: {str(e)}\n"
                "Please try rephrasing your question or contact support."
            )


class SearchProviderInfoTool(BaseTool):
    """Search for information about university facilities, culture, research"""

    name: str = "search_provider_info"
    description: str = """
    Search PDF documents for detailed information about universities:
    - Campus facilities and infrastructure
    - Research strengths and focus areas
    - Student support services
    - University culture and student life
    - Industry partnerships and internship opportunities
    - Graduate employment outcomes

    Use this when students ask about university characteristics:
    - "What is UNSW known for?"
    - "Does Macquarie have good research facilities?"
    - "Tell me about student life at UTS"
    - "What support services does the university offer?"

    DO NOT use this for:
    - Course search (use search_courses)
    - Rankings and statistics (use get_provider_details)
    - Application procedures (use search_guidance)
    """
    args_schema: type[BaseModel] = SearchProviderInfoInput

    def _run(
        self,
        query: str,
        provider_name: Optional[str] = None,
        k: int = 5
    ) -> str:
        """Search provider information"""
        try:
            vectorstore = HierarchicalVectorStore()

            # Perform similarity search
            # Note: Metadata filtering not yet implemented in HierarchicalVectorStore
            # For now, get results and filter by provider_name in post-processing
            results_with_scores = vectorstore.similarity_search_with_score(
                query=query,
                k=k * 2 if provider_name else k,  # Get more if we need to filter
                threshold=0.5
            )

            # Extract documents
            results = [doc for doc, score in results_with_scores]

            # Post-filter by provider_name if specified
            if provider_name and results:
                results = [
                    doc for doc in results
                    if doc.metadata.get("provider_name") == provider_name
                ][:k]

            if not results:
                provider_text = f" about {provider_name}" if provider_name else ""
                return (
                    f"I couldn't find specific information{provider_text} in our knowledge base. "
                    "For detailed information about the university, please visit their official website "
                    "or use get_provider_details for statistical information."
                )

            # Format results
            if provider_name:
                output = f"Information about {provider_name}:\n\n"
            else:
                output = "Based on university information:\n\n"

            for i, doc in enumerate(results, 1):
                content = doc.page_content
                metadata = doc.metadata

                output += f"{i}. "
                if metadata.get('source'):
                    source_name = metadata['source'].split('/')[-1]
                    output += f"[From {source_name}]\n"
                elif metadata.get('provider_name'):
                    output += f"[{metadata['provider_name']}]\n"

                output += f"{content}\n\n"

            return output

        except Exception as e:
            logger.error(f"Error in search_provider_info: {e}")
            return (
                f"I encountered an error while searching provider information: {str(e)}\n"
                "Please try rephrasing your question."
            )


# ============================================================================
# Tool Registry
# ============================================================================

def get_semantic_tools() -> List[BaseTool]:
    """Get all semantic search tools for the agent"""
    return [
        SearchGuidanceTool(),
        SearchProviderInfoTool(),
    ]


# ============================================================================
# Helper: Get All Tools
# ============================================================================

def get_all_tools() -> List[BaseTool]:
    """Get both structured and semantic tools"""
    from .structured_tools import get_structured_tools

    return get_structured_tools() + get_semantic_tools()
