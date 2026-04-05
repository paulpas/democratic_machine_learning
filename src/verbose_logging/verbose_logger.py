"""Verbose logging system for democratic machine learning - the "brain" that traces every step of reasoning.

This system provides comprehensive logging with:
- Full context for all prompts
- Source discovery tracking with URLs and relevance ratings
- Conjecture tracking with updates and inspirations
- Complete chain of reasoning with timestamps
- Human-readable format with machine-readable summaries
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table


class LogStep(Enum):
    """Steps in the chain of reasoning."""

    RESEARCH_QUESTION = "Research Question Identified"
    SOURCE_DISCOVERY = "Source Discovered"
    INFORMATION_EXTRACTION = "Information Extracted from Source"
    INITIAL_CONJECTURE = "Initial Conjecture Formed"
    EVIDENCE_EVALUATION = "Evidence Evaluated"
    CONJECTURE_UPDATE = "Conjecture Updated"
    FINAL_CONCLUSION = "Final Conclusion Reached"
    PROMPT_USED = "Prompt Used in Chain"
    INSPIRATION = "Update Inspired By"
    SOURCE_USEFULNESS = "Source Usefulness Rated"
    SOURCE_RELEVANCE = "Source Relevance Rated"


@dataclass
class SourceInfo:
    """Information about a discovered source."""

    source_id: str
    url: str
    title: str
    source_type: str
    relevance_rating: int
    usefulness_rating: int
    discovery_method: str
    timestamp: datetime = field(default_factory=datetime.now)
    extracted_info: Optional[str] = None
    confidence: float = 0.0
    verification_status: str = "unverified"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "url": self.url,
            "title": self.title,
            "source_type": self.source_type,
            "relevance_rating": self.relevance_rating,
            "usefulness_rating": self.usefulness_rating,
            "discovery_method": self.discovery_method,
            "timestamp": self.timestamp.isoformat(),
            "extracted_info": self.extracted_info,
            "confidence": self.confidence,
            "verification_status": self.verification_status,
        }


@dataclass
class Conjecture:
    """A conjecture in the reasoning process."""

    conjecture_id: str
    statement: str
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 0.0
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    update_reason: Optional[str] = None
    inspired_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "conjecture_id": self.conjecture_id,
            "statement": self.statement,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "update_reason": self.update_reason,
            "inspired_by": self.inspired_by,
        }


@dataclass
class PromptInfo:
    """Information about a prompt used in reasoning."""

    prompt_id: str
    prompt_text: str
    purpose: str
    timestamp: datetime = field(default_factory=datetime.now, compare=False)
    context: Dict[str, Any] = field(default_factory=dict, compare=False)
    model_response: Optional[str] = None
    chain_position: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prompt_id": self.prompt_id,
            "prompt_text": self.prompt_text,
            "timestamp": self.timestamp.isoformat(),
            "purpose": self.purpose,
            "context": self.context,
            "model_response": self.model_response,
            "chain_position": self.chain_position,
        }


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain."""

    step_number: int
    step_type: LogStep
    timestamp: datetime = field(default_factory=datetime.now)
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    sources_referenced: List[str] = field(default_factory=list)
    conjectures_involved: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "step_type": self.step_type.value,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "metadata": self.metadata,
            "sources_referenced": self.sources_referenced,
            "conjectures_involved": self.conjectures_involved,
        }


class VerboseLogger:
    """Comprehensive logging system for democratic machine learning reasoning.

    This logger traces every step of the reasoning process, including:
    - Research questions identified
    - Sources discovered with URLs, relevance, and usefulness ratings
    - Conjectures formed and updated with reasoning
    - Prompts used in the chain of reasoning
    - Complete chain of thought with timestamps
    """

    def __init__(
        self,
        output_dir: str = "output/logs",
        log_prefix: str = "chain_of_reasoning",
        log_level: int = logging.DEBUG,
    ) -> None:
        """Initialize the verbose logger.

        Args:
            output_dir: Directory for log files
            log_prefix: Prefix for log files
            log_level: Logging level
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_prefix = log_prefix
        self.log_level = log_level

        # Initialize data storage
        self.reasoning_steps: List[ReasoningStep] = []
        self.sources: Dict[str, SourceInfo] = {}
        self.conjectures: Dict[str, Conjecture] = {}
        self.prompts: List[PromptInfo] = []
        self.step_counter = 0

        # Create timestamp for this session
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.output_dir / f"{log_prefix}_{self.session_timestamp}.log"
        self.summary_file = self.output_dir / f"summary_{self.session_timestamp}.json"

        # Setup Rich console for human-readable output
        self.console = Console()

        # Setup file logger
        self._setup_logger()

        self.log("Verbose logging system initialized", level=logging.INFO)
        self.log(f"Output directory: {self.output_dir}", level=logging.INFO)
        self.log(f"Log file: {self.log_file}", level=logging.INFO)

    def _setup_logger(self) -> None:
        """Setup logging configuration."""
        # Clear any existing handlers
        logging.root.handlers = []

        # Setup file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(self.log_level)

        # Setup formatter with timestamp
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)

        # Add handler to root logger
        logging.root.addHandler(file_handler)
        logging.root.setLevel(self.log_level)

        # Setup Rich handler for console
        rich_handler = RichHandler(
            console=self.console,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        rich_handler.setLevel(self.log_level)
        logging.root.addHandler(rich_handler)

    def log(
        self,
        message: str,
        level: int = logging.INFO,
        step_type: Optional[LogStep] = None,
        **metadata: Any,
    ) -> ReasoningStep:
        """Log a message with optional step type and metadata.

        Args:
            message: Log message
            level: Logging level
            step_type: Type of reasoning step (optional)
            **metadata: Additional metadata

        Returns:
            Created reasoning step
        """
        timestamp = datetime.now()

        # Increment step counter
        self.step_counter += 1

        # Create reasoning step
        step = ReasoningStep(
            step_number=self.step_counter,
            step_type=step_type or LogStep.RESEARCH_QUESTION,
            timestamp=timestamp,
            content=message,
            metadata=metadata,
        )

        self.reasoning_steps.append(step)

        # Log to file
        logger = logging.getLogger(__name__)
        logger.log(level, message)

        # Print to console with formatting
        self._print_step(step)

        return step

    def _print_step(self, step: ReasoningStep) -> None:
        """Print a reasoning step to console with formatting.

        Args:
            step: Reasoning step to print
        """
        timestamp = step.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        if step.step_type == LogStep.RESEARCH_QUESTION:
            self.console.print(
                f"\n[bold cyan][{timestamp}] STEP: {step.step_type.value}[/bold cyan]"
            )
            self.console.print(f"[white]{step.content}[/white]")

            if step.metadata.get("reasoning"):
                self.console.print(f"[dim]Reasoning: {step.metadata['reasoning']}[/dim]")

        elif step.step_type == LogStep.SOURCE_DISCOVERY:
            source = step.metadata.get("source", {})
            self.console.print(f"\n[bold green][{timestamp}] SOURCE DISCOVERY[/bold green]")
            self.console.print(f"[white]Title: {source.get('title', 'Unknown')}[/white]")
            self.console.print(f"[white]URL: {source.get('url', 'N/A')}[/white]")
            self.console.print(
                f"[white]Source Type: {source.get('source_type', 'Unknown')}[/white]"
            )
            self.console.print(f"[yellow]Relevance: {source.get('relevance_rating', 0)}%[/yellow]")
            self.console.print(
                f"[yellow]Usefulness: {source.get('usefulness_rating', 0)}%[/yellow]"
            )
            self.console.print(
                f"[dim]Discovered via: {source.get('discovery_method', 'N/A')}[/dim]"
            )

        elif step.step_type == LogStep.SOURCE_USEFULNESS:
            self.console.print(
                f"\n[bold yellow][{timestamp}] SOURCE USEFULNESS RATED[/bold yellow]"
            )
            self.console.print(f"[white]{step.content}[/white]")
            if step.metadata.get("rating"):
                self.console.print(f"[yellow]Rating: {step.metadata['rating']}%[/yellow]")

        elif step.step_type == LogStep.SOURCE_RELEVANCE:
            self.console.print(f"\n[bold yellow][{timestamp}] SOURCE RELEVANCE RATED[/bold yellow]")
            self.console.print(f"[white]{step.content}[/white]")
            if step.metadata.get("rating"):
                self.console.print(f"[yellow]Rating: {step.metadata['rating']}%[/yellow]")

        elif step.step_type == LogStep.INITIAL_CONJECTURE:
            self.console.print(
                f"\n[bold magenta][{timestamp}] INITIAL CONJECTURE FORMED[/bold magenta]"
            )
            self.console.print(f"[white]{step.content}[/white]")
            if step.metadata.get("confidence"):
                self.console.print(f"[cyan]Confidence: {step.metadata['confidence']:.0%}[/cyan]")

        elif step.step_type == LogStep.CONJECTURE_UPDATE:
            self.console.print(f"\n[bold blue][{timestamp}] CONJECTURE UPDATED[/bold blue]")
            self.console.print(f"[white]{step.content}[/white]")
            if step.metadata.get("updated_confidence"):
                self.console.print(
                    f"[cyan]Updated Confidence: {step.metadata['updated_confidence']:.0%}[/cyan]"
                )
            if step.metadata.get("update_reason"):
                self.console.print(f"[dim]Update Reason: {step.metadata['update_reason']}[/dim]")

        elif step.step_type == LogStep.EVIDENCE_EVALUATION:
            self.console.print(f"\n[bold cyan][{timestamp}] EVIDENCE EVALUATED[/bold cyan]")
            self.console.print(f"[white]{step.content}[/white]")
            if step.metadata.get("supporting"):
                self.console.print("[green]Supporting Evidence:[/green]")
                for evidence in step.metadata["supporting"]:
                    self.console.print(f"  ✓ {evidence}")
            if step.metadata.get("contradicting"):
                self.console.print("[red]Contradicting Evidence:[/red]")
                for evidence in step.metadata["contradicting"]:
                    self.console.print(f"  ✗ {evidence}")

        elif step.step_type == LogStep.FINAL_CONCLUSION:
            self.console.print(f"\n[bold green][{timestamp}] FINAL CONCLUSION[/bold green]")
            self.console.print(f"[white]{step.content}[/white]")

            # Print supporting evidence summary
            if step.metadata.get("supporting_evidence"):
                self.console.print("[green]Supporting Evidence:[/green]")
                for evidence in step.metadata["supporting_evidence"]:
                    self.console.print(f"  ✓ {evidence}")

            if step.metadata.get("confidence"):
                self.console.print(f"[cyan]Confidence: {step.metadata['confidence']:.0%}[/cyan]")

        elif step.step_type == LogStep.PROMPT_USED:
            self.console.print(f"\n[bold cyan][{timestamp}] PROMPT USED IN CHAIN[/bold cyan]")
            self.console.print(f"[white]Purpose: {step.metadata.get('purpose', 'N/A')}[/white]")
            self.console.print(
                f"[dim]Chain Position: {step.metadata.get('chain_position', 0)}[/dim]"
            )

            prompt_text = step.metadata.get("prompt", "")
            if prompt_text:
                self.console.print(f"[dim]Prompt: {prompt_text}[/dim]")

            if step.metadata.get("response"):
                response = step.metadata["response"]
                self.console.print(f"[dim]Response: {response}[/dim]")

        elif step.step_type == LogStep.INSPIRATION:
            self.console.print(f"\n[bold magenta][{timestamp}] UPDATE INSPIRED BY[/bold magenta]")
            self.console.print(f"[white]{step.content}[/white]")
            if step.metadata.get("inspired_by"):
                self.console.print(f"[dim]Inspired By: {step.metadata['inspired_by']}[/dim]")

        else:
            self.console.print(f"\n[{timestamp}] {step.step_type.value}")
            self.console.print(f"[white]{step.content}[/white]")

    def log_research_question(
        self, question: str, reasoning: Optional[str] = None
    ) -> ReasoningStep:
        """Log a research question with full context.

        Args:
            question: The research question
            reasoning: Why this question was identified (optional)

        Returns:
            Created reasoning step
        """
        metadata = {}
        if reasoning:
            metadata["reasoning"] = reasoning

        step = self.log(
            f"Question: {question}",
            step_type=LogStep.RESEARCH_QUESTION,
            **metadata,
        )

        step.metadata["full_question"] = question
        step.metadata["reasoning_context"] = reasoning

        return step

    def log_source_discovery(
        self,
        url: str,
        title: str,
        source_type: str,
        relevance_rating: int,
        usefulness_rating: int,
        discovery_method: str = "manual_search",
        extracted_info: Optional[str] = None,
        confidence: float = 0.0,
        verification_status: str = "unverified",
        source_description: Optional[str] = None,
    ) -> ReasoningStep:
        """Log a source discovery with comprehensive details.

        Args:
            url: Source URL
            title: Source title
            source_type: Type of source (paper, website, etc.)
            relevance_rating: Relevance rating 0-100
            usefulness_rating: Usefulness rating 0-100
            discovery_method: How source was discovered
            extracted_info: Extracted information from source (optional)
            confidence: Confidence in source (optional)
            verification_status: Source verification status
            source_description: Full description of source (optional)

        Returns:
            Created reasoning step
        """
        source_id = f"S{len(self.sources) + 1:03d}"

        source = SourceInfo(
            source_id=source_id,
            url=url,
            title=title,
            source_type=source_type,
            relevance_rating=relevance_rating,
            usefulness_rating=usefulness_rating,
            discovery_method=discovery_method,
            extracted_info=extracted_info,
            confidence=confidence,
            verification_status=verification_status,
        )

        self.sources[source_id] = source

        metadata = {
            "source_id": source_id,
            "source": {
                "url": url,
                "title": title,
                "source_type": source_type,
                "relevance_rating": relevance_rating,
                "usefulness_rating": usefulness_rating,
                "discovery_method": discovery_method,
            },
        }

        if extracted_info:
            metadata["extracted_info"] = (
                extracted_info[:500] if len(extracted_info) > 500 else extracted_info
            )

        if source_description:
            metadata["source_description"] = source_description

        step = self.log(
            f"Source: {title}",
            step_type=LogStep.SOURCE_DISCOVERY,
            **metadata,
        )

        step.metadata["source"] = source.to_dict()
        step.metadata["full_url"] = url
        step.metadata["source_id"] = source_id

        return step

    def log_source_usefulness(self, source_id: str, usefulness_rating: int) -> ReasoningStep:
        """Log a source usefulness rating.

        Args:
            source_id: ID of the source
            usefulness_rating: Usefulness rating 0-100

        Returns:
            Created reasoning step
        """
        if source_id not in self.sources:
            raise ValueError(f"Source {source_id} not found")

        self.sources[source_id].usefulness_rating = usefulness_rating

        return self.log(
            f"Source {source_id} usefulness rated: {usefulness_rating}%",
            step_type=LogStep.SOURCE_USEFULNESS,
            rating=usefulness_rating,
        )

    def log_source_relevance(self, source_id: str, relevance_rating: int) -> ReasoningStep:
        """Log a source relevance rating.

        Args:
            source_id: ID of the source
            relevance_rating: Relevance rating 0-100

        Returns:
            Created reasoning step
        """
        if source_id not in self.sources:
            raise ValueError(f"Source {source_id} not found")

        self.sources[source_id].relevance_rating = relevance_rating

        return self.log(
            f"Source {source_id} relevance rated: {relevance_rating}%",
            step_type=LogStep.SOURCE_RELEVANCE,
            rating=relevance_rating,
        )

    def log_initial_conjecture(self, conjecture: str, confidence: float = 0.0) -> ReasoningStep:
        """Log an initial conjecture.

        Args:
            conjecture: The initial conjecture statement
            confidence: Confidence in conjecture 0-1

        Returns:
            Created reasoning step
        """
        conjecture_id = f"C{len(self.conjectures) + 1:03d}"

        self.conjectures[conjecture_id] = Conjecture(
            conjecture_id=conjecture_id,
            statement=conjecture,
            confidence=confidence,
        )

        return self.log(
            conjecture,
            step_type=LogStep.INITIAL_CONJECTURE,
            confidence=confidence,
            conjecture_id=conjecture_id,
        )

    def log_conjecture_update(
        self,
        conjecture_id: str,
        updated_statement: str,
        update_reason: str,
        updated_confidence: float,
        inspired_by: Optional[str] = None,
        evidence_for: Optional[List[str]] = None,
        evidence_against: Optional[List[str]] = None,
        original_statement: Optional[str] = None,
    ) -> ReasoningStep:
        """Log a conjecture update with comprehensive reasoning.

        Args:
            conjecture_id: ID of the conjecture being updated
            updated_statement: The updated conjecture statement
            update_reason: Why the conjecture was updated
            updated_confidence: New confidence level 0-1
            inspired_by: What inspired the update (optional)
            evidence_for: Evidence supporting the update (optional)
            evidence_against: Evidence contradicting the original (optional)
            original_statement: The original conjecture statement (optional)

        Returns:
            Created reasoning step
        """
        if conjecture_id not in self.conjectures:
            raise ValueError(f"Conjecture {conjecture_id} not found")

        # Log original statement if provided
        if original_statement:
            self.log(
                f"Original conjecture: {original_statement}",
                step_type=LogStep.INITIAL_CONJECTURE,
                conjecture_id=conjecture_id,
            )

        # Update existing conjecture
        self.conjectures[conjecture_id].statement = updated_statement
        self.conjectures[conjecture_id].confidence = updated_confidence
        self.conjectures[conjecture_id].update_reason = update_reason
        self.conjectures[conjecture_id].inspired_by = inspired_by

        if evidence_for:
            self.conjectures[conjecture_id].supporting_evidence.extend(evidence_for)

        if evidence_against:
            self.conjectures[conjecture_id].contradicting_evidence.extend(evidence_against)

        metadata = {
            "conjecture_id": conjecture_id,
            "original_statement": original_statement,
            "updated_statement": updated_statement,
            "update_reason": update_reason,
            "updated_confidence": updated_confidence,
        }

        if inspired_by:
            metadata["inspired_by"] = inspired_by

        if evidence_for:
            metadata["evidence_for"] = evidence_for

        if evidence_against:
            metadata["evidence_against"] = evidence_against

        step = self.log(
            updated_statement,
            step_type=LogStep.CONJECTURE_UPDATE,
            **metadata,
        )

        step.metadata["inspired_by"] = inspired_by

        # Log inspiration separately if provided
        if inspired_by:
            self.log(
                f"Conjecture update inspired by: {inspired_by}",
                step_type=LogStep.INSPIRATION,
                inspired_by=inspired_by,
            )

        return step

    def log_evidence_evaluation(
        self,
        evidence_type: str,
        evidence_list: List[str],
        supporting: Optional[List[str]] = None,
        contradicting: Optional[List[str]] = None,
    ) -> ReasoningStep:
        """Log evidence evaluation.

        Args:
            evidence_type: Type of evidence (supporting, contradicting)
            evidence_list: List of evidence items
            supporting: Supporting evidence (optional)
            contradicting: Contradicting evidence (optional)

        Returns:
            Created reasoning step
        """
        content = f"Evidence evaluated: {evidence_type}"
        if len(evidence_list) <= 3:
            content += f" - {', '.join(evidence_list)}"
        else:
            content += f" - {len(evidence_list)} items"

        metadata = {
            "evidence_type": evidence_type,
            "evidence_count": len(evidence_list),
        }

        if supporting:
            metadata["supporting"] = supporting

        if contradicting:
            metadata["contradicting"] = contradicting

        return self.log(
            content,
            step_type=LogStep.EVIDENCE_EVALUATION,
            **metadata,
        )

    def log_final_conclusion(
        self, conclusion: str, supporting_evidence: List[str], confidence: float
    ) -> ReasoningStep:
        """Log a final conclusion.

        Args:
            conclusion: The final conclusion statement
            supporting_evidence: List of supporting evidence
            confidence: Confidence in conclusion 0-1

        Returns:
            Created reasoning step
        """
        return self.log(
            conclusion,
            step_type=LogStep.FINAL_CONCLUSION,
            supporting_evidence=supporting_evidence,
            confidence=confidence,
        )

    def log_prompt(
        self,
        prompt_text: str,
        purpose: str,
        model_response: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        chain_position: int = 0,
    ) -> ReasoningStep:
        """Log a prompt used in the reasoning chain.

        Args:
            prompt_text: The prompt text
            purpose: Purpose of this prompt
            model_response: Model's response (optional)
            context: Additional context (optional)
            chain_position: Position in chain (optional)

        Returns:
            Created reasoning step
        """
        prompt_id = f"P{len(self.prompts) + 1:03d}"

        prompt_info = PromptInfo(
            prompt_id=prompt_id,
            prompt_text=prompt_text,
            purpose=purpose,
            context=context or {},
            model_response=model_response,
            chain_position=chain_position,
        )

        self.prompts.append(prompt_info)

        metadata = {
            "prompt_id": prompt_id,
            "prompt": prompt_text,
            "purpose": purpose,
            "chain_position": chain_position,
        }

        if context:
            metadata["context"] = context

        if model_response:
            metadata["response"] = model_response

        return self.log(
            f"Prompt {prompt_id}: {purpose}",
            step_type=LogStep.PROMPT_USED,
            **metadata,
        )

    def save_summary(self) -> None:
        """Save summary to JSON file."""
        summary = {
            "session_timestamp": self.session_timestamp,
            "log_file": str(self.log_file),
            "reasoning_steps_count": len(self.reasoning_steps),
            "sources_count": len(self.sources),
            "conjectures_count": len(self.conjectures),
            "prompts_count": len(self.prompts),
            "reasoning_steps": [step.to_dict() for step in self.reasoning_steps],
            "sources": {k: v.to_dict() for k, v in self.sources.items()},
            "conjectures": {k: v.to_dict() for k, v in self.conjectures.items()},
            "prompts": [p.to_dict() for p in self.prompts],
        }

        with open(self.summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        self.log(
            f"Summary saved to: {self.summary_file}",
            level=logging.INFO,
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get summary as dictionary.

        Returns:
            Summary dictionary
        """
        return {
            "session_timestamp": self.session_timestamp,
            "log_file": str(self.log_file),
            "summary_file": str(self.summary_file),
            "reasoning_steps_count": len(self.reasoning_steps),
            "sources_count": len(self.sources),
            "conjectures_count": len(self.conjectures),
            "prompts_count": len(self.prompts),
        }

    def print_summary(self) -> None:
        """Print summary to console."""
        summary = self.get_summary()

        table = Table(title="Verbose Logging Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Session Timestamp", summary["session_timestamp"])
        table.add_row("Log File", summary["log_file"])
        table.add_row("Summary File", summary["summary_file"])
        table.add_row("Reasoning Steps", str(summary["reasoning_steps_count"]))
        table.add_row("Sources", str(summary["sources_count"]))
        table.add_row("Conjectures", str(summary["conjectures_count"]))
        table.add_row("Prompts", str(summary["prompts_count"]))

        self.console.print(Panel(table, title="[bold]Logging Summary[/bold]"))

    def print_full_chain(self) -> None:
        """Print the complete chain of reasoning to console."""
        self.console.print("\n[bold underline]COMPLETE CHAIN OF REASONING[/bold underline]\n")

        for step in self.reasoning_steps:
            self._print_step(step)
            self.console.print("")

        self.console.print("\n[bold underline]SOURCES DISCOVERED[/bold underline]")
        for source_id, source in self.sources.items():
            self.console.print(f"\n[bold]Source {source_id}:[/bold]")
            self.console.print(f"  Title: {source.title}")
            self.console.print(f"  URL: {source.url}")
            self.console.print(f"  Relevance: {source.relevance_rating}%")
            self.console.print(f"  Usefulness: {source.usefulness_rating}%")

        self.console.print("\n[bold underline]CONJECTURES[/bold underline]")
        for conjecture_id, conjecture in self.conjectures.items():
            self.console.print(f"\n[bold]Conjecture {conjecture_id}:[/bold]")
            self.console.print(f"  Statement: {conjecture.statement}")
            self.console.print(f"  Confidence: {conjecture.confidence:.0%}")
            if conjecture.update_reason:
                self.console.print(f"  Update Reason: {conjecture.update_reason}")

        self.console.print("\n[bold underline]PROMPTS USED[/bold underline]")
        for prompt in self.prompts:
            self.console.print(f"\n[bold]Prompt {prompt.prompt_id}:[/bold]")
            self.console.print(f"  Purpose: {prompt.purpose}")
            self.console.print(f"  Position: {prompt.chain_position}")


# Global logger instance
_verbose_logger: Optional[VerboseLogger] = None


def get_logger(
    output_dir: str = "output/logs",
    log_prefix: str = "chain_of_reasoning",
    level: int = logging.DEBUG,
) -> VerboseLogger:
    """Get or create the global verbose logger.

    Args:
        output_dir: Directory for log files
        log_prefix: Prefix for log files
        level: Logging level

    Returns:
        VerboseLogger instance
    """
    global _verbose_logger

    if _verbose_logger is None:
        _verbose_logger = VerboseLogger(output_dir, log_prefix, level)

    return _verbose_logger


def reset_logger() -> None:
    """Reset the global logger instance."""
    global _verbose_logger
    _verbose_logger = None
