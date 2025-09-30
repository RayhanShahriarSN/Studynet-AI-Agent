#!/usr/bin/env python
"""
Test Phase 1: Query Intelligence Layer
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.query.classifier import get_classifier
from api.query.sql_builder import get_sql_builder
from api.storage.duckdb_store import get_duckdb_store
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_query(query_text: str):
    """Test a single query through the pipeline"""
    print("\n" + "="*80)
    print(f"QUERY: {query_text}")
    print("="*80)

    # Step 1: Classify
    classifier = get_classifier()
    parsed = classifier.classify(query_text)

    print(f"\nCLASSIFICATION:")
    print(f"  Type: {parsed.query_type.value}")
    print(f"  Intent: {parsed.intent.value}")
    print(f"  Entities: {len(parsed.entities)}")
    for entity in parsed.entities:
        print(f"    - {entity.type}: {entity.value} -> {entity.normalized_value}")
    print(f"  Filters: {parsed.filters}")

    # Step 2: Build SQL (if structured)
    if parsed.query_type.value in ['structured', 'hybrid', 'comparison']:
        sql_builder = get_sql_builder()
        sql, params = sql_builder.build_query(parsed)

        print(f"\nSQL QUERY:")
        print(f"  {sql[:200]}...")
        print(f"  Parameters: {params}")

        # Step 3: Execute
        db = get_duckdb_store()
        try:
            results = db.execute(sql, params)
            print(f"\nRESULTS: {len(results)} rows")

            # Show first 3 results
            for i, row in enumerate(results[:3], 1):
                print(f"\n  {i}. {row.get('course_name', row.get('provider_name', 'N/A'))}")
                if 'provider_name' in row and 'course_name' in row:
                    print(f"     Provider: {row['provider_name']}")
                if 'total_annual_fee' in row and row['total_annual_fee']:
                    print(f"     Annual Fee: ${row['total_annual_fee']:,.2f}")
                if 'address_city' in row and row['address_city']:
                    print(f"     Location: {row['address_city']}, {row['address_state']}")
                if 'study_level' in row and row['study_level']:
                    print(f"     Level: {row['study_level']}")

        except Exception as e:
            print(f"\nERROR executing SQL: {e}")

    else:
        print(f"\nSEMANTIC QUERY - Would search vector store for guidance documents")


def main():
    """Run test suite"""
    print("\n" + "="*80)
    print(" PHASE 1 TEST SUITE: Query Intelligence Layer")
    print("="*80)

    test_queries = [
        # Structured queries
        "Show me IT courses under $20k",
        "Find Business courses in Sydney",
        "Bachelor degrees in Melbourne under $25k",
        "Engineering programs with scholarships",

        # Location queries
        "Courses in Brisbane",
        "Universities in New South Wales",

        # Price queries
        "Courses between $15k and $30k",
        "Cheapest courses available",

        # Semantic queries
        "How do I apply for a student visa?",
        "What documents do I need?",

        # Hybrid queries
        "Best IT courses with scholarships in Melbourne",
        "Affordable Business programs with good job prospects",
    ]

    for query in test_queries:
        try:
            test_query(query)
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print(" TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
