# DuckDB storage for structured CSV data
import duckdb
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from .schema import ALL_SCHEMAS, ALL_COLUMN_MAPS

logger = logging.getLogger(__name__)

class DuckDBStore:
    """DuckDB-based storage for structured CSV data"""

    def __init__(self, db_path: str = "./data/studynet.duckdb"):
        """Initialize DuckDB connection"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else "./data", exist_ok=True)

        self.db_path = db_path
        self.conn = duckdb.connect(db_path)

        logger.info(f"DuckDB initialized at {db_path}")

        # Create tables
        self._create_tables()

    def _create_tables(self):
        """Create all tables if they don't exist"""
        try:
            for schema in ALL_SCHEMAS:
                self.conn.execute(schema)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def execute(self, query: str, params: Optional[List] = None) -> List[Dict]:
        """Execute a SQL query and return results as list of dicts"""
        try:
            if params:
                result = self.conn.execute(query, params).fetchall()
            else:
                result = self.conn.execute(query).fetchall()

            # Get column names
            description = self.conn.description
            columns = [desc[0] for desc in description]

            # Convert to list of dicts
            return [dict(zip(columns, row)) for row in result]

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            raise

    def execute_df(self, query: str, params: Optional[List] = None):
        """Execute a SQL query and return results as pandas DataFrame"""
        try:
            if params:
                return self.conn.execute(query, params).fetchdf()
            else:
                return self.conn.execute(query).fetchdf()
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def count(self, table: str) -> int:
        """Get row count for a table"""
        result = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        return result[0] if result else 0

    def table_exists(self, table: str) -> bool:
        """Check if a table exists"""
        result = self.conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [table]
        ).fetchone()
        return result[0] > 0 if result else False

    def clear_table(self, table: str):
        """Delete all data from a table"""
        self.conn.execute(f"DELETE FROM {table}")
        logger.info(f"Cleared table: {table}")

    def get_table_stats(self) -> Dict[str, int]:
        """Get row counts for all tables"""
        tables = ['providers', 'campus_locations', 'courses', 'fees', 'intakes']
        stats = {}
        for table in tables:
            try:
                stats[table] = self.count(table)
            except:
                stats[table] = 0
        return stats

    # === Search Methods ===

    def search_courses(self,
                      field_of_study: Optional[List[str]] = None,
                      min_fee: Optional[float] = None,
                      max_fee: Optional[float] = None,
                      location_city: Optional[str] = None,
                      location_state: Optional[str] = None,
                      provider_name: Optional[str] = None,
                      study_level: Optional[str] = None,
                      has_scholarship: Optional[bool] = None,
                      max_ranking: Optional[int] = None,
                      limit: int = 20) -> List[Dict]:
        """
        Search courses with multiple filters

        Returns courses with joined provider and location data
        """

        query = """
            SELECT
                c.course_id,
                c.course_name,
                c.provider_name,
                c.study_level,
                c.area_of_study_broad,
                c.area_of_study_narrow,
                c.duration,
                c.duration_unit,
                c.has_scholarship,
                c.has_internship,
                c.url_course_info,
                f.total_annual_fee,
                f.total_course_fee,
                f.year as fee_year,
                p.australian_ranking,
                p.global_ranking,
                p.website_url,
                p.scholarship_url,
                l.address_city,
                l.address_state,
                l.campus_name
            FROM courses c
            LEFT JOIN fees f ON c.course_id = f.course_id
            LEFT JOIN providers p ON c.provider_id = p.provider_id
            LEFT JOIN campus_locations l ON c.provider_id = l.provider_id
            WHERE c.is_active = TRUE
        """

        params = []

        # Field of study filter
        if field_of_study:
            placeholders = ','.join(['?'] * len(field_of_study))
            query += f" AND (c.area_of_study_broad IN ({placeholders}) OR c.area_of_study_narrow IN ({placeholders}))"
            params.extend(field_of_study)
            params.extend(field_of_study)

        # Price filters
        if min_fee is not None:
            query += " AND f.total_annual_fee >= ?"
            params.append(min_fee)

        if max_fee is not None:
            query += " AND f.total_annual_fee <= ?"
            params.append(max_fee)

        # Location filters
        if location_city:
            query += " AND l.address_city = ?"
            params.append(location_city)

        if location_state:
            query += " AND l.address_state = ?"
            params.append(location_state)

        # Provider filter
        if provider_name:
            query += " AND c.provider_name LIKE ?"
            params.append(f"%{provider_name}%")

        # Study level filter
        if study_level:
            query += " AND c.study_level = ?"
            params.append(study_level)

        # Scholarship filter
        if has_scholarship:
            query += " AND c.has_scholarship = TRUE"

        # Ranking filter
        if max_ranking is not None:
            query += " AND p.australian_ranking <= ?"
            params.append(max_ranking)

        # Order by fee (cheapest first)
        query += " ORDER BY f.total_annual_fee ASC NULLS LAST"

        # Limit
        query += f" LIMIT {limit}"

        return self.execute(query, params)

    def compare_providers(self, provider_names: List[str]) -> List[Dict]:
        """Compare multiple providers side-by-side"""

        if not provider_names:
            return []

        placeholders = ','.join(['?'] * len(provider_names))

        query = f"""
            SELECT
                p.provider_name,
                p.australian_ranking,
                p.global_ranking,
                p.provider_type,
                p.public_private,
                p.recognised_area_of_study,
                p.scholarship_url,
                p.website_url,
                COUNT(DISTINCT c.course_id) as total_courses,
                MIN(f.total_annual_fee) as min_fee,
                MAX(f.total_annual_fee) as max_fee,
                AVG(f.total_annual_fee) as avg_fee,
                COUNT(DISTINCT l.campus_id) as campus_count,
                STRING_AGG(DISTINCT l.address_city, ', ') as cities
            FROM providers p
            LEFT JOIN courses c ON p.provider_id = c.provider_id
            LEFT JOIN fees f ON c.course_id = f.course_id
            LEFT JOIN campus_locations l ON p.provider_id = l.provider_id
            WHERE p.provider_name IN ({placeholders})
            GROUP BY p.provider_id, p.provider_name, p.australian_ranking,
                     p.global_ranking, p.provider_type, p.public_private,
                     p.recognised_area_of_study, p.scholarship_url, p.website_url
        """

        return self.execute(query, provider_names)

    def get_provider_details(self, provider_name: str) -> Optional[Dict]:
        """Get full details about a provider"""

        query = """
            SELECT
                p.provider_id,
                p.provider_name,
                p.company_name,
                p.provider_type,
                p.public_private,
                p.australian_ranking,
                p.global_ranking,
                p.website_url,
                p.scholarship_url,
                p.recognised_area_of_study,
                COUNT(DISTINCT c.course_id) as total_courses,
                COUNT(DISTINCT l.campus_id) as campus_count,
                STRING_AGG(DISTINCT l.address_city, ', ') as cities
            FROM providers p
            LEFT JOIN courses c ON p.provider_id = c.provider_id
            LEFT JOIN campus_locations l ON p.provider_id = l.provider_id
            WHERE p.provider_name LIKE ?
            GROUP BY p.provider_id, p.provider_name, p.company_name, p.provider_type,
                     p.public_private, p.australian_ranking, p.global_ranking,
                     p.website_url, p.scholarship_url, p.recognised_area_of_study
        """

        results = self.execute(query, [f"%{provider_name}%"])
        if results and len(results) > 0:
            return results[0]
        return None

    def get_courses_by_budget(self,
                             min_budget: float = 0,
                             max_budget: float = 100000,
                             field_of_study: Optional[str] = None,
                             limit: int = 20) -> List[Dict]:
        """Find courses within a budget range"""

        query = """
            SELECT
                c.course_name,
                c.provider_name,
                c.study_level,
                c.area_of_study_broad,
                f.total_annual_fee,
                f.total_course_fee,
                p.australian_ranking,
                l.address_city,
                l.address_state
            FROM courses c
            JOIN fees f ON c.course_id = f.course_id
            LEFT JOIN providers p ON c.provider_id = p.provider_id
            LEFT JOIN campus_locations l ON c.provider_id = l.provider_id
            WHERE c.is_active = TRUE
            AND f.total_annual_fee BETWEEN ? AND ?
        """

        params = [min_budget, max_budget]

        if field_of_study:
            query += " AND c.area_of_study_broad LIKE ?"
            params.append(f"%{field_of_study}%")

        query += f" ORDER BY f.total_annual_fee ASC LIMIT {limit}"

        return self.execute(query, params)

    def get_scholarships(self, field_of_study: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Find providers with scholarships"""

        query = """
            SELECT DISTINCT
                p.provider_name,
                p.scholarship_url,
                p.australian_ranking,
                COUNT(DISTINCT c.course_id) as scholarship_courses,
                STRING_AGG(DISTINCT l.address_city, ', ') as cities
            FROM providers p
            LEFT JOIN courses c ON p.provider_id = c.provider_id AND c.has_scholarship = TRUE
            LEFT JOIN campus_locations l ON p.provider_id = l.provider_id
            WHERE p.scholarship_url IS NOT NULL AND p.scholarship_url != ''
        """

        params = []

        if field_of_study:
            query += " AND c.area_of_study_broad LIKE ?"
            params.append(f"%{field_of_study}%")

        query += f"""
            GROUP BY p.provider_id, p.provider_name, p.scholarship_url, p.australian_ranking
            ORDER BY scholarship_courses DESC
            LIMIT {limit}
        """

        return self.execute(query, params)

    def get_upcoming_intakes(self,
                            provider_name: Optional[str] = None,
                            year: Optional[int] = None,
                            limit: int = 20) -> List[Dict]:
        """Get upcoming intake dates"""

        query = """
            SELECT
                i.provider_name,
                i.year,
                i.commencement_date as intake_date,
                i.application_deadline,
                i.orientation_date,
                i.is_open,
                p.website_url
            FROM intakes i
            LEFT JOIN providers p ON i.provider_id = p.provider_id
            WHERE i.is_open = TRUE
        """

        params = []

        if provider_name:
            query += " AND i.provider_name LIKE ?"
            params.append(f"%{provider_name}%")

        if year:
            query += " AND i.year = ?"
            params.append(year)

        query += f" ORDER BY i.commencement_date ASC LIMIT {limit}"

        return self.execute(query, params)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("DuckDB connection closed")

# Singleton instance
_duckdb_store = None

def get_duckdb_store(db_path: str = "./data/studynet.duckdb") -> DuckDBStore:
    """Get or create DuckDB store singleton"""
    global _duckdb_store
    if _duckdb_store is None:
        _duckdb_store = DuckDBStore(db_path)
    return _duckdb_store
