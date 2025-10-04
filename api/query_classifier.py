# Query classification for intelligent routing between SQL and RAG
import logging
from enum import Enum
from typing import Dict, List, Optional
from langchain_openai import AzureChatOpenAI
from .config import config

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries for intelligent routing"""
    STRUCTURED_SQL = "structured_sql"  # Needs SQL query on CSV data
    SEMANTIC_RAG = "semantic_rag"      # Needs semantic search on documents
    HYBRID = "hybrid"                   # Needs both SQL and RAG


class QueryClassifier:
    """Classifier to determine query type and route to appropriate handler"""

    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=config.CHAT_MODEL_DEPLOYMENT,
            openai_api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=150
        )

        # Keywords that suggest structured SQL queries
        self.sql_keywords = {
            'count', 'total', 'sum', 'average', 'max', 'min', 'how many',
            'list all', 'show all', 'filter', 'where', 'group by',
            'aggregate', 'statistics', 'top', 'bottom', 'ranking',
            'fees', 'fee', 'provider', 'providers', 'course', 'courses',
            'data', 'records', 'entries', 'price', 'cost', 'degree', 'degrees'
        }

        # Keywords that suggest semantic RAG queries
        self.rag_keywords = {
            'how to', 'what is', 'explain', 'describe', 'why',
            'process', 'procedure', 'steps', 'guide', 'overview',
            'concept', 'definition', 'meaning', 'purpose', 'workflow',
            'application', 'management', 'leads', 'crm'
        }

    def _keyword_based_classification(self, query: str) -> Optional[QueryType]:
        """Fast keyword-based classification

        Args:
            query: User query

        Returns:
            QueryType if confident, None otherwise
        """
        query_lower = query.lower()

        # Check for SQL indicators
        sql_matches = sum(1 for keyword in self.sql_keywords if keyword in query_lower)
        rag_matches = sum(1 for keyword in self.rag_keywords if keyword in query_lower)

        # High confidence thresholds
        if sql_matches >= 2 and rag_matches == 0:
            logger.info(f"Keyword classification: STRUCTURED_SQL (matches: {sql_matches})")
            return QueryType.STRUCTURED_SQL

        if rag_matches >= 2 and sql_matches == 0:
            logger.info(f"Keyword classification: SEMANTIC_RAG (matches: {rag_matches})")
            return QueryType.SEMANTIC_RAG

        if sql_matches >= 1 and rag_matches >= 1:
            logger.info(f"Keyword classification: HYBRID (SQL: {sql_matches}, RAG: {rag_matches})")
            return QueryType.HYBRID

        # Not confident enough
        return None

    def _llm_based_classification(self, query: str, available_tables: List[str]) -> QueryType:
        """LLM-based classification for complex queries

        Args:
            query: User query
            available_tables: List of available SQL tables

        Returns:
            QueryType classification
        """
        prompt = f"""You are a query classifier. Analyze the user query and classify it into one of three categories:

1. STRUCTURED_SQL: Queries that need filtering, aggregation, counting, or statistical operations on structured data (CSV tables)
   - Examples: "How many providers are there?", "Show me all fees above 1000", "List providers in NSW"

2. SEMANTIC_RAG: Queries asking for conceptual information, explanations, procedures, or guidance from documents
   - Examples: "How to add a lead?", "What is the application process?", "Explain CRM features"

3. HYBRID: Queries that need both structured data AND conceptual information
   - Examples: "Show me all providers and explain how to contact them", "List high fees and why they are set"

Available SQL Tables: {', '.join(available_tables) if available_tables else 'None'}

User Query: "{query}"

Classification (respond with ONLY one word: STRUCTURED_SQL, SEMANTIC_RAG, or HYBRID):"""

        try:
            response = self.llm.invoke(prompt)
            classification = response.content.strip().upper()

            # Parse response
            if "STRUCTURED_SQL" in classification:
                return QueryType.STRUCTURED_SQL
            elif "SEMANTIC_RAG" in classification:
                return QueryType.SEMANTIC_RAG
            elif "HYBRID" in classification:
                return QueryType.HYBRID
            else:
                # Default to RAG if uncertain
                logger.warning(f"Unexpected classification response: {classification}")
                return QueryType.SEMANTIC_RAG

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            # Default to RAG on error
            return QueryType.SEMANTIC_RAG

    def classify_query(self, query: str, available_tables: Optional[List[str]] = None) -> Dict:
        """Classify query and return routing information

        Args:
            query: User query string
            available_tables: Optional list of available SQL tables

        Returns:
            Dictionary with classification results
        """
        available_tables = available_tables or []

        # Step 1: Try fast keyword-based classification
        keyword_result = self._keyword_based_classification(query)

        if keyword_result:
            return {
                'query_type': keyword_result.value,
                'classification_method': 'keyword',
                'confidence': 'high',
                'requires_sql': keyword_result in [QueryType.STRUCTURED_SQL, QueryType.HYBRID],
                'requires_rag': keyword_result in [QueryType.SEMANTIC_RAG, QueryType.HYBRID],
                'available_tables': available_tables
            }

        # Step 2: Use LLM for complex classification
        logger.info("Using LLM for query classification")
        llm_result = self._llm_based_classification(query, available_tables)

        return {
            'query_type': llm_result.value,
            'classification_method': 'llm',
            'confidence': 'medium',
            'requires_sql': llm_result in [QueryType.STRUCTURED_SQL, QueryType.HYBRID],
            'requires_rag': llm_result in [QueryType.SEMANTIC_RAG, QueryType.HYBRID],
            'available_tables': available_tables
        }

    def extract_sql_intent(self, query: str) -> Dict:
        """Extract SQL-specific intent from query

        Args:
            query: User query

        Returns:
            Dictionary with SQL intent information
        """
        prompt = f"""Analyze this query and extract SQL intent:

Query: "{query}"

Extract:
1. Operation type (SELECT, COUNT, AGGREGATE, FILTER, etc.)
2. Target columns (if mentioned)
3. Conditions (if any)
4. Aggregation type (if any)

Respond in this format:
Operation: <operation>
Columns: <comma-separated columns or "UNKNOWN">
Conditions: <conditions or "NONE">
Aggregation: <aggregation type or "NONE">"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()

            # Parse response
            intent = {
                'operation': 'UNKNOWN',
                'columns': [],
                'conditions': None,
                'aggregation': None
            }

            for line in content.split('\n'):
                if line.startswith('Operation:'):
                    intent['operation'] = line.split(':', 1)[1].strip()
                elif line.startswith('Columns:'):
                    cols = line.split(':', 1)[1].strip()
                    if cols.upper() != 'UNKNOWN':
                        intent['columns'] = [c.strip() for c in cols.split(',')]
                elif line.startswith('Conditions:'):
                    cond = line.split(':', 1)[1].strip()
                    if cond.upper() != 'NONE':
                        intent['conditions'] = cond
                elif line.startswith('Aggregation:'):
                    agg = line.split(':', 1)[1].strip()
                    if agg.upper() != 'NONE':
                        intent['aggregation'] = agg

            return intent

        except Exception as e:
            logger.error(f"SQL intent extraction failed: {e}")
            return {
                'operation': 'UNKNOWN',
                'columns': [],
                'conditions': None,
                'aggregation': None
            }

    def suggest_table(self, query: str, available_tables: List[str]) -> Optional[str]:
        """Suggest most relevant table for the query

        Args:
            query: User query
            available_tables: List of available table names

        Returns:
            Suggested table name or None
        """
        if not available_tables:
            return None

        if len(available_tables) == 1:
            return available_tables[0]

        prompt = f"""Given the user query and available tables, suggest the most relevant table.

Query: "{query}"

Available Tables: {', '.join(available_tables)}

Respond with ONLY the table name (choose one):"""

        try:
            response = self.llm.invoke(prompt)
            suggested = response.content.strip().lower()

            # Find matching table
            for table in available_tables:
                if table.lower() in suggested or suggested in table.lower():
                    return table

            # Default to first table
            return available_tables[0]

        except Exception as e:
            logger.error(f"Table suggestion failed: {e}")
            return available_tables[0] if available_tables else None


# Singleton instance
query_classifier = QueryClassifier()
