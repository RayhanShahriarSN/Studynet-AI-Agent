# LangChain tools for the Master Orchestrator agent
import logging
from typing import Optional, List
from langchain.tools import Tool
from langchain.schema import Document
from .sql_engine import sql_engine
from .retriever import hybrid_retriever
from .query_enhancer import query_enhancer

logger = logging.getLogger(__name__)


def sql_query_tool_func(query: str) -> str:
    """Execute SQL query on CSV data

    Args:
        query: SQL query string (e.g., "SELECT * FROM providers WHERE state='NSW'")

    Returns:
        Formatted query results as string
    """
    try:
        logger.info(f"Executing SQL query: {query[:100]}...")
        result = sql_engine.execute_query_to_string(query, limit=100)
        return result
    except Exception as e:
        logger.error(f"SQL query execution failed: {e}")
        return f"Error executing SQL query: {str(e)}"


def get_sql_schema_tool_func(table_name: Optional[str] = None) -> str:
    """Get schema information for SQL tables

    Args:
        table_name: Optional specific table name. If None, returns all schemas.

    Returns:
        Schema information as formatted string
    """
    try:
        if table_name:
            schema = sql_engine.get_table_schema(table_name)
            if 'error' in schema:
                return schema['error']

            output = f"Table: {schema['table_name']}\n"
            output += f"Total Rows: {schema['row_count']}\n\n"
            output += "Columns:\n"
            for col in schema['columns']:
                output += f"  - {col['column_name']} ({col['data_type']})\n"
                output += f"    Sample: {col['sample_values']}\n"
            return output
        else:
            # Return all schemas
            all_schemas = sql_engine.get_table_schema()
            if not all_schemas:
                return "No SQL tables available. Upload CSV files first."

            output = "Available SQL Tables:\n\n"
            for table_name, schema in all_schemas.items():
                output += f"📊 {table_name.upper()} ({schema['row_count']} rows)\n"
                cols = [col['column_name'] for col in schema['columns']]
                output += f"   Columns: {', '.join(cols)}\n\n"

            return output
    except Exception as e:
        logger.error(f"Schema retrieval failed: {e}")
        return f"Error retrieving schema: {str(e)}"


def rag_search_tool_func(query: str) -> str:
    """Search documents using hybrid RAG (semantic + keyword search)

    Args:
        query: Search query for documents

    Returns:
        Retrieved document content as string
    """
    try:
        logger.info(f"Performing RAG search: {query[:100]}...")

        # Enhance query for better retrieval
        enhanced = query_enhancer.enhance_query(query)

        # Use hybrid retrieval
        documents = hybrid_retriever.hybrid_search(
            query=query,
            k=5,
            semantic_weight=0.6,
            use_cross_encoder=True
        )

        if not documents:
            return "No relevant documents found in the knowledge base."

        # Format results
        output = f"Found {len(documents)} relevant documents:\n\n"

        for i, doc in enumerate(documents, 1):
            content = doc.page_content[:500]  # Limit content length
            source = doc.metadata.get('source_file', 'Unknown')

            # Add relevance scores if available
            scores = []
            if 'cross_encoder_score' in doc.metadata:
                scores.append(f"Relevance: {doc.metadata['cross_encoder_score']:.3f}")
            if 'rrf_score' in doc.metadata:
                scores.append(f"RRF: {doc.metadata['rrf_score']:.3f}")

            score_str = f" ({', '.join(scores)})" if scores else ""

            output += f"[{i}] Source: {source}{score_str}\n"
            output += f"{content}...\n\n"

        return output

    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        return f"Error performing document search: {str(e)}"


def get_available_tables_tool_func(input: str = "") -> str:
    """Get list of available SQL tables

    Args:
        input: Ignored (required for tool interface)

    Returns:
        List of available table names
    """
    try:
        tables = sql_engine.get_available_tables()
        if not tables:
            return "No SQL tables available. Upload CSV files to enable SQL queries."

        output = f"Available Tables ({len(tables)}):\n"
        for table in tables:
            output += f"  - {table}\n"

        output += "\nUse get_sql_schema to see column details for each table."
        return output

    except Exception as e:
        logger.error(f"Error getting table list: {e}")
        return f"Error: {str(e)}"


def table_preview_tool_func(table_name: str) -> str:
    """Preview data from a SQL table

    Args:
        table_name: Name of the table to preview

    Returns:
        Preview of table data
    """
    try:
        preview = sql_engine.get_table_preview(table_name, num_rows=5)
        return preview
    except Exception as e:
        logger.error(f"Table preview failed: {e}")
        return f"Error previewing table: {str(e)}"


# Create LangChain Tool objects
sql_query_tool = Tool(
    name="sql_query",
    func=sql_query_tool_func,
    description="""Execute SQL queries on CSV data tables.

    Use this tool when you need to:
    - Filter, aggregate, or count structured data
    - Get statistics (sum, average, min, max)
    - List records matching specific criteria
    - Perform data analysis on CSV files

    Input: Valid SQL SELECT query (e.g., "SELECT * FROM providers WHERE state='NSW' LIMIT 10")
    Output: Query results formatted as a table

    Example: "SELECT COUNT(*) FROM providers WHERE state='NSW'"
    """
)

get_sql_schema_tool = Tool(
    name="get_sql_schema",
    func=get_sql_schema_tool_func,
    description="""Get schema information for SQL tables.

    Use this tool to:
    - See what tables are available
    - View column names and data types
    - Understand table structure before writing queries
    - See sample values from each column

    Input: Table name (optional). Leave empty to see all tables.
    Output: Schema information including columns, types, and samples

    Example: "providers" or "" for all tables
    """
)

rag_search_tool = Tool(
    name="rag_search",
    func=rag_search_tool_func,
    description="""Search documents using hybrid RAG (Retrieval Augmented Generation).

    Use this tool when you need to:
    - Find information from PDF/DOCX documents
    - Get explanations, processes, or procedures
    - Understand concepts or definitions
    - Answer "how to" questions
    - Retrieve contextual information

    Input: Natural language search query
    Output: Relevant document excerpts with sources

    This tool uses both semantic search (meaning-based) and keyword search (BM25)
    with cross-encoder reranking for best results.

    Example: "How to add a new lead in the CRM system?"
    """
)

get_available_tables_tool = Tool(
    name="get_available_tables",
    func=get_available_tables_tool_func,
    description="""Get a list of all available SQL tables from CSV files.

    Use this tool to:
    - See what data tables are available
    - Check if specific data exists before querying

    Input: Empty string or any text (ignored)
    Output: List of available table names
    """
)

table_preview_tool = Tool(
    name="table_preview",
    func=table_preview_tool_func,
    description="""Preview the first few rows of a SQL table.

    Use this tool to:
    - See sample data from a table
    - Understand data format and content
    - Verify table contents

    Input: Table name
    Output: First 5 rows of the table with column information

    Example: "providers"
    """
)


# Export all tools
ALL_TOOLS = [
    sql_query_tool,
    get_sql_schema_tool,
    rag_search_tool,
    get_available_tables_tool,
    table_preview_tool
]

# Tool groups for different agent configurations
SQL_TOOLS = [sql_query_tool, get_sql_schema_tool, get_available_tables_tool, table_preview_tool]
RAG_TOOLS = [rag_search_tool]
HYBRID_TOOLS = ALL_TOOLS
