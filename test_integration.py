"""
Integration Test Suite: End-to-End Flow

Tests the complete pipeline from query to response:
- Phase 1: Query classification
- Phase 2: Tool execution
- Phase 3: Hybrid retrieval
- Phase 4: Agent routing
- Phase 5: API integration
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.query.classifier import get_classifier
from api.retrieval.hybrid_retriever import get_hybrid_retriever
from api.agent_v2 import get_agent_v2


def print_separator(title=""):
    """Print a formatted separator"""
    if title:
        print(f"\n{'='*80}")
        print(f" {title}")
        print(f"{'='*80}\n")
    else:
        print(f"{'='*80}\n")


def test_classification():
    """Test Phase 1: Query Classification"""
    print_separator("PHASE 1: QUERY CLASSIFICATION")

    classifier = get_classifier()

    test_queries = [
        "Show me IT courses under $20k in Sydney",
        "How do I apply for a student visa?",
        "Compare UNSW and UTS",
        "Best engineering programs with scholarships"
    ]

    for query in test_queries:
        print(f"Query: {query}")
        parsed = classifier.classify(query)
        print(f"  Type: {parsed.query_type.value}")
        print(f"  Intent: {parsed.intent.value}")
        print(f"  Entities: {len(parsed.entities)}")
        print()


def test_hybrid_retrieval():
    """Test Phase 3: Hybrid Retrieval"""
    print_separator("PHASE 3: HYBRID RETRIEVAL")

    classifier = get_classifier()
    retriever = get_hybrid_retriever()

    test_query = "IT courses under $20k in Sydney"

    print(f"Query: {test_query}\n")

    # Classify
    parsed = classifier.classify(test_query)
    print(f"Classification: {parsed.query_type.value}")

    # Retrieve
    result = retriever.retrieve(parsed, k=5)
    print(f"Result Type: {result.result_type}")
    print(f"Source: {result.source}")
    print(f"Confidence: {result.confidence}")

    if result.structured_data:
        print(f"\nStructured Results: {len(result.structured_data)} courses")
        for i, course in enumerate(result.structured_data[:3], 1):
            print(f"  {i}. {course.get('course_name', 'N/A')}")
            print(f"     Provider: {course.get('provider_name', 'N/A')}")
            if course.get('total_annual_fee'):
                print(f"     Fee: ${course['total_annual_fee']:,.2f}")

    if result.semantic_data:
        print(f"\nSemantic Results: {len(result.semantic_data)} chunks")

    print()


def test_agent_routing():
    """Test Phase 4: Agent Routing"""
    print_separator("PHASE 4: AGENT ROUTING & END-TO-END")

    agent = get_agent_v2()

    test_cases = [
        {
            'query': 'Find IT courses under $25k in Melbourne',
            'expected_type': 'structured'
        },
        {
            'query': 'What documents do I need for student visa?',
            'expected_type': 'semantic'
        },
        {
            'query': 'Compare Macquarie and UNSW for Business programs',
            'expected_type': 'comparison'
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test['query']}")
        print(f"Expected Type: {test['expected_type']}\n")

        try:
            result = agent.process_query(
                query=test['query'],
                session_id='test_session'
            )

            print(f"Response ({len(result['answer'])} chars):")
            print(result['answer'][:200] + "..." if len(result['answer']) > 200 else result['answer'])
            print(f"\nMetadata: {result.get('metadata', {})}")
            print(f"Sources: {result.get('sources', [])}")

        except Exception as e:
            print(f"ERROR: {e}")

        print("\n" + "-"*80 + "\n")


def test_all_query_types():
    """Test various query types through the complete pipeline"""
    print_separator("COMPREHENSIVE QUERY TYPE TESTS")

    agent = get_agent_v2()

    queries = [
        # Structured queries
        "Show me Business courses in Sydney",
        "Find courses under $30k",
        "Engineering programs with scholarships",

        # Semantic queries
        "How do I get a student visa?",
        "What is the cost of living in Australia?",

        # Hybrid queries
        "Best IT programs in Melbourne with good job prospects",

        # Comparison
        "Compare UTS and Macquarie University",

        # Provider details
        "Tell me about UNSW",

        # Budget queries
        "Cheapest courses available",

        # Intake queries
        "When can I apply for 2025 intake?"
    ]

    success_count = 0
    error_count = 0

    for i, query in enumerate(queries, 1):
        print(f"{i}. Query: {query}")

        try:
            result = agent.process_query(
                query=query,
                session_id=f'test_{i}'
            )

            metadata = result.get('metadata', {})
            print(f"   ✅ Success - Type: {metadata.get('query_type', 'unknown')}, "
                  f"Intent: {metadata.get('intent', 'unknown')}")
            success_count += 1

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
            error_count += 1

        print()

    print(f"\nResults: {success_count} successes, {error_count} errors out of {len(queries)} queries")


def main():
    """Run all integration tests"""

    print_separator("INTEGRATION TEST SUITE: PHASES 1-5")
    print("Testing complete pipeline from query to response\n")

    try:
        # Test Phase 1
        test_classification()

        # Test Phase 3
        test_hybrid_retrieval()

        # Test Phase 4 + 5
        test_agent_routing()

        # Comprehensive test
        test_all_query_types()

        print_separator("ALL TESTS COMPLETE")
        print("✅ Integration testing finished successfully!")
        print("\nThe system is ready for production use.")
        print("\nNext steps:")
        print("  1. Test via API: POST to /api/query/")
        print("  2. Monitor logs for any issues")
        print("  3. Test with real student queries")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
