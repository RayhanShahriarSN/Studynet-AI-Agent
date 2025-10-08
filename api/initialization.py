# Initialization module for knowledge base and SQL tables
import os
import logging
from pathlib import Path
from .config import config
from .vectorstore import vector_store
from .sql_engine import sql_engine
from .utils import document_processor
from .models import DataSourceStats

logger = logging.getLogger(__name__)


class KnowledgeBaseInitializer:
    """Initialize knowledge base and SQL tables on startup"""

    def __init__(self):
        self.hard_kb_path = Path(config.KNOWLEDGE_BASE_PATH)  # pdfs/
        self.uploaded_docs_path = Path("./uploaded_docs")
        self.vector_db_path = Path(config.VECTOR_DB_PATH)

    def initialize(self):
        """Main initialization method - called on Django startup"""
        logger.info("=" * 60)
        logger.info("STARTING KNOWLEDGE BASE INITIALIZATION")
        logger.info("=" * 60)

        # Ensure directories exist
        self._ensure_directories()

        # Initialize hard knowledge base (one-time)
        self._initialize_hard_knowledge_base()

        # Load user-uploaded documents (if any exist)
        self._load_user_uploads()

        logger.info("=" * 60)
        logger.info("INITIALIZATION COMPLETE")
        logger.info("=" * 60)

    def _ensure_directories(self):
        """Create necessary directories"""
        self.hard_kb_path.mkdir(parents=True, exist_ok=True)
        self.uploaded_docs_path.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Directories verified")

    def _initialize_hard_knowledge_base(self):
        """Initialize hard knowledge base from pdfs/ folder"""
        logger.info("\n[HARD KNOWLEDGE BASE]")

        # Check if already initialized
        if self._is_hard_kb_initialized():
            logger.info("✓ Hard KB already initialized (skipping)")
            self._display_kb_stats()
            return

        logger.info("⚡ Hard KB not initialized - loading now...")

        # Load documents (PDFs, DOCX, TXT)
        documents_loaded = self._load_documents_from_folder(self.hard_kb_path, is_hard_kb=True)

        # Load CSV files to SQL
        csv_loaded = self._load_csv_files_from_folder(self.hard_kb_path, is_hard_kb=True)

        logger.info(f"✓ Loaded {documents_loaded} documents and {csv_loaded} CSV tables")
        self._display_kb_stats()

    def _load_user_uploads(self):
        """Load existing user uploads from uploaded_docs/ folder"""
        logger.info("\n[USER UPLOADS]")

        if not list(self.uploaded_docs_path.glob("*")):
            logger.info("✓ No user uploads found")
            return

        logger.info("⚡ Loading user-uploaded files...")

        # Load documents
        documents_loaded = self._load_documents_from_folder(self.uploaded_docs_path, is_hard_kb=False)

        # Load CSVs
        csv_loaded = self._load_csv_files_from_folder(self.uploaded_docs_path, is_hard_kb=False)

        logger.info(f"✓ Loaded {documents_loaded} documents and {csv_loaded} CSV tables from uploads")

    def _is_hard_kb_initialized(self) -> bool:
        """Check if hard knowledge base is already initialized"""
        try:
            # Check vector store
            parent_count = vector_store.parent_store._collection.count()
            child_count = vector_store.child_store._collection.count()
            has_vectors = (parent_count + child_count) > 0

            # Check SQL tables
            sql_tables = sql_engine.get_available_tables()
            has_sql = len(sql_tables) > 0

            # Check if we have tracked sources in DB
            from .models import DataSourceStats
            has_tracked_sources = DataSourceStats.objects.filter(
                metadata__hard_kb=True
            ).exists()

            # Initialized if we have vectors OR SQL tables OR tracked sources
            return has_vectors or has_sql or has_tracked_sources

        except Exception as e:
            logger.warning(f"Could not check initialization status: {e}")
            return False

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
            return 0

        logger.info(f"   Found {len(document_files)} documents to process")

        total_loaded = 0
        for doc_file in document_files:
            try:
                # Check if already processed
                if self._is_document_already_loaded(doc_file, is_hard_kb):
                    logger.info(f"   ⏭  Skipping {doc_file.name} (already loaded)")
                    continue

                logger.info(f"   📄 Loading {doc_file.name}...")

                # Load document
                documents = document_processor.load_document(
                    str(doc_file),
                    use_docling=True  # Use Docling for better processing
                )

                # Add metadata
                for doc in documents:
                    doc.metadata['hard_kb'] = is_hard_kb
                    doc.metadata['source_folder'] = str(folder_path)

                # Add to vector store
                vector_store.add_documents(documents)

                # Track in database
                self._track_document_source(doc_file, len(documents), is_hard_kb)

                total_loaded += 1
                logger.info(f"   ✓ Embedded {len(documents)} chunks from {doc_file.name}")

            except Exception as e:
                logger.error(f"   ✗ Error loading {doc_file.name}: {e}")
                continue

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
            return 0

        logger.info(f"   Found {csv_files} CSV files to load")

        total_loaded = 0
        for csv_file in csv_files:
            try:
                # Check if already loaded
                table_name = sql_engine._sanitize_table_name(csv_file.name)
                if table_name in sql_engine.get_available_tables():
                    logger.info(f"   ⏭  Skipping {csv_file.name} (already loaded)")
                    continue

                logger.info(f"   📊 Loading {csv_file.name} to SQL...")

                # Load to SQL engine
                success = sql_engine.add_csv_file(str(csv_file), table_name)

                if success:
                    # Get table info
                    schema = sql_engine.get_table_schema(table_name)

                    # Track in database
                    self._track_csv_source(csv_file, table_name, schema, is_hard_kb)

                    total_loaded += 1
                    logger.info(f"   ✓ Loaded {schema['row_count']} rows as table '{table_name}'")

            except Exception as e:
                logger.error(f"   ✗ Error loading {csv_file.name}: {e}")
                continue

        return total_loaded

    def _is_document_already_loaded(self, doc_path: Path, is_hard_kb: bool) -> bool:
        """Check if document is already loaded in vector store"""
        try:
            return DataSourceStats.objects.filter(
                source_name=doc_path.name,
                source_type__in=['pdf_document', 'docx_document', 'text_document'],
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
                '.html': 'text_document'
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
            logger.error(f"Error tracking document: {e}")

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
            logger.error(f"Error tracking CSV: {e}")

    def _display_kb_stats(self):
        """Display knowledge base statistics"""
        try:
            # Vector store stats
            parent_count = vector_store.parent_store._collection.count()
            child_count = vector_store.child_store._collection.count()

            # SQL stats
            sql_tables = sql_engine.get_available_tables()

            logger.info(f"\n📊 KNOWLEDGE BASE STATS:")
            logger.info(f"   Vector Store: {parent_count} parent chunks, {child_count} child chunks")
            logger.info(f"   SQL Tables: {len(sql_tables)} tables ({', '.join(sql_tables)})")

        except Exception as e:
            logger.error(f"Error displaying stats: {e}")


# Singleton instance
kb_initializer = KnowledgeBaseInitializer()


def initialize_knowledge_base():
    """Entry point for initialization - called from apps.py"""
    try:
        kb_initializer.initialize()
    except Exception as e:
        logger.error(f"INITIALIZATION ERROR: {e}")
        import traceback
        traceback.print_exc()
