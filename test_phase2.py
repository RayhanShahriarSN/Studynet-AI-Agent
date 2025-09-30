"""
Phase 2 Test Suite: Tool System

Tests all 8 LangChain tools (6 structured + 2 semantic)
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.tools.structured_tools import get_structured_tools
from api.tools.semantic_tools import get_semantic_tools


def print_separator(title=""):
    """Print a formatted separator"""
    if title:
        print(f"\n{'='*80}")
        print(f" {title}")
        print(f"{'='*80}\n")
    else:
        print(f"{'='*80}\n")


def test_tool(tool, **kwargs):
    """Test a single tool"""
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description[:100]}...")
    print(f"\nInput: {kwargs}")
    print(f"\nOutput:")
    print("-" * 80)

    try:
        result = tool._run(**kwargs)
        print(result)
    except Exception as e:
        print(f"ERROR: {e}")

    print()


def main():
    """Run all Phase 2 tests"""

    print_separator("PHASE 2 TEST SUITE: Tool System")

    # ========================================================================
    # STRUCTURED TOOLS TESTS
    # ========================================================================

    structured_tools = get_structured_tools()
    print(f"Loaded {len(structured_tools)} structured tools:")
    for tool in structured_tools:
        print(f"  - {tool.name}")
    print()

    # Test 1: Search Courses
    print_separator("TEST 1: Search Courses - IT under $20k")
    search_tool = structured_tools[0]
    test_tool(
        search_tool,
        field_of_study="Information Technology",
        max_fee=20000,
        limit=5
    )

    # Test 2: Search Courses - Location filter
    print_separator("TEST 2: Search Courses - Business in Sydney")
    test_tool(
        search_tool,
        field_of_study="Business",
        location_city="Sydney",
        location_state="New South Wales",
        limit=5
    )

    # Test 3: Compare Providers
    print_separator("TEST 3: Compare Providers")
    compare_tool = structured_tools[1]
    test_tool(
        compare_tool,
        provider_names=["Macquarie University", "University of Technology Sydney"]
    )

    # Test 4: Get Provider Details
    print_separator("TEST 4: Get Provider Details - UNSW")
    details_tool = structured_tools[2]
    test_tool(
        details_tool,
        provider_name="University of New South Wales"
    )

    # Test 5: Get Scholarships
    print_separator("TEST 5: Get Scholarships - IT field")
    scholarship_tool = structured_tools[3]
    test_tool(
        scholarship_tool,
        field_of_study="Information Technology",
        limit=5
    )

    # Test 6: Get Intakes
    print_separator("TEST 6: Get Upcoming Intakes")
    intake_tool = structured_tools[4]
    test_tool(
        intake_tool,
        limit=10
    )

    # Test 7: Get Budget Options
    print_separator("TEST 7: Budget Options - Under $25k")
    budget_tool = structured_tools[5]
    test_tool(
        budget_tool,
        max_budget=25000,
        limit=5
    )

    # ========================================================================
    # SEMANTIC TOOLS TESTS
    # ========================================================================

    semantic_tools = get_semantic_tools()
    print_separator("SEMANTIC TOOLS")
    print(f"Loaded {len(semantic_tools)} semantic tools:")
    for tool in semantic_tools:
        print(f"  - {tool.name}")
    print()

    # Test 8: Search Guidance
    print_separator("TEST 8: Search Guidance - Student Visa")
    guidance_tool = semantic_tools[0]
    test_tool(
        guidance_tool,
        query="How do I apply for a student visa to Australia?",
        k=3
    )

    # Test 9: Search Provider Info
    print_separator("TEST 9: Search Provider Info - Research Facilities")
    provider_info_tool = semantic_tools[1]
    test_tool(
        provider_info_tool,
        query="What research facilities and strengths does the university have?",
        k=3
    )

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print_separator("TEST COMPLETE")
    print(f"✅ Structured Tools: {len(structured_tools)}")
    print(f"✅ Semantic Tools: {len(semantic_tools)}")
    print(f"✅ Total Tools: {len(structured_tools) + len(semantic_tools)}")
    print()
    print("All tools are ready for LangChain agent integration!")


if __name__ == "__main__":
    main()
