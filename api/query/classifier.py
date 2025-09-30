# Query classification and intent detection
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from langchain_openai import AzureChatOpenAI
from ..config import config
import logging

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Type of query based on data source needed"""
    STRUCTURED = "structured"      # Needs SQL queries (courses, fees, providers)
    SEMANTIC = "semantic"          # Needs vector search (guidance PDFs)
    HYBRID = "hybrid"              # Needs both
    COMPARISON = "comparison"      # Compare multiple providers

class Intent(Enum):
    """User's primary intent"""
    SEARCH_COURSES = "search_courses"              # Find courses
    FILTER_BY_CRITERIA = "filter_by_criteria"      # Filter with multiple criteria
    COMPARE_PROVIDERS = "compare_providers"        # Compare universities
    GET_PROVIDER_INFO = "get_provider_info"        # Info about specific university
    GET_GUIDANCE = "get_guidance"                  # How-to, process, visa info
    CALCULATE_COSTS = "calculate_costs"            # Cost calculations
    GET_SCHOLARSHIPS = "get_scholarships"          # Scholarship info
    GET_INTAKES = "get_intakes"                    # Application deadlines

class Entity(BaseModel):
    """Extracted entity from query"""
    type: str  # field_of_study, price_range, location, provider_name, etc.
    value: Any
    normalized_value: Any  # Mapped to database value
    confidence: float

class ParsedQuery(BaseModel):
    """Structured representation of parsed query"""
    original_query: str
    query_type: QueryType
    intent: Intent
    entities: List[Entity]
    filters: Dict[str, Any]  # SQL-ready filters
    semantic_context: Optional[str] = None
    top_k: int = 10

class QueryClassifier:
    """Classifies and parses student queries"""

    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=config.CHAT_MODEL_DEPLOYMENT,
            openai_api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=500
        )

        # Keyword patterns for quick classification
        self.structured_keywords = [
            'course', 'courses', 'program', 'programs', 'university', 'universities',
            'fee', 'fees', 'price', 'cost', 'cheap', 'expensive', 'under', 'below',
            'bachelor', 'master', 'diploma', 'phd', 'degree',
            'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide',
            'scholarship', 'scholarships', 'intake', 'deadline'
        ]

        self.semantic_keywords = [
            'how', 'what', 'why', 'when', 'where',
            'apply', 'application', 'process', 'procedure',
            'visa', 'student visa', 'requirement', 'requirements',
            'document', 'documents', 'need', 'necessary',
            'guide', 'help', 'explain'
        ]

        self.comparison_keywords = [
            'compare', 'comparison', 'versus', 'vs', 'between',
            'difference', 'differences', 'better', 'best'
        ]

    def classify(self, query: str) -> ParsedQuery:
        """Main classification pipeline"""

        logger.info(f"Classifying query: {query}")

        # Initialize variables
        intent = None
        query_type = None

        # Step 1: Quick pattern-based detection
        query_lower = query.lower()

        # Detect comparison queries
        if any(kw in query_lower for kw in self.comparison_keywords):
            if any(kw in query_lower for kw in ['university', 'universities', 'provider']):
                intent = Intent.COMPARE_PROVIDERS
                query_type = QueryType.COMPARISON
                logger.info("Detected COMPARISON query")

        # Detect semantic queries
        elif any(query_lower.startswith(kw) for kw in ['how ', 'what ', 'why ', 'when ']):
            if not any(kw in query_lower for kw in self.structured_keywords):
                intent = Intent.GET_GUIDANCE
                query_type = QueryType.SEMANTIC
                logger.info("Detected SEMANTIC query")

        # Default to structured/hybrid - use LLM
        if intent is None or query_type is None:
            # Use LLM for more nuanced classification
            intent, query_type = self._classify_with_llm(query)

        # Step 2: Extract entities (always do this)
        from .entity_extractor import EntityExtractor
        entity_extractor = EntityExtractor()
        entities = entity_extractor.extract(query)

        # Step 3: Build filters from entities
        filters = self._build_filters(entities)

        # Step 4: Refine query type based on entities
        if query_type == QueryType.STRUCTURED:
            # If we have entities AND semantic keywords, it's hybrid
            has_semantic = any(kw in query_lower for kw in self.semantic_keywords)
            if has_semantic and len(entities) > 0:
                query_type = QueryType.HYBRID
                logger.info("Upgraded to HYBRID query (has both structured and semantic elements)")

        logger.info(f"Final classification - Type: {query_type.value}, Intent: {intent.value}")
        logger.info(f"Extracted {len(entities)} entities")

        return ParsedQuery(
            original_query=query,
            query_type=query_type,
            intent=intent,
            entities=entities,
            filters=filters,
            semantic_context=self._extract_semantic_context(query),
            top_k=10
        )

    def _classify_with_llm(self, query: str) -> tuple[Intent, QueryType]:
        """Use LLM to classify query when patterns aren't clear"""

        prompt = f"""Classify this student query about Australian universities.

Query: "{query}"

Determine the PRIMARY intent:
1. SEARCH_COURSES - Student wants to find courses
2. FILTER_BY_CRITERIA - Student wants courses with specific criteria (price, location, field)
3. GET_PROVIDER_INFO - Student asks about a specific university
4. GET_GUIDANCE - Student asks HOW to do something (apply, get visa, etc.)
5. CALCULATE_COSTS - Student asks about total costs or expenses
6. GET_SCHOLARSHIPS - Student asks about scholarships
7. GET_INTAKES - Student asks about application deadlines

Also determine the DATA TYPE needed:
- STRUCTURED: Needs course/provider database (prices, locations, names)
- SEMANTIC: Needs guidance documents (how-to, procedures)
- HYBRID: Needs both

Respond in this exact format:
INTENT: [one of the intents above]
DATA_TYPE: [STRUCTURED, SEMANTIC, or HYBRID]
REASONING: [one sentence why]"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()

            # Parse response
            intent_line = [l for l in content.split('\n') if l.startswith('INTENT:')]
            data_line = [l for l in content.split('\n') if l.startswith('DATA_TYPE:')]

            if intent_line and data_line:
                intent_str = intent_line[0].split(':', 1)[1].strip()
                data_str = data_line[0].split(':', 1)[1].strip()

                # Map to enums
                intent_map = {
                    'SEARCH_COURSES': Intent.SEARCH_COURSES,
                    'FILTER_BY_CRITERIA': Intent.FILTER_BY_CRITERIA,
                    'GET_PROVIDER_INFO': Intent.GET_PROVIDER_INFO,
                    'GET_GUIDANCE': Intent.GET_GUIDANCE,
                    'CALCULATE_COSTS': Intent.CALCULATE_COSTS,
                    'GET_SCHOLARSHIPS': Intent.GET_SCHOLARSHIPS,
                    'GET_INTAKES': Intent.GET_INTAKES,
                }

                data_map = {
                    'STRUCTURED': QueryType.STRUCTURED,
                    'SEMANTIC': QueryType.SEMANTIC,
                    'HYBRID': QueryType.HYBRID,
                }

                intent = intent_map.get(intent_str, Intent.SEARCH_COURSES)
                query_type = data_map.get(data_str, QueryType.STRUCTURED)

                logger.info(f"LLM classification: {intent.value}, {query_type.value}")
                return intent, query_type

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")

        # Fallback
        return Intent.SEARCH_COURSES, QueryType.STRUCTURED

    def _build_filters(self, entities: List[Entity]) -> Dict[str, Any]:
        """Convert entities to SQL-ready filters"""
        filters = {}

        for entity in entities:
            if entity.type == 'field_of_study':
                filters['field_of_study'] = entity.normalized_value

            elif entity.type == 'price_range':
                filters['price_range'] = entity.normalized_value

            elif entity.type == 'location':
                loc = entity.normalized_value
                if isinstance(loc, dict):
                    if loc.get('city'):
                        filters['location_city'] = loc['city']
                    if loc.get('state'):
                        filters['location_state'] = loc['state']

            elif entity.type == 'provider_name':
                filters['provider_name'] = entity.normalized_value

            elif entity.type == 'study_level':
                filters['study_level'] = entity.normalized_value

            elif entity.type == 'has_scholarship':
                filters['has_scholarship'] = entity.normalized_value

            elif entity.type == 'ranking':
                filters['max_ranking'] = entity.normalized_value

        return filters

    def _extract_semantic_context(self, query: str) -> Optional[str]:
        """Extract semantic context for guidance queries"""
        query_lower = query.lower()

        # Common semantic contexts
        if 'visa' in query_lower:
            return "student visa application"
        elif 'apply' in query_lower or 'application' in query_lower:
            return "university application process"
        elif 'document' in query_lower or 'requirement' in query_lower:
            return "application requirements"
        elif 'scholarship' in query_lower:
            return "scholarship information"

        return None

# Singleton instance
_classifier = None

def get_classifier() -> QueryClassifier:
    """Get or create classifier singleton"""
    global _classifier
    if _classifier is None:
        _classifier = QueryClassifier()
    return _classifier
