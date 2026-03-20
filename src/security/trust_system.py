"""Security and trust verification utilities."""

from typing import Dict, List, Optional, Tuple
import numpy as np
from src.models.voter import Voter, VoterType
from src.models.policy import Policy
from src.utils.metrics import FairnessMetrics


class TrustScorer:
    """Calculates trust scores for voters based on behavior and data quality."""

    def __init__(
        self,
        base_score: float = 1.0,
        expertise_boost: float = 0.3,
        consistency_weight: float = 0.4,
        participation_weight: float = 0.3,
        evidence_weight: float = 0.3,
    ) -> None:
        """Initialize the trust scorer.

        Args:
            base_score: Base trust score
            expertise_boost: Maximum boost from expertise
            consistency_weight: Weight for preference consistency
            participation_weight: Weight for participation history
            evidence_weight: Weight for evidence quality
        """
        self.base_score = base_score
        self.expertise_boost = expertise_boost
        self.consistency_weight = consistency_weight
        self.participation_weight = participation_weight
        self.evidence_weight = evidence_weight

        self.trust_scores: Dict[str, float] = {}
        self.voter_consistency: Dict[str, float] = {}
        self.participation_history: Dict[str, int] = {}
        self.evidence_quality: Dict[str, float] = {}

    def calculate_trust_score(self, voter: Voter) -> float:
        """Calculate trust score for a voter.

        Args:
            voter: The voter to score

        Returns:
            Trust score (0-1)
        """
        score = self.base_score

        # Boost for verified expertise
        if voter.voter_type == VoterType.EXPERT:
            score += self.expertise_boost

        # Boost for consistency in preferences
        consistency = self.voter_consistency.get(voter.voter_id, 0.7)
        score += consistency * self.consistency_weight

        # Boost for participation
        participation = self.participation_history.get(voter.voter_id, 0)
        participation_factor = min(participation / 10, 1.0)
        score += participation_factor * self.participation_weight

        # Boost for evidence quality
        evidence = self.evidence_quality.get(voter.voter_id, 0.5)
        score += evidence * self.evidence_weight

        return min(1.0, score)

    def detect_anomaly(self, voter: Voter, threshold: float = 2.0) -> bool:
        """Detect if voter's preferences are anomalous.

        Args:
            voter: The voter to check
            threshold: Standard deviations for anomaly detection

        Returns:
            True if anomaly detected
        """
        preferences = list(voter.preferences.values())
        if not preferences:
            return False

        mean = np.mean(preferences)
        std = np.std(preferences) if np.std(preferences) > 0 else 1.0

        for pref in preferences:
            if abs(pref - mean) > threshold * std:
                return True

        return False

    def detect_inconsistency(self, voter: Voter, threshold: float = 0.5) -> bool:
        """Detect inconsistent preferences that may indicate manipulation.

        Args:
            voter: The voter to check
            threshold: Maximum allowed preference change

        Returns:
            True if inconsistency detected
        """
        if len(voter.preferences) < 2:
            return False

        pref_values = list(voter.preferences.values())
        pref_keys = list(voter.preferences.keys())

        for i, key1 in enumerate(pref_keys):
            for key2 in pref_keys[i + 1 :]:
                if abs(pref_values[i] - pref_values[i + 1]) > threshold:
                    continue

                # Check for contradictory preferences
                if (pref_values[i] > 0.5 and pref_values[i + 1] < -0.5) or (
                    pref_values[i] < -0.5 and pref_values[i + 1] > 0.5
                ):
                    return True

        return False

    def update_consistency(self, voter_id: str, consistency: float) -> None:
        """Update consistency score for a voter.

        Args:
            voter_id: Voter ID
            consistency: Consistency score (0-1)
        """
        self.voter_consistency[voter_id] = consistency

    def update_participation(self, voter_id: str, count: int) -> None:
        """Update participation count for a voter.

        Args:
            voter_id: Voter ID
            count: Number of participations
        """
        self.participation_history[voter_id] = count

    def update_evidence_quality(self, voter_id: str, quality: float) -> None:
        """Update evidence quality score for a voter.

        Args:
            voter_id: Voter ID
            quality: Evidence quality score (0-1)
        """
        self.evidence_quality[voter_id] = quality

    def get_trusted_voters(
        self, voters: List[Voter], min_trust: float = 0.7
    ) -> List[Voter]:
        """Get voters with trust scores above threshold.

        Args:
            voters: List of voters
            min_trust: Minimum trust threshold

        Returns:
            List of trusted voters
        """
        return [v for v in voters if self.calculate_trust_score(v) >= min_trust]


class EvidenceValidator:
    """Validates evidence and data sources for trustworthiness."""

    def __init__(
        self,
        source_verification: bool = True,
        cross_reference: bool = True,
        temporal_validation: bool = True,
    ) -> None:
        """Initialize the evidence validator.

        Args:
            source_verification: Verify data sources
            cross_reference: Cross-reference with other sources
            temporal_validation: Validate temporal consistency
        """
        self.source_verification = source_verification
        self.cross_reference = cross_reference
        self.temporal_validation = temporal_validation

        self.verified_sources: Dict[str, bool] = {}
        self.source_reputation: Dict[str, float] = {}

    def verify_source(self, source_id: str, source_type: str = "unknown") -> bool:
        """Verify a data source.

        Args:
            source_id: Source identifier
            source_type: Type of source (social_media, news, official, etc.)

        Returns:
            True if source is verified
        """
        # Official sources are automatically verified
        if source_type in ["official", "government", "academic"]:
            self.verified_sources[source_id] = True
            self.source_reputation[source_id] = 0.95
            return True

        # Social media sources need verification
        if source_type == "social_media":
            reputation = self._calculate_reputation(source_id)
            verified = reputation > 0.7
            self.verified_sources[source_id] = verified
            self.source_reputation[source_id] = reputation
            return verified

        return False

    def _calculate_reputation(self, source_id: str) -> float:
        """Calculate reputation score for a source."""
        # In real implementation, this would analyze:
        # - Historical accuracy
        # - Bias patterns
        # - Fact-checking history
        # - Cross-reference with other sources

        # Placeholder: use base reputation
        return 0.6

    def cross_reference(self, data: Dict, sources: List[str]) -> Tuple[bool, float]:
        """Cross-reference data with multiple sources.

        Args:
            data: Data to verify
            sources: List of source IDs

        Returns:
            Tuple of (verified, confidence)
        """
        if len(sources) < 2:
            return False, 0.0

        # In real implementation, compare data across sources
        # For now, assume verified if multiple sources agree
        verified_count = sum(1 for s in sources if self.verified_sources.get(s, False))

        confidence = verified_count / len(sources)
        return verified_count >= 2, confidence

    def validate_temporal(self, data_points: List[Dict]) -> Tuple[bool, float]:
        """Validate temporal consistency of data.

        Args:
            data_points: List of data points with timestamps

        Returns:
            Tuple of (consistent, confidence)
        """
        if len(data_points) < 2:
            return True, 1.0

        # Check for anomalies in temporal patterns
        values = [dp.get("value", 0) for dp in data_points]

        # Detect sudden large changes that may indicate manipulation
        for i in range(1, len(values)):
            if abs(values[i] - values[i - 1]) > 0.5:
                return False, 0.0

        return True, 0.9


class SocialInfluenceAnalyzer:
    """Analyzes social media influence and manipulation patterns."""

    def __init__(
        self, bot_threshold: float = 0.7, manipulation_threshold: float = 0.6
    ) -> None:
        """Initialize the social influence analyzer.

        Args:
            bot_threshold: Bot detection threshold
            manipulation_threshold: Manipulation detection threshold
        """
        self.bot_threshold = bot_threshold
        self.manipulation_threshold = manipulation_threshold

        self.bot_scores: Dict[str, float] = {}
        self.manipulation_scores: Dict[str, float] = {}

    def detect_bot(self, voter: Voter) -> Tuple[bool, float]:
        """Detect if voter behavior suggests bot activity.

        Args:
            voter: The voter to analyze

        Returns:
            Tuple of (is_bot, confidence)
        """
        # Analyze patterns that suggest bot activity:
        # - Rapid, identical preferences
        # - Unusual timing patterns
        # - Repetitive language
        # - Lack of expertise

        bot_score = 0.0

        # Check preference uniformity (bots often have uniform preferences)
        if len(voter.preferences) > 0:
            pref_values = list(voter.preferences.values())
            if np.std(pref_values) < 0.1:
                bot_score += 0.3

        # Check expertise (bots often lack expertise)
        if not voter.expertise:
            bot_score += 0.2

        # Check voting weight (bots may have unusual weights)
        if voter.voting_weight != 1.0:
            bot_score += 0.1

        is_bot = bot_score >= self.bot_threshold
        return is_bot, bot_score

    def detect_manipulation(self, voter: Voter) -> Tuple[bool, float]:
        """Detect if voter preferences may be manipulated.

        Args:
            voter: The voter to analyze

        Returns:
            Tuple of (manipulated, confidence)
        """
        manipulation_score = 0.0

        # Check for extreme preferences (may indicate manipulation)
        for pref in voter.preferences.values():
            if abs(pref) > 0.95:
                manipulation_score += 0.2

        # Check for sudden preference changes (in real implementation)
        # This would track history of preference changes

        # Check for suspicious patterns
        if (
            len(voter.preferences) == 1
            and abs(list(voter.preferences.values())[0]) > 0.8
        ):
            manipulation_score += 0.3

        is_manipulated = manipulation_score >= self.manipulation_threshold
        return is_manipulated, manipulation_score

    def analyze_influence_network(self, voters: List[Voter]) -> Dict[str, float]:
        """Analyze influence network for manipulation patterns.

        Args:
            voters: List of voters

        Returns:
            Dictionary of influence scores
        """
        # In real implementation, this would:
        # - Map voter connections
        # - Identify influence centers
        # - Detect coordinated manipulation
        # - Track information flow

        # Placeholder implementation
        return {v.voter_id: 0.5 for v in voters}


class ObjectiveGovernanceEngine:
    """Engine for objective governance that resists manipulation."""

    def __init__(
        self,
        trust_scorer: Optional[TrustScorer] = None,
        evidence_validator: Optional[EvidenceValidator] = None,
        influence_analyzer: Optional[SocialInfluenceAnalyzer] = None,
    ) -> None:
        """Initialize the objective governance engine.

        Args:
            trust_scorer: Trust scoring component
            evidence_validator: Evidence validation component
            influence_analyzer: Social influence analyzer
        """
        self.trust_scorer = trust_scorer or TrustScorer()
        self.evidence_validator = evidence_validator or EvidenceValidator()
        self.influence_analyzer = influence_analyzer or SocialInfluenceAnalyzer()
        self.trusted_voters: List[Voter] = []

    def filter_voters(self, voters: List[Voter]) -> List[Voter]:
        """Filter voters based on trust and influence analysis.

        Args:
            voters: List of voters to filter

        Returns:
            Filtered list of trusted voters
        """
        self.trusted_voters = []

        for voter in voters:
            # Check for bot activity
            is_bot, bot_confidence = self.influence_analyzer.detect_bot(voter)
            if is_bot:
                continue

            # Check for manipulation
            is_manipulated, manipulation_confidence = (
                self.influence_analyzer.detect_manipulation(voter)
            )
            if is_manipulated:
                continue

            # Calculate trust score
            trust_score = self.trust_scorer.calculate_trust_score(voter)
            if trust_score >= 0.7:
                self.trusted_voters.append(voter)

        return self.trusted_voters

    def get_trusted_voters(self) -> List[Voter]:
        """Get currently trusted voters.

        Returns:
            List of trusted voters
        """
        return self.trusted_voters
