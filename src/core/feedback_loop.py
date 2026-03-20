"""
Feedback loop for adaptive democratic decision-making.

This module implements self-balancing mechanisms that adjust the system
based on outcomes and fairness metrics.
"""

from typing import Dict, List, Optional
from src.models.decision import Decision
from src.models.voter import Voter
from src.models.region import Region
from src.utils.metrics import FairnessMetrics


class FeedbackLoop:
    """Implements feedback mechanisms for adaptive decision-making."""

    def __init__(
        self,
        learning_rate: float = 0.1,
        fairness_target: float = 0.7,
        stability_threshold: float = 0.2,
    ) -> None:
        """Initialize the feedback loop.

        Args:
            learning_rate: How quickly the system adapts
            fairness_target: Target fairness score
            stability_threshold: Maximum allowed variance in fairness
        """
        self.learning_rate = learning_rate
        self.fairness_target = fairness_target
        self.stability_threshold = stability_threshold

        self.fairness_metrics = FairnessMetrics()
        self.history: List[Dict] = []
        self.adaptation_factors: Dict[str, float] = {}

    def evaluate_decision(self, decision: Decision) -> Dict:
        """Evaluate a decision and generate feedback.

        Args:
            decision: The decision to evaluate

        Returns:
            Dictionary with evaluation metrics
        """
        fairness = self.fairness_metrics.calculate_fairness(decision, {}, {})

        effectiveness = self._calculate_effectiveness(decision)

        return {
            "decision_id": decision.decision_id,
            "fairness": fairness,
            "effectiveness": effectiveness,
            "balance": (fairness + effectiveness) / 2,
        }

    def _calculate_effectiveness(self, decision: Decision) -> float:
        """Calculate effectiveness score for a decision.

        Args:
            decision: The decision to evaluate

        Returns:
            Effectiveness score (0-1)
        """
        if decision.confidence < 0.5:
            return 0.0

        if decision.outcome == "approved":
            return decision.confidence
        else:
            return 1.0 - decision.confidence

    def adapt_weighting(
        self, region_id: str, fairness_score: float, effectiveness_score: float
    ) -> None:
        """Adapt weighting system based on feedback.

        Args:
            region_id: The region to adapt
            fairness_score: Current fairness score
            effectiveness_score: Current effectiveness score
        """
        if region_id not in self.adaptation_factors:
            self.adaptation_factors[region_id] = 1.0

        gap = self.fairness_target - fairness_score
        adaptation = gap * self.learning_rate

        self.adaptation_factors[region_id] *= 1 + adaptation

    def get_adaptation_factor(self, region_id: str) -> float:
        """Get the adaptation factor for a region.

        Args:
            region_id: The region to get factor for

        Returns:
            Adaptation factor (default 1.0)
        """
        return self.adaptation_factors.get(region_id, 1.0)

    def record_history(self, metrics: Dict) -> None:
        """Record decision metrics for historical analysis.

        Args:
            metrics: Dictionary of metrics to record
        """
        self.history.append(
            {**metrics, "adaptation_factors": self.adaptation_factors.copy()}
        )

    def get_trends(self, window: int = 10) -> Dict:
        """Get trends from recent history.

        Args:
            window: Number of recent decisions to analyze

        Returns:
            Dictionary with trend metrics
        """
        recent = self.history[-window:] if len(self.history) > window else self.history

        if not recent:
            return {}

        return {
            "avg_fairness": sum(h.get("fairness", 0) for h in recent) / len(recent),
            "avg_effectiveness": sum(h.get("effectiveness", 0) for h in recent)
            / len(recent),
            "avg_balance": sum(h.get("balance", 0) for h in recent) / len(recent),
            "variance": sum(
                (
                    h.get("fairness", 0)
                    - sum(r.get("fairness", 0) for r in recent) / len(recent)
                )
                ** 2
                for h in recent
            )
            / len(recent),
        }
