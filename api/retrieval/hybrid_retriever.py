"""
Hybrid Retrieval System for StudyNet AI Counselor

Combines structured (SQL) and semantic (vector) retrieval with intelligent merging.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..storage.duckdb_store import DuckDBStore
from ..vectorstore import HierarchicalVectorStore
from ..query.classifier import ParsedQuery, QueryType

logger = logging.getLogger(__name__)


@dataclass
class HybridResult:
    """Combined result from both structured and semantic sources"""

    # Result type
    result_type: str  # 'course', 'provider', 'guidance', 'mixed'

    # Structured data (courses, providers)
    structured_data: Optional[List[Dict]] = None

    # Semantic data (PDF chunks)
    semantic_data: Optional[List[Dict]] = None

    # Metadata
    source: str = ""  # 'structured', 'semantic', 'hybrid'
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'result_type': self.result_type,
            'structured_data': self.structured_data,
            'semantic_data': self.semantic_data,
            'source': self.source,
            'confidence': self.confidence
        }


class HybridRetriever:
    """
    Hybrid retrieval system that combines:
    1. Structured retrieval (SQL queries on DuckDB)
    2. Semantic retrieval (Vector search on ChromaDB)
    3. Result merging and enrichment
    """

    def __init__(self):
        self.db_store = DuckDBStore()
        self.vector_store = HierarchicalVectorStore()

    def retrieve(self, parsed_query: ParsedQuery, k: int = 10) -> HybridResult:
        """
        Main retrieval method - routes to appropriate handler based on query type

        Args:
            parsed_query: Classified and parsed query from QueryClassifier
            k: Number of results to return

        Returns:
            HybridResult containing combined data
        """
        logger.info(f"Hybrid retrieval for query type: {parsed_query.query_type.value}")

        if parsed_query.query_type == QueryType.STRUCTURED:
            return self._retrieve_structured(parsed_query, k)

        elif parsed_query.query_type == QueryType.SEMANTIC:
            return self._retrieve_semantic(parsed_query, k)

        elif parsed_query.query_type == QueryType.HYBRID:
            return self._retrieve_hybrid(parsed_query, k)

        elif parsed_query.query_type == QueryType.COMPARISON:
            return self._retrieve_comparison(parsed_query)

        else:
            # Fallback to semantic
            return self._retrieve_semantic(parsed_query, k)

    def _retrieve_structured(self, parsed_query: ParsedQuery, k: int) -> HybridResult:
        """Handle pure structured queries (course search, provider details, etc.)"""

        logger.info(f"Structured retrieval for intent: {parsed_query.intent.value}")

        # Use the filters from parsed_query to build SQL
        filters = parsed_query.filters

        # Determine which query to run based on intent
        from ..query.classifier import Intent

        if parsed_query.intent == Intent.SEARCH_COURSES or parsed_query.intent == Intent.FILTER_BY_CRITERIA:
            # Search courses
            results = self.db_store.search_courses(
                field_of_study=filters.get('field_of_study'),
                min_fee=filters.get('price_range', {}).get('min'),
                max_fee=filters.get('price_range', {}).get('max'),
                location_city=filters.get('location_city'),
                location_state=filters.get('location_state'),
                provider_name=filters.get('provider_name'),
                study_level=filters.get('study_level'),
                has_scholarship=filters.get('has_scholarship'),
                limit=k
            )

            return HybridResult(
                result_type='course',
                structured_data=results,
                source='structured',
                confidence=0.95
            )

        elif parsed_query.intent == Intent.GET_PROVIDER_INFO:
            # Get provider details
            provider_name = filters.get('provider_name', '')

            if provider_name:
                provider = self.db_store.get_provider_details(provider_name)
                results = [provider] if provider else []
            else:
                # No specific provider - return all providers in the location
                results = self.db_store.search_courses(
                    location_city=filters.get('location_city'),
                    location_state=filters.get('location_state'),
                    limit=k
                )

            return HybridResult(
                result_type='provider',
                structured_data=results,
                source='structured',
                confidence=0.95
            )

        elif parsed_query.intent == Intent.FIND_SCHOLARSHIPS:
            # Get scholarships
            field = filters.get('field_of_study', [None])[0] if filters.get('field_of_study') else None
            results = self.db_store.get_scholarships(field_of_study=field, limit=k)

            return HybridResult(
                result_type='provider',
                structured_data=results,
                source='structured',
                confidence=0.95
            )

        else:
            # Default course search
            results = self.db_store.search_courses(
                field_of_study=filters.get('field_of_study'),
                limit=k
            )

            return HybridResult(
                result_type='course',
                structured_data=results,
                source='structured',
                confidence=0.9
            )

    def _retrieve_semantic(self, parsed_query: ParsedQuery, k: int) -> HybridResult:
        """Handle pure semantic queries (guidance, how-to questions)"""

        logger.info("Semantic retrieval for guidance/procedural question")

        # Perform vector search
        try:
            results_with_scores = self.vector_store.similarity_search_with_score(
                query=parsed_query.original_query,
                k=k,
                threshold=0.5
            )

            # Convert to structured format
            semantic_results = []
            for doc, score in results_with_scores:
                semantic_results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': score
                })

            return HybridResult(
                result_type='guidance',
                semantic_data=semantic_results,
                source='semantic',
                confidence=0.85
            )

        except Exception as e:
            logger.error(f"Error in semantic retrieval: {e}")
            return HybridResult(
                result_type='guidance',
                semantic_data=[],
                source='semantic',
                confidence=0.0
            )

    def _retrieve_hybrid(self, parsed_query: ParsedQuery, k: int) -> HybridResult:
        """
        Handle hybrid queries requiring both structured and semantic retrieval

        Example: "Best IT courses with scholarships in Melbourne"
        - Structured: Get IT courses with scholarships in Melbourne
        - Semantic: Get guidance about what makes a course "best"
        """

        logger.info("Hybrid retrieval - combining structured and semantic")

        # 1. Get structured results (primary)
        structured_result = self._retrieve_structured(parsed_query, k)

        # 2. Get semantic results (contextual enrichment)
        semantic_result = self._retrieve_semantic(parsed_query, k=3)

        # 3. Merge results
        return HybridResult(
            result_type='mixed',
            structured_data=structured_result.structured_data,
            semantic_data=semantic_result.semantic_data,
            source='hybrid',
            confidence=0.9
        )

    def _retrieve_comparison(self, parsed_query: ParsedQuery) -> HybridResult:
        """Handle provider comparison queries"""

        logger.info("Comparison retrieval")

        # Extract provider names from filters or entities
        provider_names = []

        # Check filters first
        if 'provider_names' in parsed_query.filters:
            provider_names = parsed_query.filters['provider_names']
        elif 'provider_name' in parsed_query.filters:
            provider_names = [parsed_query.filters['provider_name']]

        # Fallback: try to extract from entities
        if not provider_names and parsed_query.entities:
            for entity in parsed_query.entities:
                if entity.type == 'provider_name':
                    provider_names.append(entity.normalized)

        if len(provider_names) >= 2:
            results = self.db_store.compare_providers(provider_names)

            return HybridResult(
                result_type='provider',
                structured_data=results,
                source='structured',
                confidence=0.95
            )
        else:
            # Not enough providers to compare - fallback to structured search
            return self._retrieve_structured(parsed_query, k=10)

    def enrich_with_context(self, result: HybridResult) -> HybridResult:
        """
        Enrich structured results with semantic context from PDFs

        For example, if we found IT courses, we can add context about:
        - IT job market in Australia
        - Career prospects for IT graduates
        - Industry partnerships of the universities
        """

        if not result.structured_data or result.result_type != 'course':
            return result

        # Get top 3 courses
        top_courses = result.structured_data[:3]

        # Extract provider names
        provider_names = list(set([c.get('provider_name') for c in top_courses if c.get('provider_name')]))

        # Search for context about these providers
        if provider_names:
            context_query = f"Tell me about {', '.join(provider_names)} universities"

            try:
                context_results = self.vector_store.similarity_search_with_score(
                    query=context_query,
                    k=3,
                    threshold=0.5
                )

                # Add semantic context
                semantic_data = []
                for doc, score in context_results:
                    semantic_data.append({
                        'content': doc.page_content,
                        'metadata': doc.metadata,
                        'score': score
                    })

                result.semantic_data = semantic_data
                result.source = 'hybrid'

            except Exception as e:
                logger.warning(f"Could not enrich with context: {e}")

        return result

    def rerank_results(self, result: HybridResult, query: str) -> HybridResult:
        """
        Rerank results based on relevance to original query

        This is a placeholder for more sophisticated reranking algorithms like:
        - Cross-encoder models
        - LLM-based relevance scoring
        - Diversity-based reranking
        """

        # For now, just return as-is
        # In a production system, you would implement:
        # 1. Calculate relevance scores for each result
        # 2. Apply diversity filtering to avoid redundant results
        # 3. Boost results based on recency, popularity, or other signals

        logger.info("Reranking results (placeholder)")

        return result


# Singleton instance
_retriever_instance = None

def get_hybrid_retriever() -> HybridRetriever:
    """Get singleton instance of HybridRetriever"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = HybridRetriever()
    return _retriever_instance
