# Query enhancement for improved retrieval
import logging
import re
from typing import List, Dict, Optional
from langchain_openai import AzureChatOpenAI
from .config import config

logger = logging.getLogger(__name__)


class QueryEnhancer:
    """Enhanced query processing with expansion, variations, and multi-query retrieval"""

    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=config.CHAT_MODEL_DEPLOYMENT,
            openai_api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            temperature=0.7,  # Higher temperature for diverse variations
            max_tokens=300
        )

        # Common acronyms in business/CRM context
        self.acronym_dict = {
            'CRM': 'Customer Relationship Management',
            'AI': 'Artificial Intelligence',
            'ML': 'Machine Learning',
            'NLP': 'Natural Language Processing',
            'RAG': 'Retrieval Augmented Generation',
            'LLM': 'Large Language Model',
            'API': 'Application Programming Interface',
            'UI': 'User Interface',
            'UX': 'User Experience',
            'PDF': 'Portable Document Format',
            'CSV': 'Comma-Separated Values',
            'SQL': 'Structured Query Language',
            'RPL': 'Recognition of Prior Learning',
            'NSW': 'New South Wales'
        }

        # Stop words for query optimization
        self.stop_words = {
            'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an',
            'as', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'shall', 'to', 'of', 'in', 'for', 'with',
            'by', 'from', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'up', 'down',
            'out', 'off', 'over', 'under', 'again', 'further'
        }

    def expand_acronyms(self, query: str) -> str:
        """Expand known acronyms in the query

        Args:
            query: Original query

        Returns:
            Query with expanded acronyms
        """
        expanded = query
        words = query.split()

        for i, word in enumerate(words):
            # Check if word is an acronym (all caps, 2+ letters)
            clean_word = word.strip('.,!?;:')
            if clean_word.upper() in self.acronym_dict:
                expansion = self.acronym_dict[clean_word.upper()]
                # Replace with "ACRONYM (full form)"
                words[i] = f"{clean_word} ({expansion})"

        return ' '.join(words)

    def remove_stop_words(self, query: str) -> str:
        """Remove stop words for keyword extraction

        Args:
            query: Original query

        Returns:
            Query with stop words removed
        """
        words = query.lower().split()
        filtered = [w for w in words if w not in self.stop_words]
        return ' '.join(filtered) if filtered else query

    def extract_keywords(self, query: str, max_keywords: int = 5) -> List[str]:
        """Extract important keywords from query

        Args:
            query: Original query
            max_keywords: Maximum number of keywords to extract

        Returns:
            List of keywords
        """
        # Remove stop words
        cleaned = self.remove_stop_words(query)

        # Split and filter
        words = [w.strip('.,!?;:') for w in cleaned.split()]

        # Sort by length (longer words often more specific)
        words.sort(key=len, reverse=True)

        # Remove duplicates while preserving order
        seen = set()
        keywords = []
        for word in words:
            if word.lower() not in seen and len(word) > 2:
                seen.add(word.lower())
                keywords.append(word)
                if len(keywords) >= max_keywords:
                    break

        return keywords

    def generate_query_variations(self, query: str, num_variations: int = 3) -> List[str]:
        """Generate alternative query phrasings using LLM

        Args:
            query: Original query
            num_variations: Number of variations to generate

        Returns:
            List of query variations (includes original)
        """
        prompt = f"""Generate {num_variations} alternative phrasings of the following query.
Each variation should:
- Capture the same intent
- Use different wording or perspective
- Be concise and clear
- Focus on the core question

Original Query: "{query}"

Generate {num_variations} variations (one per line, no numbering):"""

        try:
            response = self.llm.invoke(prompt)
            variations = response.content.strip().split('\n')

            # Clean variations
            variations = [
                v.strip().lstrip('123456789.-) ')
                for v in variations
                if v.strip()
            ][:num_variations]

            # Always include original query first
            all_queries = [query] + [v for v in variations if v and v != query]

            logger.info(f"Generated {len(all_queries)} query variations")
            return all_queries

        except Exception as e:
            logger.error(f"Query variation generation failed: {e}")
            return [query]

    def enhance_query(self, query: str, context: Optional[str] = None) -> Dict:
        """Comprehensive query enhancement

        Args:
            query: Original query
            context: Optional conversation context

        Returns:
            Dictionary with enhanced query variants
        """
        # Expand acronyms
        expanded_query = self.expand_acronyms(query)

        # Extract keywords
        keywords = self.extract_keywords(query)

        # Generate variations
        variations = self.generate_query_variations(query, num_variations=3)

        # If context provided, generate context-aware variation
        context_aware_query = query
        if context:
            context_aware_query = self._generate_context_aware_query(query, context)
            if context_aware_query not in variations:
                variations.append(context_aware_query)

        return {
            'original': query,
            'expanded': expanded_query,
            'keywords': keywords,
            'variations': variations,
            'context_aware': context_aware_query,
            'total_queries': len(variations)
        }

    def _generate_context_aware_query(self, query: str, context: str) -> str:
        """Generate context-aware query variation

        Args:
            query: Current query
            context: Conversation context

        Returns:
            Context-aware query
        """
        prompt = f"""Given the conversation context and current query, generate a standalone version of the query that incorporates relevant context.

Conversation Context:
{context[-500:]}

Current Query: "{query}"

Standalone Query (one line):"""

        try:
            response = self.llm.invoke(prompt)
            context_aware = response.content.strip().lstrip('123.-) ')
            return context_aware if context_aware else query

        except Exception as e:
            logger.error(f"Context-aware query generation failed: {e}")
            return query

    def optimize_for_sql(self, query: str) -> str:
        """Optimize query for SQL search

        Args:
            query: Original query

        Returns:
            SQL-optimized query
        """
        prompt = f"""Convert this natural language query into a more SQL-friendly format while preserving intent.
Focus on entities, attributes, and conditions.

Query: "{query}"

SQL-friendly version (one line):"""

        try:
            response = self.llm.invoke(prompt)
            optimized = response.content.strip()
            return optimized if optimized else query

        except Exception as e:
            logger.error(f"SQL optimization failed: {e}")
            return query

    def optimize_for_semantic(self, query: str) -> str:
        """Optimize query for semantic search

        Args:
            query: Original query

        Returns:
            Semantically-optimized query
        """
        # For semantic search, we want conceptual and descriptive queries
        # Expand acronyms and add context
        expanded = self.expand_acronyms(query)

        prompt = f"""Rephrase this query to be more conceptual and descriptive for semantic search.
Focus on the underlying concept and intent.

Query: "{query}"

Semantic version (one line):"""

        try:
            response = self.llm.invoke(prompt)
            optimized = response.content.strip()
            return optimized if optimized else expanded

        except Exception as e:
            logger.error(f"Semantic optimization failed: {e}")
            return expanded

    def decompose_complex_query(self, query: str) -> List[str]:
        """Decompose complex multi-part query into sub-queries

        Args:
            query: Complex query

        Returns:
            List of simpler sub-queries
        """
        # Check if query has multiple questions
        if '?' not in query:
            return [query]

        # Simple heuristic: multiple questions
        questions = re.split(r'\?|\band\b|\bor\b', query)
        sub_queries = [q.strip() for q in questions if q.strip()]

        if len(sub_queries) <= 1:
            return [query]

        logger.info(f"Decomposed query into {len(sub_queries)} sub-queries")
        return sub_queries


# Singleton instance
query_enhancer = QueryEnhancer()
