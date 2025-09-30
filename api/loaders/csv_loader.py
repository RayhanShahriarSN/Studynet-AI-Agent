# CSV data loader for StudyNet
import pandas as pd
import os
import logging
from typing import Dict, List
from ..storage.schema import ALL_COLUMN_MAPS
from ..storage.duckdb_store import get_duckdb_store

logger = logging.getLogger(__name__)

class CSVDataLoader:
    """Load CSV files into DuckDB"""

    def __init__(self, csv_directory: str = "./pdfs"):
        self.csv_directory = csv_directory
        self.db_store = get_duckdb_store()

        # CSV file mappings
        self.csv_files = {
            'providers': '01_SN_Provider_Data(Provider).csv',
            'campus_locations': '02_SN_Campus_Locations(CampusLocation).csv',
            'intakes': '03_SN_Intakes(Intake).csv',
            'courses': '04_SN_Courses(Course).csv',
            'fees': '05_SN_Fees(Fees).csv'
        }

    def load_all(self, clear_existing: bool = True):
        """Load all CSV files into database"""
        logger.info("Starting CSV data load...")

        if clear_existing:
            logger.info("Clearing existing data...")
            for table in self.csv_files.keys():
                try:
                    self.db_store.clear_table(table)
                except:
                    pass

        # Load in order (respecting foreign keys)
        load_order = ['providers', 'campus_locations', 'courses', 'fees', 'intakes']

        for table in load_order:
            try:
                self.load_table(table)
            except Exception as e:
                logger.error(f"Error loading {table}: {e}")
                raise

        # Print statistics
        stats = self.db_store.get_table_stats()
        logger.info("=== Data Load Complete ===")
        for table, count in stats.items():
            logger.info(f"  {table}: {count:,} rows")

        return stats

    def load_table(self, table_name: str):
        """Load a single CSV file into a table"""
        csv_file = self.csv_files.get(table_name)
        if not csv_file:
            raise ValueError(f"Unknown table: {table_name}")

        file_path = os.path.join(self.csv_directory, csv_file)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        logger.info(f"Loading {table_name} from {csv_file}...")

        # Read CSV - try different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, low_memory=False, encoding=encoding, on_bad_lines='skip')
                logger.info(f"  Successfully read with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"  Error with {encoding}: {e}")
                continue

        if df is None:
            raise ValueError(f"Could not read CSV with any encoding: {file_path}")

        logger.info(f"  Read {len(df)} rows from CSV")

        # Rename columns
        column_map = ALL_COLUMN_MAPS[table_name]
        df = df.rename(columns=column_map)

        # Keep only mapped columns
        mapped_cols = list(column_map.values())
        existing_cols = [col for col in mapped_cols if col in df.columns]
        df = df[existing_cols]

        # Filter out rows with missing primary keys or critical fields
        df = self._filter_valid_rows(df, table_name)

        # Clean and transform data
        df = self._clean_dataframe(df, table_name)

        # Insert into database
        self._insert_dataframe(df, table_name)

        logger.info(f"  ✓ Loaded {len(df)} rows into {table_name}")

    def _filter_valid_rows(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Filter out rows with missing critical data"""
        initial_count = len(df)

        # Primary keys must not be null
        primary_keys = {
            'providers': 'provider_id',
            'campus_locations': 'campus_id',
            'courses': 'course_id',
            'fees': None,  # Auto-generated
            'intakes': 'intake_id'
        }

        pk = primary_keys.get(table_name)
        if pk and pk in df.columns:
            df = df[df[pk].notna() & (df[pk] != '')]

        # Additional validation per table
        if table_name == 'providers':
            # Keep only rows with at least provider_id
            pass  # Already filtered by PK

        elif table_name == 'courses':
            # Keep only courses with a course_id
            pass  # Already filtered by PK

        elif table_name == 'fees':
            # Keep only fees with course_id or provider_id
            if 'course_id' in df.columns:
                df = df[df['course_id'].notna() | df['provider_id'].notna()]

        filtered_count = initial_count - len(df)
        if filtered_count > 0:
            logger.info(f"  Filtered out {filtered_count} invalid rows")

        return df

    def _clean_dataframe(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Clean and transform DataFrame before insertion"""

        # Handle boolean conversions
        boolean_cols = {
            'providers': ['accepts_ielts', 'accepts_toefl', 'accepts_duolingo', 'accepts_sat', 'accepts_act', 'has_on_campus_accommodation', 'is_active'],
            'campus_locations': ['on_campus_accommodation'],
            'courses': ['is_active', 'has_scholarship', 'has_internship', 'has_bridging_program', 'is_international'],
            'intakes': ['is_open', 'tentative']
        }

        if table_name in boolean_cols:
            for col in boolean_cols[table_name]:
                if col in df.columns:
                    df[col] = df[col].apply(self._to_boolean)

        # Handle numeric conversions
        numeric_cols = {
            'providers': ['global_ranking', 'australian_ranking'],
            'courses': ['duration', 'ielts_overall', 'ielts_reading', 'ielts_writing', 'ielts_speaking', 'ielts_listening',
                       'toefl_overall_ibt', 'toefl_reading_ibt', 'toefl_writing_ibt', 'toefl_speaking_ibt', 'toefl_listening_ibt',
                       'toefl_overall_pbt', 'duolingo_score', 'pte_score', 'atar', 'cae_score', 'sat_score', 'act_score',
                       'gre_verbal_reasoning', 'gre_quantitative_reasoning', 'gre_analytic_writing', 'lsat_score',
                       'application_fee_paper', 'application_fee_online'],
            'fees': ['year', 'unit_price', 'unit_count', 'total_annual_fee', 'total_course_fee'],
            'intakes': ['year']
        }

        if table_name in numeric_cols:
            for col in numeric_cols[table_name]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

        # Handle date conversions
        date_cols = {
            'intakes': ['commencement_date', 'end_date', 'orientation_date', 'application_deadline']
        }

        if table_name in date_cols:
            for col in date_cols[table_name]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

        # Replace NaN with None for database NULL
        df = df.where(pd.notnull(df), None)

        # Clean text fields - remove extra whitespace
        text_cols = df.select_dtypes(include=['object']).columns
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

        # Generate auto-increment IDs for fees table
        if table_name == 'fees' and 'id' not in df.columns:
            df.insert(0, 'id', range(1, len(df) + 1))

        return df

    def _to_boolean(self, value) -> bool:
        """Convert various representations to boolean"""
        if pd.isna(value):
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value = value.strip().upper()
            if value in ['YES', 'TRUE', '1', 'Y', 'T']:
                return True
            elif value in ['NO', 'FALSE', '0', 'N', 'F', '']:
                return False
        if isinstance(value, (int, float)):
            return value > 0
        return False

    def _insert_dataframe(self, df: pd.DataFrame, table_name: str):
        """Insert DataFrame into database table"""
        try:
            # Use DuckDB's from pandas directly for efficiency
            self.db_store.conn.execute(
                f"INSERT INTO {table_name} SELECT * FROM df"
            )
        except Exception as e:
            logger.error(f"Error inserting into {table_name}: {e}")
            logger.error(f"Sample data: {df.head()}")
            raise

    def reload_data(self):
        """Convenience method to reload all data"""
        return self.load_all(clear_existing=True)

# Create loader instance
csv_loader = CSVDataLoader()
