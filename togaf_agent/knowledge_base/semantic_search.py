"""Metadata-driven semantic search system for TOGAF content."""

from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

from ..utils.config import Settings
from ..utils.openai_client import OpenAIClient
from .vector_store import TOGAFVectorStore, MetadataSearchBuilder
from .metadata_schema import CertificationLevel, ContentType, DifficultyLevel

logger = logging.getLogger(__name__)


@dataclass
class SearchQuery:
    """Structured search query with metadata filters."""
    text: str
    filters: Optional[Dict[str, Any]] = None
    certification_level: Optional[CertificationLevel] = None
    content_type: Optional[ContentType] = None
    difficulty_level: Optional[DifficultyLevel] = None
    n_results: int = 10
    include_images: Optional[bool] = None
    include_tables: Optional[bool] = None
    collections: Optional[List[str]] = None


@dataclass
class SearchResult:
    """Enhanced search result with TOGAF context."""
    chunk_id: str
    content: str
    relevance_score: float
    metadata: Dict[str, Any]
    collection: str
    certification_context: str
    content_summary: str
    key_concepts: List[str]
    chapter_context: Optional[str] = None
    adm_phases: List[str] = None


class TOGAFSemanticSearch:
    """Advanced semantic search system with TOGAF-specific intelligence."""
    
    def __init__(self, settings: Settings):
        """Initialize semantic search system."""
        self.settings = settings
        self.openai_client = OpenAIClient(settings)
        self.vector_store = TOGAFVectorStore(settings)
        
        logger.info("Initialized TOGAF semantic search system")
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Perform intelligent semantic search with metadata filtering.
        
        Args:
            query: Structured search query
            
        Returns:
            List of enhanced search results
        """
        logger.debug(f"Performing search: '{query.text[:50]}...'")
        
        # Generate query embedding
        query_embedding = await self.openai_client.create_embedding(query.text)
        
        # Build comprehensive filters
        filters = self._build_comprehensive_filters(query)
        
        # Perform vector search
        raw_results = self.vector_store.search(
            query_text=query.text,
            query_embedding=query_embedding,
            n_results=query.n_results,
            filters=filters,
            collections=query.collections
        )
        
        # Enhance results with TOGAF context
        enhanced_results = []
        for result in raw_results:
            enhanced_result = self._enhance_search_result(result, query.text)
            enhanced_results.append(enhanced_result)
        
        logger.info(f"Found {len(enhanced_results)} results for query")
        return enhanced_results
    
    def _build_comprehensive_filters(self, query: SearchQuery) -> Dict[str, Any]:
        """Build comprehensive filters from query parameters."""
        filters = query.filters.copy() if query.filters else {}
        
        # Add certification level filter
        if query.certification_level:
            filters["certification_level"] = query.certification_level.value
        
        # Add content type filter
        if query.content_type:
            filters["content_type"] = query.content_type.value
        
        # Add difficulty level filter
        if query.difficulty_level:
            filters["difficulty_level"] = query.difficulty_level.value
        
        # Add image filter
        if query.include_images is not None:
            filters["has_images"] = query.include_images
        
        # Add table filter
        if query.include_tables is not None:
            filters["has_tables"] = query.include_tables
        
        return filters
    
    def _enhance_search_result(self, raw_result: Dict[str, Any], query_text: str) -> SearchResult:
        """Enhance raw search result with TOGAF-specific context."""
        metadata = raw_result["metadata"]
        
        # Extract key information
        chunk_id = raw_result.get("chunk_id", "")
        content = raw_result["document"]
        relevance_score = raw_result["relevance_score"]
        collection = raw_result["collection"]
        
        # Build certification context
        cert_level = metadata.get("certification_level", "unknown")
        part_or_guide = metadata.get("foundation_part") or metadata.get("practitioner_guide", "")
        
        if cert_level == "foundation":
            certification_context = f"TOGAF Foundation - {part_or_guide.replace('_', ' ').title()}"
        elif cert_level == "practitioner":
            certification_context = f"TOGAF Practitioner - {part_or_guide.replace('_', ' ').title()}"
        else:
            certification_context = "TOGAF Content"
        
        # Build chapter context
        chapter_context = None
        chapter_title = metadata.get("chapter_title", "")
        section_title = metadata.get("section_title", "")
        
        if chapter_title and section_title:
            chapter_context = f"{chapter_title} → {section_title}"
        elif chapter_title:
            chapter_context = chapter_title
        
        # Extract key concepts
        key_concepts = []
        key_concepts_str = metadata.get("key_concepts", "")
        if key_concepts_str:
            key_concepts = [concept.strip() for concept in key_concepts_str.split(",")]
        
        # Extract ADM phases
        adm_phases = []
        adm_phases_str = metadata.get("adm_phases", "")
        if adm_phases_str:
            adm_phases = [phase.strip().replace("_", " ").title() for phase in adm_phases_str.split(",")]
        
        # Create content summary
        content_summary = self._create_content_summary(content, metadata)
        
        return SearchResult(
            chunk_id=chunk_id,
            content=content,
            relevance_score=relevance_score,
            metadata=metadata,
            collection=collection,
            certification_context=certification_context,
            content_summary=content_summary,
            key_concepts=key_concepts,
            chapter_context=chapter_context,
            adm_phases=adm_phases
        )
    
    def _create_content_summary(self, content: str, metadata: Dict[str, Any]) -> str:
        """Create a brief summary of the content."""
        # Get content type and characteristics
        content_type = metadata.get("content_type", "").replace("_", " ").title()
        has_images = metadata.get("has_images", False)
        has_tables = metadata.get("has_tables", False)
        word_count = metadata.get("word_count", 0)
        
        # Build summary components
        summary_parts = [content_type]
        
        if has_images:
            summary_parts.append("with diagrams")
        if has_tables:
            summary_parts.append("with tables")
        
        summary_parts.append(f"({word_count} words)")
        
        return " ".join(summary_parts)
    
    async def search_foundation_content(self, query_text: str, part: str = None, 
                                       difficulty: DifficultyLevel = None, n_results: int = 5) -> List[SearchResult]:
        """Convenience method for searching Foundation content."""
        filters = MetadataSearchBuilder.foundation_only()
        
        if part:
            filters.update(MetadataSearchBuilder.foundation_part(part))
        
        query = SearchQuery(
            text=query_text,
            filters=filters,
            difficulty_level=difficulty,
            n_results=n_results,
            collections=["foundation"]
        )
        
        return await self.search(query)
    
    async def search_practitioner_content(self, query_text: str, guide: str = None,
                                         difficulty: DifficultyLevel = None, n_results: int = 5) -> List[SearchResult]:
        """Convenience method for searching Practitioner content."""
        filters = MetadataSearchBuilder.practitioner_only()
        
        if guide:
            filters.update(MetadataSearchBuilder.practitioner_guide(guide))
        
        query = SearchQuery(
            text=query_text,
            filters=filters,
            difficulty_level=difficulty,
            n_results=n_results,
            collections=["practitioner"]
        )
        
        return await self.search(query)
    
    async def search_with_context(self, query_text: str, user_level: str = "beginner",
                                 user_goal: str = "foundation", n_results: int = 10) -> List[SearchResult]:
        """
        Context-aware search based on user profile.
        
        Args:
            query_text: Search query
            user_level: User skill level (beginner, intermediate, advanced)
            user_goal: User's certification goal (foundation, practitioner, both)
            n_results: Number of results to return
        """
        # Map user level to difficulty
        level_mapping = {
            "beginner": DifficultyLevel.BASIC,
            "intermediate": DifficultyLevel.INTERMEDIATE,
            "advanced": DifficultyLevel.ADVANCED
        }
        
        difficulty = level_mapping.get(user_level, DifficultyLevel.BASIC)
        
        # Map user goal to certification level
        if user_goal == "foundation":
            cert_level = CertificationLevel.FOUNDATION
            collections = ["foundation"]
        elif user_goal == "practitioner":
            cert_level = CertificationLevel.PRACTITIONER
            collections = ["practitioner"]
        else:  # both
            cert_level = None
            collections = ["foundation", "practitioner"]
        
        query = SearchQuery(
            text=query_text,
            certification_level=cert_level,
            difficulty_level=difficulty,
            n_results=n_results,
            collections=collections
        )
        
        return await self.search(query)
    
    async def find_related_content(self, chunk_id: str, n_results: int = 5) -> List[SearchResult]:
        """Find content related to a specific chunk."""
        # This would require retrieving the chunk first, then searching for similar content
        # Implementation depends on having chunk retrieval capability
        logger.warning("find_related_content not fully implemented - requires chunk retrieval")
        return []
    
    def get_search_suggestions(self, query_text: str) -> List[str]:
        """Get search suggestions based on TOGAF concepts."""
        suggestions = []
        
        # Common TOGAF search terms and their expansions
        togaf_concepts = {
            "adm": ["Architecture Development Method", "ADM phases", "ADM guidelines"],
            "architecture": ["Business Architecture", "Data Architecture", "Application Architecture", "Technology Architecture"],
            "governance": ["Architecture Governance", "Architecture Board", "Architecture Compliance"],
            "stakeholder": ["Stakeholder Management", "Stakeholder Requirements", "Stakeholder Concerns"],
            "gap": ["Gap Analysis", "Architecture Gap", "Solution Gap"],
            "migration": ["Migration Planning", "Implementation Migration", "Transition Architecture"]
        }
        
        query_lower = query_text.lower()
        for key, expansions in togaf_concepts.items():
            if key in query_lower:
                suggestions.extend(expansions)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        collection_stats = self.vector_store.get_collection_stats()
        
        return {
            "collections": collection_stats,
            "embedding_model": self.settings.openai_embedding_model,
            "vector_store_path": str(self.settings.chroma_persist_directory),
            "total_documents": sum(stats.get("document_count", 0) for stats in collection_stats.values())
        }