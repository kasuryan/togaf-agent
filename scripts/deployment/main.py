"""Main entry point for TOGAF Agent."""

import asyncio
from pathlib import Path
from togaf_agent.utils.config import load_settings, ensure_directories
from togaf_agent.knowledge_base.pdf_processor import PDFProcessor


async def main():
    """Main function to initialize and run TOGAF Agent."""
    print("🚀 Starting TOGAF Agent...")
    
    # Load configuration
    settings = load_settings()
    ensure_directories(settings)
    
    print(f"📁 Data directory: {settings.data_dir}")
    print(f"👤 Users directory: {settings.users_dir}")
    print(f"🧠 Knowledge base directory: {settings.knowledge_base_dir}")
    
    # Initialize PDF processor
    pdf_processor = PDFProcessor(
        extract_images=True,
        save_images=True,
        image_dir=settings.knowledge_base_dir / "images"
    )
    
    print("✅ TOGAF Agent initialized successfully!")
    print("📚 Ready to process TOGAF documents and serve users.")
    
    # TODO: Add more initialization logic here
    # - Process PDFs if not already done
    # - Initialize ChromaDB
    # - Start conversation interface


def cli_main():
    """CLI entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
