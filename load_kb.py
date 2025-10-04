#!/usr/bin/env python
"""
Knowledge Base Loader Script

This script loads documents and CSV files into the RAG system:
- Loads PDFs, DOCX, TXT, HTML from pdfs/ folder (hard knowledge base)
- Loads CSVs from pdfs/ folder as SQL tables
- Loads user-uploaded files from uploaded_docs/ folder (if exist)
- Tracks all files in database to prevent re-processing

Usage:
    python load_kb.py                    # Load everything
    python load_kb.py --hard-kb-only     # Only load pdfs/ folder
    python load_kb.py --uploads-only     # Only load uploaded_docs/ folder
    python load_kb.py --csv-only         # Only load CSV files
    python load_kb.py --docs-only        # Only load documents
    python load_kb.py --force            # Force reload (ignore tracking)
"""

import os
import sys
import django
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.utils import document_processor
from api.config import config
from api.vectorstore import vector_store
from api.sql_engine import sql_engine
from api.models import DataSourceStats

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeBaseLoader:
    """Load documents and CSVs into the RAG system"""

    def __init__(self, force_reload: bool = False):
        self.hard_kb_path = Path(config.KNOWLEDGE_BASE_PATH)  # pdfs/
        self.uploaded_docs_path = Path("./uploaded_docs")
        self.force_reload = force_reload

    def load_all(self, csv_only: bool = False, docs_only: bool = False):
        """Load all knowledge base files"""
        logger.info("=" * 70)
        logger.info("KNOWLEDGE BASE LOADER")
        logger.info("=" * 70)

        # Ensure directories exist
        self._ensure_directories()

        # Load hard knowledge base
        self.load_hard_kb(csv_only=csv_only, docs_only=docs_only)

        # Load user uploads
        self.load_user_uploads(csv_only=csv_only, docs_only=docs_only)

        # Display final stats
        self._display_final_stats()

        logger.info("=" * 70)
        logger.info("✅ LOADING COMPLETE!")
        logger.info("=" * 70)

    def load_hard_kb(self, csv_only: bool = False, docs_only: bool = False):
        """Load hard knowledge base from pdfs/ folder"""
        logger.info("\n" + "=" * 70)
        logger.info("HARD KNOWLEDGE BASE (pdfs/)")
        logger.info("=" * 70)

        if not self.hard_kb_path.exists():
            logger.warning(f"⚠️  Folder not found: {self.hard_kb_path}")
            logger.info("   Creating folder...")
            self.hard_kb_path.mkdir(parents=True, exist_ok=True)
            return

        doc_count = 0
        csv_count = 0

        # Load documents (unless csv_only)
        if not csv_only:
            doc_count = self._load_documents_from_folder(self.hard_kb_path, is_hard_kb=True)

        # Load CSVs (unless docs_only)
        if not docs_only:
            csv_count = self._load_csv_files_from_folder(self.hard_kb_path, is_hard_kb=True)

        logger.info(f"\n📊 Hard KB Summary: {doc_count} documents, {csv_count} CSVs")

    def load_user_uploads(self, csv_only: bool = False, docs_only: bool = False):
        """Load user uploads from uploaded_docs/ folder"""
        logger.info("\n" + "=" * 70)
        logger.info("USER UPLOADS (uploaded_docs/)")
        logger.info("=" * 70)

        if not self.uploaded_docs_path.exists():
            logger.info(f"ℹ️  No uploads folder found")
            logger.info("   Creating folder for future uploads...")
            self.uploaded_docs_path.mkdir(parents=True, exist_ok=True)
            return

        if not list(self.uploaded_docs_path.glob("*")):
            logger.info(f"ℹ️  No user uploads found")
            return

        doc_count = 0
        csv_count = 0

        # Load documents (unless csv_only)
        if not csv_only:
            doc_count = self._load_documents_from_folder(self.uploaded_docs_path, is_hard_kb=False)

        # Load CSVs (unless docs_only)
        if not docs_only:
            csv_count = self._load_csv_files_from_folder(self.uploaded_docs_path, is_hard_kb=False)

        logger.info(f"\n📊 User Uploads Summary: {doc_count} documents, {csv_count} CSVs")

    def _ensure_directories(self):
        """Create necessary directories"""
        self.hard_kb_path.mkdir(parents=True, exist_ok=True)
        self.uploaded_docs_path.mkdir(parents=True, exist_ok=True)
        Path(config.VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)

    def _load_documents_from_folder(self, folder_path: Path, is_hard_kb: bool = False) -> int:
        """Load PDF/DOCX/TXT documents from folder and embed them

        Args:
            folder_path: Path to folder containing documents
            is_hard_kb: Whether this is the hard knowledge base

        Returns:
            Number of documents loaded
        """
        doc_extensions = ['.pdf', '.docx', '.doc', '.txt', '.html']
        document_files = []

        for ext in doc_extensions:
            document_files.extend(folder_path.glob(f"*{ext}"))

        if not document_files:
            logger.info(f"   No documents found")
            return 0

        logger.info(f"\n📄 Found {len(document_files)} document(s)")

        total_loaded = 0
        total_skipped = 0

        for doc_file in document_files:
            try:
                # Check if already processed (unless force reload)
                if not self.force_reload and self._is_document_already_loaded(doc_file, is_hard_kb):
                    logger.info(f"   ⏭️  {doc_file.name:<40} [SKIPPED - already loaded]")
                    total_skipped += 1
                    continue

                logger.info(f"   📥 {doc_file.name:<40} [LOADING...]")

                # Load document using Docling for better processing
                documents = document_processor.load_document(
                    str(doc_file),
                    use_docling=True
                )

                # Add metadata
                for doc in documents:
                    doc.metadata['hard_kb'] = is_hard_kb
                    doc.metadata['source_folder'] = str(folder_path)
                    doc.metadata['original_filename'] = doc_file.name

                # Add to vector store
                vector_store.add_documents(documents)

                # Track in database
                self._track_document_source(doc_file, len(documents), is_hard_kb)

                total_loaded += 1
                logger.info(f"      ✅ Embedded {len(documents)} chunks")

            except Exception as e:
                logger.error(f"      ❌ ERROR: {str(e)}")
                continue

        logger.info(f"\n   Summary: {total_loaded} loaded, {total_skipped} skipped")
        return total_loaded

    def _load_csv_files_from_folder(self, folder_path: Path, is_hard_kb: bool = False) -> int:
        """Load CSV files into SQL tables

        Args:
            folder_path: Path to folder containing CSVs
            is_hard_kb: Whether this is the hard knowledge base

        Returns:
            Number of CSV files loaded
        """
        csv_files = list(folder_path.glob("*.csv"))

        if not csv_files:
            logger.info(f"   No CSV files found")
            return 0

        logger.info(f"\n📊 Found {len(csv_files)} CSV file(s)")

        total_loaded = 0
        total_skipped = 0

        for csv_file in csv_files:
            try:
                # Generate table name
                table_name = sql_engine._sanitize_table_name(csv_file.stem)

                # Check if already loaded (unless force reload)
                if not self.force_reload and table_name in sql_engine.get_available_tables():
                    logger.info(f"   ⏭️  {csv_file.name:<40} [SKIPPED - table '{table_name}' exists]")
                    total_skipped += 1
                    continue

                logger.info(f"   📥 {csv_file.name:<40} [LOADING...]")

                # Load to SQL engine
                success = sql_engine.add_csv_file(str(csv_file), table_name)

                if success:
                    # Get table info
                    schema = sql_engine.get_table_schema(table_name)

                    # Track in database
                    self._track_csv_source(csv_file, table_name, schema, is_hard_kb)

                    total_loaded += 1
                    logger.info(f"      ✅ Created table '{table_name}' with {schema['row_count']} rows")
                else:
                    logger.error(f"      ❌ Failed to load CSV")

            except Exception as e:
                logger.error(f"      ❌ ERROR: {str(e)}")
                continue

        logger.info(f"\n   Summary: {total_loaded} loaded, {total_skipped} skipped")
        return total_loaded

    def _is_document_already_loaded(self, doc_path: Path, is_hard_kb: bool) -> bool:
        """Check if document is already loaded in vector store"""
        try:
            return DataSourceStats.objects.filter(
                source_name=doc_path.name,
                source_type__in=['pdf_document', 'docx_document', 'text_document', 'html_document'],
                metadata__hard_kb=is_hard_kb
            ).exists()
        except:
            return False

    def _track_document_source(self, doc_path: Path, chunk_count: int, is_hard_kb: bool):
        """Track document in database"""
        try:
            # Determine source type
            ext = doc_path.suffix.lower()
            source_type_map = {
                '.pdf': 'pdf_document',
                '.docx': 'docx_document',
                '.doc': 'docx_document',
                '.txt': 'text_document',
                '.html': 'html_document'
            }
            source_type = source_type_map.get(ext, 'text_document')

            DataSourceStats.objects.update_or_create(
                source_name=doc_path.name,
                defaults={
                    'source_type': source_type,
                    'chunk_count': chunk_count,
                    'file_size_kb': doc_path.stat().st_size // 1024,
                    'metadata': {
                        'hard_kb': is_hard_kb,
                        'file_path': str(doc_path)
                    }
                }
            )
        except Exception as e:
            logger.error(f"      ⚠️  Warning: Could not track in database: {e}")

    def _track_csv_source(self, csv_path: Path, table_name: str, schema: dict, is_hard_kb: bool):
        """Track CSV in database"""
        try:
            DataSourceStats.objects.update_or_create(
                source_name=table_name,
                defaults={
                    'source_type': 'csv_table',
                    'row_count': schema['row_count'],
                    'file_size_kb': csv_path.stat().st_size // 1024,
                    'columns': [col['column_name'] for col in schema['columns']],
                    'metadata': {
                        'hard_kb': is_hard_kb,
                        'file_path': str(csv_path),
                        'original_filename': csv_path.name
                    }
                }
            )
        except Exception as e:
            logger.error(f"      ⚠️  Warning: Could not track in database: {e}")

    def _display_final_stats(self):
        """Display final knowledge base statistics"""
        logger.info("\n" + "=" * 70)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 70)

        try:
            # Vector store stats
            parent_count = vector_store.parent_store._collection.count()
            child_count = vector_store.child_store._collection.count()

            # SQL stats
            sql_tables = sql_engine.get_available_tables()

            # Database tracking stats
            doc_stats = DataSourceStats.objects.filter(
                source_type__in=['pdf_document', 'docx_document', 'text_document', 'html_document']
            )
            csv_stats = DataSourceStats.objects.filter(source_type='csv_table')

            logger.info(f"\n📊 VECTOR STORE:")
            logger.info(f"   Parent chunks: {parent_count}")
            logger.info(f"   Child chunks:  {child_count}")
            logger.info(f"   Documents:     {doc_stats.count()}")

            logger.info(f"\n📊 SQL ENGINE:")
            logger.info(f"   Tables:        {len(sql_tables)}")
            if sql_tables:
                logger.info(f"   Table names:   {', '.join(sql_tables)}")

            # Hard KB vs User uploads
            hard_kb_docs = doc_stats.filter(metadata__hard_kb=True).count()
            user_docs = doc_stats.filter(metadata__hard_kb=False).count()
            hard_kb_csvs = csv_stats.filter(metadata__hard_kb=True).count()
            user_csvs = csv_stats.filter(metadata__hard_kb=False).count()

            logger.info(f"\n📊 SOURCE BREAKDOWN:")
            logger.info(f"   Hard KB:       {hard_kb_docs} documents, {hard_kb_csvs} CSVs")
            logger.info(f"   User uploads:  {user_docs} documents, {user_csvs} CSVs")

        except Exception as e:
            logger.error(f"❌ Error displaying stats: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Load knowledge base files')
    parser.add_argument('--hard-kb-only', action='store_true',
                        help='Only load hard knowledge base (pdfs/ folder)')
    parser.add_argument('--uploads-only', action='store_true',
                        help='Only load user uploads (uploaded_docs/ folder)')
    parser.add_argument('--csv-only', action='store_true',
                        help='Only load CSV files (skip documents)')
    parser.add_argument('--docs-only', action='store_true',
                        help='Only load documents (skip CSV files)')
    parser.add_argument('--force', action='store_true',
                        help='Force reload all files (ignore tracking)')

    args = parser.parse_args()

    # Validate conflicting options
    if args.csv_only and args.docs_only:
        logger.error("❌ Cannot use --csv-only and --docs-only together")
        return

    loader = KnowledgeBaseLoader(force_reload=args.force)

    if args.force:
        logger.info("⚡ FORCE MODE: Will reload all files")
    if args.csv_only:
        logger.info("📊 CSV ONLY MODE: Skipping documents")
    if args.docs_only:
        logger.info("📄 DOCS ONLY MODE: Skipping CSVs")

    if args.hard_kb_only:
        loader.load_hard_kb(csv_only=args.csv_only, docs_only=args.docs_only)
        loader._display_final_stats()
    elif args.uploads_only:
        loader.load_user_uploads(csv_only=args.csv_only, docs_only=args.docs_only)
        loader._display_final_stats()
    else:
        loader.load_all(csv_only=args.csv_only, docs_only=args.docs_only)


if __name__ == "__main__":
    main()
