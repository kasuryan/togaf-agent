"""Rich metadata schema for TOGAF content embeddings based on actual document structure."""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime
import uuid


class CertificationLevel(Enum):
    """TOGAF certification levels based on directory structure."""
    FOUNDATION = "foundation"      # ./data/core_topics (6 PDFs)
    PRACTITIONER = "practitioner"  # ./data/extended_topics (27+ PDFs)


class FoundationPart(Enum):
    """TOGAF Foundation parts (core_topics directory - 6 official parts)."""
    PART_0_INTRODUCTION_CORE_CONCEPTS = "part_0_introduction_core_concepts"              # C220-Part0e.pdf
    PART_1_ARCHITECTURE_DEVELOPMENT_METHOD = "part_1_architecture_development_method"    # C220-Part1e.pdf  
    PART_2_ADM_TECHNIQUES = "part_2_adm_techniques"                                     # C220-Part2e.pdf
    PART_3_APPLYING_ADM = "part_3_applying_adm"                                         # C220-Part3e.pdf
    PART_4_ARCHITECTURE_CONTENT = "part_4_architecture_content"                         # C220-Part4e.pdf
    PART_5_ENTERPRISE_CAPABILITY_GOVERNANCE = "part_5_enterprise_capability_governance" # C220-Part5e.pdf


class PractitionerGuide(Enum):
    """TOGAF Practitioner Series Guides (extended_topics directory)."""
    # Based on actual document analysis from extended_topics
    RISK_SECURITY_INTEGRATION = "risk_security_integration"              # G152e.pdf
    INFORMATION_MAPPING = "information_mapping"                          # G190e.pdf
    PRACTITIONERS_APPROACH_ADM = "practitioners_approach_adm"            # G186e.pdf
    DIGITAL_ENTERPRISE = "digital_enterprise"                           # G217e.pdf
    ENTERPRISE_AGILITY = "enterprise_agility"                           # G20Fe.pdf
    BUSINESS_MODELS = "business_models"                                  # G18Ae.pdf
    ADM_AGILE_SPRINTS = "adm_agile_sprints"                             # G210e.pdf
    VALUE_STREAMS = "value_streams"                                      # G178e.pdf
    ORGANIZATION_MAPPING = "organization_mapping"                        # G206e.pdf
    SOA_GUIDE = "soa_guide"                                             # G174e.pdf
    TRM_GUIDE = "trm_guide"                                             # G175e.pdf
    III_RM_GUIDE = "iii_rm_guide"                                       # G179e.pdf
    BUSINESS_CAPABILITIES = "business_capabilities"                      # G211e.pdf
    DIGITAL_TECHNOLOGY_ADOPTION = "digital_technology_adoption"          # G212e.pdf
    MICROSERVICES_ARCHITECTURE = "microservices_architecture"           # G21Ie.pdf
    BUSINESS_SCENARIOS = "business_scenarios"                            # G176e.pdf
    GOVERNMENT_REFERENCE_MODEL = "government_reference_model"            # G21De.pdf
    ARCHITECTURE_SKILLS_FRAMEWORK = "architecture_skills_framework"      # G198e.pdf
    BUSINESS_CAPABILITY_PLANNING = "business_capability_planning"        # G233e.pdf
    DIGITAL_BUSINESS_REFERENCE_MODEL = "digital_business_reference_model" # G21He.pdf
    INFORMATION_ARCH_METADATA = "information_arch_metadata"              # G234e.pdf
    BI_ANALYTICS = "bi_analytics"                                       # G238e.pdf
    EA_CAPABILITY_GUIDE = "ea_capability_guide"                         # G184e.pdf
    SUSTAINABLE_IS = "sustainable_is"                                   # G242e.pdf
    ARCHITECTURE_MATURITY_MODELS = "architecture_maturity_models"       # G203e.pdf
    CUSTOMER_MDM = "customer_mdm"                                       # G21Be.pdf
    ARCHITECTURE_PROJECT_MANAGEMENT = "architecture_project_management"  # G188e.pdf


class ContentType(Enum):
    """Types of content for learning classification based on actual TOC analysis."""
    CONCEPT = "concept"
    PROCESS = "process"
    DIAGRAM = "diagram"
    EXAMPLE = "example"
    CHECKLIST = "checklist"
    DELIVERABLE = "deliverable"
    QUESTION = "question"
    ASSESSMENT = "assessment"
    TABLE = "table"
    DEFINITION = "definition"
    GUIDELINE = "guideline"
    PROCEDURE = "procedure"
    TEMPLATE = "template"
    TECHNIQUE = "technique"
    PATTERN = "pattern"
    REFERENCE_MODEL = "reference_model"  # For TRM, III-RM guides
    METHODOLOGY = "methodology"          # For ADM techniques and methods
    FRAMEWORK = "framework"              # For capability frameworks
    METAMODEL = "metamodel"              # For enterprise metamodel content
    READINESS_ASSESSMENT = "readiness_assessment"  # For transformation readiness
    MATURITY_MODEL = "maturity_model"    # For architecture maturity content


class DifficultyLevel(Enum):
    """Content difficulty levels."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TOGAFPhase(Enum):
    """TOGAF ADM phases."""
    PRELIMINARY = "preliminary"
    PHASE_A = "phase_a"  # Architecture Vision
    PHASE_B = "phase_b"  # Business Architecture
    PHASE_C = "phase_c"  # Information Systems Architecture
    PHASE_D = "phase_d"  # Technology Architecture
    PHASE_E = "phase_e"  # Opportunities & Solutions
    PHASE_F = "phase_f"  # Migration Planning
    PHASE_G = "phase_g"  # Implementation Governance
    PHASE_H = "phase_h"  # Architecture Change Management
    REQUIREMENTS_MANAGEMENT = "requirements_management"


class ArchitectureDomain(Enum):
    """TOGAF Architecture domains."""
    BUSINESS = "business"
    DATA = "data"
    APPLICATION = "application"
    TECHNOLOGY = "technology"


class LearningObjective(Enum):
    """TOGAF learning objectives aligned with actual certification levels and content."""
    
    # Foundation Level Objectives (Understanding/Knowledge - all 6 parts focus on comprehension)
    UNDERSTAND_TOGAF_CONCEPTS = "understand_togaf_concepts"                      # Part 0
    UNDERSTAND_ADM = "understand_adm"                                           # Part 1
    UNDERSTAND_ADM_TECHNIQUES = "understand_adm_techniques"                     # Part 2 
    UNDERSTAND_ADM_APPLICATION = "understand_adm_application"                   # Part 3
    UNDERSTAND_ARCHITECTURE_CONTENT = "understand_architecture_content"         # Part 4
    UNDERSTAND_EA_GOVERNANCE = "understand_ea_governance"                       # Part 5
    UNDERSTAND_ARCHITECTURE_PRINCIPLES = "understand_architecture_principles"   # Part 2
    UNDERSTAND_STAKEHOLDER_MANAGEMENT = "understand_stakeholder_management"     # Part 2
    UNDERSTAND_GAP_ANALYSIS = "understand_gap_analysis"                        # Part 2
    UNDERSTAND_MIGRATION_PLANNING = "understand_migration_planning"            # Part 2
    UNDERSTAND_ENTERPRISE_CONTINUUM = "understand_enterprise_continuum"        # Part 4
    UNDERSTAND_ARCHITECTURE_REPOSITORY = "understand_architecture_repository"   # Part 4
    UNDERSTAND_ARCHITECTURE_GOVERNANCE = "understand_architecture_governance"   # Part 5
    
    # Practitioner Level Objectives (Application/Skills - specific guide contexts)
    APPLY_RISK_SECURITY_INTEGRATION = "apply_risk_security_integration"        # G152e
    APPLY_INFORMATION_MAPPING = "apply_information_mapping"                    # G190e
    APPLY_PRACTITIONERS_ADM_APPROACH = "apply_practitioners_adm_approach"      # G186e
    APPLY_IN_DIGITAL_ENTERPRISE = "apply_in_digital_enterprise"               # G217e
    APPLY_ENTERPRISE_AGILITY = "apply_enterprise_agility"                     # G20Fe
    APPLY_BUSINESS_MODELS = "apply_business_models"                           # G18Ae
    APPLY_ADM_WITH_AGILE_SPRINTS = "apply_adm_with_agile_sprints"            # G210e
    APPLY_VALUE_STREAMS = "apply_value_streams"                               # G178e
    APPLY_ORGANIZATION_MAPPING = "apply_organization_mapping"                  # G206e
    APPLY_SOA_ARCHITECTURE = "apply_soa_architecture"                         # G174e
    APPLY_TRM_GUIDE = "apply_trm_guide"                                       # G175e
    APPLY_III_RM_GUIDE = "apply_iii_rm_guide"                                # G179e
    APPLY_BUSINESS_CAPABILITIES = "apply_business_capabilities"                # G211e
    APPLY_DIGITAL_TECHNOLOGY_ADOPTION = "apply_digital_technology_adoption"    # G212e
    APPLY_MICROSERVICES_ARCHITECTURE = "apply_microservices_architecture"     # G21Ie
    APPLY_BUSINESS_SCENARIOS = "apply_business_scenarios"                      # G176e
    APPLY_GOVERNMENT_REFERENCE_MODEL = "apply_government_reference_model"      # G21De
    APPLY_ARCHITECTURE_SKILLS_FRAMEWORK = "apply_architecture_skills_framework" # G198e
    APPLY_BUSINESS_CAPABILITY_PLANNING = "apply_business_capability_planning"  # G233e
    APPLY_DIGITAL_BUSINESS_REFERENCE_MODEL = "apply_digital_business_reference_model" # G21He
    APPLY_INFORMATION_ARCH_METADATA = "apply_information_arch_metadata"        # G234e
    APPLY_BI_ANALYTICS = "apply_bi_analytics"                                 # G238e
    IMPLEMENT_EA_CAPABILITY = "implement_ea_capability"                        # G184e
    APPLY_SUSTAINABLE_IS = "apply_sustainable_is"                             # G242e
    APPLY_ARCHITECTURE_MATURITY_MODELS = "apply_architecture_maturity_models"  # G203e
    APPLY_CUSTOMER_MDM = "apply_customer_mdm"                                 # G21Be
    MANAGE_ARCHITECTURE_PROJECTS = "manage_architecture_projects"              # G188e


class DocumentInfo(BaseModel):
    """Document-level metadata with actual TOGAF document information."""
    source_file: str
    document_title: str  # Official title from PDF metadata
    document_type: str = "PDF"
    total_pages: int
    processed_at: datetime = Field(default_factory=datetime.now)
    processing_method: str
    
    # Directory-based classification
    source_directory: str  # "core_topics" or "extended_topics"
    
    # Official TOGAF document identifiers
    togaf_part: Optional[str] = None           # For Foundation: "Part 0", "Part 1", etc.
    togaf_guide_id: Optional[str] = None       # For Practitioner: "G152e", "G186e", etc.
    
    # Actual document titles from TOC analysis
    official_title: Optional[str] = None       # e.g., "TOGAF® Standard – ADM Techniques"
    part_description: Optional[str] = None     # e.g., "Part 2: ADM Techniques"
    series_title: Optional[str] = None         # For practitioner: "TOGAF® Series Guide"
    
    @validator('source_directory')
    def validate_source_directory(cls, v):
        valid_dirs = ["core_topics", "extended_topics", "sample_questions_answers", "certification"]
        if v not in valid_dirs:
            raise ValueError(f"Invalid source directory: {v}")
        return v


class StructuralInfo(BaseModel):
    """Structural information about content placement."""
    page_number: int
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_chunk: Optional[str] = None
    child_chunks: List[str] = Field(default_factory=list)
    
    # Hierarchical structure from actual TOC
    chapter_number: Optional[str] = None       # e.g., "1", "2.1", "A"
    chapter_title: Optional[str] = None        # e.g., "Introduction", "Architecture Principles"
    section_number: Optional[str] = None       # e.g., "2.1.1"
    section_title: Optional[str] = None        # e.g., "Characteristics of Architecture Principles"
    subsection_number: Optional[str] = None
    subsection_title: Optional[str] = None
    
    # Layout information
    bbox: Optional[List[float]] = None
    font_info: List[str] = Field(default_factory=list)
    
    # Content positioning
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    word_count: int = 0


class SemanticInfo(BaseModel):
    """Semantic enrichment metadata."""
    key_concepts: List[str] = Field(default_factory=list)
    related_topics: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)
    
    # TOGAF-specific concepts
    adm_phases: List[TOGAFPhase] = Field(default_factory=list)
    architecture_domains: List[ArchitectureDomain] = Field(default_factory=list)
    stakeholders: List[str] = Field(default_factory=list)
    
    # Content classification by level
    foundation_part: Optional[FoundationPart] = None
    practitioner_guide: Optional[PractitionerGuide] = None
    
    # Cross-references
    referenced_sections: List[str] = Field(default_factory=list)
    external_references: List[str] = Field(default_factory=list)


class AssessmentInfo(BaseModel):
    """Assessment and learning metadata."""
    learning_objectives: List[LearningObjective] = Field(default_factory=list)
    assessment_topics: List[str] = Field(default_factory=list)
    question_types: List[str] = Field(default_factory=list)
    
    # Learning path information
    prerequisite_knowledge: List[str] = Field(default_factory=list)
    follow_up_topics: List[str] = Field(default_factory=list)
    estimated_reading_time: Optional[int] = None  # minutes
    
    # Certification alignment
    exam_part: Optional[str] = None  # "Part 1" (Foundation) or "Part 2" (Practitioner)


class ContentMetadata(BaseModel):
    """Comprehensive metadata schema for TOGAF content embeddings."""
    
    # Core Classification - determined by directory structure
    certification_level: CertificationLevel
    content_type: ContentType
    difficulty_level: DifficultyLevel
    
    # Hierarchical Structure - actual document title from PDFs
    document_title: str
    
    # Document Information
    document_info: DocumentInfo
    
    # Structural Information
    structural_info: StructuralInfo
    
    # Semantic Information
    semantic_info: SemanticInfo
    
    # Assessment Information
    assessment_info: AssessmentInfo
    
    # Content Characteristics
    has_diagrams: bool = False
    has_tables: bool = False
    has_examples: bool = False
    has_checklists: bool = False
    has_templates: bool = False
    
    # Quality Metrics
    content_quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    
    # Custom fields for extensibility
    custom_tags: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for storage."""
        return self.dict()
    
    def get_search_tags(self) -> List[str]:
        """Generate search tags for filtering."""
        tags = [
            self.certification_level.value,
            self.content_type.value,
            self.difficulty_level.value
        ]
        
        # Add part/guide specific tags
        if self.semantic_info.foundation_part:
            tags.append(f"foundation_part:{self.semantic_info.foundation_part.value}")
        if self.semantic_info.practitioner_guide:
            tags.append(f"practitioner_guide:{self.semantic_info.practitioner_guide.value}")
            
        # Add structural tags
        if self.structural_info.chapter_title:
            clean_chapter = self.structural_info.chapter_title.lower().replace(' ', '_')
            tags.append(f"chapter:{clean_chapter}")
        if self.structural_info.section_title:
            clean_section = self.structural_info.section_title.lower().replace(' ', '_')
            tags.append(f"section:{clean_section}")
            
        # Add semantic tags
        tags.extend([f"concept:{concept.lower().replace(' ', '_')}" for concept in self.semantic_info.key_concepts])
        tags.extend([f"phase:{phase.value}" for phase in self.semantic_info.adm_phases])
        tags.extend([f"domain:{domain.value}" for domain in self.semantic_info.architecture_domains])
        tags.extend([f"objective:{obj.value}" for obj in self.assessment_info.learning_objectives])
        
        return tags
    
    def is_relevant_for_user(self, user_level: str, user_certification_goal: str) -> bool:
        """Check if content is relevant for specific user profile."""
        # Check certification level alignment
        if user_certification_goal == "foundation" and self.certification_level == CertificationLevel.PRACTITIONER:
            return False
        
        # Check difficulty alignment
        level_mapping = {
            "beginner": [DifficultyLevel.BASIC],
            "intermediate": [DifficultyLevel.BASIC, DifficultyLevel.INTERMEDIATE],
            "advanced": [DifficultyLevel.BASIC, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]
        }
        
        return self.difficulty_level in level_mapping.get(user_level, [DifficultyLevel.BASIC])
    
    def get_certification_context(self) -> str:
        """Get human-readable certification context."""
        if self.certification_level == CertificationLevel.FOUNDATION:
            part_name = self.semantic_info.foundation_part.value.replace('_', ' ').title() if self.semantic_info.foundation_part else ""
            return f"TOGAF Foundation - {part_name}"
        else:
            guide_name = self.semantic_info.practitioner_guide.value.replace('_', ' ').title() if self.semantic_info.practitioner_guide else ""
            return f"TOGAF Practitioner - {guide_name}"


class MetadataBuilder:
    """Helper class to build metadata incrementally based on actual TOGAF structure."""
    
    def __init__(self, source_directory: str, file_name: str):
        """Initialize with source directory and file name to determine classification."""
        self.source_directory = source_directory
        self.file_name = file_name
        
        # Determine certification level and specific part/guide
        if source_directory == "core_topics":
            certification_level = CertificationLevel.FOUNDATION
            foundation_part = self._map_foundation_file(file_name)
            practitioner_guide = None
        elif source_directory == "extended_topics":
            certification_level = CertificationLevel.PRACTITIONER
            foundation_part = None
            practitioner_guide = self._map_practitioner_file(file_name)
        else:
            certification_level = CertificationLevel.FOUNDATION  # default
            foundation_part = None
            practitioner_guide = None
        
        self.metadata = {
            "certification_level": certification_level,
            "semantic_info": {
                "foundation_part": foundation_part,
                "practitioner_guide": practitioner_guide
            }
        }
    
    def _map_foundation_file(self, file_name: str) -> Optional[FoundationPart]:
        """Map foundation file names to parts with official titles."""
        mapping = {
            "C220-Part0e.pdf": FoundationPart.PART_0_INTRODUCTION_CORE_CONCEPTS,
            "C220-Part1e.pdf": FoundationPart.PART_1_ARCHITECTURE_DEVELOPMENT_METHOD,
            "C220-Part2e.pdf": FoundationPart.PART_2_ADM_TECHNIQUES,
            "C220-Part3e.pdf": FoundationPart.PART_3_APPLYING_ADM,
            "C220-Part4e.pdf": FoundationPart.PART_4_ARCHITECTURE_CONTENT,
            "C220-Part5e.pdf": FoundationPart.PART_5_ENTERPRISE_CAPABILITY_GOVERNANCE
        }
        return mapping.get(file_name)
    
    def _get_foundation_official_info(self, file_name: str) -> Dict[str, str]:
        """Get official document information for foundation parts."""
        info_mapping = {
            "C220-Part0e.pdf": {
                "official_title": "TOGAF® Standard – Introduction and Core Concepts",
                "part_description": "Part 0: Introduction and Core Concepts",
                "togaf_part": "Part 0"
            },
            "C220-Part1e.pdf": {
                "official_title": "TOGAF® Standard – Architecture Development Method",
                "part_description": "Part 1: Architecture Development Method", 
                "togaf_part": "Part 1"
            },
            "C220-Part2e.pdf": {
                "official_title": "TOGAF® Standard – ADM Techniques",
                "part_description": "Part 2: ADM Techniques",
                "togaf_part": "Part 2"
            },
            "C220-Part3e.pdf": {
                "official_title": "TOGAF® Standard – Applying the ADM",
                "part_description": "Part 3: Applying the ADM",
                "togaf_part": "Part 3"
            },
            "C220-Part4e.pdf": {
                "official_title": "TOGAF® Standard – Architecture Content",
                "part_description": "Part 4: Architecture Content",
                "togaf_part": "Part 4"
            },
            "C220-Part5e.pdf": {
                "official_title": "TOGAF® Standard – Enterprise Architecture Capability and Governance",
                "part_description": "Part 5: Enterprise Architecture Capability and Governance",
                "togaf_part": "Part 5"
            }
        }
        return info_mapping.get(file_name, {})
    
    def _map_practitioner_file(self, file_name: str) -> Optional[PractitionerGuide]:
        """Map practitioner file names to guides."""
        mapping = {
            "G152e.pdf": PractitionerGuide.RISK_SECURITY_INTEGRATION,
            "G190e.pdf": PractitionerGuide.INFORMATION_MAPPING,
            "G186e.pdf": PractitionerGuide.PRACTITIONERS_APPROACH_ADM,
            "G217e.pdf": PractitionerGuide.DIGITAL_ENTERPRISE,
            "G20Fe.pdf": PractitionerGuide.ENTERPRISE_AGILITY,
            "G18Ae.pdf": PractitionerGuide.BUSINESS_MODELS,
            "G210e.pdf": PractitionerGuide.ADM_AGILE_SPRINTS,
            "G178e.pdf": PractitionerGuide.VALUE_STREAMS,
            "G206e.pdf": PractitionerGuide.ORGANIZATION_MAPPING,
            "G174e.pdf": PractitionerGuide.SOA_GUIDE,
            "G175e.pdf": PractitionerGuide.TRM_GUIDE,
            "G179e.pdf": PractitionerGuide.III_RM_GUIDE,
            "G211e.pdf": PractitionerGuide.BUSINESS_CAPABILITIES,
            "G212e.pdf": PractitionerGuide.DIGITAL_TECHNOLOGY_ADOPTION,
            "G21Ie.pdf": PractitionerGuide.MICROSERVICES_ARCHITECTURE,
            "G176e.pdf": PractitionerGuide.BUSINESS_SCENARIOS,
            "G21De.pdf": PractitionerGuide.GOVERNMENT_REFERENCE_MODEL,
            "G198e.pdf": PractitionerGuide.ARCHITECTURE_SKILLS_FRAMEWORK,
            "G233e.pdf": PractitionerGuide.BUSINESS_CAPABILITY_PLANNING,
            "G21He.pdf": PractitionerGuide.DIGITAL_BUSINESS_REFERENCE_MODEL,
            "G234e.pdf": PractitionerGuide.INFORMATION_ARCH_METADATA,
            "G238e.pdf": PractitionerGuide.BI_ANALYTICS,
            "G184e.pdf": PractitionerGuide.EA_CAPABILITY_GUIDE,
            "G242e.pdf": PractitionerGuide.SUSTAINABLE_IS,
            "G203e.pdf": PractitionerGuide.ARCHITECTURE_MATURITY_MODELS,
            "G21Be.pdf": PractitionerGuide.CUSTOMER_MDM,
            "G188e.pdf": PractitionerGuide.ARCHITECTURE_PROJECT_MANAGEMENT
        }
        return mapping.get(file_name)
    
    def set_content_info(self, content_type: ContentType, difficulty: DifficultyLevel):
        """Set content classification."""
        self.metadata.update({
            "content_type": content_type,
            "difficulty_level": difficulty
        })
        return self
    
    def set_document_hierarchy(self, doc_title: str, chapter: str = None, section: str = None, subsection: str = None):
        """Set document hierarchy from actual TOC."""
        self.metadata.update({
            "document_title": doc_title
        })
        
        # Update structural info
        structural_info = self.metadata.get("structural_info", {})
        if chapter:
            structural_info["chapter_title"] = chapter
        if section:
            structural_info["section_title"] = section
        if subsection:
            structural_info["subsection_title"] = subsection
        self.metadata["structural_info"] = structural_info
        return self
    
    def add_semantic_info(self, key_concepts: List[str] = None, 
                         related_topics: List[str] = None,
                         adm_phases: List[TOGAFPhase] = None,
                         architecture_domains: List[ArchitectureDomain] = None):
        """Add semantic information."""
        semantic_info = self.metadata.get("semantic_info", {})
        if key_concepts:
            semantic_info["key_concepts"] = key_concepts
        if related_topics:
            semantic_info["related_topics"] = related_topics
        if adm_phases:
            semantic_info["adm_phases"] = adm_phases
        if architecture_domains:
            semantic_info["architecture_domains"] = architecture_domains
        self.metadata["semantic_info"] = semantic_info
        return self
    
    def build(self, document_info: DocumentInfo, structural_info: StructuralInfo) -> ContentMetadata:
        """Build final metadata object with official document information."""
        # Ensure document_info has correct source_directory
        document_info.source_directory = self.source_directory
        
        # Add official document information
        if self.source_directory == "core_topics":
            official_info = self._get_foundation_official_info(self.file_name)
            for key, value in official_info.items():
                setattr(document_info, key, value)
        elif self.source_directory == "extended_topics":
            document_info.togaf_guide_id = self.file_name.replace(".pdf", "")
            document_info.series_title = "TOGAF® Series Guide"
        
        # Merge structural info
        structural_dict = structural_info.dict()
        existing_structural = self.metadata.get("structural_info", {})
        structural_dict.update(existing_structural)
        structural_info = StructuralInfo(**structural_dict)
        
        # Set required fields
        self.metadata.update({
            "document_info": document_info,
            "structural_info": structural_info,
            "semantic_info": SemanticInfo(**self.metadata.get("semantic_info", {})),
            "assessment_info": AssessmentInfo()
        })
        
        return ContentMetadata(**self.metadata)