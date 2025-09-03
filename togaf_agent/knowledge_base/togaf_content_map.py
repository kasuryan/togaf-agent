"""TOGAF content mapping based on actual TOC analysis."""

from typing import Dict, List, Optional
from .metadata_schema import FoundationPart, PractitionerGuide


class TOGAFFoundationChapters:
    """Mapping of actual chapters from TOGAF Foundation documents."""
    
    PART_0_CHAPTERS = [
        "Introduction",
        "1 Introduction", 
        "2 The TOGAF Documentation Set",
        "3 Core Concepts",
        "4 Definitions",
        "A Referenced Documents",
        "B Glossary of Supplementary Definitions", 
        "C Abbreviations"
    ]
    
    PART_1_CHAPTERS = [
        "ADM",
        "1 Introduction",
        "2 Preliminary Phase",
        "3 Phase A: Architecture Vision",
        "4 Phase B: Business Architecture", 
        "5 Phase C: Information Systems Architectures",
        "6 Phase C: Information Systems Architectures – Data Architecture",
        "7 Phase C: Information Systems Architectures – Application Architecture",
        "8 Phase D: Technology Architecture",
        "9 Phase E: Opportunities & Solutions",
        "10 Phase F: Migration Planning",
        "11 Phase G: Implementation Governance",
        "12 Phase H: Architecture Change Management",
        "13 ADM Architecture Requirements Management"
    ]
    
    PART_2_CHAPTERS = [
        "1 Introduction",
        "2 Architecture Principles",
        "3 Stakeholder Management",
        "4 Architecture Patterns", 
        "5 Gap Analysis",
        "6 Migration Planning Techniques",
        "7 Interoperability Requirements",
        "8 Business Transformation Readiness Assessment",
        "9 Risk Management",
        "10 Architecture Alternatives and Trade-Offs"
    ]
    
    PART_3_CHAPTERS = [
        "1 Introduction",
        "2 Applying Iteration to the ADM",
        "3 Applying the ADM Across the Architecture Landscape",
        "4 Architecture Partitioning"
    ]
    
    PART_4_CHAPTERS = [
        "Architecture-Content",
        "1 Introduction",
        "2 TOGAF Content Framework and Enterprise Metamodel",
        "3 Architectural Artifacts", 
        "4 Architecture Deliverables",
        "5 Building Blocks",
        "6 Enterprise Continuum",
        "7 Architecture Repository"
    ]
    
    PART_5_CHAPTERS = [
        "EA-Capability-Governance",
        "1 Introduction",
        "2 Establishing an Architecture Capability",
        "3 Architecture Governance",
        "4 Architecture Board",
        "5 Architecture Contracts", 
        "6 Architecture Compliance"
    ]


class TOGAFContentMapper:
    """Maps TOGAF content to learning objectives and prerequisites."""
    
    @staticmethod
    def get_chapter_list(part: FoundationPart) -> List[str]:
        """Get chapter list for a foundation part."""
        chapter_mapping = {
            FoundationPart.PART_0_INTRODUCTION_CORE_CONCEPTS: TOGAFFoundationChapters.PART_0_CHAPTERS,
            FoundationPart.PART_1_ARCHITECTURE_DEVELOPMENT_METHOD: TOGAFFoundationChapters.PART_1_CHAPTERS,
            FoundationPart.PART_2_ADM_TECHNIQUES: TOGAFFoundationChapters.PART_2_CHAPTERS,
            FoundationPart.PART_3_APPLYING_ADM: TOGAFFoundationChapters.PART_3_CHAPTERS,
            FoundationPart.PART_4_ARCHITECTURE_CONTENT: TOGAFFoundationChapters.PART_4_CHAPTERS,
            FoundationPart.PART_5_ENTERPRISE_CAPABILITY_GOVERNANCE: TOGAFFoundationChapters.PART_5_CHAPTERS
        }
        return chapter_mapping.get(part, [])
    
    @staticmethod
    def get_prerequisites(part: FoundationPart) -> List[FoundationPart]:
        """Get prerequisite parts for a foundation part."""
        prerequisites = {
            FoundationPart.PART_0_INTRODUCTION_CORE_CONCEPTS: [],
            FoundationPart.PART_1_ARCHITECTURE_DEVELOPMENT_METHOD: [FoundationPart.PART_0_INTRODUCTION_CORE_CONCEPTS],
            FoundationPart.PART_2_ADM_TECHNIQUES: [FoundationPart.PART_0_INTRODUCTION_CORE_CONCEPTS, FoundationPart.PART_1_ARCHITECTURE_DEVELOPMENT_METHOD],
            FoundationPart.PART_3_APPLYING_ADM: [FoundationPart.PART_1_ARCHITECTURE_DEVELOPMENT_METHOD, FoundationPart.PART_2_ADM_TECHNIQUES],
            FoundationPart.PART_4_ARCHITECTURE_CONTENT: [FoundationPart.PART_0_INTRODUCTION_CORE_CONCEPTS, FoundationPart.PART_1_ARCHITECTURE_DEVELOPMENT_METHOD],
            FoundationPart.PART_5_ENTERPRISE_CAPABILITY_GOVERNANCE: [FoundationPart.PART_0_INTRODUCTION_CORE_CONCEPTS, FoundationPart.PART_1_ARCHITECTURE_DEVELOPMENT_METHOD]
        }
        return prerequisites.get(part, [])
    
    @staticmethod
    def get_key_concepts(part: FoundationPart) -> List[str]:
        """Get key concepts for each foundation part."""
        concepts = {
            FoundationPart.PART_0_INTRODUCTION_CORE_CONCEPTS: [
                "TOGAF Framework", "Enterprise Architecture", "Architecture Development", 
                "Business Architecture", "Data Architecture", "Application Architecture", 
                "Technology Architecture", "Architecture Governance"
            ],
            FoundationPart.PART_1_ARCHITECTURE_DEVELOPMENT_METHOD: [
                "ADM", "Architecture Vision", "Business Architecture", "Information Systems Architecture",
                "Technology Architecture", "Opportunities & Solutions", "Migration Planning",
                "Implementation Governance", "Architecture Change Management", "Requirements Management"
            ],
            FoundationPart.PART_2_ADM_TECHNIQUES: [
                "Architecture Principles", "Stakeholder Management", "Architecture Patterns",
                "Gap Analysis", "Migration Planning", "Interoperability", "Business Transformation",
                "Risk Management", "Trade-off Analysis"
            ],
            FoundationPart.PART_3_APPLYING_ADM: [
                "ADM Iteration", "Architecture Landscape", "Architecture Partitioning",
                "Security Architecture", "SOA"
            ],
            FoundationPart.PART_4_ARCHITECTURE_CONTENT: [
                "Content Framework", "Enterprise Metamodel", "Architectural Artifacts",
                "Architecture Deliverables", "Building Blocks", "Enterprise Continuum",
                "Architecture Repository", "Standards Information Base"
            ],
            FoundationPart.PART_5_ENTERPRISE_CAPABILITY_GOVERNANCE: [
                "Architecture Capability", "Architecture Governance", "Architecture Board",
                "Architecture Contracts", "Architecture Compliance", "Architecture Maturity"
            ]
        }
        return concepts.get(part, [])
    
    @staticmethod
    def get_practitioner_prerequisites(guide: PractitionerGuide) -> List[FoundationPart]:
        """Get foundation prerequisites for practitioner guides."""
        # Most practitioner guides require foundation knowledge
        common_prerequisites = [
            FoundationPart.PART_0_INTRODUCTION_CORE_CONCEPTS,
            FoundationPart.PART_1_ARCHITECTURE_DEVELOPMENT_METHOD
        ]
        
        specific_prerequisites = {
            PractitionerGuide.RISK_SECURITY_INTEGRATION: common_prerequisites + [FoundationPart.PART_2_ADM_TECHNIQUES],
            PractitionerGuide.BUSINESS_SCENARIOS: common_prerequisites + [FoundationPart.PART_2_ADM_TECHNIQUES],
            PractitionerGuide.ADM_AGILE_SPRINTS: common_prerequisites + [FoundationPart.PART_3_APPLYING_ADM],
            PractitionerGuide.PRACTITIONERS_APPROACH_ADM: common_prerequisites + [FoundationPart.PART_2_ADM_TECHNIQUES, FoundationPart.PART_3_APPLYING_ADM],
            PractitionerGuide.EA_CAPABILITY_GUIDE: common_prerequisites + [FoundationPart.PART_5_ENTERPRISE_CAPABILITY_GOVERNANCE],
            PractitionerGuide.ARCHITECTURE_PROJECT_MANAGEMENT: common_prerequisites + [FoundationPart.PART_5_ENTERPRISE_CAPABILITY_GOVERNANCE],
            # Add more specific mappings as needed
        }
        
        return specific_prerequisites.get(guide, common_prerequisites)
    
    @staticmethod
    def map_chapter_to_adm_phase(chapter_title: str) -> Optional[str]:
        """Map chapter titles to ADM phases."""
        phase_mapping = {
            "preliminary phase": "preliminary",
            "phase a": "phase_a",
            "architecture vision": "phase_a", 
            "phase b": "phase_b",
            "business architecture": "phase_b",
            "phase c": "phase_c",
            "information systems": "phase_c",
            "data architecture": "phase_c",
            "application architecture": "phase_c",
            "phase d": "phase_d", 
            "technology architecture": "phase_d",
            "phase e": "phase_e",
            "opportunities": "phase_e",
            "solutions": "phase_e",
            "phase f": "phase_f",
            "migration planning": "phase_f",
            "phase g": "phase_g", 
            "implementation governance": "phase_g",
            "phase h": "phase_h",
            "architecture change management": "phase_h",
            "requirements management": "requirements_management"
        }
        
        chapter_lower = chapter_title.lower()
        for key, phase in phase_mapping.items():
            if key in chapter_lower:
                return phase
        return None
    
    @staticmethod
    def get_difficulty_level(part: FoundationPart, chapter_title: str) -> str:
        """Determine difficulty level based on part and chapter."""
        # Part 0 and basic chapters are basic level
        if part == FoundationPart.PART_0_INTRODUCTION_CORE_CONCEPTS:
            return "basic"
        
        # Introduction chapters are basic
        if "introduction" in chapter_title.lower():
            return "basic"
        
        # Advanced techniques and applying concepts are intermediate
        if part in [FoundationPart.PART_2_ADM_TECHNIQUES, FoundationPart.PART_3_APPLYING_ADM]:
            if any(term in chapter_title.lower() for term in ["advanced", "complex", "enterprise", "governance"]):
                return "advanced"
            return "intermediate"
        
        # Content and governance parts are intermediate to advanced
        if part in [FoundationPart.PART_4_ARCHITECTURE_CONTENT, FoundationPart.PART_5_ENTERPRISE_CAPABILITY_GOVERNANCE]:
            if any(term in chapter_title.lower() for term in ["compliance", "governance", "metamodel"]):
                return "advanced"
            return "intermediate"
        
        return "basic"