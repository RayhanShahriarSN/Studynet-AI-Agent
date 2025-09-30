#!/usr/bin/env python
"""
Load CSV data into DuckDB database
Run this script to initialize the structured data storage
"""
import os
import sys
import django

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.loaders.csv_loader import csv_loader
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Load all CSV data into DuckDB"""
    print("=" * 60)
    print("StudyNet CSV Data Loader")
    print("=" * 60)
    print()

    try:
        # Load all data
        stats = csv_loader.load_all(clear_existing=True)

        print()
        print("=" * 60)
        print("✅ Data Load Successful!")
        print("=" * 60)
        print()
        print("Summary:")
        for table, count in stats.items():
            print(f"  • {table:<20} : {count:>6,} rows")
        print()
        print("You can now use the structured query system!")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Error loading data")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
