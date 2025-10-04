# SQL Engine for querying CSV files using pandasql
import os
import logging
import pandas as pd
from typing import Dict, List, Optional, Any
from pandasql import sqldf
from pathlib import Path

logger = logging.getLogger(__name__)


class SQLEngine:
    """SQL query execution engine for CSV files"""

    def __init__(self, csv_directories: Optional[List[str]] = None):
        """Initialize SQL engine with CSV directories

        Args:
            csv_directories: List of directories containing CSV files.
                           Defaults to ['./pdfs', './uploaded_docs']
        """
        self.csv_directories = csv_directories or ["./pdfs", "./uploaded_docs"]
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.table_schemas: Dict[str, List[Dict[str, str]]] = {}
        self.load_all_csv_files()

    def load_all_csv_files(self) -> int:
        """Load all CSV files from all directories into pandas DataFrames

        Returns:
            Number of CSV files loaded
        """
        total_csv_count = 0

        for csv_directory in self.csv_directories:
            if not os.path.exists(csv_directory):
                logger.info(f"CSV directory does not exist (skipping): {csv_directory}")
                continue

            logger.info(f"Loading CSVs from: {csv_directory}")
            csv_count = 0

            for filename in os.listdir(csv_directory):
                if filename.lower().endswith('.csv'):
                    file_path = os.path.join(csv_directory, filename)
                    try:
                        # Create table name from filename (remove .csv and special chars)
                        table_name = self._sanitize_table_name(filename)

                        # Skip if already loaded (avoid duplicates)
                        if table_name in self.dataframes:
                            logger.info(f"Table '{table_name}' already loaded, skipping {filename}")
                            continue

                        # Try loading CSV with different encodings
                        df = self._read_csv_with_encoding(file_path)

                        if df is None:
                            logger.error(f"Failed to load CSV {filename} with any encoding")
                            continue

                        self.dataframes[table_name] = df

                        # Store schema information
                        self.table_schemas[table_name] = self._get_schema(df)

                        logger.info(f"Loaded CSV: {filename} as table '{table_name}' ({len(df)} rows, {len(df.columns)} columns)")
                        csv_count += 1

                    except Exception as e:
                        logger.error(f"Error loading CSV {filename}: {e}")
                        continue

            total_csv_count += csv_count

        logger.info(f"Total CSV files loaded from all directories: {total_csv_count}")
        return total_csv_count

    def _sanitize_table_name(self, filename: str) -> str:
        """Convert filename to valid SQL table name

        Args:
            filename: CSV filename

        Returns:
            Sanitized table name
        """
        # Remove .csv extension
        name = filename.replace('.csv', '').replace('.CSV', '')

        # Replace special characters with underscores
        name = ''.join(c if c.isalnum() else '_' for c in name)

        # Remove leading numbers and multiple underscores
        name = name.lstrip('0123456789_')
        name = '_'.join(filter(None, name.split('_')))

        # Ensure it doesn't start with a number
        if name and name[0].isdigit():
            name = 'table_' + name

        return name.lower() if name else 'unnamed_table'

    def _read_csv_with_encoding(self, file_path: str) -> Optional[pd.DataFrame]:
        """Try reading CSV with different encodings

        Args:
            file_path: Path to CSV file

        Returns:
            DataFrame if successful, None otherwise
        """
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"Successfully read CSV with {encoding} encoding")
                return df
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
            except Exception as e:
                logger.debug(f"Failed with {encoding}: {e}")
                continue

        return None

    def _get_schema(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Extract schema information from DataFrame

        Args:
            df: pandas DataFrame

        Returns:
            List of column information dicts
        """
        schema = []
        for col in df.columns:
            schema.append({
                'column_name': col,
                'data_type': str(df[col].dtype),
                'sample_values': str(df[col].head(3).tolist())
            })
        return schema

    def get_available_tables(self) -> List[str]:
        """Get list of available table names

        Returns:
            List of table names
        """
        return list(self.dataframes.keys())

    def get_table_schema(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Get schema for a specific table or all tables

        Args:
            table_name: Optional specific table name

        Returns:
            Schema information
        """
        if table_name:
            if table_name in self.table_schemas:
                return {
                    'table_name': table_name,
                    'row_count': len(self.dataframes[table_name]),
                    'columns': self.table_schemas[table_name]
                }
            else:
                return {'error': f"Table '{table_name}' not found"}
        else:
            # Return all schemas
            all_schemas = {}
            for table_name in self.table_schemas:
                all_schemas[table_name] = {
                    'row_count': len(self.dataframes[table_name]),
                    'columns': self.table_schemas[table_name]
                }
            return all_schemas

    def execute_query(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """Execute SQL query on loaded CSV data

        Args:
            query: SQL query string
            limit: Maximum number of rows to return (default 100)

        Returns:
            Query results as dict with data and metadata
        """
        try:
            # Add LIMIT if not present and not already limited
            query_upper = query.upper().strip()
            if 'LIMIT' not in query_upper and not query_upper.endswith(';'):
                query = f"{query.rstrip(';')} LIMIT {limit}"

            # Execute query using pandasql
            # pandasql uses local scope to find DataFrames
            result_df = sqldf(query, self.dataframes)

            # Convert result to dict
            result = {
                'success': True,
                'row_count': len(result_df),
                'column_count': len(result_df.columns),
                'columns': result_df.columns.tolist(),
                'data': result_df.to_dict('records'),
                'query': query
            }

            logger.info(f"Query executed successfully: {len(result_df)} rows returned")
            return result

        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query
            }

    def execute_query_to_string(self, query: str, limit: int = 100) -> str:
        """Execute query and return formatted string result

        Args:
            query: SQL query string
            limit: Maximum number of rows to return

        Returns:
            Formatted string representation of results
        """
        result = self.execute_query(query, limit)

        if not result['success']:
            return f"Error executing query: {result['error']}"

        if result['row_count'] == 0:
            return "Query executed successfully but returned no results."

        # Format as table-like string
        output = f"Query Results ({result['row_count']} rows):\n\n"

        # Convert to DataFrame for better formatting
        df = pd.DataFrame(result['data'])
        output += df.to_string(index=False, max_rows=limit)

        if result['row_count'] > limit:
            output += f"\n\n... (showing first {limit} of {result['row_count']} rows)"

        return output

    def add_csv_file(self, file_path: str, table_name: Optional[str] = None) -> bool:
        """Add a new CSV file to the SQL engine

        Args:
            file_path: Path to CSV file
            table_name: Optional custom table name

        Returns:
            True if successful, False otherwise
        """
        try:
            filename = os.path.basename(file_path)
            table_name = table_name or self._sanitize_table_name(filename)

            # Load CSV with encoding detection
            df = self._read_csv_with_encoding(file_path)

            if df is None:
                logger.error(f"Failed to load CSV {filename} with any encoding")
                return False

            self.dataframes[table_name] = df
            self.table_schemas[table_name] = self._get_schema(df)

            logger.info(f"Added CSV: {filename} as table '{table_name}'")
            return True

        except Exception as e:
            logger.error(f"Error adding CSV file: {e}")
            return False

    def get_table_preview(self, table_name: str, num_rows: int = 5) -> str:
        """Get a preview of table data

        Args:
            table_name: Name of the table
            num_rows: Number of rows to preview

        Returns:
            Formatted string preview
        """
        if table_name not in self.dataframes:
            return f"Table '{table_name}' not found"

        df = self.dataframes[table_name]
        preview = f"Table: {table_name}\n"
        preview += f"Total Rows: {len(df)}\n"
        preview += f"Columns: {', '.join(df.columns.tolist())}\n\n"
        preview += "First few rows:\n"
        preview += df.head(num_rows).to_string(index=False)

        return preview

    def reload_csv_files(self) -> int:
        """Reload all CSV files from all directories

        Returns:
            Number of files loaded
        """
        self.dataframes.clear()
        self.table_schemas.clear()
        return self.load_all_csv_files()


# Singleton instance
sql_engine = SQLEngine()
