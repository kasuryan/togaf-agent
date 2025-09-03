"""Embedding generation with comprehensive metadata for TOGAF content using latest OpenAI API."""

import asyncio
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import asdict
import logging

from ..utils.config import Settings
from ..utils.openai_client import OpenAIClient
from .content_chunker import ContentChunk
from .metadata_schema import ContentMetadata

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate and manage embeddings with comprehensive metadata using latest OpenAI API."""
    
    def __init__(self, settings: Settings):
        """Initialize embedding generator with OpenAI client."""
        self.settings = settings
        self.openai_client = OpenAIClient(settings)
        self.embeddings_dir = settings.knowledge_base_dir / "embeddings"
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        
        # Embedding cache to avoid regenerating identical content
        self.embedding_cache = {}
        self.load_embedding_cache()
    
    async def generate_chunk_embeddings(self, chunks: List[ContentChunk]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for content chunks with metadata using latest OpenAI API.
        
        Args:
            chunks: List of content chunks to embed
            
        Returns:
            List of embedding records with metadata
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        embedding_records = []
        batch_texts = []
        batch_chunks = []
        
        # Prepare batches for efficient processing
        for chunk in chunks:
            # Create embedding text that includes both content and metadata context
            embedding_text = self._create_embedding_text(chunk)
            content_hash = self._generate_content_hash(embedding_text)
            
            # Check cache first
            if content_hash in self.embedding_cache:
                logger.debug(f"Using cached embedding for chunk {chunk.metadata.structural_info.chunk_id}")
                embedding_record = self._create_embedding_record(
                    chunk, 
                    self.embedding_cache[content_hash],
                    embedding_text,
                    content_hash
                )
                embedding_records.append(embedding_record)
            else:
                batch_texts.append(embedding_text)
                batch_chunks.append((chunk, content_hash))
        
        # Generate embeddings for uncached content using latest API
        if batch_texts:
            logger.info(f"Generating new embeddings for {len(batch_texts)} chunks using {self.settings.openai_embedding_model}")
            try:
                embeddings = await self.openai_client.create_embeddings_batch(batch_texts)
                
                for i, (chunk, content_hash) in enumerate(batch_chunks):
                    embedding_vector = embeddings[i]
                    embedding_text = batch_texts[i]
                    
                    # Cache the embedding
                    self.embedding_cache[content_hash] = embedding_vector
                    
                    # Create embedding record
                    embedding_record = self._create_embedding_record(
                        chunk, embedding_vector, embedding_text, content_hash
                    )
                    embedding_records.append(embedding_record)
                
                # Save updated cache
                self.save_embedding_cache()
                
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                raise
        
        logger.info(f"Generated {len(embedding_records)} embedding records")
        return embedding_records
    
    def _create_embedding_text(self, chunk: ContentChunk) -> str:
        """
        Create optimized text for embedding that includes content and context.
        
        This combines the actual content with metadata context to create
        semantically rich embeddings that understand TOGAF structure.
        """
        # Start with the main content
        embedding_parts = [chunk.text]
        
        # Add metadata context for richer embeddings
        metadata = chunk.metadata
        
        # Add certification level and part/guide context
        if metadata.certification_level:
            level_context = f"TOGAF {metadata.certification_level.value} level content"
            embedding_parts.append(level_context)
        
        # Add specific part/guide context
        if metadata.semantic_info.foundation_part:
            part_name = metadata.semantic_info.foundation_part.value.replace('_', ' ').title()
            embedding_parts.append(f"From {part_name}")
        
        if metadata.semantic_info.practitioner_guide:
            guide_name = metadata.semantic_info.practitioner_guide.value.replace('_', ' ').title()
            embedding_parts.append(f"From TOGAF Series Guide: {guide_name}")
        
        # Add chapter/section context
        if metadata.structural_info.chapter_title:
            embedding_parts.append(f"Chapter: {metadata.structural_info.chapter_title}")
        
        if metadata.structural_info.section_title:
            embedding_parts.append(f"Section: {metadata.structural_info.section_title}")
        
        # Add key concepts for semantic richness
        if metadata.semantic_info.key_concepts:
            key_concepts = ", ".join(metadata.semantic_info.key_concepts[:5])  # Limit to top 5
            embedding_parts.append(f"Key concepts: {key_concepts}")
        
        # Add ADM phase context if applicable
        if metadata.semantic_info.adm_phases:
            phases = [phase.value.replace('_', ' ').title() for phase in metadata.semantic_info.adm_phases]
            embedding_parts.append(f"ADM phases: {', '.join(phases)}")
        
        # Add content type context
        content_type = metadata.content_type.value.replace('_', ' ').title()
        embedding_parts.append(f"Content type: {content_type}")
        
        # Combine all parts with separators
        return " | ".join(embedding_parts)
    
    def _create_embedding_record(self, chunk: ContentChunk, embedding_vector: List[float], 
                                embedding_text: str, content_hash: str) -> Dict[str, Any]:
        """Create a comprehensive embedding record with metadata."""
        
        # Convert metadata to dictionary
        metadata_dict = chunk.metadata.to_dict()
        
        # Create comprehensive embedding record
        record = {
            # Core identifiers
            "chunk_id": chunk.metadata.structural_info.chunk_id,
            "content_hash": content_hash,
            
            # Content
            "text": chunk.text,
            "embedding_text": embedding_text,  # Text used for embedding (with context)
            "embedding_vector": embedding_vector,
            
            # Chunk information
            "chunk_type": chunk.chunk_type,
            "word_count": chunk.word_count,
            "char_count": chunk.char_count,
            "start_page": chunk.start_page,
            "end_page": chunk.end_page,
            
            # Rich metadata
            "metadata": metadata_dict,
            
            # Search tags for efficient filtering
            "search_tags": chunk.metadata.get_search_tags(),
            
            # Content characteristics
            "has_images": len(chunk.images) > 0,
            "has_tables": len(chunk.tables) > 0,
            "image_count": len(chunk.images),
            "table_count": len(chunk.tables),
            
            # Embedding metadata (using latest API info)
            "embedding_model": self.settings.openai_embedding_model,
            "embedding_dimensions": len(embedding_vector),
            "encoding_format": "float",  # Latest API format
            
            # Quality scores
            "content_quality_score": chunk.metadata.content_quality_score,
            "extraction_confidence": chunk.metadata.extraction_confidence,
        }
        
        return record
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash for content to enable caching."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def load_embedding_cache(self) -> None:
        """Load embedding cache from disk."""
        cache_file = self.embeddings_dir / "embedding_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.embedding_cache = json.load(f)
                logger.info(f"Loaded {len(self.embedding_cache)} cached embeddings")
            except Exception as e:
                logger.warning(f"Error loading embedding cache: {e}")
                self.embedding_cache = {}
        else:
            self.embedding_cache = {}
    
    def save_embedding_cache(self) -> None:
        """Save embedding cache to disk."""
        cache_file = self.embeddings_dir / "embedding_cache.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.embedding_cache, f)
            logger.debug(f"Saved {len(self.embedding_cache)} embeddings to cache")
        except Exception as e:
            logger.error(f"Error saving embedding cache: {e}")
    
    def save_embedding_records(self, embedding_records: List[Dict[str, Any]], 
                              filename: str = None) -> Path:
        """Save embedding records to disk."""
        if filename is None:
            filename = f"embeddings_{len(embedding_records)}_chunks.json"
        
        output_file = self.embeddings_dir / filename
        
        try:
            with open(output_file, 'w') as f:
                json.dump(embedding_records, f, indent=2)
            logger.info(f"Saved {len(embedding_records)} embedding records to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error saving embedding records: {e}")
            raise
    
    def load_embedding_records(self, filename: str) -> List[Dict[str, Any]]:
        """Load embedding records from disk."""
        input_file = self.embeddings_dir / filename
        
        if not input_file.exists():
            raise FileNotFoundError(f"Embedding file not found: {input_file}")
        
        try:
            with open(input_file, 'r') as f:
                embedding_records = json.load(f)
            logger.info(f"Loaded {len(embedding_records)} embedding records from {input_file}")
            return embedding_records
        except Exception as e:
            logger.error(f"Error loading embedding records: {e}")
            raise
    
    async def process_pdf_to_embeddings(self, pdf_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Complete pipeline: PDF -> Chunks -> Embeddings with metadata using latest API.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (embedding_records, statistics)
        """
        from .pdf_processor import PDFProcessor
        from .content_chunker import StructureAwareChunker
        
        logger.info(f"Processing PDF to embeddings: {pdf_path}")
        
        # Extract content from PDF
        pdf_processor = PDFProcessor(extract_images=True, save_images=True,
                                   image_dir=self.settings.knowledge_base_dir / "images")
        extracted_pages = pdf_processor.extract_content(pdf_path)
        
        # Chunk content intelligently
        chunker = StructureAwareChunker(
            target_chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            max_chunk_size=self.settings.max_tokens_per_chunk
        )
        chunks = chunker.chunk_extracted_pages(extracted_pages, pdf_path)
        
        # Generate embeddings using latest API
        embedding_records = await self.generate_chunk_embeddings(chunks)
        
        # Gather comprehensive statistics
        processing_stats = pdf_processor.get_processing_stats()
        chunking_stats = chunker.get_chunk_statistics(chunks)
        embedding_stats = {
            "total_embeddings": len(embedding_records),
            "embedding_model": self.settings.openai_embedding_model,
            "embedding_dimensions": len(embedding_records[0]["embedding_vector"]) if embedding_records else 0,
            "cached_embeddings": len([r for r in embedding_records if r["content_hash"] in self.embedding_cache]),
            "new_embeddings": len([r for r in embedding_records if r["content_hash"] not in self.embedding_cache]),
            "encoding_format": "float",
            "api_version": "latest"
        }
        
        statistics = {
            "pdf_processing": processing_stats,
            "chunking": chunking_stats,
            "embedding": embedding_stats,
            "pdf_path": str(pdf_path),
            "total_pages": len(extracted_pages),
            "processing_timestamp": asyncio.get_event_loop().time()
        }
        
        logger.info(f"Successfully processed {pdf_path} -> {len(embedding_records)} embeddings")
        return embedding_records, statistics
    
    async def validate_embedding_system(self) -> Dict[str, bool]:
        """Comprehensive validation of the embedding system."""
        results = {}
        
        # Test API connection
        results["api_connection"] = await self.openai_client.validate_api_key_async()
        
        # Test embedding functionality
        results["embedding_functionality"] = await self.openai_client.test_embedding_functionality()
        
        # Test cache system
        try:
            test_hash = "test_hash"
            test_embedding = [0.1] * 1536  # Mock embedding
            self.embedding_cache[test_hash] = test_embedding
            self.save_embedding_cache()
            self.load_embedding_cache()
            results["cache_system"] = test_hash in self.embedding_cache
            # Clean up test
            del self.embedding_cache[test_hash]
        except Exception:
            results["cache_system"] = False
        
        # Test directory creation
        try:
            test_dir = self.embeddings_dir / "test"
            test_dir.mkdir(exist_ok=True)
            test_dir.rmdir()
            results["directory_creation"] = True
        except Exception:
            results["directory_creation"] = False
        
        return results