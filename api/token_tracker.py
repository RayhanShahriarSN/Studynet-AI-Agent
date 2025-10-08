# Token tracking and cost calculation utility
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class TokenTracker:
    """Track token usage and calculate costs for OpenAI API calls"""

    # Azure OpenAI Pricing (as of 2025)
    # GPT-4 Turbo pricing
    PRICING = {
        'gpt-4': {
            'prompt': 0.00003,  # $0.03 per 1K prompt tokens
            'completion': 0.00006  # $0.06 per 1K completion tokens
        },
        'gpt-4-turbo': {
            'prompt': 0.00001,  # $0.01 per 1K prompt tokens
            'completion': 0.00003  # $0.03 per 1K completion tokens
        },
        'gpt-35-turbo': {
            'prompt': 0.0000015,  # $0.0015 per 1K prompt tokens
            'completion': 0.000002  # $0.002 per 1K completion tokens
        },
        'text-embedding-3-large': {
            'prompt': 0.00013,  # $0.13 per 1M tokens
            'completion': 0  # Embeddings don't have completion tokens
        },
        'text-embedding-3-small': {
            'prompt': 0.00002,  # $0.02 per 1M tokens
            'completion': 0
        }
    }

    @staticmethod
    def calculate_cost(prompt_tokens: int, completion_tokens: int, model: str = 'gpt-4-turbo') -> Decimal:
        """Calculate cost in USD for token usage

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            model: Model name (gpt-4, gpt-4-turbo, gpt-35-turbo, etc.)

        Returns:
            Cost in USD as Decimal
        """
        # Normalize model name
        if 'gpt-4-turbo' in model.lower() or 'gpt-4o' in model.lower():
            model_key = 'gpt-4-turbo'
        elif 'gpt-4' in model.lower():
            model_key = 'gpt-4'
        elif 'gpt-3.5' in model.lower() or 'gpt-35' in model.lower():
            model_key = 'gpt-35-turbo'
        elif 'text-embedding-3-large' in model.lower():
            model_key = 'text-embedding-3-large'
        elif 'text-embedding' in model.lower():
            model_key = 'text-embedding-3-small'
        else:
            model_key = 'gpt-4-turbo'  # Default to GPT-4 Turbo

        pricing = TokenTracker.PRICING.get(model_key, TokenTracker.PRICING['gpt-4-turbo'])

        prompt_cost = (prompt_tokens / 1000) * pricing['prompt']
        completion_cost = (completion_tokens / 1000) * pricing['completion']

        total_cost = Decimal(str(prompt_cost + completion_cost))
        return round(total_cost, 6)

    @staticmethod
    def extract_token_usage(response: Any) -> Dict[str, int]:
        """Extract token usage from OpenAI API response

        Args:
            response: OpenAI API response object

        Returns:
            Dictionary with prompt_tokens, completion_tokens, total_tokens
        """
        try:
            if hasattr(response, 'usage'):
                usage = response.usage
                return {
                    'prompt_tokens': getattr(usage, 'prompt_tokens', 0),
                    'completion_tokens': getattr(usage, 'completion_tokens', 0),
                    'total_tokens': getattr(usage, 'total_tokens', 0)
                }
            elif hasattr(response, 'response_metadata'):
                # LangChain response format
                metadata = response.response_metadata
                token_usage = metadata.get('token_usage', {})
                return {
                    'prompt_tokens': token_usage.get('prompt_tokens', 0),
                    'completion_tokens': token_usage.get('completion_tokens', 0),
                    'total_tokens': token_usage.get('total_tokens', 0)
                }
            else:
                return {
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0
                }
        except Exception as e:
            logger.error(f"Error extracting token usage: {e}")
            return {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            }

    @staticmethod
    def format_cost(cost_usd: Decimal) -> str:
        """Format cost for display

        Args:
            cost_usd: Cost in USD

        Returns:
            Formatted cost string
        """
        if cost_usd < 0.01:
            return f"${cost_usd:.6f}"
        else:
            return f"${cost_usd:.4f}"


# Singleton instance
token_tracker = TokenTracker()
