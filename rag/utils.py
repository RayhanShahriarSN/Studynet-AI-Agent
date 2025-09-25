# Utility functions for Django RAG backend
import os
import logging
import re
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    CSVLoader,
    JSONLoader
)
import hashlib
import json
from django.conf import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Utility class for processing various document types"""
    
    @staticmethod
    def load_knowledge_base(knowledge_base_path: Optional[str] = None) -> List[Document]:
        """Load all supported documents from the knowledge base folder"""
        documents = []
        
        # Default to media/pdfs if no path provided
        if not knowledge_base_path:
            knowledge_base_path = os.path.join(settings.BASE_DIR, "media", "pdfs")
        
        if not os.path.exists(knowledge_base_path):
            logger.warning(f"Knowledge base path does not exist: {knowledge_base_path}")
            return documents
        
        # Supported file types
        supported_extensions = ['.pdf', '.txt', '.csv', '.json', '.doc', '.docx']
        
        for filename in os.listdir(knowledge_base_path):
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in supported_extensions:
                file_path = os.path.join(knowledge_base_path, filename)
                try:
                    logger.info(f"Loading document: {filename}")
                    docs = DocumentProcessor.load_document(file_path)
                    documents.extend(docs)
                    logger.info(f"Successfully loaded {len(docs)} chunks from {filename}")
                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")
                    continue
        
        logger.info(f"Total documents loaded from knowledge base: {len(documents)}")
        return documents
    
    
    @staticmethod
    def generate_doc_id(content: str) -> str:
        """Generate unique ID for document content"""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    @staticmethod
    def process_text(text: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        """Process raw text into Document"""
        doc = Document(
            page_content=text,
            metadata=metadata or {}
        )
        doc.metadata['doc_id'] = DocumentProcessor.generate_doc_id(text)
        return doc
    
    @staticmethod
    def load_knowledge_base(knowledge_base_path: str) -> List[Document]:
        """Load all documents from the knowledge base PDFs folder"""
        documents = []
        
        if not os.path.exists(knowledge_base_path):
            logger.warning(f"Knowledge base path does not exist: {knowledge_base_path}")
            return documents
        
        # Get all PDF files from the knowledge base folder
        for filename in os.listdir(knowledge_base_path):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(knowledge_base_path, filename)
                try:
                    logger.info(f"Loading document: {filename}")
                    docs = DocumentProcessor.load_document(file_path)
                    documents.extend(docs)
                    logger.info(f"Successfully loaded {len(docs)} chunks from {filename}")
                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")
                    continue
        
        logger.info(f"Total documents loaded from PDFs folder: {len(documents)}")
        return documents

class QueryOptimizer:
    """Utilities for query optimization"""
    
    @staticmethod
    def expand_acronyms(query: str, acronym_dict: Optional[Dict[str, str]] = None) -> str:
        """Expand known acronyms in query"""
        if not acronym_dict:
            acronym_dict = {
                'AI': 'Artificial Intelligence',
                'ML': 'Machine Learning',
                'DL': 'Deep Learning',
                'NLP': 'Natural Language Processing',
                'RAG': 'Retrieval Augmented Generation',
                'LLM': 'Large Language Model'
            }
        
        words = query.split()
        expanded = []
        for word in words:
            upper_word = word.upper()
            if upper_word in acronym_dict:
                expanded.append(f"{word} ({acronym_dict[upper_word]})")
            else:
                expanded.append(word)
        
        return " ".join(expanded)
    
    @staticmethod
    def remove_stop_words(query: str) -> str:
        """Remove common stop words from query"""
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an',
            'as', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'shall', 'to', 'of', 'in', 'for', 'with',
            'by', 'from', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'up', 'down',
            'out', 'off', 'over', 'under', 'again', 'further'
        }
        
        words = query.lower().split()
        filtered = [w for w in words if w not in stop_words]
        return " ".join(filtered)
    
    @staticmethod
    def extract_keywords(query: str, max_keywords: int = 5) -> List[str]:
        """Extract important keywords from query"""
        # Remove stop words first
        cleaned = QueryOptimizer.remove_stop_words(query)
        
        # Split and sort by length (longer words often more specific)
        words = cleaned.split()
        words.sort(key=len, reverse=True)
        
        # Return top keywords
        return words[:max_keywords]

class ResponseFormatter:
    """Utilities for formatting responses"""
    
    @staticmethod
    def format_sources(sources: List[Dict[str, Any]]) -> str:
        """Format sources for display"""
        if not sources:
            return "No sources available."
        
        formatted = []
        for i, source in enumerate(sources, 1):
            source_type = source.get('type', 'unknown')
            content = source.get('content', '')[:100]
            formatted.append(f"{i}. [{source_type}] {content}...")
        
        return "\n".join(formatted)
    
    @staticmethod
    def create_citation(text: str, sources: List[Dict[str, Any]]) -> str:
        """Add citations to text"""
        if not sources:
            return text
        
        # Add citations at the end
        citations = "\n\nSources:\n" + ResponseFormatter.format_sources(sources)
        return text + citations
    
    @staticmethod
    def highlight_keywords(text: str, keywords: List[str]) -> str:
        """Highlight keywords in text"""
        for keyword in keywords:
            text = text.replace(keyword, f"**{keyword}**")
        return text

class MetricsCollector:
    """Collect and analyze system metrics"""
    
    def __init__(self):
        self.metrics = {
            'queries_processed': 0,
            'avg_response_time': 0,
            'kb_hits': 0,
            'web_searches': 0,
            'errors': 0
        }
    
    def record_query(self, response_time: float, kb_hit: bool, web_search_used: bool):
        """Record metrics for a query"""
        self.metrics['queries_processed'] += 1
        
        # Update average response time
        n = self.metrics['queries_processed']
        self.metrics['avg_response_time'] = (
            (self.metrics['avg_response_time'] * (n - 1) + response_time) / n
        )
        
        if kb_hit:
            self.metrics['kb_hits'] += 1
        if web_search_used:
            self.metrics['web_searches'] += 1
    
    def record_error(self):
        """Record an error"""
        self.metrics['errors'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            'queries_processed': 0,
            'avg_response_time': 0,
            'kb_hits': 0,
            'web_searches': 0,
            'errors': 0
        }

class ResponseEnhancer:
    """Enhance response formatting and add follow-up questions"""
    
    @staticmethod
    def enhance_response(answer: str, query: str, sources: List[Dict]) -> str:
        """Enhance the response with better formatting and follow-up questions"""
        
        # Detect if it's a how-to or procedural answer
        if any(keyword in query.lower() for keyword in ['how to', 'how do i', 'steps', 'process']):
            enhanced = ResponseEnhancer._format_procedural_answer(answer, query)
        else:
            enhanced = ResponseEnhancer._format_general_answer(answer, query)
        
        # Add follow-up questions
        follow_up = ResponseEnhancer._generate_follow_up_questions(query, answer)
        
        # Convert markdown to clean HTML
        final_response = f"{enhanced}\n\n{follow_up}"
        return ResponseEnhancer._convert_markdown_to_html(final_response)
    
    @staticmethod
    def _format_procedural_answer(answer: str, query: str) -> str:
        """Format procedural/how-to answers with steps and highlights"""
        
        # Extract key action words and highlight them
        action_words = ['go to', 'click', 'select', 'choose', 'fill', 'enter', 'save', 'add']
        
        # Create a structured format
        formatted = f"## How to {query.replace('how to ', '').replace('how do i ', '').title()}\n\n"
        
        # Try to identify steps in the original answer
        sentences = answer.split('.')
        steps = []
        current_step = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if this looks like a step
            if any(action in sentence.lower() for action in action_words):
                if current_step:
                    steps.append(current_step.strip())
                current_step = sentence
            else:
                current_step += f". {sentence}" if current_step else sentence
        
        if current_step:
            steps.append(current_step.strip())
        
        # Format as numbered steps
        if len(steps) > 1:
            formatted += "### Steps:\n\n"
            for i, step in enumerate(steps, 1):
                # Highlight key actions
                for action in action_words:
                    if action in step.lower():
                        step = step.replace(action, f"**{action}**")
                formatted += f"{i}. {step}\n\n"
        else:
            # Single instruction - format with highlights
            enhanced_answer = answer
            for action in action_words:
                enhanced_answer = re.sub(
                    f"({action})", 
                    r"**\1**", 
                    enhanced_answer, 
                    flags=re.IGNORECASE
                )
            formatted += f"{enhanced_answer}\n\n"
        
        return formatted
    
    @staticmethod
    def _format_general_answer(answer: str, query: str) -> str:
        """Format general answers with structure and highlights"""
        
        # Add a clear header
        formatted = f"## {query.title()}\n\n"
        
        # Break into paragraphs and add structure
        paragraphs = answer.split('.')
        
        # Identify key terms to highlight
        key_terms = ResponseEnhancer._extract_key_terms(answer)
        
        enhanced_answer = answer
        for term in key_terms:
            enhanced_answer = enhanced_answer.replace(term, f"**{term}**")
        
        formatted += f"{enhanced_answer}\n\n"
        
        return formatted
    
    @staticmethod
    def _extract_key_terms(text: str) -> List[str]:
        """Extract important terms that should be highlighted"""
        
        # Common important terms in CRM/business context
        important_terms = [
            'required fields', 'service type', 'lead source', 'counsellor', 
            'Education', 'Visa Services', 'Health Cover', 'RPL',
            'study level', 'course name', 'application type',
            'Save', 'Add Leads', 'Leads'
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in important_terms:
            if term.lower() in text_lower:
                found_terms.append(term)
        
        return found_terms
    
    @staticmethod
    def _generate_follow_up_questions(query: str, answer: str) -> str:
        """Generate relevant follow-up questions"""
        
        follow_ups = []
        
        # Analyze the query to suggest relevant follow-ups
        if 'add' in query.lower() and 'lead' in query.lower():
            follow_ups = [
                "Would you like to know about different lead sources available?",
                "Need help with managing leads after adding them?",
                "Want to learn about lead assignment and tracking?",
                "Curious about lead conversion best practices?"
            ]
        elif 'how' in query.lower():
            follow_ups = [
                "Would you like more details about any specific step?",
                "Need help with troubleshooting common issues?",
                "Want to know about related features?",
                "Looking for tips to optimize this process?"
            ]
        else:
            follow_ups = [
                "Would you like more specific information about this topic?",
                "Need help with related procedures?",
                "Want to explore additional features?",
                "Looking for best practices in this area?"
            ]
        
        if follow_ups:
            formatted_follow_ups = "### 💡 **What else would you like to know?**\n\n"
            for question in follow_ups[:3]:  # Limit to 3 questions
                formatted_follow_ups += f"• {question}\n"
            
            return formatted_follow_ups
        
        return ""
    
    @staticmethod
    def _convert_markdown_to_html(text: str) -> str:
        """Convert markdown syntax to clean HTML"""
        import re
        
        # Convert headers
        text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        
        # Convert bold text
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        
        # Convert italic text
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        
        # Convert bullet points
        text = re.sub(r'^• (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        
        # Convert numbered lists
        text = re.sub(r'^(\d+)\. (.+)$', r'<li>\1. \2</li>', text, flags=re.MULTILINE)
        
        # Wrap consecutive list items in ul/ol tags
        text = re.sub(r'(<li>.*</li>\n?)+', lambda m: '<ul>' + m.group(0) + '</ul>', text, flags=re.MULTILINE)
        
        # Convert line breaks to HTML breaks
        text = text.replace('\n', '<br>')
        
        # Clean up multiple breaks
        text = re.sub(r'(<br>){3,}', '<br><br>', text)
        
        # Convert code blocks
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        
        return text



# Singleton instances
document_processor = DocumentProcessor()
query_optimizer = QueryOptimizer()
response_formatter = ResponseFormatter()
metrics_collector = MetricsCollector()
response_enhancer = ResponseEnhancer()
