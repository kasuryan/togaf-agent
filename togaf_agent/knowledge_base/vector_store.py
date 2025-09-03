"""ChromaDB vector store with metadata-driven search for TOGAF content."""

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
from pathlib import Path
import uuid

from ..utils.config import Settings
from .metadata_schema import CertificationLevel, ContentType, DifficultyLevel

logger = logging.getLogger(__name__)


class TOGAFVectorStore:
    """ChromaDB vector store optimized for TOGAF content with metadata filtering."""
    
    def __init__(self, settings: Settings):
        """Initialize ChromaDB with TOGAF-specific configuration."""
        self.settings = settings
        self.persist_directory = settings.chroma_persist_directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create collections for different TOGAF content types
        self.collections = {
            "foundation": self._get_or_create_collection("togaf_foundation"),
            "practitioner": self._get_or_create_collection("togaf_practitioner"),
            "assessments": self._get_or_create_collection("togaf_assessments")
        }
        
        logger.info(f"Initialized TOGAF vector store at {self.persist_directory}")
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        try:
            collection = self.client.get_collection(name=name)
            logger.debug(f"Retrieved existing collection: {name}")
        except (ValueError, Exception):  # Catch both ValueError and NotFoundError
            collection = self.client.create_collection(
                name=name,
                metadata={"description": f"TOGAF {name.split('_')[1].title()} content embeddings"}
            )
            logger.info(f"Created new collection: {name}")
        
        return collection
    
    def add_embedding_records(self, embedding_records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Add embedding records to appropriate collections with metadata.
        
        Args:
            embedding_records: List of embedding records with metadata
            
        Returns:
            Dictionary with counts of records added to each collection
        """
        stats = {"foundation": 0, "practitioner": 0, "assessments": 0}
        
        for record in embedding_records:
            try:
                # Determine which collection to use
                collection_name = self._determine_collection(record)
                collection = self.collections[collection_name]
                
                # Prepare data for ChromaDB
                chunk_id = record["chunk_id"]
                embedding_vector = record["embedding_vector"]
                document_text = record["text"]
                
                # Prepare metadata (ChromaDB has limitations on nested objects)
                metadata = self._flatten_metadata_for_chroma(record)
                
                # Add to collection
                collection.add(
                    embeddings=[embedding_vector],
                    documents=[document_text],
                    metadatas=[metadata],
                    ids=[chunk_id]
                )
                
                stats[collection_name] += 1
                logger.debug(f"Added chunk {chunk_id} to {collection_name} collection")
                
            except Exception as e:
                logger.error(f"Error adding record {record.get('chunk_id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Added records to collections: {stats}")
        return stats
    
    def _determine_collection(self, record: Dict[str, Any]) -> str:
        """Determine which collection a record belongs to."""
        metadata = record.get("metadata", {})
        
        # Check if it's assessment content
        if "assessment" in record.get("chunk_type", "").lower():
            return "assessments"
        
        # Check certification level from metadata
        cert_level = metadata.get("certification_level")
        if cert_level == "foundation":
            return "foundation"
        elif cert_level == "practitioner":
            return "practitioner"
        
        # Default to foundation for unknown content
        return "foundation"
    
    def _flatten_metadata_for_chroma(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten metadata for ChromaDB storage (it doesn't support nested objects well).
        """
        metadata = record.get("metadata", {})
        flattened = {}
        
        # Core identifiers
        flattened["chunk_id"] = record["chunk_id"]
        flattened["content_hash"] = record["content_hash"]
        flattened["chunk_type"] = record["chunk_type"]
        
        # Basic properties
        flattened["word_count"] = record["word_count"]
        flattened["char_count"] = record["char_count"]
        flattened["start_page"] = record["start_page"]
        flattened["end_page"] = record["end_page"]
        
        # Content characteristics
        flattened["has_images"] = record["has_images"]
        flattened["has_tables"] = record["has_tables"]
        flattened["image_count"] = record["image_count"]
        flattened["table_count"] = record["table_count"]
        
        # Metadata fields (flattened)
        flattened["certification_level"] = metadata.get("certification_level", "unknown")
        flattened["content_type"] = metadata.get("content_type", "unknown")
        flattened["difficulty_level"] = metadata.get("difficulty_level", "unknown")
        flattened["document_title"] = metadata.get("document_title", "")
        
        # Document info (flattened)
        doc_info = metadata.get("document_info", {})
        flattened["source_file"] = doc_info.get("source_file", "")
        flattened["source_directory"] = doc_info.get("source_directory", "")
        flattened["togaf_part"] = doc_info.get("togaf_part", "")
        flattened["togaf_guide_id"] = doc_info.get("togaf_guide_id", "")
        
        # Structural info (flattened)  
        structural_info = metadata.get("structural_info", {})
        flattened["page_number"] = structural_info.get("page_number", 0)
        flattened["chapter_title"] = structural_info.get("chapter_title", "")
        flattened["section_title"] = structural_info.get("section_title", "")
        flattened["chapter_number"] = structural_info.get("chapter_number", "")
        
        # Semantic info (flattened)
        semantic_info = metadata.get("semantic_info", {})
        flattened["foundation_part"] = semantic_info.get("foundation_part", "")
        flattened["practitioner_guide"] = semantic_info.get("practitioner_guide", "")
        
        # Key concepts as comma-separated string
        key_concepts = semantic_info.get("key_concepts", [])
        if key_concepts:
            flattened["key_concepts"] = ",".join(key_concepts)
        
        # ADM phases as comma-separated string
        adm_phases = semantic_info.get("adm_phases", [])
        if adm_phases:
            flattened["adm_phases"] = ",".join([phase["value"] if isinstance(phase, dict) else str(phase) for phase in adm_phases])
        
        # Search tags as comma-separated string
        search_tags = record.get("search_tags", [])
        if search_tags:
            flattened["search_tags"] = ",".join(search_tags)
        
        # Quality scores
        flattened["content_quality_score"] = record.get("content_quality_score", 1.0)
        flattened["extraction_confidence"] = record.get("extraction_confidence", 1.0)
        
        # Embedding info
        flattened["embedding_model"] = record.get("embedding_model", "")
        flattened["embedding_dimensions"] = record.get("embedding_dimensions", 0)
        
        return flattened
    
    def search(self, query_text: str, query_embedding: List[float] = None, 
               n_results: int = 10, filters: Dict[str, Any] = None,
               collections: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant content across TOGAF collections.
        
        Args:
            query_text: Text query for semantic search
            query_embedding: Pre-computed query embedding (optional)
            n_results: Number of results to return
            filters: Metadata filters to apply
            collections: Specific collections to search (default: all)
            
        Returns:
            List of search results with metadata and scores
        """
        if collections is None:
            collections = list(self.collections.keys())
        
        all_results = []
        
        for collection_name in collections:
            try:
                collection = self.collections[collection_name]
                
                # Build ChromaDB where clause from filters
                where_clause = self._build_where_clause(filters) if filters else None
                
                # Perform search
                if query_embedding:
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=n_results,
                        where=where_clause,
                        include=["documents", "metadatas", "distances"]
                    )
                else:
                    results = collection.query(
                        query_texts=[query_text],
                        n_results=n_results,
                        where=where_clause,
                        include=["documents", "metadatas", "distances"]
                    )
                
                # Process results
                for i in range(len(results["documents"][0])):
                    result = {
                        "collection": collection_name,
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "relevance_score": 1 - results["distances"][0][i],  # Convert distance to relevance
                        "chunk_id": results["ids"][0][i] if "ids" in results else None
                    }
                    all_results.append(result)
                    
            except Exception as e:
                logger.error(f"Error searching collection {collection_name}: {e}")
                continue
        
        # Sort by relevance score and return top results
        all_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return all_results[:n_results]
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build ChromaDB where clause from filters."""
        conditions = []
        
        # Map common filter keys to ChromaDB metadata keys
        filter_mapping = {
            "certification_level": "certification_level",
            "content_type": "content_type", 
            "difficulty_level": "difficulty_level",
            "has_images": "has_images",
            "has_tables": "has_tables",
            "source_directory": "source_directory",
            "togaf_part": "togaf_part",
            "foundation_part": "foundation_part",
            "practitioner_guide": "practitioner_guide"
        }
        
        # Build individual conditions
        for filter_key, value in filters.items():
            if filter_key in filter_mapping:
                chroma_key = filter_mapping[filter_key]
                conditions.append({chroma_key: {"$eq": value}})
        
        # Handle special cases for word count
        if "min_word_count" in filters:
            conditions.append({"word_count": {"$gte": filters["min_word_count"]}})
        
        if "max_word_count" in filters:
            conditions.append({"word_count": {"$lte": filters["max_word_count"]}})
        
        # Return appropriate where clause format
        if len(conditions) == 0:
            return {}
        elif len(conditions) == 1:
            # Single condition - return directly
            return conditions[0]
        else:
            # Multiple conditions - use $and operator
            return {"$and": conditions}
    
    def get_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all collections."""
        stats = {}
        
        for name, collection in self.collections.items():
            try:
                count = collection.count()
                stats[name] = {
                    "document_count": count,
                    "name": name
                }
            except Exception as e:
                logger.error(f"Error getting stats for collection {name}: {e}")
                stats[name] = {"document_count": 0, "error": str(e)}
        
        return stats
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection and recreate it empty."""
        try:
            self.client.delete_collection(name=f"togaf_{collection_name}")
            self.collections[collection_name] = self._get_or_create_collection(f"togaf_{collection_name}")
            logger.info(f"Deleted and recreated collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
            return False
    
    def reset_all_collections(self) -> bool:
        """Reset all collections (useful for development)."""
        try:
            for collection_name in self.collections.keys():
                self.delete_collection(collection_name)
            logger.info("Reset all collections")
            return True
        except Exception as e:
            logger.error(f"Error resetting collections: {e}")
            return False
    
    def close(self):
        """Close the ChromaDB client."""
        # ChromaDB automatically persists data, no explicit close needed
        logger.info("ChromaDB client closed")


class MetadataSearchBuilder:
    """Helper class to build search queries with TOGAF-specific metadata filters."""
    
    @staticmethod
    def foundation_only() -> Dict[str, Any]:
        """Filter for Foundation content only."""
        return {"certification_level": "foundation"}
    
    @staticmethod  
    def practitioner_only() -> Dict[str, Any]:
        """Filter for Practitioner content only."""
        return {"certification_level": "practitioner"}
    
    @staticmethod
    def difficulty_level(level: DifficultyLevel) -> Dict[str, Any]:
        """Filter by difficulty level."""
        return {"difficulty_level": level.value}
    
    @staticmethod
    def content_type(content_type: ContentType) -> Dict[str, Any]:
        """Filter by content type."""
        return {"content_type": content_type.value}
    
    @staticmethod
    def with_images() -> Dict[str, Any]:
        """Filter for content with images/diagrams."""
        return {"has_images": True}
    
    @staticmethod
    def with_tables() -> Dict[str, Any]:
        """Filter for content with tables."""
        return {"has_tables": True}
    
    @staticmethod
    def foundation_part(part: str) -> Dict[str, Any]:
        """Filter by specific Foundation part."""
        return {
            "certification_level": "foundation",
            "foundation_part": part
        }
    
    @staticmethod
    def practitioner_guide(guide: str) -> Dict[str, Any]:
        """Filter by specific Practitioner guide.""" 
        return {
            "certification_level": "practitioner",
            "practitioner_guide": guide
        }
    
    @staticmethod
    def combine_filters(**filters) -> Dict[str, Any]:
        """Combine multiple filters."""
        return filters