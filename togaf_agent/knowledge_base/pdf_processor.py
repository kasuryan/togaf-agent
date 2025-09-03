"""PDF processing with PyMuPDF-first approach and intelligent fallbacks."""

import pymupdf  # Modern PyMuPDF import
import pdfplumber
import PyPDF2
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
import base64
from io import BytesIO

from .metadata_schema import (
    ContentMetadata, MetadataBuilder, DocumentInfo, StructuralInfo,
    FoundationPart, PractitionerGuide, ContentType, DifficultyLevel
)
from .togaf_content_map import TOGAFContentMapper

logger = logging.getLogger(__name__)


class ProcessingMethod(Enum):
    """PDF processing methods."""
    PYMUPDF = "pymupdf"
    PDFPLUMBER = "pdfplumber"
    PYPDF2 = "pypdf2"


@dataclass
class ExtractedContent:
    """Container for extracted PDF content with metadata."""
    text: str
    images: List[Dict[str, Any]]
    tables: List[List[List[str]]]
    metadata: Dict[str, Any]
    method_used: ProcessingMethod
    page_number: int
    structure_info: Dict[str, Any]


class PDFProcessor:
    """Intelligent PDF processor with PyMuPDF-first approach and fallbacks."""
    
    def __init__(self, extract_images: bool = True, save_images: bool = False, image_dir: Optional[Path] = None):
        self.extract_images = extract_images
        self.save_images = save_images
        self.image_dir = image_dir
        if self.save_images and self.image_dir:
            self.image_dir.mkdir(parents=True, exist_ok=True)
            
        self.processing_stats = {
            ProcessingMethod.PYMUPDF: {"success": 0, "failed": 0},
            ProcessingMethod.PDFPLUMBER: {"success": 0, "failed": 0},
            ProcessingMethod.PYPDF2: {"success": 0, "failed": 0}
        }
    
    def extract_content(self, pdf_path: Path) -> List[ExtractedContent]:
        """
        Extract content from PDF using intelligent processing strategy.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of ExtractedContent objects, one per page
        """
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Try PyMuPDF first (primary method)
        try:
            content = self._extract_with_pymupdf(pdf_path)
            if self._validate_extraction(content):
                self.processing_stats[ProcessingMethod.PYMUPDF]["success"] += 1
                logger.info(f"Successfully processed {pdf_path} with PyMuPDF")
                return content
            else:
                raise ValueError("PyMuPDF extraction validation failed")
        except Exception as e:
            logger.warning(f"PyMuPDF failed for {pdf_path}: {str(e)}")
            self.processing_stats[ProcessingMethod.PYMUPDF]["failed"] += 1
        
        # Fallback 1: pdfplumber (good for tables and complex layouts)
        try:
            content = self._extract_with_pdfplumber(pdf_path)
            if self._validate_extraction(content):
                self.processing_stats[ProcessingMethod.PDFPLUMBER]["success"] += 1
                logger.info(f"Successfully processed {pdf_path} with pdfplumber")
                return content
            else:
                raise ValueError("pdfplumber extraction validation failed")
        except Exception as e:
            logger.warning(f"pdfplumber failed for {pdf_path}: {str(e)}")
            self.processing_stats[ProcessingMethod.PDFPLUMBER]["failed"] += 1
        
        # Fallback 2: PyPDF2 (basic text extraction)
        try:
            content = self._extract_with_pypdf2(pdf_path)
            if self._validate_extraction(content):
                self.processing_stats[ProcessingMethod.PYPDF2]["success"] += 1
                logger.info(f"Successfully processed {pdf_path} with PyPDF2")
                return content
            else:
                raise ValueError("PyPDF2 extraction validation failed")
        except Exception as e:
            logger.error(f"All processing methods failed for {pdf_path}: {str(e)}")
            self.processing_stats[ProcessingMethod.PYPDF2]["failed"] += 1
            raise Exception(f"Failed to process PDF {pdf_path} with all available methods")
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> List[ExtractedContent]:
        """Extract content using PyMuPDF with structure awareness and image extraction."""
        doc = pymupdf.open(pdf_path)
        extracted_pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text with structure
            text_dict = page.get_text("dict")
            text = page.get_text()
            
            # Extract images with actual image data
            images = []
            if self.extract_images:
                images = self._extract_images_pymupdf(doc, page, page_num, pdf_path.stem)
            
            # Extract structure info (blocks, fonts, layout)
            structure_info = {
                "blocks": len(text_dict["blocks"]),
                "fonts": self._extract_font_info(text_dict),
                "bbox": page.rect,
                "rotation": page.rotation
            }
            
            # Table detection using PyMuPDF
            tables = self._detect_tables_pymupdf(page)
            
            extracted_pages.append(ExtractedContent(
                text=text,
                images=images,
                tables=tables,
                metadata={"pdf_path": str(pdf_path), "total_pages": len(doc)},
                method_used=ProcessingMethod.PYMUPDF,
                page_number=page_num + 1,
                structure_info=structure_info
            ))
        
        doc.close()
        return extracted_pages
    
    def _extract_images_pymupdf(self, doc, page, page_num: int, pdf_name: str) -> List[Dict[str, Any]]:
        """Extract actual image data from PDF page using PyMuPDF."""
        images = []
        
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                
                # Extract image
                pix = pymupdf.Pixmap(doc, xref)
                
                # Skip CMYK images (they're problematic)
                if pix.n - pix.alpha >= 4:
                    pix = None
                    continue
                
                # Convert to RGB if necessary
                if pix.colorspace and pix.colorspace.n > 3:
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                
                # Get image bytes
                img_bytes = pix.tobytes("png")
                
                # Create image info
                image_info = {
                    "index": img_index,
                    "page_number": page_num + 1,
                    "xref": xref,
                    "width": pix.width,
                    "height": pix.height,
                    "colorspace": pix.colorspace.name if pix.colorspace else "unknown",
                    "size_bytes": len(img_bytes),
                    "format": "png"
                }
                
                # Save image to base64 for embedding storage
                image_info["base64_data"] = base64.b64encode(img_bytes).decode('utf-8')
                
                # Optionally save image to disk
                if self.save_images and self.image_dir:
                    image_filename = f"{pdf_name}_page{page_num+1}_img{img_index}.png"
                    image_path = self.image_dir / image_filename
                    with open(image_path, "wb") as img_file:
                        img_file.write(img_bytes)
                    image_info["saved_path"] = str(image_path)
                
                images.append(image_info)
                pix = None
                
            except Exception as e:
                logger.warning(f"Failed to extract image {img_index} from page {page_num}: {e}")
                continue
        
        return images
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> List[ExtractedContent]:
        """Extract content using pdfplumber (excellent for tables)."""
        extracted_pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                
                # Extract tables (pdfplumber's strength)
                tables = []
                try:
                    page_tables = page.extract_tables()
                    tables = page_tables if page_tables else []
                except Exception:
                    tables = []
                
                # Basic image detection (pdfplumber has limited image extraction)
                images = []
                if hasattr(page, 'images'):
                    for i, img in enumerate(page.images):
                        images.append({
                            "index": i,
                            "page_number": page_num + 1,
                            "bbox": img.get('bbox', []),
                            "width": img.get('width', 0),
                            "height": img.get('height', 0),
                            "note": "Image metadata only (use PyMuPDF for full extraction)"
                        })
                
                structure_info = {
                    "bbox": page.bbox,
                    "width": page.width,
                    "height": page.height,
                    "rotation": getattr(page, 'rotation', 0)
                }
                
                extracted_pages.append(ExtractedContent(
                    text=text,
                    images=images,
                    tables=tables,
                    metadata={"pdf_path": str(pdf_path), "total_pages": len(pdf.pages)},
                    method_used=ProcessingMethod.PDFPLUMBER,
                    page_number=page_num + 1,
                    structure_info=structure_info
                ))
        
        return extracted_pages
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> List[ExtractedContent]:
        """Extract content using PyPDF2 (basic text extraction)."""
        extracted_pages = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                except Exception:
                    text = ""
                
                # Basic metadata
                structure_info = {
                    "mediabox": page.mediabox if hasattr(page, 'mediabox') else None,
                    "rotation": page.get('/Rotate', 0)
                }
                
                extracted_pages.append(ExtractedContent(
                    text=text,
                    images=[],  # PyPDF2 doesn't handle images
                    tables=[],  # PyPDF2 doesn't handle tables
                    metadata={"pdf_path": str(pdf_path), "total_pages": len(pdf_reader.pages)},
                    method_used=ProcessingMethod.PYPDF2,
                    page_number=page_num + 1,
                    structure_info=structure_info
                ))
        
        return extracted_pages
    
    def _validate_extraction(self, content: List[ExtractedContent]) -> bool:
        """Validate that extraction produced meaningful content."""
        if not content:
            return False
        
        # Check if at least 50% of pages have meaningful text (>50 chars)
        meaningful_pages = sum(1 for page in content if len(page.text.strip()) > 50)
        return meaningful_pages >= len(content) * 0.5
    
    def _extract_font_info(self, text_dict: Dict[str, Any]) -> List[str]:
        """Extract font information from PyMuPDF text dictionary."""
        fonts = set()
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        if "font" in span:
                            fonts.add(span["font"])
        return list(fonts)
    
    def _detect_tables_pymupdf(self, page) -> List[List[List[str]]]:
        """Table detection using modern PyMuPDF API."""
        tables = []
        try:
            # Use find_tables method available in newer PyMuPDF versions
            if hasattr(page, 'find_tables'):
                table_finder = page.find_tables()
                for table in table_finder:
                    tables.append(table.extract())
        except Exception as e:
            logger.debug(f"Table extraction failed: {e}")
            # Fallback: no table extraction
            pass
        return tables
    
    def get_processing_stats(self) -> Dict[str, Dict[str, int]]:
        """Get processing statistics for different methods."""
        return dict(self.processing_stats)
    
    def create_content_metadata(self, pdf_path: Path, page_content: ExtractedContent, 
                               chapter_info: Optional[Dict[str, str]] = None) -> ContentMetadata:
        """Create rich metadata for extracted content."""
        
        # Determine source directory and file name
        source_directory = pdf_path.parent.name
        file_name = pdf_path.name
        
        # Initialize metadata builder
        builder = MetadataBuilder(source_directory, file_name)
        
        # Create document info
        doc_info = DocumentInfo(
            source_file=str(pdf_path),
            document_title=page_content.metadata.get("title", file_name),
            total_pages=page_content.metadata.get("total_pages", 1),
            processing_method=page_content.method_used.value,
            source_directory=source_directory
        )
        
        # Create structural info
        structural_info = StructuralInfo(
            page_number=page_content.page_number,
            word_count=len(page_content.text.split()) if page_content.text else 0
        )
        
        # Add chapter information if available
        if chapter_info:
            structural_info.chapter_title = chapter_info.get("title")
            structural_info.chapter_number = chapter_info.get("number")
            
            # Map chapter to ADM phase if applicable
            if chapter_info.get("title"):
                adm_phase = TOGAFContentMapper.map_chapter_to_adm_phase(chapter_info["title"])
                if adm_phase:
                    from .metadata_schema import TOGAFPhase
                    try:
                        phase_enum = TOGAFPhase(adm_phase)
                        builder.add_semantic_info(adm_phases=[phase_enum])
                    except ValueError:
                        pass
        
        # Determine content type based on content characteristics
        content_type = self._determine_content_type(page_content)
        
        # Determine difficulty level
        difficulty = self._determine_difficulty_level(source_directory, file_name, chapter_info)
        
        # Set content classification
        builder.set_content_info(content_type, difficulty)
        
        # Add key concepts if foundation part
        if source_directory == "core_topics":
            foundation_part = builder._map_foundation_file(file_name)
            if foundation_part:
                key_concepts = TOGAFContentMapper.get_key_concepts(foundation_part)
                builder.add_semantic_info(key_concepts=key_concepts)
        
        # Build and return metadata
        return builder.build(doc_info, structural_info)
    
    def _determine_content_type(self, page_content: ExtractedContent) -> ContentType:
        """Determine content type using dictionary mapping approach."""
        text_lower = page_content.text.lower() if page_content.text else ""
        
        # Priority checks first (non-text based)
        if page_content.images:
            return ContentType.DIAGRAM
        elif page_content.tables:
            return ContentType.TABLE
        
        # Dictionary mapping for text-based detection (compound conditions)
        compound_patterns = {
            ContentType.READINESS_ASSESSMENT: ["assessment", "readiness"],
            ContentType.MATURITY_MODEL: ["maturity", "model"],
        }
        
        # Check compound patterns first (more specific)
        for content_type, patterns in compound_patterns.items():
            if all(pattern in text_lower for pattern in patterns):
                return content_type
        
        # Simple pattern mapping
        simple_patterns = {
            ContentType.REFERENCE_MODEL: ["reference model"],
            ContentType.DEFINITION: ["definition", "means"],
            ContentType.CHECKLIST: ["checklist", "check list"],
            ContentType.EXAMPLE: ["example", "for example"],
            ContentType.DELIVERABLE: ["deliverable"],
            ContentType.TECHNIQUE: ["technique", "method"],
            ContentType.PATTERN: ["pattern"],
            ContentType.FRAMEWORK: ["framework"],
            ContentType.METAMODEL: ["metamodel"],
        }
        
        # Check simple patterns
        for content_type, patterns in simple_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return content_type
        
        return ContentType.CONCEPT
    
    def _determine_difficulty_level(self, source_directory: str, file_name: str, 
                                   chapter_info: Optional[Dict[str, str]] = None) -> DifficultyLevel:
        """Determine difficulty level based on source and content."""
        
        # Practitioner guides are generally intermediate to advanced
        if source_directory == "extended_topics":
            return DifficultyLevel.INTERMEDIATE
        
        # Foundation parts - use content mapper if available
        if source_directory == "core_topics" and chapter_info:
            builder = MetadataBuilder(source_directory, file_name)
            foundation_part = builder._map_foundation_file(file_name)
            if foundation_part:
                chapter_title = chapter_info.get("title", "")
                difficulty = TOGAFContentMapper.get_difficulty_level(foundation_part, chapter_title)
                return DifficultyLevel(difficulty)
        
        return DifficultyLevel.BASIC