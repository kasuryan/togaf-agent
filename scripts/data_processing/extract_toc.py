"""Script to extract Table of Contents from TOGAF PDFs using PyMuPDF."""

import pymupdf
from pathlib import Path
import json
import re
from typing import Dict, List, Any


def extract_pdf_toc(pdf_path: Path) -> Dict[str, Any]:
    """Extract table of contents and document info from a PDF."""
    try:
        doc = pymupdf.open(pdf_path)
        
        # Get document metadata
        metadata = doc.metadata
        doc_info = {
            "file_name": pdf_path.name,
            "file_path": str(pdf_path),
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "total_pages": len(doc),
        }
        
        # Get table of contents
        toc = doc.get_toc()
        
        # Process TOC entries
        toc_entries = []
        for entry in toc:
            level, title, page = entry
            toc_entries.append({
                "level": level,
                "title": title.strip(),
                "page": page
            })
        
        # Get first page text to extract title
        if len(doc) > 0:
            first_page_text = doc[0].get_text()
            # Try to extract title from first page
            lines = first_page_text.split('\n')
            title_candidates = []
            for line in lines[:20]:  # Check first 20 lines
                line = line.strip()
                if line and len(line) > 10 and not line.startswith('©'):
                    title_candidates.append(line)
            
            if title_candidates:
                doc_info["extracted_title"] = title_candidates[0]
        
        doc.close()
        
        return {
            "document_info": doc_info,
            "table_of_contents": toc_entries
        }
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return None


def analyze_directory(directory: Path, output_file: str):
    """Analyze all PDFs in a directory and extract their TOCs."""
    results = {
        "directory": str(directory),
        "documents": []
    }
    
    pdf_files = list(directory.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {directory}")
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        toc_data = extract_pdf_toc(pdf_file)
        if toc_data:
            results["documents"].append(toc_data)
    
    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_file}")
    return results


def main():
    """Main function to extract TOC from both directories."""
    data_dir = Path("./data")
    
    # Process core_topics (Foundation)
    core_topics_dir = data_dir / "core_topics"
    if core_topics_dir.exists():
        print("=" * 50)
        print("PROCESSING FOUNDATION TOPICS (core_topics)")
        print("=" * 50)
        foundation_results = analyze_directory(core_topics_dir, "scripts/data_processing/foundation_toc.json")
        
        # Print summary
        print(f"\nFOUNDATION DOCUMENTS FOUND:")
        for doc in foundation_results["documents"]:
            title = doc["document_info"].get("extracted_title", doc["document_info"]["file_name"])
            print(f"  - {title}")
            print(f"    File: {doc['document_info']['file_name']}")
            print(f"    Pages: {doc['document_info']['total_pages']}")
            print(f"    TOC Entries: {len(doc['table_of_contents'])}")
            print()
    
    # Process extended_topics (Practitioner)
    extended_topics_dir = data_dir / "extended_topics"
    if extended_topics_dir.exists():
        print("=" * 50)
        print("PROCESSING PRACTITIONER TOPICS (extended_topics)")
        print("=" * 50)
        practitioner_results = analyze_directory(extended_topics_dir, "scripts/data_processing/practitioner_toc.json")
        
        # Print summary
        print(f"\nPRACTITIONER DOCUMENTS FOUND:")
        for doc in practitioner_results["documents"]:
            title = doc["document_info"].get("extracted_title", doc["document_info"]["file_name"])
            print(f"  - {title}")
            print(f"    File: {doc['document_info']['file_name']}")
            print(f"    Pages: {doc['document_info']['total_pages']}")
            print(f"    TOC Entries: {len(doc['table_of_contents'])}")
            print()


if __name__ == "__main__":
    main()