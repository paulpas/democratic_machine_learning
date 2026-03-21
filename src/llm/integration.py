"""LLM integration for democratic machine learning.

This module provides LLM-based reasoning, analysis, and conjecture formation
using a llama.cpp endpoint at http://localhost:8080.
"""

import json
import os
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error


class LLMClient:
    """Client for LLM-based reasoning using llama.cpp endpoint."""

    def __init__(self, endpoint: Optional[str] = None, model: Optional[str] = None):
        """Initialize LLM client.

        Args:
            endpoint: Llama.cpp endpoint URL (default: http://localhost:8080)
            model: Model name to use (for logging purposes)
        """
        self.endpoint = endpoint or os.environ.get(
            "LLAMA_CPP_ENDPOINT", "http://localhost:8080"
        )
        self.model = model or os.environ.get("LLAMA_MODEL", "llama.cpp-model")
        self.timeout = int(os.environ.get("LLAMA_TIMEOUT", "120"))

        # Test connection to endpoint
        self.available = self._test_connection()
        if self.available:
            print(f"Initialized llama.cpp client with endpoint: {self.endpoint}")
        else:
            print(
                f"Warning: Could not connect to llama.cpp endpoint at {self.endpoint} - LLM will use fallback"
            )

    def _test_connection(self) -> bool:
        """Test if the llama.cpp endpoint is available."""
        try:
            # Simple health check - try to make a minimal request
            data = json.dumps(
                {"prompt": "test", "max_tokens": 1, "temperature": 0.0}
            ).encode("utf-8")

            req = urllib.request.Request(
                f"{self.endpoint}/completion",
                data=data,
                headers={"Content-Type": "application/json"},
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                return response.getcode() == 200
        except Exception:
            return False

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
        if self.available:
            prompt = self._build_reasoning_prompt(
                context, research_questions, principles
            )

            try:
                data = json.dumps(
                    {
                        "prompt": prompt,
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                        "stop": ["</s>", "\n\n\n"],
                    }
                ).encode("utf-8")

                req = urllib.request.Request(
                    f"{self.endpoint}/completion",
                    data=data,
                    headers={"Content-Type": "application/json"},
                )

                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    return result.get("content", "")
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
        if self.available:
            prompt = self._build_conjecture_prompt(question, context, evidence)

            try:
                data = json.dumps(
                    {
                        "prompt": prompt,
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                        "stop": ["</s>", "\n\n\n"],
                    }
                ).encode("utf-8")

                req = urllib.request.Request(
                    f"{self.endpoint}/completion",
                    data=data,
                    headers={"Content-Type": "application/json"},
                )

                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    response_text = result.get("content", "")
                    return self._parse_conjecture_response(response_text)
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
        if self.available:
            prompt = self._build_policy_analysis_prompt(topic, research_data)

            try:
                data = json.dumps(
                    {
                        "prompt": prompt,
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                        "stop": ["</s>", "\n\n\n"],
                    }
                ).encode("utf-8")

                req = urllib.request.Request(
                    f"{self.endpoint}/completion",
                    data=data,
                    headers={"Content-Type": "application/json"},
                )

                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    response_text = result.get("content", "")
                    return self._parse_analysis_response(response_text)
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
        # Extract structured information from LLM response
        lines = response.strip().split("\n")
        statement = ""
        confidence = 0.75
        supporting_evidence = []
        contradicting_evidence = []

        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for section headers
            if line.lower().startswith("statement:") or line.lower().startswith(
                "conjecture:"
            ):
                current_section = "statement"
                statement = line.split(":", 1)[1].strip() if ":" in line else ""
            elif line.lower().startswith("confidence:"):
                current_section = "confidence"
                try:
                    conf_str = line.split(":", 1)[1].strip()
                    # Extract numeric value
                    import re

                    num_match = re.search(r"(\d+\.?\d*)", conf_str)
                    if num_match:
                        confidence = float(num_match.group(1))
                        # Ensure it's in 0-1 range
                        if confidence > 1.0:
                            confidence = (
                                confidence / 100.0 if confidence <= 100.0 else 1.0
                            )
                except:
                    confidence = 0.75
            elif line.lower().startswith(
                "supporting evidence:"
            ) or line.lower().startswith("supports:"):
                current_section = "supporting"
            elif line.lower().startswith(
                "contradicting evidence:"
            ) or line.lower().startswith("contradicts:"):
                current_section = "contradicting"
            elif (
                line.startswith("- ") or line.startswith("* ") or line.startswith("• ")
            ):
                # List item
                item = line[2:].strip()
                if current_section == "supporting":
                    supporting_evidence.append(item)
                elif current_section == "contradicting":
                    contradicting_evidence.append(item)
            elif current_section == "statement" and not line.startswith("#"):
                # Continue building statement
                if statement:
                    statement += " " + line
                else:
                    statement = line

        # If we didn't find a clear statement, use the first substantial line
        if not statement:
            for line in lines:
                if len(line.strip()) > 10 and not line.startswith("#"):
                    statement = line.strip()
                    break

        # Default fallback
        if not statement:
            statement = "Based on the available evidence, a reasonable conjecture can be formed."

        return {
            "statement": statement[:500] if statement else "No conjecture formed",
            "confidence": max(0.0, min(1.0, confidence)),  # Clamp to 0-1
            "supporting_evidence": supporting_evidence[:10],  # Limit to 10 items
            "contradicting_evidence": contradicting_evidence[:10],  # Limit to 10 items
            "update_reason": "LLM reasoning via llama.cpp",
        }

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse analysis response from LLM."""
        # Extract structured information from LLM response
        lines = response.strip().split("\n")
        findings = ""
        consensus = 0.75
        recommendations = []
        implementation = []
        outcomes = []

        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for section headers
            if line.lower().startswith("findings:") or line.lower().startswith(
                "key findings:"
            ):
                current_section = "findings"
                findings = line.split(":", 1)[1].strip() if ":" in line else ""
            elif line.lower().startswith("consensus:"):
                current_section = "consensus"
                try:
                    conf_str = line.split(":", 1)[1].strip()
                    # Extract numeric value
                    import re

                    num_match = re.search(r"(\d+\.?\d*)", conf_str)
                    if num_match:
                        consensus = float(num_match.group(1))
                        # Ensure it's in 0-1 range
                        if consensus > 1.0:
                            consensus = consensus / 100.0 if consensus <= 100.0 else 1.0
                except:
                    consensus = 0.75
            elif line.lower().startswith("recommendations:") or line.lower().startswith(
                "recommend:"
            ):
                current_section = "recommendations"
            elif line.lower().startswith("implementation:") or line.lower().startswith(
                "implement:"
            ):
                current_section = "implementation"
            elif line.lower().startswith("outcomes:") or line.lower().startswith(
                "expected outcomes:"
            ):
                current_section = "outcomes"
            elif (
                line.startswith("- ") or line.startswith("* ") or line.startswith("• ")
            ):
                # List item
                item = line[2:].strip()
                if current_section == "recommendations":
                    recommendations.append(item)
                elif current_section == "implementation":
                    implementation.append(item)
                elif current_section == "outcomes":
                    outcomes.append(item)
            elif current_section == "findings" and not line.startswith("#"):
                # Continue building findings
                if findings:
                    findings += " " + line
                else:
                    findings = line

        # If we didn't find clear sections, use heuristics
        if not findings:
            # Use first substantial paragraph as findings
            for line in lines:
                if (
                    len(line.strip()) > 15
                    and not line.startswith("#")
                    and not line.lower().startswith(
                        ("recommend", "implement", "outcome")
                    )
                ):
                    findings = line.strip()
                    break

        # Default fallbacks
        if not findings:
            findings = f"Analysis of {topic} based on available research data."
        if not recommendations:
            recommendations = [
                "Implement policy with phased approach",
                "Monitor outcomes and adjust as needed",
            ]
        if not implementation:
            implementation = [
                "Phase 1: Planning and stakeholder engagement",
                "Phase 2: Pilot implementation",
                "Phase 3: Full rollout",
            ]
        if not outcomes:
            outcomes = [
                "Improved governance",
                "Increased citizen satisfaction",
                "Better policy outcomes",
            ]

        return {
            "findings": findings[:1000] if findings else "No findings",
            "consensus": max(0.0, min(1.0, consensus)),  # Clamp to 0-1
            "recommendations": recommendations[:10],  # Limit to 10 items
            "implementation": implementation[:10],  # Limit to 10 items
            "outcomes": outcomes[:10],  # Limit to 10 items
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
