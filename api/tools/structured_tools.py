"""
Structured Data Tools for StudyNet AI Counselor

LangChain tools that wrap DuckDB queries for course search, provider comparison,
scholarship search, and intake queries.
"""

import logging
from typing import Optional, List, Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ..storage.duckdb_store import DuckDBStore

logger = logging.getLogger(__name__)


# ============================================================================
# Tool Input Schemas
# ============================================================================

class SearchCoursesInput(BaseModel):
    """Input schema for search_courses_tool"""
    field_of_study: Optional[str] = Field(None, description="Field of study (e.g., 'Information Technology', 'Business')")
    min_fee: Optional[float] = Field(None, description="Minimum annual fee in AUD")
    max_fee: Optional[float] = Field(None, description="Maximum annual fee in AUD")
    location_city: Optional[str] = Field(None, description="City name (e.g., 'Sydney', 'Melbourne')")
    location_state: Optional[str] = Field(None, description="State name (e.g., 'New South Wales', 'Victoria')")
    provider_name: Optional[str] = Field(None, description="University/provider name")
    study_level: Optional[str] = Field(None, description="Study level (e.g., 'Bachelor Degree', 'Master Degree')")
    has_scholarship: Optional[bool] = Field(None, description="Filter for providers offering scholarships")
    limit: int = Field(10, description="Maximum number of results to return")


class CompareProvidersInput(BaseModel):
    """Input schema for compare_providers_tool"""
    provider_names: List[str] = Field(..., description="List of 2-4 provider names to compare")


class GetProviderDetailsInput(BaseModel):
    """Input schema for get_provider_details_tool"""
    provider_name: str = Field(..., description="Provider/university name")


class GetScholarshipsInput(BaseModel):
    """Input schema for get_scholarships_tool"""
    field_of_study: Optional[str] = Field(None, description="Filter scholarships by field of study")
    limit: int = Field(10, description="Maximum number of results")


class GetIntakesInput(BaseModel):
    """Input schema for get_intakes_tool"""
    provider_name: Optional[str] = Field(None, description="Filter by provider name")
    year: Optional[int] = Field(None, description="Filter by year")
    limit: int = Field(20, description="Maximum number of results")


class GetBudgetOptionsInput(BaseModel):
    """Input schema for get_budget_options_tool"""
    max_budget: float = Field(..., description="Maximum budget in AUD")
    field_of_study: Optional[str] = Field(None, description="Optional field filter")
    limit: int = Field(10, description="Maximum number of results")


# ============================================================================
# Tool Implementations
# ============================================================================

class SearchCoursesTool(BaseTool):
    """Search for courses with multiple filters"""

    name: str = "search_courses"
    description: str = """
    Search for courses in Australian universities with multiple filters.
    Use this when students ask about finding courses with specific criteria like:
    - Field of study (IT, Business, Engineering, etc.)
    - Price range (min/max annual fee)
    - Location (city or state)
    - Study level (Bachelor, Master, etc.)
    - Scholarship availability

    Example queries:
    - "Show me IT courses under $20k in Sydney"
    - "Find Business courses in Melbourne"
    - "Engineering programs with scholarships"
    """
    args_schema: type[BaseModel] = SearchCoursesInput

    def _run(
        self,
        field_of_study: Optional[str] = None,
        min_fee: Optional[float] = None,
        max_fee: Optional[float] = None,
        location_city: Optional[str] = None,
        location_state: Optional[str] = None,
        provider_name: Optional[str] = None,
        study_level: Optional[str] = None,
        has_scholarship: Optional[bool] = None,
        limit: int = 10
    ) -> str:
        """Execute the search"""
        try:
            db = DuckDBStore()

            # Convert field to list if provided (for compatibility with entity extractor)
            field_list = [field_of_study] if field_of_study else None

            results = db.search_courses(
                field_of_study=field_list,
                min_fee=min_fee,
                max_fee=max_fee,
                location_city=location_city,
                location_state=location_state,
                provider_name=provider_name,
                study_level=study_level,
                has_scholarship=has_scholarship,
                limit=limit
            )

            if not results:
                return "No courses found matching your criteria. Try broadening your search filters."

            # Format results
            output = f"Found {len(results)} courses:\n\n"
            for i, course in enumerate(results, 1):
                output += f"{i}. {course['course_name']}\n"
                output += f"   Provider: {course['provider_name']}\n"
                output += f"   Level: {course['study_level']}\n"
                if course.get('total_annual_fee'):
                    output += f"   Annual Fee: ${course['total_annual_fee']:,.2f}\n"
                if course.get('address_city'):
                    output += f"   Location: {course['address_city']}, {course.get('address_state', '')}\n"
                output += "\n"

            return output

        except Exception as e:
            logger.error(f"Error in search_courses: {e}")
            return f"Error searching courses: {str(e)}"


class CompareProvidersTool(BaseTool):
    """Compare multiple universities/providers"""

    name: str = "compare_providers"
    description: str = """
    Compare 2-4 universities side-by-side based on rankings, course offerings,
    locations, and fee ranges.

    Use this when students ask to compare universities:
    - "Compare Macquarie and UNSW"
    - "Difference between UTS and University of Sydney"
    - "Which is better: Monash or Melbourne University?"
    """
    args_schema: type[BaseModel] = CompareProvidersInput

    def _run(self, provider_names: List[str]) -> str:
        """Execute the comparison"""
        try:
            db = DuckDBStore()
            results = db.compare_providers(provider_names)

            if not results:
                return f"Could not find data for providers: {', '.join(provider_names)}"

            # Format comparison
            output = f"Comparison of {len(results)} universities:\n\n"

            for provider in results:
                output += f"{'='*60}\n"
                output += f"{provider['provider_name']}\n"
                output += f"{'='*60}\n"
                output += f"Type: {provider.get('provider_type', 'N/A')}\n"
                if provider.get('australian_ranking'):
                    output += f"Australian Ranking: #{provider['australian_ranking']}\n"
                if provider.get('global_ranking'):
                    output += f"Global Ranking: #{provider['global_ranking']}\n"
                output += f"Total Courses: {provider.get('total_courses', 0)}\n"
                output += f"Campus Locations: {provider.get('campus_count', 0)}\n"
                if provider.get('cities'):
                    output += f"Cities: {provider['cities']}\n"
                if provider.get('min_fee') and provider.get('max_fee'):
                    output += f"Fee Range: ${provider['min_fee']:,.2f} - ${provider['max_fee']:,.2f}\n"
                if provider.get('scholarship_url'):
                    output += f"Scholarships Available: Yes\n"
                output += "\n"

            return output

        except Exception as e:
            logger.error(f"Error in compare_providers: {e}")
            return f"Error comparing providers: {str(e)}"


class GetProviderDetailsTool(BaseTool):
    """Get detailed information about a specific provider"""

    name: str = "get_provider_details"
    description: str = """
    Get comprehensive details about a specific university/provider including:
    - Rankings (Australian and Global)
    - Number of courses offered
    - Campus locations
    - Fee ranges
    - Scholarship availability
    - Recognized areas of study

    Use this when students ask about a specific university:
    - "Tell me about UNSW"
    - "Information about Macquarie University"
    - "What courses does UTS offer?"
    """
    args_schema: type[BaseModel] = GetProviderDetailsInput

    def _run(self, provider_name: str) -> str:
        """Get provider details"""
        try:
            db = DuckDBStore()
            provider = db.get_provider_details(provider_name)

            if not provider:
                return f"Could not find information for provider: {provider_name}"

            output = f"{provider['provider_name']}\n"
            output += f"{'='*60}\n\n"

            if provider.get('company_name'):
                output += f"Full Name: {provider['company_name']}\n"
            output += f"Type: {provider.get('provider_type', 'N/A')}\n"
            output += f"Sector: {provider.get('public_private', 'N/A')}\n\n"

            output += "Rankings:\n"
            if provider.get('australian_ranking'):
                output += f"  - Australian Ranking: #{provider['australian_ranking']}\n"
            if provider.get('global_ranking'):
                output += f"  - Global Ranking: #{provider['global_ranking']}\n"
            output += "\n"

            output += f"Total Courses: {provider.get('total_courses', 0)}\n"
            output += f"Campus Locations: {provider.get('campus_count', 0)}\n"
            if provider.get('cities'):
                output += f"Cities: {provider['cities']}\n"
            output += "\n"

            if provider.get('min_fee') and provider.get('max_fee'):
                output += f"Fee Range: ${provider['min_fee']:,.2f} - ${provider['max_fee']:,.2f}\n"

            if provider.get('scholarship_url'):
                output += f"\nScholarships: Available\n"
                output += f"Scholarship URL: {provider['scholarship_url']}\n"

            if provider.get('website_url'):
                output += f"\nWebsite: {provider['website_url']}\n"

            if provider.get('recognised_area_of_study'):
                output += f"\nRecognized Areas: {provider['recognised_area_of_study']}\n"

            return output

        except Exception as e:
            logger.error(f"Error in get_provider_details: {e}")
            return f"Error getting provider details: {str(e)}"


class GetScholarshipsTool(BaseTool):
    """Find providers offering scholarships"""

    name: str = "get_scholarships"
    description: str = """
    Find universities that offer scholarships, optionally filtered by field of study.

    Use this when students ask about:
    - "Which universities offer scholarships?"
    - "Scholarships for IT students"
    - "Universities with financial aid"
    """
    args_schema: type[BaseModel] = GetScholarshipsInput

    def _run(self, field_of_study: Optional[str] = None, limit: int = 10) -> str:
        """Find scholarships"""
        try:
            db = DuckDBStore()
            results = db.get_scholarships(field_of_study=field_of_study, limit=limit)

            if not results:
                filter_text = f" in {field_of_study}" if field_of_study else ""
                return f"No scholarships found{filter_text}."

            output = f"Found {len(results)} universities offering scholarships:\n\n"

            for i, provider in enumerate(results, 1):
                output += f"{i}. {provider['provider_name']}\n"
                if provider.get('australian_ranking'):
                    output += f"   Ranking: #{provider['australian_ranking']}\n"
                output += f"   Courses with scholarships: {provider.get('scholarship_courses', 0)}\n"
                if provider.get('scholarship_url'):
                    output += f"   URL: {provider['scholarship_url']}\n"
                output += "\n"

            return output

        except Exception as e:
            logger.error(f"Error in get_scholarships: {e}")
            return f"Error finding scholarships: {str(e)}"


class GetIntakesTool(BaseTool):
    """Get upcoming intake/application deadlines"""

    name: str = "get_intakes"
    description: str = """
    Get upcoming course intake dates and application deadlines.
    Can be filtered by provider name or year.

    Use this when students ask about:
    - "When can I apply?"
    - "Application deadlines for UNSW"
    - "Intake dates for 2025"
    """
    args_schema: type[BaseModel] = GetIntakesInput

    def _run(
        self,
        provider_name: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 20
    ) -> str:
        """Get intake information"""
        try:
            db = DuckDBStore()
            results = db.get_upcoming_intakes(
                provider_name=provider_name,
                year=year,
                limit=limit
            )

            if not results:
                return "No upcoming intakes found matching your criteria."

            output = f"Found {len(results)} upcoming intakes:\n\n"

            for i, intake in enumerate(results, 1):
                output += f"{i}. {intake.get('course_name', 'N/A')}\n"
                output += f"   Provider: {intake.get('provider_name', 'N/A')}\n"
                if intake.get('intake_date'):
                    output += f"   Intake Date: {intake['intake_date']}\n"
                if intake.get('application_deadline'):
                    output += f"   Application Deadline: {intake['application_deadline']}\n"
                output += "\n"

            return output

        except Exception as e:
            logger.error(f"Error in get_intakes: {e}")
            return f"Error getting intakes: {str(e)}"


class GetBudgetOptionsTool(BaseTool):
    """Find courses within a specific budget"""

    name: str = "get_budget_options"
    description: str = """
    Find all courses within a specific budget, sorted by price.
    Can be optionally filtered by field of study.

    Use this when students ask about:
    - "Courses under $25,000"
    - "Cheapest IT courses"
    - "What can I study with $20k budget?"
    """
    args_schema: type[BaseModel] = GetBudgetOptionsInput

    def _run(
        self,
        max_budget: float,
        field_of_study: Optional[str] = None,
        limit: int = 10
    ) -> str:
        """Find budget options"""
        try:
            db = DuckDBStore()
            results = db.get_courses_by_budget(
                max_budget=max_budget,
                field_of_study=field_of_study,
                limit=limit
            )

            if not results:
                filter_text = f" in {field_of_study}" if field_of_study else ""
                return f"No courses found under ${max_budget:,.2f}{filter_text}."

            output = f"Found {len(results)} courses under ${max_budget:,.2f}:\n\n"

            for i, course in enumerate(results, 1):
                output += f"{i}. {course['course_name']}\n"
                output += f"   Provider: {course['provider_name']}\n"
                if course.get('total_annual_fee'):
                    output += f"   Annual Fee: ${course['total_annual_fee']:,.2f}\n"
                if course.get('study_level'):
                    output += f"   Level: {course['study_level']}\n"
                output += "\n"

            return output

        except Exception as e:
            logger.error(f"Error in get_budget_options: {e}")
            return f"Error finding budget options: {str(e)}"


# ============================================================================
# Tool Registry
# ============================================================================

def get_structured_tools() -> List[BaseTool]:
    """Get all structured data tools for the agent"""
    return [
        SearchCoursesTool(),
        CompareProvidersTool(),
        GetProviderDetailsTool(),
        GetScholarshipsTool(),
        GetIntakesTool(),
        GetBudgetOptionsTool(),
    ]
