"""Structure-aware content extraction and chunking for TOGAF documents."""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import re
from pathlib import Path

from .pdf_processor import ExtractedContent
from .metadata_schema import ContentMetadata, StructuralInfo
from .togaf_content_map import TOGAFContentMapper


@dataclass
class ContentChunk:
    """A semantically meaningful chunk of content."""
    text: str
    metadata: ContentMetadata
    chunk_type: str  # "section", "paragraph", "table", "diagram_caption"
    start_page: int
    end_page: int
    images: List[Dict[str, Any]]
    tables: List[List[List[str]]]
    
    def __post_init__(self):
        """Calculate additional properties after initialization."""
        self.word_count = len(self.text.split()) if self.text else 0
        self.char_count = len(self.text) if self.text else 0


class StructureAwareChunker:
    """Intelligent chunker that respects document structure and TOGAF organization."""
    
    def __init__(self, target_chunk_size: int = 2000, chunk_overlap: int = 200, 
                 max_chunk_size: int = 3000):
        """
        Initialize chunker with size constraints.
        
        Args:
            target_chunk_size: Target number of characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
            max_chunk_size: Maximum characters per chunk (hard limit)
        """
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunk_size = max_chunk_size
        
        # TOC patterns for detecting structure
        self.toc_patterns = [
            r'^(\d+\.?\d*\.?\d*)\s+(.+?)\.{3,}\s*\d+$',  # "1.2.3 Chapter Name...123"
            r'^(\d+\.?\d*\.?\d*)\s+(.+?)$',               # "1.2.3 Chapter Name"
            r'^([A-Z]\.?\d*)\s+(.+?)$',                   # "A.1 Appendix Name"
        ]
        
        # Section header patterns
        self.section_patterns = [
            r'^(\d+\.?\d*\.?\d*)\s+(.+)$',  # Numbered sections
            r'^([A-Z]\.?\d*)\s+(.+)$',      # Appendix sections
        ]
    
    def chunk_extracted_pages(self, extracted_pages: List[ExtractedContent], 
                             pdf_path: Path) -> List[ContentChunk]:
        """
        Chunk extracted pages while preserving document structure.
        
        Args:
            extracted_pages: List of extracted content from PDF pages
            pdf_path: Path to the source PDF
            
        Returns:
            List of semantically meaningful content chunks
        """
        chunks = []
        current_section = None
        accumulated_text = ""
        accumulated_images = []
        accumulated_tables = []
        section_start_page = 1
        
        for page_content in extracted_pages:
            # Detect if this page starts a new section
            section_info = self._extract_section_info(page_content.text)
            
            if section_info and accumulated_text:
                # Finalize current section chunk
                if len(accumulated_text.strip()) > 50:  # Minimum meaningful content
                    chunk = self._create_chunk(
                        text=accumulated_text,
                        section_info=current_section,
                        pdf_path=pdf_path,
                        start_page=section_start_page,
                        end_page=page_content.page_number - 1,
                        images=accumulated_images,
                        tables=accumulated_tables
                    )
                    chunks.append(chunk)
                
                # Reset for new section
                accumulated_text = ""
                accumulated_images = []
                accumulated_tables = []
                section_start_page = page_content.page_number
                current_section = section_info
            elif section_info:
                # First section or starting fresh
                current_section = section_info
                section_start_page = page_content.page_number
            
            # Accumulate content
            if page_content.text:
                accumulated_text += f"\n\n{page_content.text}"
            accumulated_images.extend(page_content.images)
            accumulated_tables.extend(page_content.tables)
            
            # Check if accumulated content is getting too large
            if len(accumulated_text) > self.max_chunk_size:
                # Force chunk creation to respect size limits
                chunk = self._create_chunk(
                    text=accumulated_text[:self.max_chunk_size],
                    section_info=current_section,
                    pdf_path=pdf_path,
                    start_page=section_start_page,
                    end_page=page_content.page_number,
                    images=accumulated_images,
                    tables=accumulated_tables
                )
                chunks.append(chunk)
                
                # Keep overlap for continuity
                overlap_start = max(0, self.max_chunk_size - self.chunk_overlap)
                accumulated_text = accumulated_text[overlap_start:]
                section_start_page = page_content.page_number
        
        # Handle remaining content
        if accumulated_text.strip():
            chunk = self._create_chunk(
                text=accumulated_text,
                section_info=current_section,
                pdf_path=pdf_path,
                start_page=section_start_page,
                end_page=extracted_pages[-1].page_number if extracted_pages else 1,
                images=accumulated_images,
                tables=accumulated_tables
            )
            chunks.append(chunk)
        
        # Post-process chunks to ensure optimal sizing
        return self._optimize_chunk_sizes(chunks)
    
    def _extract_section_info(self, text: str) -> Optional[Dict[str, str]]:
        """Extract section information from text."""
        if not text:
            return None
        
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines for headers
            line = line.strip()
            if not line:
                continue
                
            # Check for section patterns
            for pattern in self.section_patterns:
                match = re.match(pattern, line)
                if match:
                    return {
                        "number": match.group(1),
                        "title": match.group(2).strip(),
                        "full_header": line
                    }
        
        return None
    
    def _create_chunk(self, text: str, section_info: Optional[Dict[str, str]], 
                     pdf_path: Path, start_page: int, end_page: int,
                     images: List[Dict[str, Any]], tables: List[List[List[str]]]) -> ContentChunk:
        """Create a content chunk with appropriate metadata."""
        
        from .pdf_processor import PDFProcessor
        
        # Create mock ExtractedContent for metadata generation
        mock_content = ExtractedContent(
            text=text,
            images=images,
            tables=tables,
            metadata={"title": pdf_path.stem, "total_pages": end_page},
            method_used="chunking_process",  # This will be converted to ProcessingMethod
            page_number=start_page,
            structure_info={}
        )
        
        # Create metadata using PDF processor
        processor = PDFProcessor()
        metadata = processor.create_content_metadata(
            pdf_path=pdf_path,
            page_content=mock_content,
            chapter_info=section_info
        )
        
        # Determine chunk type
        chunk_type = self._determine_chunk_type(text, images, tables, section_info)
        
        return ContentChunk(
            text=text.strip(),
            metadata=metadata,
            chunk_type=chunk_type,
            start_page=start_page,
            end_page=end_page,
            images=images,
            tables=tables
        )
    
    def _determine_chunk_type(self, text: str, images: List[Dict], 
                            tables: List[List[List[str]]], 
                            section_info: Optional[Dict[str, str]]) -> str:
        """Determine the type of content chunk."""
        
        if tables:
            return "table"
        elif images:
            return "diagram"
        elif section_info:
            return "section"
        elif len(text.split()) < 100:
            return "paragraph"
        else:
            return "content"
    
    def _optimize_chunk_sizes(self, chunks: List[ContentChunk]) -> List[ContentChunk]:
        """Optimize chunk sizes by splitting large chunks and merging small ones."""
        optimized_chunks = []
        
        for chunk in chunks:
            if len(chunk.text) > self.max_chunk_size:
                # Split large chunks
                sub_chunks = self._split_large_chunk(chunk)
                optimized_chunks.extend(sub_chunks)
            elif (len(chunk.text) < self.target_chunk_size // 2 and 
                  optimized_chunks and 
                  len(optimized_chunks[-1].text) < self.target_chunk_size):
                # Merge small chunks with previous chunk
                prev_chunk = optimized_chunks[-1]
                merged_chunk = self._merge_chunks(prev_chunk, chunk)
                optimized_chunks[-1] = merged_chunk
            else:
                optimized_chunks.append(chunk)
        
        return optimized_chunks
    
    def _split_large_chunk(self, chunk: ContentChunk) -> List[ContentChunk]:
        """Split a large chunk into smaller ones while preserving context."""
        sub_chunks = []
        text = chunk.text
        
        # Try to split on natural boundaries (paragraphs, sentences)
        paragraphs = text.split('\n\n')
        current_text = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            if len(current_text + paragraph) > self.max_chunk_size and current_text:
                # Create sub-chunk
                sub_chunk = ContentChunk(
                    text=current_text.strip(),
                    metadata=chunk.metadata,
                    chunk_type=f"{chunk.chunk_type}_part_{chunk_index}",
                    start_page=chunk.start_page,
                    end_page=chunk.end_page,
                    images=chunk.images if chunk_index == 0 else [],  # Images only in first sub-chunk
                    tables=chunk.tables if chunk_index == 0 else []   # Tables only in first sub-chunk
                )
                sub_chunks.append(sub_chunk)
                
                # Start new chunk with overlap
                overlap_sentences = current_text.split('. ')[-2:] if '. ' in current_text else []
                current_text = '. '.join(overlap_sentences) + '. ' if overlap_sentences else ""
                chunk_index += 1
            
            current_text += f"\n\n{paragraph}"
        
        # Handle remaining text
        if current_text.strip():
            sub_chunk = ContentChunk(
                text=current_text.strip(),
                metadata=chunk.metadata,
                chunk_type=f"{chunk.chunk_type}_part_{chunk_index}",
                start_page=chunk.start_page,
                end_page=chunk.end_page,
                images=chunk.images if chunk_index == 0 else [],
                tables=chunk.tables if chunk_index == 0 else []
            )
            sub_chunks.append(sub_chunk)
        
        return sub_chunks if sub_chunks else [chunk]
    
    def _merge_chunks(self, chunk1: ContentChunk, chunk2: ContentChunk) -> ContentChunk:
        """Merge two consecutive chunks."""
        merged_text = f"{chunk1.text}\n\n{chunk2.text}"
        
        return ContentChunk(
            text=merged_text,
            metadata=chunk1.metadata,  # Use metadata from first chunk
            chunk_type=f"merged_{chunk1.chunk_type}_{chunk2.chunk_type}",
            start_page=chunk1.start_page,
            end_page=chunk2.end_page,
            images=chunk1.images + chunk2.images,
            tables=chunk1.tables + chunk2.tables
        )
    
    def get_chunk_statistics(self, chunks: List[ContentChunk]) -> Dict[str, Any]:
        """Get statistics about the chunking process."""
        if not chunks:
            return {"total_chunks": 0}
        
        chunk_sizes = [len(chunk.text) for chunk in chunks]
        word_counts = [chunk.word_count for chunk in chunks]
        chunk_types = {}
        
        for chunk in chunks:
            chunk_types[chunk.chunk_type] = chunk_types.get(chunk.chunk_type, 0) + 1
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) // len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "avg_word_count": sum(word_counts) // len(word_counts),
            "chunk_types": chunk_types,
            "total_images": sum(len(chunk.images) for chunk in chunks),
            "total_tables": sum(len(chunk.tables) for chunk in chunks)
        }