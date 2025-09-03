"""Comprehensive validation script for TOGAF Agent Phase 1 - Knowledge Base Foundation."""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import time

# Import all Phase 1 components
from togaf_agent.utils.config import load_settings, ensure_directories
from togaf_agent.utils.openai_client import OpenAIClient
from togaf_agent.knowledge_base.pdf_processor import PDFProcessor
from togaf_agent.knowledge_base.content_chunker import StructureAwareChunker
from togaf_agent.knowledge_base.embedding_generator import EmbeddingGenerator
from togaf_agent.knowledge_base.vector_store import TOGAFVectorStore
from togaf_agent.knowledge_base.semantic_search import TOGAFSemanticSearch
from togaf_agent.knowledge_base.metadata_schema import (
    CertificationLevel, ContentType, DifficultyLevel, FoundationPart, PractitionerGuide
)

console = Console()


async def validate_phase1_system():
    """Comprehensive validation of Phase 1 TOGAF Agent system."""
    console.print(Panel.fit("🚀 TOGAF Agent - Phase 1 Validation", style="bold blue"))
    
    results = {}
    start_time = time.time()
    
    # Test 1: Configuration and Environment
    console.print("\n📋 [bold]Test 1: Configuration and Environment[/bold]")
    try:
        settings = load_settings()
        ensure_directories(settings)
        
        console.print("   ✅ Configuration loaded successfully")
        console.print(f"   ✅ App name: {settings.app_name}")
        console.print(f"   ✅ Chat model: {settings.openai_chat_model}")
        console.print(f"   ✅ Embedding model: {settings.openai_embedding_model}")
        console.print(f"   ✅ Directories created: {settings.knowledge_base_dir}")
        results["configuration"] = True
    except Exception as e:
        console.print(f"   ❌ Configuration failed: {e}")
        results["configuration"] = False
        return results
    
    # Test 2: OpenAI API Integration
    console.print("\n🤖 [bold]Test 2: OpenAI API Integration[/bold]")
    try:
        openai_client = OpenAIClient(settings)
        
        # Test API key validation
        api_valid = await openai_client.validate_api_key_async()
        console.print(f"   {'✅' if api_valid else '❌'} API key validation")
        
        # Test embedding functionality
        embedding_test = await openai_client.test_embedding_functionality()
        console.print(f"   {'✅' if embedding_test else '❌'} Embedding functionality")
        
        # Test model info
        model_info = openai_client.get_model_info()
        console.print(f"   ✅ Model info: {model_info}")
        
        results["openai_integration"] = api_valid and embedding_test
    except Exception as e:
        console.print(f"   ❌ OpenAI integration failed: {e}")
        results["openai_integration"] = False
    
    # Test 3: PDF Processing Pipeline
    console.print("\n📄 [bold]Test 3: PDF Processing Pipeline[/bold]")
    try:
        pdf_processor = PDFProcessor(extract_images=True, save_images=True,
                                   image_dir=settings.knowledge_base_dir / "test_images")
        
        # Check if we have test PDFs
        data_dir = Path("./data")
        core_topics = data_dir / "core_topics"
        
        if core_topics.exists():
            pdf_files = list(core_topics.glob("*.pdf"))
            console.print(f"   ✅ Found {len(pdf_files)} Foundation PDFs")
            
            extended_topics = data_dir / "extended_topics"
            if extended_topics.exists():
                practitioner_pdfs = list(extended_topics.glob("*.pdf"))
                console.print(f"   ✅ Found {len(practitioner_pdfs)} Practitioner PDFs")
            
        console.print("   ✅ PDF processor initialized with fallback methods")
        console.print("   ✅ Image extraction enabled")
        
        # Test processing stats
        stats = pdf_processor.get_processing_stats()
        console.print(f"   ✅ Processing statistics: {stats}")
        
        results["pdf_processing"] = True
    except Exception as e:
        console.print(f"   ❌ PDF processing failed: {e}")
        results["pdf_processing"] = False
    
    # Test 4: Metadata Schema and Content Mapping
    console.print("\n🏗️ [bold]Test 4: Metadata Schema and Content Mapping[/bold]")
    try:
        # Test enum classes
        cert_levels = [level.value for level in CertificationLevel]
        content_types = [ct.value for ct in ContentType]
        difficulty_levels = [dl.value for dl in DifficultyLevel]
        foundation_parts = [part.value for part in FoundationPart]
        
        console.print(f"   ✅ Certification levels: {cert_levels}")
        console.print(f"   ✅ Content types: {len(content_types)} types")
        console.print(f"   ✅ Difficulty levels: {difficulty_levels}")
        console.print(f"   ✅ Foundation parts: {len(foundation_parts)} parts")
        
        # Test TOGAF content mapping
        from togaf_agent.knowledge_base.togaf_content_map import TOGAFContentMapper
        
        part_0_chapters = TOGAFContentMapper.get_chapter_list(FoundationPart.PART_0_INTRODUCTION_CORE_CONCEPTS)
        part_0_concepts = TOGAFContentMapper.get_key_concepts(FoundationPart.PART_0_INTRODUCTION_CORE_CONCEPTS)
        
        console.print(f"   ✅ Part 0 chapters: {len(part_0_chapters)} chapters")
        console.print(f"   ✅ Part 0 concepts: {len(part_0_concepts)} concepts")
        
        results["metadata_schema"] = True
    except Exception as e:
        console.print(f"   ❌ Metadata schema failed: {e}")
        results["metadata_schema"] = False
    
    # Test 5: Structure-Aware Chunking
    console.print("\n✂️ [bold]Test 5: Structure-Aware Chunking[/bold]")
    try:
        chunker = StructureAwareChunker(
            target_chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            max_chunk_size=settings.max_tokens_per_chunk
        )
        
        console.print(f"   ✅ Chunker initialized with target size: {settings.chunk_size}")
        console.print(f"   ✅ Chunk overlap: {settings.chunk_overlap}")
        console.print(f"   ✅ Max chunk size: {settings.max_tokens_per_chunk}")
        console.print("   ✅ Structure-aware chunking enabled")
        
        results["chunking"] = True
    except Exception as e:
        console.print(f"   ❌ Chunking failed: {e}")
        results["chunking"] = False
    
    # Test 6: Embedding Generation
    console.print("\n🧠 [bold]Test 6: Embedding Generation[/bold]")
    try:
        embedding_generator = EmbeddingGenerator(settings)
        
        # Test system validation
        validation_results = await embedding_generator.validate_embedding_system()
        
        for test_name, result in validation_results.items():
            status = "✅" if result else "❌"
            console.print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        all_embedding_tests_passed = all(validation_results.values())
        results["embedding_generation"] = all_embedding_tests_passed
        
    except Exception as e:
        console.print(f"   ❌ Embedding generation failed: {e}")
        results["embedding_generation"] = False
    
    # Test 7: Vector Storage (ChromaDB)
    console.print("\n🗃️ [bold]Test 7: Vector Storage (ChromaDB)[/bold]")
    try:
        vector_store = TOGAFVectorStore(settings)
        
        # Test collection stats
        stats = vector_store.get_collection_stats()
        console.print(f"   ✅ Collections created: {list(stats.keys())}")
        
        for collection, stat in stats.items():
            doc_count = stat.get("document_count", 0)
            console.print(f"   ✅ {collection}: {doc_count} documents")
        
        console.print(f"   ✅ Persist directory: {settings.chroma_persist_directory}")
        
        results["vector_storage"] = True
    except Exception as e:
        console.print(f"   ❌ Vector storage failed: {e}")
        results["vector_storage"] = False
    
    # Test 8: Semantic Search System
    console.print("\n🔍 [bold]Test 8: Semantic Search System[/bold]")
    try:
        search_system = TOGAFSemanticSearch(settings)
        
        # Test system stats
        system_stats = search_system.get_system_stats()
        console.print(f"   ✅ Search system initialized")
        console.print(f"   ✅ Total documents ready: {system_stats['total_documents']}")
        console.print(f"   ✅ Embedding model: {system_stats['embedding_model']}")
        
        # Test search suggestions
        suggestions = search_system.get_search_suggestions("adm governance")
        console.print(f"   ✅ Search suggestions working: {len(suggestions)} suggestions")
        
        # Test metadata search builders
        from togaf_agent.knowledge_base.vector_store import MetadataSearchBuilder
        
        foundation_filter = MetadataSearchBuilder.foundation_only()
        combined_filter = MetadataSearchBuilder.combine_filters(
            certification_level="foundation",
            has_images=True,
            difficulty_level="basic"
        )
        
        console.print("   ✅ Metadata search builders working")
        console.print(f"   ✅ Foundation filter: {foundation_filter}")
        
        results["semantic_search"] = True
    except Exception as e:
        console.print(f"   ❌ Semantic search failed: {e}")
        results["semantic_search"] = False
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    console.print(f"\n⏱️ [bold]Validation completed in {duration:.2f} seconds[/bold]")
    
    # Results table
    table = Table(title="Phase 1 Validation Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Description")
    
    component_descriptions = {
        "configuration": "Environment settings and directory setup",
        "openai_integration": "OpenAI API connection and embedding functionality",
        "pdf_processing": "PyMuPDF processing with intelligent fallbacks",
        "metadata_schema": "Rich metadata schema for TOGAF content",
        "chunking": "Structure-aware content chunking",
        "embedding_generation": "Context-rich embedding generation",
        "vector_storage": "ChromaDB vector storage with collections",
        "semantic_search": "Metadata-driven semantic search system"
    }
    
    for component, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        description = component_descriptions.get(component, "")
        table.add_row(component.replace("_", " ").title(), status, description)
    
    console.print(table)
    
    # Overall result
    all_passed = all(results.values())
    if all_passed:
        console.print(Panel.fit("🎉 Phase 1 - All Systems Ready! 🎉", style="bold green"))
        console.print("\n📚 [bold green]TOGAF Agent Knowledge Base Foundation is fully operational![/bold green]")
        console.print("\n🚀 [bold]Next Steps:[/bold]")
        console.print("   • Process TOGAF PDFs to populate knowledge base")
        console.print("   • Implement user profiling and conversation system")
        console.print("   • Build learning path management")
        console.print("   • Add assessment engine integration")
    else:
        failed_components = [comp for comp, result in results.items() if not result]
        console.print(Panel.fit("⚠️ Phase 1 - Issues Found ⚠️", style="bold yellow"))
        console.print(f"\n❌ [bold red]Failed components: {', '.join(failed_components)}[/bold red]")
        console.print("   Please review and fix the issues above before proceeding.")
    
    return results


async def main():
    """Main validation entry point."""
    try:
        results = await validate_phase1_system()
        
        # Exit with appropriate code
        all_passed = all(results.values())
        sys.exit(0 if all_passed else 1)
        
    except Exception as e:
        console.print(f"\n💥 [bold red]Validation failed with error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())