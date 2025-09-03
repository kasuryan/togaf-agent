"""Analyze extracted TOC data to understand TOGAF document structure."""

import json
from pathlib import Path


def analyze_foundation_documents():
    """Analyze foundation documents structure."""
    print("=" * 80)
    print("FOUNDATION DOCUMENTS ANALYSIS (core_topics)")
    print("=" * 80)
    
    with open("scripts/data_processing/foundation_toc.json", 'r') as f:
        data = json.load(f)
    
    documents = []
    for doc in data["documents"]:
        doc_info = doc["document_info"]
        file_name = doc_info["file_name"]
        
        # Map file names to actual document parts
        part_mapping = {
            "C220-Part0e.pdf": "Part 0: Introduction and Core Concepts",
            "C220-Part1e.pdf": "Part 1: Architecture Development Method",
            "C220-Part2e.pdf": "Part 2: ADM Techniques", 
            "C220-Part3e.pdf": "Part 3: Applying the ADM",
            "C220-Part4e.pdf": "Part 4: Architecture Content",
            "C220-Part5e.pdf": "Part 5: Enterprise Architecture Capability and Governance"
        }
        
        part_title = part_mapping.get(file_name, doc_info.get("title", file_name))
        
        # Get main chapters from TOC
        main_chapters = []
        for toc_entry in doc["table_of_contents"]:
            if toc_entry["level"] <= 2 and not toc_entry["title"].lower().startswith(("contents", "preface", "trademarks")):
                title = toc_entry["title"]
                if not title.startswith(("ADM-", "Part")):  # Skip meta entries
                    main_chapters.append(title)
        
        documents.append({
            "file": file_name,
            "part": part_title,
            "title": doc_info.get("title", ""),
            "pages": doc_info["total_pages"],
            "main_chapters": main_chapters[:10]  # First 10 chapters
        })
        
        print(f"\n{part_title}")
        print(f"  File: {file_name}")
        print(f"  Official Title: {doc_info.get('title', 'N/A')}")
        print(f"  Pages: {doc_info['total_pages']}")
        print(f"  Main Chapters:")
        for chapter in main_chapters[:8]:
            print(f"    • {chapter}")
        print()
    
    return documents


def analyze_practitioner_documents():
    """Analyze practitioner documents structure."""
    print("=" * 80)
    print("PRACTITIONER DOCUMENTS ANALYSIS (extended_topics)")
    print("=" * 80)
    
    with open("scripts/data_processing/practitioner_toc.json", 'r') as f:
        data = json.load(f)
    
    documents = []
    for doc in data["documents"]:
        doc_info = doc["document_info"]
        file_name = doc_info["file_name"]
        title = doc_info.get("title", "Unknown")
        
        # Get main chapters from TOC
        main_chapters = []
        for toc_entry in doc["table_of_contents"]:
            if toc_entry["level"] <= 2 and not toc_entry["title"].lower().startswith(("contents", "preface", "trademarks", "acknowledgements")):
                chapter_title = toc_entry["title"]
                if len(chapter_title) > 5:  # Skip very short titles
                    main_chapters.append(chapter_title)
        
        documents.append({
            "file": file_name,
            "title": title,
            "pages": doc_info["total_pages"],
            "main_chapters": main_chapters[:8]  # First 8 chapters
        })
        
        # Extract key topic from title
        topic = "Unknown"
        if "Risk and Security" in title:
            topic = "Risk and Security Integration"
        elif "Business Scenarios" in title:
            topic = "Business Scenarios"
        elif "Stakeholder Management" in title:
            topic = "Stakeholder Management"
        elif "Gap Analysis" in title:
            topic = "Gap Analysis"
        elif "Migration Planning" in title:
            topic = "Migration Planning"
        # Add more mappings as needed
        
        print(f"\n{topic}")
        print(f"  File: {file_name}")
        print(f"  Full Title: {title}")
        print(f"  Pages: {doc_info['total_pages']}")
        if main_chapters:
            print(f"  Key Chapters:")
            for chapter in main_chapters[:5]:
                print(f"    • {chapter}")
        print()
    
    return documents


def generate_metadata_enums():
    """Generate proper enum classes based on actual content."""
    print("=" * 80)
    print("SUGGESTED METADATA ENUMS")
    print("=" * 80)
    
    print("""
# Foundation Topics (based on 6 PDF parts in core_topics)
class FoundationPart(Enum):
    PART_0_INTRODUCTION_CORE_CONCEPTS = "part_0_introduction_core_concepts"
    PART_1_ARCHITECTURE_DEVELOPMENT_METHOD = "part_1_architecture_development_method" 
    PART_2_ADM_TECHNIQUES = "part_2_adm_techniques"
    PART_3_APPLYING_ADM = "part_3_applying_adm"
    PART_4_ARCHITECTURE_CONTENT = "part_4_architecture_content"
    PART_5_ENTERPRISE_CAPABILITY_GOVERNANCE = "part_5_enterprise_capability_governance"

# Practitioner Topics (based on extended_topics TOGAF Series Guides)
class PractitionerGuide(Enum):
    # These should be extracted from actual titles in practitioner_toc.json
    RISK_SECURITY_INTEGRATION = "risk_security_integration"
    BUSINESS_SCENARIOS = "business_scenarios"
    STAKEHOLDER_MANAGEMENT = "stakeholder_management"
    # ... add more based on actual document analysis
    """)


def main():
    """Main analysis function."""
    foundation_docs = analyze_foundation_documents()
    practitioner_docs = analyze_practitioner_documents()
    generate_metadata_enums()
    
    # Save analysis results
    analysis_results = {
        "foundation_documents": foundation_docs,
        "practitioner_documents": practitioner_docs
    }
    
    with open("toc_analysis.json", 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    print(f"\nAnalysis saved to: toc_analysis.json")


if __name__ == "__main__":
    main()