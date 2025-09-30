# SQL query builder from parsed entities
from typing import Tuple, List, Dict, Any, Optional
from .classifier import ParsedQuery, Intent
import logging

logger = logging.getLogger(__name__)

class SQLQueryBuilder:
    """Build SQL queries from parsed query entities"""

    def build_query(self, parsed_query: ParsedQuery) -> Tuple[str, List[Any]]:
        """
        Convert ParsedQuery to SQL

        Returns:
            Tuple of (sql_string, parameters)
        """

        filters = parsed_query.filters
        intent = parsed_query.intent

        logger.info(f"Building SQL for intent: {intent.value}")
        logger.info(f"Filters: {filters}")

        if intent == Intent.SEARCH_COURSES or intent == Intent.FILTER_BY_CRITERIA:
            return self._build_course_search(filters, parsed_query.top_k)

        elif intent == Intent.COMPARE_PROVIDERS:
            # Need provider names from query
            provider_filter = filters.get('provider_name')
            if provider_filter:
                # If single provider, can't compare
                # This should be handled by extracting multiple providers
                return self._build_provider_comparison([provider_filter])
            else:
                # Fallback to course search
                return self._build_course_search(filters, parsed_query.top_k)

        elif intent == Intent.GET_PROVIDER_INFO:
            return self._build_provider_details(filters)

        elif intent == Intent.GET_SCHOLARSHIPS:
            return self._build_scholarship_search(filters)

        elif intent == Intent.GET_INTAKES:
            return self._build_intake_search(filters)

        else:
            # Default to course search
            return self._build_course_search(filters, parsed_query.top_k)

    def _build_course_search(self, filters: Dict[str, Any], limit: int = 20) -> Tuple[str, List]:
        """Build course search query with filters"""

        sql = """
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
                c.description,
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
        conditions = []

        # Field of study filter
        if 'field_of_study' in filters:
            fields = filters['field_of_study']
            if isinstance(fields, list) and len(fields) > 0:
                placeholders = ','.join(['?'] * len(fields))
                conditions.append(f"""(
                    c.area_of_study_broad IN ({placeholders})
                    OR c.area_of_study_narrow IN ({placeholders})
                )""")
                params.extend(fields)
                params.extend(fields)
                logger.info(f"Added field filter: {fields}")

        # Price filters
        if 'price_range' in filters:
            price = filters['price_range']
            if isinstance(price, dict):
                if price.get('min') is not None and price['min'] > 0:
                    conditions.append("f.total_annual_fee >= ?")
                    params.append(price['min'])
                    logger.info(f"Added min price: {price['min']}")

                if price.get('max') is not None and price['max'] < 999999:
                    conditions.append("f.total_annual_fee <= ?")
                    params.append(price['max'])
                    logger.info(f"Added max price: {price['max']}")

        # Location filters
        if 'location_city' in filters:
            conditions.append("l.address_city = ?")
            params.append(filters['location_city'])
            logger.info(f"Added city filter: {filters['location_city']}")

        if 'location_state' in filters:
            conditions.append("l.address_state = ?")
            params.append(filters['location_state'])
            logger.info(f"Added state filter: {filters['location_state']}")

        # Provider filter
        if 'provider_name' in filters:
            conditions.append("c.provider_name LIKE ?")
            params.append(f"%{filters['provider_name']}%")
            logger.info(f"Added provider filter: {filters['provider_name']}")

        # Study level filter
        if 'study_level' in filters:
            conditions.append("c.study_level = ?")
            params.append(filters['study_level'])
            logger.info(f"Added study level filter: {filters['study_level']}")

        # Scholarship filter
        if filters.get('has_scholarship'):
            conditions.append("c.has_scholarship = TRUE")
            logger.info("Added scholarship filter")

        # Internship filter
        if filters.get('has_internship'):
            conditions.append("c.has_internship = TRUE")
            logger.info("Added internship filter")

        # Ranking filter
        if 'max_ranking' in filters:
            conditions.append("p.australian_ranking <= ?")
            params.append(filters['max_ranking'])
            logger.info(f"Added ranking filter: top {filters['max_ranking']}")

        # Add conditions to SQL
        if conditions:
            sql += " AND " + " AND ".join(conditions)

        # Order by fee (cheapest first) if price filter exists
        if 'price_range' in filters:
            sql += " ORDER BY f.total_annual_fee ASC NULLS LAST"
        else:
            # Order by ranking if available
            sql += " ORDER BY p.australian_ranking ASC NULLS LAST, f.total_annual_fee ASC NULLS LAST"

        # Limit
        sql += f" LIMIT {limit}"

        logger.info(f"Built SQL with {len(conditions)} conditions")
        return sql, params

    def _build_provider_comparison(self, provider_names: List[str]) -> Tuple[str, List]:
        """Build provider comparison query"""

        if not provider_names or len(provider_names) == 0:
            # Return empty query
            return "SELECT 1 WHERE 1=0", []

        placeholders = ','.join(['?'] * len(provider_names))

        sql = f"""
            SELECT
                p.provider_name,
                p.australian_ranking,
                p.global_ranking,
                p.provider_type,
                p.public_private,
                p.recognised_area_of_study,
                p.website_url,
                p.scholarship_url,
                COUNT(DISTINCT c.course_id) as total_courses,
                MIN(f.total_annual_fee) as min_fee,
                MAX(f.total_annual_fee) as max_fee,
                AVG(f.total_annual_fee) as avg_fee,
                COUNT(DISTINCT l.campus_id) as campus_count,
                STRING_AGG(DISTINCT l.address_city, ', ') as cities
            FROM providers p
            LEFT JOIN courses c ON p.provider_id = c.provider_id AND c.is_active = TRUE
            LEFT JOIN fees f ON c.course_id = f.course_id
            LEFT JOIN campus_locations l ON p.provider_id = l.provider_id
            WHERE p.provider_name IN ({placeholders})
            GROUP BY p.provider_id, p.provider_name, p.australian_ranking,
                     p.global_ranking, p.provider_type, p.public_private,
                     p.recognised_area_of_study, p.website_url, p.scholarship_url
            ORDER BY p.australian_ranking ASC NULLS LAST
        """

        return sql, provider_names

    def _build_provider_details(self, filters: Dict[str, Any]) -> Tuple[str, List]:
        """Build query for provider details"""

        provider_name = filters.get('provider_name', '')

        sql = """
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
                STRING_AGG(DISTINCT l.address_city, ', ') as cities,
                MIN(f.total_annual_fee) as min_fee,
                MAX(f.total_annual_fee) as max_fee
            FROM providers p
            LEFT JOIN courses c ON p.provider_id = c.provider_id AND c.is_active = TRUE
            LEFT JOIN campus_locations l ON p.provider_id = l.provider_id
            LEFT JOIN fees f ON c.course_id = f.course_id
            WHERE p.provider_name LIKE ?
            GROUP BY p.provider_id, p.provider_name, p.company_name, p.provider_type,
                     p.public_private, p.australian_ranking, p.global_ranking,
                     p.website_url, p.scholarship_url, p.recognised_area_of_study
        """

        return sql, [f"%{provider_name}%"]

    def _build_scholarship_search(self, filters: Dict[str, Any]) -> Tuple[str, List]:
        """Build scholarship search query"""

        sql = """
            SELECT DISTINCT
                p.provider_name,
                p.scholarship_url,
                p.australian_ranking,
                p.website_url,
                COUNT(DISTINCT c.course_id) as courses_with_scholarship,
                STRING_AGG(DISTINCT l.address_city, ', ') as cities
            FROM providers p
            LEFT JOIN courses c ON p.provider_id = c.provider_id
                AND c.has_scholarship = TRUE
                AND c.is_active = TRUE
            LEFT JOIN campus_locations l ON p.provider_id = l.provider_id
            WHERE p.scholarship_url IS NOT NULL
                AND p.scholarship_url != ''
        """

        params = []

        # Optional field filter
        if 'field_of_study' in filters:
            fields = filters['field_of_study']
            if isinstance(fields, list):
                placeholders = ','.join(['?'] * len(fields))
                sql += f" AND c.area_of_study_broad IN ({placeholders})"
                params.extend(fields)

        sql += """
            GROUP BY p.provider_id, p.provider_name, p.scholarship_url,
                     p.australian_ranking, p.website_url
            ORDER BY courses_with_scholarship DESC, p.australian_ranking ASC
            LIMIT 20
        """

        return sql, params

    def _build_intake_search(self, filters: Dict[str, Any]) -> Tuple[str, List]:
        """Build intake/deadline search query"""

        sql = """
            SELECT
                i.provider_name,
                i.year,
                i.commencement_date,
                i.application_deadline,
                i.orientation_date,
                i.is_open,
                p.website_url,
                p.australian_ranking
            FROM intakes i
            LEFT JOIN providers p ON i.provider_id = p.provider_id
            WHERE i.is_open = TRUE
        """

        params = []

        # Provider filter
        if 'provider_name' in filters:
            sql += " AND i.provider_name LIKE ?"
            params.append(f"%{filters['provider_name']}%")

        sql += " ORDER BY i.commencement_date ASC LIMIT 20"

        return sql, params

# Singleton
_sql_builder = None

def get_sql_builder() -> SQLQueryBuilder:
    """Get or create SQL builder singleton"""
    global _sql_builder
    if _sql_builder is None:
        _sql_builder = SQLQueryBuilder()
    return _sql_builder
