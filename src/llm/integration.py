"""LLM integration for democratic machine learning.

This module provides LLM-based reasoning, analysis, and conjecture formation
using the Anthropic Claude model.
"""

import os
from typing import Any, Dict, List, Optional

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class LLMClient:
    """Client for LLM-based reasoning."""

    def __init__(self, model: Optional[str] = None):
        """Initialize LLM client.

        Args:
            model: Model to use (default: from ANTHROPIC_MODEL env var)
        """
        self.model = model or os.environ.get(
            "ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"
        )
        self.client = None

        if ANTHROPIC_AVAILABLE:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)
                print(f"Initialized Anthropic client with model: {self.model}")
            else:
                print("Warning: ANTHROPIC_API_KEY not set - LLM will use fallback")
        else:
            print("Warning: anthropic library not installed - LLM will use fallback")

    def generate_reasoning(
        self,
        context: Dict[str, Any],
        research_questions: List[str],
        principles: List[str],
        max_tokens: int = 4096,
    ) -> str:
        """Generate governance reasoning using LLM.

        Args:
            context: Governance context (population, diversity, etc.)
            research_questions: List of research questions
            principles: List of core principles
            max_tokens: Maximum tokens for response

        Returns:
            Generated reasoning text
        """
        if self.client:
            prompt = self._build_reasoning_prompt(
                context, research_questions, principles
            )

            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                # Handle different content types
                if hasattr(message.content[0], "text"):
                    return message.content[0].text
                return str(message.content[0])
            except Exception as e:
                print(f"LLM error: {e}")
                return self._generate_fallback_reasoning(context, principles)
        else:
            return self._generate_fallback_reasoning(context, principles)

    def form_conjecture(
        self,
        question: str,
        context: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """Form a conjecture from evidence using LLM.

        Args:
            question: Research question
            context: Context information
            evidence: List of evidence items
            max_tokens: Maximum tokens for response

        Returns:
            Conjecture with statement, confidence, and supporting evidence
        """
        if self.client:
            prompt = self._build_conjecture_prompt(question, context, evidence)

            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                return self._parse_conjecture_response(message.content[0].text)
            except Exception as e:
                print(f"LLM error: {e}")
                return self._form_fallback_conjecture(question, evidence)
        else:
            return self._form_fallback_conjecture(question, evidence)

    def analyze_policy(
        self, topic: str, research_data: Dict[str, Any], max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """Analyze policy using LLM.

        Args:
            topic: Policy topic
            research_data: Research data
            max_tokens: Maximum tokens for response

        Returns:
            Analysis with recommendations
        """
        if self.client:
            prompt = self._build_policy_analysis_prompt(topic, research_data)

            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                return self._parse_analysis_response(message.content[0].text)
            except Exception as e:
                print(f"LLM error: {e}")
                return self._generate_fallback_analysis(topic, research_data)
        else:
            return self._generate_fallback_analysis(topic, research_data)

    def _build_reasoning_prompt(
        self,
        context: Dict[str, Any],
        research_questions: List[str],
        principles: List[str],
    ) -> str:
        """Build reasoning prompt for LLM."""
        return f"""You are an expert in democratic governance and political philosophy.

GOVERNANCE CONTEXT:
- Population: {context.get("population", "N/A")}
- Diversity Index: {context.get("diversity_index", "N/A")}
- Urban Ratio: {context.get("urban_ratio", "N/A")}

RESEARCH QUESTIONS:
{chr(10).join(f"- {q}" for q in research_questions)}

CORE PRINCIPLES:
{chr(10).join(f"- {p}" for p in principles)}

Based on this context, research questions, and principles, provide comprehensive reasoning for designing a democratic governance system. Your reasoning should:
1. Analyze the challenges posed by the context
2. Explain how the principles address these challenges
3. Recommend specific governance mechanisms
4. Address potential anti-patterns

Provide your reasoning in a structured format."""

    def _build_conjecture_prompt(
        self, question: str, context: Dict[str, Any], evidence: List[Dict[str, Any]]
    ) -> str:
        """Build conjecture formation prompt."""
        return f"""You are forming a conjecture based on evidence.

QUESTION: {question}

CONTEXT:
- Population: {context.get("population", "N/A")}
- Diversity Index: {context.get("diversity_index", "N/A")}

EVIDENCE:
{chr(10).join(f"- {e.get('finding', 'N/A')} (confidence: {e.get('confidence', 0):.2f})" for e in evidence)}

Form a conjecture that answers the question based on this evidence. Include:
1. The conjecture statement
2. Confidence level (0-1)
3. Supporting evidence from the provided evidence
4. Any contradicting evidence found"""

    def _build_policy_analysis_prompt(
        self, topic: str, research_data: Dict[str, Any]
    ) -> str:
        """Build policy analysis prompt."""
        return f"""You are analyzing a policy topic for democratic decision-making.

TOPIC: {topic}

RESEARCH DATA:
{self._format_research_data(research_data)}

Provide analysis including:
1. Key findings from the research
2. Consensus levels across different perspectives
3. Policy recommendations
4. Implementation considerations
5. Expected outcomes"""

    def _format_research_data(self, data: Dict[str, Any]) -> str:
        """Format research data for prompt."""
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for subkey, subval in value.items():
                    lines.append(f"  - {subkey}: {subval}")
            else:
                lines.append(f"{key}: {value}")
        return chr(10).join(lines)

    def _parse_conjecture_response(self, response: str) -> Dict[str, Any]:
        """Parse conjecture response from LLM."""
        # Simple parsing - in production, use structured output
        conjecture = {
            "statement": response[:200] if response else "No conjecture formed",
            "confidence": 0.75,
            "supporting_evidence": ["LLM analysis"],
            "contradicting_evidence": [],
            "update_reason": "LLM reasoning",
        }
        return conjecture

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse analysis response from LLM."""
        return {
            "findings": response[:500] if response else "No findings",
            "consensus": 0.75,
            "recommendations": ["LLM-generated"],
            "implementation": ["LLM-generated"],
            "outcomes": ["LLM-generated"],
        }

    def _generate_fallback_reasoning(
        self, context: Dict[str, Any], principles: List[str]
    ) -> str:
        """Generate fallback reasoning when LLM unavailable."""
        return f"""Based on comprehensive research into historical governance models and anti-patterns, 
this system is designed to serve ALL citizens in a virtuous society.

Key Principles Applied:
{chr(10).join(f"- {p}" for p in principles)}

Context Analysis:
- Population: {context.get("population", "N/A")} citizens
- Diversity Index: {context.get("diversity_index", "N/A")} (high diversity requires inclusive mechanisms)
- Urban Ratio: {context.get("urban_ratio", "N/A")}

Design Rationale:
1. Multi-tiered representation (Local → State → National) ensures geographic balance
2. Weighted proportional representation balances majority rule with minority protection
3. Approval voting allows expressing support for multiple options
4. 55% approval threshold prevents tyranny of the majority
5. Continuous feedback enables adaptation to changing needs
6. Full transparency builds trust and prevents corruption

Anti-Pattern Prevention:
- Power concentration: Prevented through tiered representation and term limits
- Elite capture: Prevented through campaign finance reform and transparency
- Populist decay: Prevented through evidence-based decision-making
- Information manipulation: Prevented through source verification and oversight"""

    def _form_fallback_conjecture(
        self, question: str, evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Form fallback conjecture when LLM unavailable."""
        return {
            "statement": f"Based on available evidence for: {question}",
            "confidence": 0.7 if evidence else 0.5,
            "supporting_evidence": [
                e.get("finding", "No finding") for e in evidence[:3]
            ],
            "contradicting_evidence": [],
            "update_reason": "Fallback reasoning",
        }

    def _generate_fallback_analysis(
        self, topic: str, research_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback analysis when LLM unavailable."""
        return {
            "findings": f"Analysis of {topic} based on research data",
            "consensus": 0.75,
            "recommendations": ["Implement policy with phased approach"],
            "implementation": [
                "Phase 1: Planning",
                "Phase 2: Implementation",
                "Phase 3: Evaluation",
            ],
            "outcomes": ["Improved governance", "Increased citizen satisfaction"],
        }
