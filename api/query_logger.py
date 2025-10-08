"""
Query Logger - JSON file logging utility for query analytics
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from threading import Lock
from decimal import Decimal

logger = logging.getLogger(__name__)


class QueryLoggerJSON:
    """Manages query_log.json file for persistent analytics tracking"""

    def __init__(self, log_file_path: str = "query_log.json"):
        """Initialize the query logger

        Args:
            log_file_path: Path to the JSON log file
        """
        self.log_file_path = Path(log_file_path)
        self.lock = Lock()  # Thread-safe file operations
        self._initialize_log_file()

    def _initialize_log_file(self):
        """Create the log file if it doesn't exist"""
        if not self.log_file_path.exists():
            initial_data = {
                "last_updated": datetime.now().isoformat(),
                "token_usage": {
                    "total_tokens": 0,
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "total_cost_usd": "0.000000",
                    "avg_tokens_per_query": 0.0,
                    "avg_cost_per_query": "0.000000",
                    "queries_count": 0
                },
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "success_rate": 0.0,
                "sql_queries_count": 0,
                "rag_queries_count": 0,
                "hybrid_queries_count": 0,
                "queries": []
            }
            self._write_to_file(initial_data)
            logger.info(f"Initialized query log file: {self.log_file_path}")

    def _read_from_file(self) -> Dict[str, Any]:
        """Read data from the JSON file

        Returns:
            Dictionary containing the log data
        """
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading query log: {e}")
            # Return default structure if file is corrupted
            return {
                "last_updated": datetime.now().isoformat(),
                "token_usage": {
                    "total_tokens": 0,
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "total_cost_usd": "0.000000",
                    "avg_tokens_per_query": 0.0,
                    "avg_cost_per_query": "0.000000",
                    "queries_count": 0
                },
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "success_rate": 0.0,
                "sql_queries_count": 0,
                "rag_queries_count": 0,
                "hybrid_queries_count": 0,
                "queries": []
            }

    def _write_to_file(self, data: Dict[str, Any]):
        """Write data to the JSON file

        Args:
            data: Dictionary to write to file
        """
        try:
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error writing query log: {e}")

    def log_query(self,
                  query_text: str,
                  query_type: str,
                  tokens_used: int,
                  prompt_tokens: int,
                  completion_tokens: int,
                  cost_usd: Decimal,
                  response_time_ms: int,
                  success: bool = True,
                  sql_used: bool = False,
                  rag_used: bool = False,
                  confidence_score: float = 0.5):
        """Log a query and update aggregated statistics

        Args:
            query_text: The query text
            query_type: Type of query (structured_sql, semantic_rag, hybrid, unknown)
            tokens_used: Total tokens used
            prompt_tokens: Prompt tokens
            completion_tokens: Completion tokens
            cost_usd: Cost in USD
            response_time_ms: Response time in milliseconds
            success: Whether query succeeded
            sql_used: Whether SQL was used
            rag_used: Whether RAG was used
            confidence_score: Confidence score
        """
        with self.lock:
            try:
                # Read current data
                data = self._read_from_file()

                # Update token usage
                data["token_usage"]["total_tokens"] += tokens_used
                data["token_usage"]["total_prompt_tokens"] += prompt_tokens
                data["token_usage"]["total_completion_tokens"] += completion_tokens

                # Update costs
                current_cost = Decimal(data["token_usage"]["total_cost_usd"])
                new_cost = current_cost + cost_usd
                data["token_usage"]["total_cost_usd"] = str(new_cost)

                # Update query counts
                data["total_queries"] += 1
                data["token_usage"]["queries_count"] = data["total_queries"]

                if success:
                    data["successful_queries"] += 1
                else:
                    data["failed_queries"] += 1

                # Update success rate
                if data["total_queries"] > 0:
                    data["success_rate"] = round(
                        (data["successful_queries"] / data["total_queries"]) * 100,
                        2
                    )

                # Update query type counts
                if sql_used and rag_used:
                    data["hybrid_queries_count"] += 1
                elif sql_used:
                    data["sql_queries_count"] += 1
                elif rag_used:
                    data["rag_queries_count"] += 1

                # Update averages
                if data["total_queries"] > 0:
                    data["token_usage"]["avg_tokens_per_query"] = round(
                        data["token_usage"]["total_tokens"] / data["total_queries"],
                        2
                    )
                    avg_cost = new_cost / data["total_queries"]
                    data["token_usage"]["avg_cost_per_query"] = str(round(avg_cost, 6))

                # Add individual query record (keep last 100 queries)
                query_record = {
                    "timestamp": datetime.now().isoformat(),
                    "query_text": query_text[:200],  # Truncate long queries
                    "query_type": query_type,
                    "tokens_used": tokens_used,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost_usd": str(cost_usd),
                    "response_time_ms": response_time_ms,
                    "success": success,
                    "confidence_score": confidence_score
                }

                data["queries"].append(query_record)

                # Keep only last 100 queries
                if len(data["queries"]) > 100:
                    data["queries"] = data["queries"][-100:]

                # Update last updated timestamp
                data["last_updated"] = datetime.now().isoformat()

                # Write back to file
                self._write_to_file(data)

                logger.info(f"Query logged successfully. Total queries: {data['total_queries']}")

            except Exception as e:
                logger.error(f"Error logging query: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """Get the current summary statistics

        Returns:
            Dictionary with summary statistics
        """
        with self.lock:
            data = self._read_from_file()
            return {
                "last_updated": data.get("last_updated"),
                "token_usage": data.get("token_usage"),
                "total_queries": data.get("total_queries"),
                "successful_queries": data.get("successful_queries"),
                "failed_queries": data.get("failed_queries"),
                "success_rate": data.get("success_rate"),
                "sql_queries_count": data.get("sql_queries_count"),
                "rag_queries_count": data.get("rag_queries_count"),
                "hybrid_queries_count": data.get("hybrid_queries_count")
            }

    def get_recent_queries(self, limit: int = 10) -> list:
        """Get recent query records

        Args:
            limit: Number of recent queries to return

        Returns:
            List of recent query records
        """
        with self.lock:
            data = self._read_from_file()
            queries = data.get("queries", [])
            return queries[-limit:]

    def reset_log(self):
        """Reset the log file to initial state"""
        with self.lock:
            self._initialize_log_file()
            logger.info("Query log has been reset")


# Singleton instance
query_logger = QueryLoggerJSON()
