"""Verbose logging system for democratic machine learning.

This system tracks every step of reasoning with full context,
including prompts, sources, conjectures, and evidence evaluation.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class LogStep(Enum):
    """Types of reasoning steps."""

    RESEARCH_QUESTION = "research_question"
    SOURCE_DISCOVERY = "source_discovery"
    SOURCE_EVALUATION = "source_evaluation"
    INFORMATION_EXTRACTION = "information_extraction"
    INITIAL_CONJECTURE = "initial_conjecture"
    CONJECTURE_UPDATE = "conjecture_update"
    EVIDENCE_EVALUATION = "evidence_evaluation"
    FINAL_CONCLUSION = "final_conclusion"
    PROMPT_EXECUTION = "prompt_execution"


@dataclass
class SourceInfo:
    """Information about a discovered source."""

    url: str
    title: str
    relevance: float  # 0-100
    usefulness: float  # 0-100
    discovery_method: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Conjecture:
    """A conjecture with its reasoning and updates."""

    id: str
    initial_statement: str
    updates: List[Dict] = field(default_factory=list)
    evidence_supporting: List[str] = field(default_factory=list)
    evidence_contradicting: List[str] = field(default_factory=list)
    reasoning: str = ""
    inspiration_source: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PromptInfo:
    """Information about a prompt."""

    id: str
    prompt: str
    context: str = ""
    position_in_chain: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReasoningStep:
    """A step in the chain of reasoning."""

    step_type: LogStep
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source_ids: List[str] = field(default_factory=list)
    conjecture_id: Optional[str] = None
    prompt_id: Optional[str] = None


class VerboseLogger:
    """Comprehensive logging system for reasoning chains."""

    def __init__(self, output_dir: str = "output/logs") -> None:
        """Initialize the verbose logger.

        Args:
            output_dir: Directory for log output
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(
            output_dir, f"chain_of_reasoning_{self.timestamp}.log"
        )
        self.summary_file = os.path.join(output_dir, f"summary_{self.timestamp}.json")

        self.steps: List[ReasoningStep] = []
        self.sources: Dict[str, SourceInfo] = {}
        self.conjectures: Dict[str, Conjecture] = {}
        self.prompts: Dict[str, PromptInfo] = {}
        self.current_conjecture_id: Optional[str] = None

        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up file logging."""
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(message)s",
            filemode="w",
        )

    def log_step(
        self,
        step_type: LogStep,
        content: str,
        source_ids: Optional[List[str]] = None,
        conjecture_id: Optional[str] = None,
        prompt_id: Optional[str] = None,
    ) -> ReasoningStep:
        """Log a reasoning step.

        Args:
            step_type: Type of reasoning step
            content: Step content
            source_ids: Related source IDs
            conjecture_id: Related conjecture ID
            prompt_id: Related prompt ID

        Returns:
            The logged step
        """
        step = ReasoningStep(
            step_type=step_type,
            content=content,
            source_ids=source_ids or [],
            conjecture_id=conjecture_id,
            prompt_id=prompt_id,
        )
        self.steps.append(step)

        # Log to file
        self._write_log_entry(step)

        return step

    def discover_source(
        self,
        url: str,
        title: str,
        relevance: float,
        usefulness: float,
        discovery_method: str,
    ) -> str:
        """Discover and log a source.

        Args:
            url: Source URL
            title: Source title
            relevance: Relevance rating (0-100)
            usefulness: Usefulness rating (0-100)
            discovery_method: How source was found

        Returns:
            Source ID
        """
        source_id = f"S{len(self.sources) + 1:04d}"
        source = SourceInfo(
            url=url,
            title=title,
            relevance=relevance,
            usefulness=usefulness,
            discovery_method=discovery_method,
        )
        self.sources[source_id] = source

        self.log_step(
            LogStep.SOURCE_DISCOVERY,
            f"Discovered source: {title} ({url})",
            source_ids=[source_id],
        )

        return source_id

    def record_conjecture(
        self, statement: str, reasoning: str, inspiration: Optional[str] = None
    ) -> str:
        """Record an initial conjecture.

        Args:
            statement: Conjecture statement
            reasoning: Reasoning behind conjecture
            inspiration: What inspired this conjecture

        Returns:
            Conjecture ID
        """
        conjecture_id = f"C{len(self.conjectures) + 1:04d}"
        conjecture = Conjecture(
            id=conjecture_id,
            initial_statement=statement,
            reasoning=reasoning,
            inspiration_source=inspiration,
        )
        self.conjectures[conjecture_id] = conjecture
        self.current_conjecture_id = conjecture_id

        self.log_step(
            LogStep.INITIAL_CONJECTURE,
            f"Initial conjecture: {statement}",
            conjecture_id=conjecture_id,
        )

        return conjecture_id

    def update_conjecture(
        self,
        conjecture_id: str,
        update: str,
        new_reasoning: str,
        inspiration: Optional[str] = None,
    ) -> None:
        """Update an existing conjecture.

        Args:
            conjecture_id: ID of conjecture to update
            update: Update description
            new_reasoning: Updated reasoning
            inspiration: What inspired the update
        """
        if conjecture_id not in self.conjectures:
            raise ValueError(f"Conjecture {conjecture_id} not found")

        conjecture = self.conjectures[conjecture_id]
        conjecture.updates.append(
            {
                "update": update,
                "reasoning": new_reasoning,
                "inspiration": inspiration,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self.log_step(
            LogStep.CONJECTURE_UPDATE,
            f"Conjecture {conjecture_id} updated: {update}",
            conjecture_id=conjecture_id,
        )

    def add_evidence(
        self, conjecture_id: str, evidence: str, type: str = "supporting"
    ) -> None:
        """Add evidence to a conjecture.

        Args:
            conjecture_id: ID of conjecture
            evidence: Evidence statement
            type: 'supporting' or 'contradicting'
        """
        if conjecture_id not in self.conjectures:
            raise ValueError(f"Conjecture {conjecture_id} not found")

        conjecture = self.conjectures[conjecture_id]

        if type == "supporting":
            conjecture.evidence_supporting.append(evidence)
        else:
            conjecture.evidence_contradicting.append(evidence)

        self.log_step(
            LogStep.EVIDENCE_EVALUATION,
            f"Added {type} evidence to {conjecture_id}: {evidence}",
            conjecture_id=conjecture_id,
        )

    def record_prompt(self, prompt: str, context: str = "", position: int = 0) -> str:
        """Record a prompt execution.

        Args:
            prompt: Prompt text
            context: Context for prompt
            position: Position in prompt chain

        Returns:
            Prompt ID
        """
        prompt_id = f"P{len(self.prompts) + 1:04d}"
        prompt_info = PromptInfo(
            id=prompt_id, prompt=prompt, context=context, position_in_chain=position
        )
        self.prompts[prompt_id] = prompt_info

        self.log_step(
            LogStep.PROMPT_EXECUTION,
            f"Prompt {position}: {prompt[:100]}...",
            prompt_id=prompt_id,
        )

        return prompt_id

    def record_research_question(self, question: str, reasoning: str = "") -> None:
        """Record a research question.

        Args:
            question: Research question
            reasoning: Why this question matters
        """
        self.log_step(
            LogStep.RESEARCH_QUESTION,
            f"Research Question: {question}\nReasoning: {reasoning}",
        )

    def record_information_extraction(self, source_id: str, information: str) -> None:
        """Record information extracted from a source.

        Args:
            source_id: Source to extract from
            information: Extracted information
        """
        self.log_step(
            LogStep.INFORMATION_EXTRACTION,
            f"Extracted from {source_id}: {information}",
            source_ids=[source_id],
        )

    def record_final_conclusion(self, conclusion: str, confidence: float) -> None:
        """Record the final conclusion.

        Args:
            conclusion: Final conclusion
            confidence: Confidence level (0-100)
        """
        self.log_step(
            LogStep.FINAL_CONCLUSION,
            f"Final Conclusion: {conclusion}\nConfidence: {confidence}%",
        )

    def _write_log_entry(self, step: ReasoningStep) -> None:
        """Write a log entry to file.

        Args:
            step: Step to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        step_name = step.step_type.value.upper()

        entry = f"[{timestamp}] {step_name}: {step.content}"

        if step.source_ids:
            entry += f"\n  Sources: {', '.join(step.source_ids)}"
        if step.conjecture_id:
            entry += f"\n  Conjecture: {step.conjecture_id}"
        if step.prompt_id:
            entry += f"\n  Prompt: {step.prompt_id}"

        logging.info(entry)

    def save_summary(self) -> None:
        """Save machine-readable summary to JSON."""

        def convert_to_dict(obj: Any, visited: Optional[set] = None) -> Any:
            """Convert objects to dictionaries recursively with cycle detection."""
            if visited is None:
                visited = set()

            obj_id = id(obj)
            if obj_id in visited:
                return str(obj)
            visited.add(obj_id)

            if hasattr(obj, "__dict__"):
                result = {}
                for k, v in obj.__dict__.items():
                    if k.startswith("_"):
                        continue
                    result[k] = convert_to_dict(v, visited)
                return result
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, list):
                return [convert_to_dict(item, visited) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_dict(v, visited) for k, v in obj.items()}
            return obj

        summary = {
            "timestamp": self.timestamp,
            "total_steps": len(self.steps),
            "total_sources": len(self.sources),
            "total_conjectures": len(self.conjectures),
            "total_prompts": len(self.prompts),
            "sources": {k: convert_to_dict(v) for k, v in self.sources.items()},
            "conjectures": {k: convert_to_dict(v) for k, v in self.conjectures.items()},
            "prompts": {k: convert_to_dict(v) for k, v in self.prompts.items()},
            "steps": [convert_to_dict(s) for s in self.steps],
        }

        with open(self.summary_file, "w") as f:
            json.dump(summary, f, indent=2)

    def print_summary(self) -> None:
        """Print human-readable summary."""
        print(f"\n{'=' * 70}")
        print("VERBOSE LOGGING SUMMARY")
        print(f"{'=' * 70}")
        print(f"Timestamp: {self.timestamp}")
        print(f"Log File: {self.log_file}")
        print(f"Summary File: {self.summary_file}")
        print(f"\nStatistics:")
        print(f"  - Total steps: {len(self.steps)}")
        print(f"  - Total sources: {len(self.sources)}")
        print(f"  - Total conjectures: {len(self.conjectures)}")
        print(f"  - Total prompts: {len(self.prompts)}")
        print(f"{'=' * 70}\n")


def get_logger(output_dir: str = "output/logs") -> VerboseLogger:
    """Get a new verbose logger instance.

    Args:
        output_dir: Directory for log output

    Returns:
        Configured VerboseLogger instance
    """
    return VerboseLogger(output_dir)
