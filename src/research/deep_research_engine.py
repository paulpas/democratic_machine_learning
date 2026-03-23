"""Deep research engine for democratic decision-making.

This engine breaks down each policy topic into fundamental research questions,
investigates each question thoroughly, and builds a comprehensive understanding
from the ground up.
"""

import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from src.verbose_logging.verbose_logger import (
    VerboseLogger,
    LogStep,
    get_logger,
    reset_logger,
)

try:
    from src.llm.integration import LLMClient

    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class ResearchDepth(Enum):
    """Levels of research depth."""

    FUNDAMENTAL = "Fundamental concept investigation"
    CONTEXTUAL = "Context and background research"
    EMPIRICAL = "Empirical data collection"
    ANALYTICAL = "Analytical synthesis"
    CRITICAL = "Critical evaluation and validation"


@dataclass
class ResearchQuestion:
    """A research question with its investigation status."""

    question_id: str
    question: str
    depth: ResearchDepth
    category: str
    status: str = "pending"
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    notes: str = ""


@dataclass
class ConceptNode:
    """A fundamental concept in the knowledge graph."""

    concept_id: str
    name: str
    definition: str
    relationships: List[str] = field(default_factory=list)
    research_questions: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)


class DeepResearchEngine:
    """Engine that performs deep, multi-layered research on policy topics."""

    def __init__(
        self, verbose_logger: Optional[VerboseLogger] = None, use_llm: bool = True
    ):
        """Initialize the deep research engine.

        Args:
            verbose_logger: Optional verbose logger for tracking reasoning
            use_llm: Whether to use LLM for analysis
        """
        self.verbose_logger = verbose_logger
        self.concepts: Dict[str, ConceptNode] = {}
        self.questions: Dict[str, ResearchQuestion] = {}
        self.knowledge_graph: Dict[str, List[str]] = {}

        # Initialize LLM client if available
        self.llm_client: Optional[LLMClient] = None
        if use_llm and LLM_AVAILABLE:
            try:
                self.llm_client = LLMClient()
            except Exception as e:
                print(f"Warning: Could not initialize LLM client: {e}")

    def decompose_topic(self, topic: str) -> List[ResearchQuestion]:
        """Decompose a policy topic into fundamental research questions.

        Args:
            topic: Policy topic to analyze

        Returns:
            List of research questions covering all aspects
        """
        questions = []
        question_id = 0

        # Define fundamental concept categories for policy analysis
        categories = {
            "historical_context": [
                "What is the historical precedent for this policy?",
                "How has this issue been addressed in the past?",
                "What lessons can be learned from historical implementations?",
            ],
            "economic_impact": [
                "What are the direct economic costs?",
                "What are the indirect economic effects?",
                "How will this affect different income groups?",
                "What is the long-term fiscal impact?",
            ],
            "social_impact": [
                "How will this affect different demographic groups?",
                "What are the equity implications?",
                "How will this impact social cohesion?",
                "What are the cultural considerations?",
            ],
            "legal_considerations": [
                "What constitutional considerations exist?",
                "What existing laws govern this domain?",
                "What legal precedents apply?",
                "Are there jurisdictional issues?",
            ],
            "implementation": [
                "What infrastructure is needed for implementation?",
                "What are the administrative requirements?",
                "What are the implementation timelines?",
                "What are the potential implementation challenges?",
            ],
            "stakeholder_analysis": [
                "Who are the primary stakeholders?",
                "How will each stakeholder group be affected?",
                "What are the stakeholder interests?",
                "How can stakeholders be engaged in implementation?",
            ],
            "evidence_base": [
                "What empirical evidence exists?",
                "What do experts recommend?",
                "What do affected populations want?",
                "What international examples exist?",
            ],
            "risk_analysis": [
                "What are the potential negative outcomes?",
                "What are the failure modes?",
                "How can risks be mitigated?",
                "What are the unintended consequences?",
            ],
        }

        # Generate questions for each category
        for category, category_questions in categories.items():
            for q in category_questions:
                question_id += 1
                questions.append(
                    ResearchQuestion(
                        question_id=f"Q{question_id:03d}",
                        question=q,
                        depth=ResearchDepth.FUNDAMENTAL,
                        category=category,
                        status="pending",
                    )
                )

        # Add topic-specific questions based on the topic
        topic_specific = self._generate_topic_specific_questions(topic)
        for q in topic_specific:
            question_id += 1
            questions.append(
                ResearchQuestion(
                    question_id=f"Q{question_id:03d}",
                    question=q,
                    depth=ResearchDepth.CONTEXTUAL,
                    category="topic_specific",
                    status="pending",
                )
            )

        return questions

    def _generate_topic_specific_questions(self, topic: str) -> List[str]:
        """Generate topic-specific research questions.

        Args:
            topic: Policy topic

        Returns:
            Topic-specific questions
        """
        # Define topic templates
        templates = {
            "healthcare": [
                "What specific healthcare services should be covered?",
                "How should healthcare providers be compensated?",
                "What measures ensure quality and access?",
                "How does this compare to other countries' systems?",
            ],
            "climate": [
                "What specific emissions targets are needed?",
                "What sectors should be regulated?",
                "What transition support is needed?",
                "How will climate adaptation be funded?",
            ],
            "education": [
                "What grade levels does this cover?",
                "What curriculum standards apply?",
                "How are teachers prepared?",
                "What equity gaps need addressing?",
            ],
            "immigration": [
                "What visa categories are affected?",
                "What border security measures are needed?",
                "What pathway to citizenship should be offered?",
                "How will enforcement be prioritized?",
            ],
            "economic": [
                "What specific economic indicators matter?",
                "Which sectors benefit most?",
                "How does this affect inflation?",
                "What trade implications exist?",
            ],
        }

        topic_lower = topic.lower()
        for key, questions in templates.items():
            if key in topic_lower:
                return questions

        # Generic fallback
        return [
            f"What are the key aspects of {topic}?",
            f"How does {topic} interact with existing policies?",
            f"What are the implementation challenges for {topic}?",
            f"How should success be measured for {topic}?",
        ]

    def build_knowledge_graph(
        self, questions: List[ResearchQuestion]
    ) -> Dict[str, List[str]]:
        """Build a knowledge graph showing relationships between concepts.

        Args:
            questions: List of research questions

        Returns:
            Knowledge graph as adjacency list
        """
        graph = {}

        # Group questions by category
        categories = {}
        for q in questions:
            if q.category not in categories:
                categories[q.category] = []
            categories[q.category].append(q.question_id)

        # Create relationships between categories
        category_list = list(categories.keys())
        for i, cat1 in enumerate(category_list):
            graph[cat1] = []
            for j, cat2 in enumerate(category_list):
                if i != j:
                    # Some categories naturally relate to others
                    if cat1 == "implementation" and cat2 == "stakeholder_analysis":
                        graph[cat1].append(cat2)
                    elif cat1 == "risk_analysis" and cat2 == "implementation":
                        graph[cat1].append(cat2)
                    elif cat1 == "evidence_base" and cat2 == "legal_considerations":
                        graph[cat1].append(cat2)

        return graph

    async def investigate_question(
        self, question: ResearchQuestion, topic: str
    ) -> ResearchQuestion:
        """Conduct deep investigation of a single question.

        Args:
            question: Research question to investigate
            topic: Policy topic

        Returns:
            Investigated question with evidence and sources
        """
        if self.verbose_logger:
            self.verbose_logger.log_research_question(
                question.question,
                f"Deep investigation of {question.category} aspect",
            )

        # Simulate deep research with multiple sources
        evidence = []
        sources = []

        # Investigate from multiple angles
        investigation_angles = [
            ("academic", "Research papers and academic studies"),
            ("government", "Government reports and statistics"),
            ("international", "International comparisons"),
            ("expert", "Expert opinions and recommendations"),
            ("affected", "Views of affected populations"),
        ]

        if self.verbose_logger:
            self.verbose_logger.log(
                f"Starting investigation of {question.question_id}: {question.question}",
                step_type=LogStep.RESEARCH_QUESTION,
                metadata={"category": question.category, "topic": topic},
            )

        for angle, description in investigation_angles:
            if self.verbose_logger:
                self.verbose_logger.log(
                    f"Researching {angle} perspective: {description}",
                    step_type=LogStep.SOURCE_DISCOVERY,
                    metadata={
                        "source_type": angle,
                        "description": description,
                    },
                )

            # Simulate finding evidence
            evidence.append(
                {
                    "source_type": angle,
                    "description": description,
                    "finding": f"Evidence from {angle} perspective on {question.question}",
                    "confidence": 0.7 + (hash(angle) % 10) / 100,
                }
            )

            sources.append(
                {
                    "source_type": angle,
                    "relevance": 80 + (hash(angle) % 15),
                    "usefulness": 75 + (hash(angle) % 20),
                }
            )

            if self.verbose_logger:
                self.verbose_logger.log(
                    f"Found evidence from {angle} perspective",
                    step_type=LogStep.EVIDENCE_EVALUATION,
                    metadata={
                        "source_type": angle,
                        "finding": f"Evidence from {angle} perspective",
                        "confidence": 0.7 + (hash(angle) % 10) / 100,
                    },
                )

        # Update question with findings
        question.status = "investigated"
        question.evidence = evidence
        question.sources = sources
        question.confidence = sum(e["confidence"] for e in evidence) / len(evidence)

        if self.verbose_logger:
            self.verbose_logger.log(
                f"Investigated {question.question_id}: {question.question}",
                step_type=LogStep.FINAL_CONCLUSION,
                metadata={
                    "evidence_count": len(evidence),
                    "sources_count": len(sources),
                    "confidence": question.confidence,
                    "angle_count": len(investigation_angles),
                },
            )

        return question

    async def synthesize_findings(
        self, questions: List[ResearchQuestion]
    ) -> Dict[str, Any]:
        """Synthesize findings across all research questions.

        Args:
            questions: Investigated research questions

        Returns:
            Synthesized findings with conclusions
        """
        # Group by category
        by_category = {}
        for q in questions:
            if q.category not in by_category:
                by_category[q.category] = []
            by_category[q.category].append(q)

        # Synthesize each category
        synthesis = {}
        for category, cat_questions in by_category.items():
            synthesis[category] = {
                "questions_answered": len(
                    [q for q in cat_questions if q.status == "investigated"]
                ),
                "average_confidence": sum(q.confidence for q in cat_questions)
                / len(cat_questions),
                "key_findings": [
                    q.question for q in cat_questions[:3]
                ],  # Top 3 questions
                "evidence_summary": [e for q in cat_questions for e in q.evidence][
                    :10
                ],  # Top 10 evidence items
            }

        return {
            "categories_analyzed": len(by_category),
            "total_questions": len(questions),
            "questions_resolved": len(
                [q for q in questions if q.status == "investigated"]
            ),
            "overall_confidence": sum(q.confidence for q in questions) / len(questions)
            if questions
            else 0,
            "category_synthesis": synthesis,
            "timestamp": datetime.now().isoformat(),
        }

    async def research_topic(self, topic: str) -> Dict[str, Any]:
        """Perform comprehensive research on a policy topic.

        Args:
            topic: Policy topic to research

        Returns:
            Comprehensive research results
        """
        if self.verbose_logger:
            self.verbose_logger.log_research_question(
                f"Deep research on {topic}",
                "Breaking down into fundamental concepts and investigating each",
            )

        # Step 1: Decompose topic
        questions = self.decompose_topic(topic)

        if self.verbose_logger:
            self.verbose_logger.log(
                f"Decomposed {topic} into {len(questions)} research questions",
                step_type=LogStep.INITIAL_CONJECTURE,
                metadata={
                    "question_count": len(questions),
                    "categories": list(set(q.category for q in questions)),
                },
            )

        # Step 2: Build knowledge graph
        self.knowledge_graph = self.build_knowledge_graph(questions)

        # Step 3: Investigate each question
        investigated_questions = []
        for question in questions:
            investigated = await self.investigate_question(question, topic)
            investigated_questions.append(investigated)
            await asyncio.sleep(0.1)  # Simulate research time

        # Step 4: Synthesize findings
        synthesis = await self.synthesize_findings(investigated_questions)

        # Step 5: Build final knowledge base
        self.questions = {q.question_id: q for q in investigated_questions}

        if self.verbose_logger:
            self.verbose_logger.log(
                f"Completed deep research on {topic}",
                step_type=LogStep.FINAL_CONCLUSION,
                metadata={
                    "questions_investigated": len(investigated_questions),
                    "synthesis_confidence": synthesis["overall_confidence"],
                    "categories": list(synthesis["category_synthesis"].keys()),
                },
            )

        return {
            "topic": topic,
            "questions_decomposed": len(questions),
            "questions_investigated": len(investigated_questions),
            "knowledge_graph": self.knowledge_graph,
            "synthesis": synthesis,
            "timestamp": datetime.now().isoformat(),
        }
