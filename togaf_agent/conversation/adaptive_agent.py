"""
Adaptive agent intelligence for content delivery based on user profiles and context.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field

from ..user_management.user_profile import UserProfile, ExperienceLevel, LearningStyle, LearningApproach
from ..user_management.progress_tracker import ProgressTracker
from ..conversation.session_manager import SessionManager, ConversationMode, ConversationContext
from ..knowledge_base.semantic_search import TOGAFSemanticSearch
from ..knowledge_base.metadata_schema import CertificationLevel, DifficultyLevel
from ..utils.openai_client import OpenAIClient


class ResponseStyle(str, Enum):
    CONCISE = "concise"
    DETAILED = "detailed"
    CONVERSATIONAL = "conversational"
    INSTRUCTIONAL = "instructional"
    SOCRATIC = "socratic"  # Question-based learning


class ContentAdaptation(BaseModel):
    # Content complexity
    difficulty_level: DifficultyLevel
    explanation_depth: str = "moderate"  # brief, moderate, detailed
    technical_detail: str = "balanced"   # minimal, balanced, comprehensive
    
    # Presentation style
    use_examples: bool = True
    use_analogies: bool = True
    use_visual_aids: bool = False
    include_diagrams: bool = False
    
    # Interactive elements
    ask_follow_up_questions: bool = True
    provide_practice_opportunities: bool = True
    suggest_related_topics: bool = True
    
    # Personalization
    reference_user_experience: bool = True
    adapt_to_learning_pace: bool = True
    connect_to_user_goals: bool = True


class AdaptiveResponse(BaseModel):
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Response content
    primary_content: str
    supplementary_content: Optional[str] = None
    visual_content: Optional[str] = None  # Mermaid diagrams, ASCII charts
    
    # Response metadata
    topics_addressed: List[str] = Field(default_factory=list)
    concepts_explained: List[str] = Field(default_factory=list)
    difficulty_level: DifficultyLevel
    response_style: ResponseStyle
    
    # Adaptation details
    adaptation_applied: ContentAdaptation
    user_context_used: Dict[str, Any] = Field(default_factory=dict)
    
    # Follow-up planning
    suggested_next_questions: List[str] = Field(default_factory=list)
    recommended_practice: List[str] = Field(default_factory=list)
    related_topics: List[str] = Field(default_factory=list)


class AdaptiveAgent:
    """Intelligent content delivery engine that adapts to user profiles and context."""
    
    def __init__(self, openai_client: OpenAIClient, semantic_search: TOGAFSemanticSearch,
                 progress_tracker: ProgressTracker, session_manager: SessionManager):
        self.openai_client = openai_client
        self.semantic_search = semantic_search
        self.progress_tracker = progress_tracker
        self.session_manager = session_manager
        
        # Response templates and prompts
        self.response_templates = self._initialize_response_templates()
        self.adaptation_strategies = self._initialize_adaptation_strategies()
    
    async def generate_adaptive_response(self, user_query: str, user_id: str, 
                                       session_id: str, context: Optional[Dict[str, Any]] = None) -> AdaptiveResponse:
        """Generate an adaptive response based on user profile, context, and query."""
        
        # Get user profile and session context
        session_context = self.session_manager.get_session_context(session_id)
        if not session_context:
            raise ValueError(f"Session not found: {session_id}")
        
        user_profile_data = session_context["user_profile"]
        conversation_context = session_context["conversation_context"]
        learning_preferences = session_context["learning_preferences"]
        
        # Determine content adaptation strategy
        adaptation = self._determine_content_adaptation(
            user_profile_data, learning_preferences, conversation_context
        )
        
        # Search for relevant content
        search_results = await self._search_relevant_content(
            user_query, user_profile_data, conversation_context
        )
        
        # Generate personalized prompt
        system_prompt = self._create_adaptive_system_prompt(
            user_profile_data, adaptation, conversation_context
        )
        
        user_prompt = self._create_user_prompt(
            user_query, search_results, conversation_context
        )
        
        # Generate response using OpenAI
        response_content = await self._generate_openai_response(
            system_prompt, user_prompt, adaptation
        )
        
        # Add visual content if requested
        visual_content = None
        if adaptation.include_diagrams or adaptation.use_visual_aids:
            visual_content = await self._generate_visual_content(
                user_query, response_content, adaptation
            )
        
        # Create adaptive response
        response = AdaptiveResponse(
            user_id=user_id,
            session_id=session_id,
            primary_content=response_content,
            visual_content=visual_content,
            topics_addressed=self._extract_topics_from_content(response_content),
            concepts_explained=self._extract_concepts_from_content(response_content),
            difficulty_level=adaptation.difficulty_level,
            response_style=self._determine_response_style(adaptation),
            adaptation_applied=adaptation,
            user_context_used=self._extract_used_context(session_context)
        )
        
        # Add follow-up suggestions
        await self._add_followup_suggestions(response, user_query, conversation_context)
        
        return response
    
    async def generate_exam_question(self, user_id: str, topic_id: Optional[str] = None,
                                   difficulty: Optional[DifficultyLevel] = None) -> Dict[str, Any]:
        """Generate adaptive exam questions based on user progress and gaps."""
        
        # Get user analytics to identify focus areas
        analytics = self.progress_tracker.get_progress_analytics(user_id)
        if not analytics:
            return {"error": "User analytics not found"}
        
        # Determine topic focus
        if not topic_id:
            # Choose from knowledge gaps or improvement areas
            focus_topics = analytics.improvement_focus[:3] if analytics.improvement_focus else ["adm_overview"]
            topic_id = focus_topics[0]
        
        # Determine difficulty based on user proficiency
        if not difficulty:
            # Use overall completion as proficiency indicator (0.0 to 1.0 scale)
            topic_proficiency = analytics.overall_completion / 100.0 if analytics.overall_completion else 0.0
            if topic_proficiency < 0.4:
                difficulty = DifficultyLevel.BASIC
            elif topic_proficiency < 0.7:
                difficulty = DifficultyLevel.INTERMEDIATE
            else:
                difficulty = DifficultyLevel.ADVANCED
        
        # Search for relevant content
        search_results = await self.semantic_search.search_with_context(
            f"TOGAF {topic_id} concepts and principles",
            user_level="intermediate",
            user_goal="foundation",
            n_results=3
        )
        
        # Generate question using OpenAI
        question_prompt = self._create_exam_question_prompt(topic_id, difficulty, search_results)
        
        try:
            response = await self.openai_client.async_client.chat.completions.create(
                model=self.openai_client.chat_model,
                messages=[
                    {"role": "system", "content": "You are an expert TOGAF exam question generator."},
                    {"role": "user", "content": question_prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            question_data = self._parse_exam_question_response(response.choices[0].message.content)
            question_data["topic_id"] = topic_id
            question_data["difficulty"] = difficulty.value
            
            return question_data
            
        except Exception as e:
            return {"error": f"Failed to generate question: {str(e)}"}
    
    async def provide_explanation(self, concept: str, user_id: str, session_id: str,
                                detail_level: str = "adaptive") -> AdaptiveResponse:
        """Provide adaptive explanation of a TOGAF concept."""
        
        # Get session context
        session_context = self.session_manager.get_session_context(session_id)
        if not session_context:
            raise ValueError(f"Session not found: {session_id}")
        
        user_profile_data = session_context["user_profile"]
        learning_preferences = session_context["learning_preferences"]
        
        # Determine explanation depth
        if detail_level == "adaptive":
            experience_level = user_profile_data["experience_level"]
            if experience_level == "beginner":
                detail_level = "detailed"
            elif experience_level == "expert":
                detail_level = "concise"
            else:
                detail_level = learning_preferences.get("explanation_depth", "moderate")
        
        # Search for concept information
        target_cert = user_profile_data.get("target_certification", "foundation")
        user_level = user_profile_data.get("experience_level", "beginner")
        search_results = await self.semantic_search.search_with_context(
            f"TOGAF {concept} definition explanation examples",
            user_level=user_level,
            user_goal=target_cert,
            n_results=5
        )
        
        # Create explanation-specific adaptation
        adaptation = ContentAdaptation(
            difficulty_level=DifficultyLevel.BASIC if user_profile_data["experience_level"] == "beginner" else DifficultyLevel.INTERMEDIATE,
            explanation_depth=detail_level,
            use_examples=True,
            use_analogies=user_profile_data["experience_level"] in ["beginner", "intermediate"],
            include_diagrams=learning_preferences.get("learning_style") == "visual",
            ask_follow_up_questions=learning_preferences.get("interactive_mode", True)
        )
        
        # Generate explanation
        system_prompt = self._create_explanation_system_prompt(adaptation, user_profile_data)
        user_prompt = f"Explain the TOGAF concept '{concept}' using this context:\n\n{self._format_search_results(search_results)}"
        
        explanation_content = await self._generate_openai_response(system_prompt, user_prompt, adaptation)
        
        # Create response
        response = AdaptiveResponse(
            user_id=user_id,
            session_id=session_id,
            primary_content=explanation_content,
            topics_addressed=[concept],
            concepts_explained=[concept],
            difficulty_level=adaptation.difficulty_level,
            response_style=ResponseStyle.INSTRUCTIONAL,
            adaptation_applied=adaptation,
            user_context_used={"concept_requested": concept, "detail_level": detail_level}
        )
        
        return response
    
    def _determine_content_adaptation(self, user_profile: Dict[str, Any], 
                                    learning_preferences: Dict[str, Any],
                                    conversation_context: Dict[str, Any]) -> ContentAdaptation:
        """Determine how to adapt content based on user characteristics."""
        
        experience_level = user_profile.get("experience_level", "beginner")
        learning_style = learning_preferences.get("learning_style", "reading_writing")
        explanation_depth = learning_preferences.get("explanation_depth", "moderate")
        
        # Map experience level to difficulty
        difficulty_mapping = {
            "beginner": DifficultyLevel.BASIC,
            "intermediate": DifficultyLevel.INTERMEDIATE,
            "advanced": DifficultyLevel.ADVANCED,
            "expert": DifficultyLevel.ADVANCED
        }
        
        return ContentAdaptation(
            difficulty_level=difficulty_mapping[experience_level],
            explanation_depth=explanation_depth,
            technical_detail="minimal" if experience_level == "beginner" else "balanced",
            use_examples=experience_level in ["beginner", "intermediate"],
            use_analogies=experience_level == "beginner",
            use_visual_aids=learning_style == "visual",
            include_diagrams=learning_style == "visual" and learning_preferences.get("use_diagrams", False),
            ask_follow_up_questions=learning_preferences.get("interactive_mode", True),
            provide_practice_opportunities=user_profile.get("exam_preparation_mode", False),
            reference_user_experience=experience_level in ["advanced", "expert"],
            adapt_to_learning_pace=True,
            connect_to_user_goals=True
        )
    
    async def _search_relevant_content(self, query: str, user_profile: Dict[str, Any],
                                     conversation_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for relevant content based on query and user context."""
        
        # Enhance query with context
        enhanced_query = query
        current_topic = conversation_context.get("current_topic")
        if current_topic:
            enhanced_query = f"{current_topic} {query}"
        
        # Search with user's certification level
        target_certification = user_profile.get("target_certification", "foundation")
        
        user_level = user_profile.get("experience_level", "beginner")
        results = await self.semantic_search.search_with_context(
            enhanced_query,
            user_level=user_level,
            user_goal=target_certification,
            n_results=5
        )
        
        return results
    
    def _create_adaptive_system_prompt(self, user_profile: Dict[str, Any],
                                     adaptation: ContentAdaptation,
                                     conversation_context: Dict[str, Any]) -> str:
        """Create a system prompt that adapts to user characteristics."""
        
        experience_level = user_profile.get("experience_level", "beginner")
        target_cert = user_profile.get("target_certification", "foundation")
        exam_mode = user_profile.get("exam_preparation_mode", False)
        
        base_prompt = f"""You are an expert TOGAF tutor specializing in enterprise architecture education.

User Context:
- Experience Level: {experience_level.title()}
- Target Certification: {target_cert.title()}
- Exam Preparation Mode: {"Yes" if exam_mode else "No"}
- Learning Approach: {user_profile.get('learning_approach', 'hybrid').title()}

Content Adaptation Rules:
- Explanation Depth: {adaptation.explanation_depth}
- Technical Detail: {adaptation.technical_detail}
- Difficulty Level: {adaptation.difficulty_level.value}"""
        
        # Add style guidelines based on experience
        if experience_level == "beginner":
            base_prompt += """

Teaching Style for Beginners:
- Use simple, clear language
- Provide step-by-step explanations
- Include real-world examples and analogies
- Define technical terms when first used
- Build concepts incrementally
- Encourage questions and interaction"""
        
        elif experience_level == "expert":
            base_prompt += """

Teaching Style for Experts:
- Use precise, technical language
- Focus on advanced concepts and edge cases
- Reference latest industry practices
- Discuss implementation challenges
- Provide comparative analysis
- Engage in peer-level discussion"""
        
        # Add interaction guidelines
        if adaptation.ask_follow_up_questions:
            base_prompt += """

Interaction Guidelines:
- Ask thoughtful follow-up questions to gauge understanding
- Encourage deeper exploration of concepts
- Suggest practical applications"""
        
        if adaptation.use_visual_aids:
            base_prompt += """

Visual Content:
- Include mermaid diagrams when helpful
- Use ASCII charts for simple visualizations
- Structure content with clear headings and bullet points"""
        
        return base_prompt
    
    def _create_user_prompt(self, user_query: str, search_results: List[Dict[str, Any]],
                          conversation_context: Dict[str, Any]) -> str:
        """Create the user prompt with relevant context and search results."""
        
        prompt = f"User Question: {user_query}\n\n"
        
        # Add relevant context
        current_topic = conversation_context.get("current_topic")
        if current_topic:
            prompt += f"Current Topic Context: {current_topic}\n\n"
        
        # Add search results
        if search_results:
            prompt += "Relevant TOGAF Content:\n"
            prompt += self._format_search_results(search_results)
            prompt += "\n"
        
        # Add conversation history context
        topics_discussed = conversation_context.get("topics_discussed", [])
        if topics_discussed:
            prompt += f"Previously Discussed Topics: {', '.join(topics_discussed[-5:])}\n\n"
        
        prompt += "Please provide a helpful, personalized response based on the user's question and context."
        
        return prompt
    
    async def _generate_openai_response(self, system_prompt: str, user_prompt: str,
                                      adaptation: ContentAdaptation) -> str:
        """Generate response using OpenAI with adaptive parameters."""
        
        # Adjust temperature based on adaptation
        temperature = 0.3 if adaptation.technical_detail == "comprehensive" else 0.7
        
        # Adjust max tokens based on explanation depth
        token_mapping = {
            "brief": 300,
            "moderate": 600,
            "detailed": 1000
        }
        max_tokens = token_mapping.get(adaptation.explanation_depth, 600)
        
        try:
            response = await self.openai_client.async_client.chat.completions.create(
                model=self.openai_client.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"I apologize, but I'm having trouble generating a response right now. Error: {str(e)}"
    
    async def _generate_visual_content(self, query: str, response_content: str,
                                     adaptation: ContentAdaptation) -> Optional[str]:
        """Generate visual content like mermaid diagrams if requested."""
        
        if not adaptation.include_diagrams:
            return None
        
        # Check if the content would benefit from a diagram
        diagram_keywords = ["process", "flow", "architecture", "relationship", "structure", "phases"]
        
        if not any(keyword in query.lower() or keyword in response_content.lower() 
                  for keyword in diagram_keywords):
            return None
        
        # Generate mermaid diagram
        diagram_prompt = f"""Create a mermaid diagram to visualize the following TOGAF content:

Query: {query}
Content: {response_content[:500]}...

Return only the mermaid diagram code, starting with ```mermaid and ending with ```."""
        
        try:
            response = await self.openai_client.async_client.chat.completions.create(
                model=self.openai_client.chat_model,
                messages=[
                    {"role": "system", "content": "You are an expert at creating clear, informative mermaid diagrams for TOGAF concepts."},
                    {"role": "user", "content": diagram_prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            diagram_content = response.choices[0].message.content.strip()
            
            # Validate it's a proper mermaid diagram
            if "```mermaid" in diagram_content and "```" in diagram_content:
                return diagram_content
            
        except Exception:
            pass
        
        return None
    
    async def _add_followup_suggestions(self, response: AdaptiveResponse, 
                                      original_query: str, conversation_context: Dict[str, Any]) -> None:
        """Add follow-up questions and suggestions to the response."""
        
        # Generate contextual follow-up questions
        followup_prompt = f"""Based on this TOGAF learning interaction, suggest 2-3 relevant follow-up questions:

Original Question: {original_query}
Response Topics: {', '.join(response.topics_addressed)}
User Context: {conversation_context.get('current_topic', 'general TOGAF learning')}

Provide questions that would naturally extend the learning or clarify understanding."""
        
        try:
            followup_response = await self.openai_client.async_client.chat.completions.create(
                model=self.openai_client.chat_model,
                messages=[
                    {"role": "system", "content": "Generate helpful follow-up questions for TOGAF learning."},
                    {"role": "user", "content": followup_prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            # Parse follow-up questions
            followup_content = followup_response.choices[0].message.content.strip()
            questions = [q.strip() for q in followup_content.split('\n') if q.strip() and '?' in q]
            response.suggested_next_questions = questions[:3]
            
        except Exception:
            # Provide default follow-ups based on topics
            if response.topics_addressed:
                topic = response.topics_addressed[0]
                response.suggested_next_questions = [
                    f"Can you provide a practical example of {topic}?",
                    f"How does {topic} relate to other TOGAF concepts?",
                    f"What are common challenges with {topic}?"
                ]
    
    def _format_search_results(self, search_results) -> str:
        """Format search results for inclusion in prompts."""
        if not search_results:
            return "No specific content found."
        
        formatted = ""
        for i, result in enumerate(search_results, 1):
            # Handle both SearchResult dataclass and dict formats
            if hasattr(result, 'content'):  # SearchResult dataclass
                content = result.content
                metadata = result.metadata
                source = metadata.get("source", "") if metadata else ""
            else:  # Dict format
                content = result.get("content", "")
                metadata = result.get("metadata", {})
                source = metadata.get("source", "")
            
            formatted += f"{i}. {content[:300]}..."
            if source:
                formatted += f" (Source: {source})"
            formatted += "\n\n"
        
        return formatted
    
    def _extract_topics_from_content(self, content: str) -> List[str]:
        """Extract TOGAF topics mentioned in the content."""
        topics = []
        togaf_topics = [
            "ADM", "Preliminary Phase", "Phase A", "Phase B", "Phase C", "Phase D", 
            "Phase E", "Phase F", "Phase G", "Phase H", "Requirements Management",
            "Business Architecture", "Data Architecture", "Application Architecture", 
            "Technology Architecture", "Architecture Governance", "Implementation",
            "Migration", "Architecture Board", "Architecture Compliance"
        ]
        
        content_lower = content.lower()
        for topic in togaf_topics:
            if topic.lower() in content_lower:
                topics.append(topic)
        
        return list(set(topics))
    
    def _extract_concepts_from_content(self, content: str) -> List[str]:
        """Extract key concepts explained in the content."""
        # This is a simplified implementation
        # In production, this would use NLP to extract key concepts
        concepts = []
        
        # Look for definition patterns
        import re
        definition_patterns = [
            r"(\w+(?:\s+\w+)*)\s+is\s+defined\s+as",
            r"(\w+(?:\s+\w+)*)\s+refers\s+to",
            r"(\w+(?:\s+\w+)*)\s+means"
        ]
        
        for pattern in definition_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts.extend(matches)
        
        return list(set(concepts))
    
    def _determine_response_style(self, adaptation: ContentAdaptation) -> ResponseStyle:
        """Determine the appropriate response style based on adaptation."""
        if adaptation.ask_follow_up_questions:
            return ResponseStyle.SOCRATIC
        elif adaptation.explanation_depth == "detailed":
            return ResponseStyle.INSTRUCTIONAL
        elif adaptation.explanation_depth == "brief":
            return ResponseStyle.CONCISE
        else:
            return ResponseStyle.CONVERSATIONAL
    
    def _extract_used_context(self, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the context information that was used in response generation."""
        return {
            "experience_level": session_context.get("user_profile", {}).get("experience_level"),
            "target_certification": session_context.get("user_profile", {}).get("target_certification"),
            "learning_style": session_context.get("learning_preferences", {}).get("learning_style"),
            "current_topic": session_context.get("conversation_context", {}).get("current_topic"),
            "conversation_mode": session_context.get("session_info", {}).get("conversation_mode")
        }
    
    def _initialize_response_templates(self) -> Dict[str, str]:
        """Initialize response templates for different scenarios."""
        return {
            "beginner_explanation": """Let me explain {concept} in simple terms.

{definition}

Here's a practical example:
{example}

Key points to remember:
{key_points}

Would you like me to explain how this connects to other TOGAF concepts?""",
            
            "expert_discussion": """Regarding {concept}:

{technical_details}

Implementation considerations:
{considerations}

Current industry practices:
{practices}

What's your experience with this in practice?""",
            
            "exam_preparation": """For certification purposes, here are the key points about {concept}:

Essential knowledge:
{essentials}

Common exam topics:
{exam_focus}

Practice question: {practice_question}"""
        }
    
    def _initialize_adaptation_strategies(self) -> Dict[str, ContentAdaptation]:
        """Initialize predefined adaptation strategies."""
        return {
            "beginner_structured": ContentAdaptation(
                difficulty_level=DifficultyLevel.BASIC,
                explanation_depth="detailed",
                use_examples=True,
                use_analogies=True,
                ask_follow_up_questions=True
            ),
            "expert_concise": ContentAdaptation(
                difficulty_level=DifficultyLevel.ADVANCED,
                explanation_depth="brief",
                technical_detail="comprehensive",
                use_examples=False,
                reference_user_experience=True
            ),
            "exam_focused": ContentAdaptation(
                difficulty_level=DifficultyLevel.INTERMEDIATE,
                explanation_depth="moderate",
                provide_practice_opportunities=True,
                ask_follow_up_questions=False
            )
        }
    
    def _create_exam_question_prompt(self, topic_id: str, difficulty: DifficultyLevel,
                                   search_results: List[Dict[str, Any]]) -> str:
        """Create a prompt for generating exam questions."""
        
        content_context = self._format_search_results(search_results)
        
        return f"""Generate a TOGAF certification exam question about {topic_id}.

Difficulty Level: {difficulty.value}
Content Context: {content_context}

Requirements:
1. Multiple choice question with 4 options (A, B, C, D)
2. Only one correct answer
3. Plausible distractors that test understanding
4. Clear, unambiguous wording
5. Explanation for the correct answer

Format your response as JSON:
{{
  "question": "Question text here?",
  "options": {{
    "A": "Option A text",
    "B": "Option B text", 
    "C": "Option C text",
    "D": "Option D text"
  }},
  "correct_answer": "A",
  "explanation": "Explanation of why A is correct and others are wrong"
}}"""
    
    def _parse_exam_question_response(self, response: str) -> Dict[str, Any]:
        """Parse the exam question response from OpenAI."""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Fallback: return error response
        return {
            "question": "Failed to generate question",
            "options": {"A": "Error", "B": "Error", "C": "Error", "D": "Error"},
            "correct_answer": "A",
            "explanation": "Question generation failed"
        }
    
    def _create_explanation_system_prompt(self, adaptation: ContentAdaptation, 
                                        user_profile: Dict[str, Any]) -> str:
        """Create system prompt specifically for concept explanations."""
        
        experience_level = user_profile.get("experience_level", "beginner")
        
        prompt = f"""You are a TOGAF expert providing concept explanations.

User Experience Level: {experience_level.title()}
Explanation Depth: {adaptation.explanation_depth}
Use Examples: {adaptation.use_examples}
Use Analogies: {adaptation.use_analogies}

Explanation Structure:
1. Clear definition
2. Context within TOGAF framework"""
        
        if adaptation.use_examples:
            prompt += "\n3. Practical examples"
        
        if adaptation.use_analogies and experience_level == "beginner":
            prompt += "\n4. Simple analogies to familiar concepts"
        
        prompt += f"\n\nAdapt your language and depth to a {experience_level} level user."
        
        return prompt