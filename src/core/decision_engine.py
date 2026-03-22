"""Core decision engine for democratic decision-making."""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from src.models.voter import Voter, VoterType
from src.models.policy import Policy
from src.models.region import Region
from src.models.decision import Decision
from src.utils.metrics import FairnessMetrics
from src.policy.policy_tree import PolicyTree, PolicyHierarchyLevel
from src.history.anti_patterns import AntiPatternDatabase
from src.security.trust_system import (
    TrustScorer,
    EvidenceValidator,
    SocialInfluenceAnalyzer,
)
from src.llm.integration import LLMClient
from src.data.social_narrative_collector import SocialNarrativeCollector


class DecisionEngine:
    """Main engine for making democratic decisions."""

    def __init__(self, fairness_threshold: float = 0.7) -> None:
        """Initialize the decision engine.

        Args:
            fairness_threshold: Minimum fairness score required for decisions
        """
        self.fairness_threshold = fairness_threshold
        self.voters: Dict[str, Voter] = {}
        self.policies: Dict[str, Policy] = {}
        self.regions: Dict[str, Region] = {}
        self.decisions: List[Decision] = []
        self.fairness_metrics = FairnessMetrics()

        # Initialize LLM client for intelligent analysis
        self.llm_client = LLMClient()

        # Initialize social narrative collector for real-world data
        self.social_collector = SocialNarrativeCollector()

        # Initialize anti-pattern database
        self.anti_pattern_db = AntiPatternDatabase()

        # Initialize policy tree and anti-pattern detection
        self.policy_tree = PolicyTree(self.anti_pattern_db)

        # Initialize trust and security systems
        self.trust_scorer = TrustScorer()
        self.evidence_validator = EvidenceValidator()
        self.influence_analyzer = SocialInfluenceAnalyzer()

    def register_voter(self, voter: Voter) -> None:
        """Register a voter in the system."""
        self.voters[voter.voter_id] = voter

    def register_policy(self, policy: Policy) -> None:
        """Register a policy in the system."""
        self.policies[policy.policy_id] = policy

    def register_region(self, region: Region) -> None:
        """Register a region in the system."""
        self.regions[region.region_id] = region

    def make_decision(
        self, policy_id: str, region_id: str, decision_type: str = "direct_vote"
    ) -> Decision:
        """Make a decision on a policy for a specific region.

        Args:
            policy_id: ID of the policy to decide on
            region_id: ID of the region to apply the decision to
            decision_type: Type of decision-making method

        Returns:
            Decision object with the outcome
        """
        policy = self.policies.get(policy_id)
        region = self.regions.get(region_id)

        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
        if not region:
            raise ValueError(f"Region {region_id} not found")

        # Get voters in region
        voters_in_region = [
            v
            for v in self.voters.values()
            if v.region_id == region_id or region_id in v.region_id
        ]

        votes_for = 0
        votes_against = 0

        for voter in voters_in_region:
            preference = voter.get_preference(policy_id)
            if preference > 0:
                votes_for += voter.voting_weight
            elif preference < 0:
                votes_against += voter.voting_weight

        total_weight = votes_for + votes_against
        if total_weight == 0:
            outcome = "abstain"
            confidence = 0.0
        else:
            support_percentage = votes_for / total_weight
            if support_percentage > 0.5:
                outcome = "approved"
            else:
                outcome = "rejected"
            confidence = abs(support_percentage - 0.5) * 2

        decision = Decision(
            decision_id=f"{policy_id}_{region_id}_{len(self.decisions)}",
            policy_id=policy_id,
            region_id=region_id,
            decision_type=decision_type,
            outcome=outcome,
            confidence=confidence,
            voters_participated=[v.voter_id for v in voters_in_region],
            votes_for=int(votes_for),
            votes_against=int(votes_against),
        )

        self.decisions.append(decision)
        return decision

    def check_fairness(self) -> bool:
        """Check if all recent decisions meet fairness threshold.

        Returns:
            True if all decisions are fair, False otherwise
        """
        recent_decisions = (
            self.decisions[-10:] if len(self.decisions) > 10 else self.decisions
        )

        for decision in recent_decisions:
            fairness_score = self.fairness_metrics.calculate_fairness(
                decision, self.voters, self.regions
            )
            if fairness_score < self.fairness_threshold:
                return False

        return True

    def build_policy_tree_for_domain(
        self, domain: str, legislation_data: Dict
    ) -> PolicyTree:
        """Build a policy tree for a specific domain using legislation data.

        Args:
            domain: Policy domain (e.g., 'immigration', 'healthcare')
            legislation_data: Dictionary of legislation to scan

        Returns:
            PolicyTree: Built policy tree with anti-pattern detection
        """
        # Clear existing tree for this domain
        self.policy_tree = PolicyTree(self.anti_pattern_db)

        # Add policies from legislation data
        for policy_id, policy_data in legislation_data.items():
            # Extract policy information
            name = policy_data.get("name", f"Policy {policy_id}")
            description = policy_data.get("description", "")
            level_str = policy_data.get("level", "national")

            # Map string level to enum
            level_mapping = {
                "national": PolicyHierarchyLevel.NATIONAL,
                "state": PolicyHierarchyLevel.STATE,
                "county": PolicyHierarchyLevel.COUNTY,
                "municipal": PolicyHierarchyLevel.MUNICIPAL,
                "local": PolicyHierarchyLevel.LOCAL,
            }
            level = level_mapping.get(level_str.lower(), PolicyHierarchyLevel.NATIONAL)

            # Add policy to tree
            parent_id = policy_data.get("parent_id")
            self.policy_tree.add_policy(
                policy_id=policy_id,
                name=name,
                description=description,
                level=level,
                parent_id=parent_id,
            )

            # Add legislation references if provided
            if "legislation_references" in policy_data:
                for ref in policy_data["legislation_references"]:
                    policy_node = self.policy_tree.nodes.get(policy_id)
                    if policy_node:
                        policy_node.add_legislation(ref)

        # Scan for anti-patterns in the legislation data
        self.policy_tree.scan_for_anti_patterns(legislation_data)

        return self.policy_tree

    def detect_anti_patterns_in_decisions(self, decision_data: Dict) -> List[str]:
        """Detect anti-patterns in decision data.

        Args:
            decision_data: Dictionary containing decision metrics

        Returns:
            List of detected anti-pattern IDs
        """
        patterns = self.anti_pattern_db.detect_patterns(decision_data)
        return [p.pattern_id for p in patterns]

    def get_trusted_voters(self, min_trust: float = 0.7) -> List[Voter]:
        """Get voters with trust scores above threshold.

        Args:
            min_trust: Minimum trust threshold (0-1)

        Returns:
            List of trusted Voter objects
        """
        voter_list = list(self.voters.values())
        return self.trust_scorer.get_trusted_voters(voter_list, min_trust)

    def analyze_decision_for_manipulation(
        self, voter: Voter
    ) -> Tuple[bool, float, bool, float]:
        """Analyze a voter for bot activity and manipulation.

        Args:
            voter: Voter to analyze

        Returns:
            Tuple of (is_bot, bot_confidence, is_manipulated, manipulation_confidence)
        """
        is_bot, bot_confidence = self.influence_analyzer.detect_bot(voter)
        is_manipulated, manipulation_confidence = (
            self.influence_analyzer.detect_manipulation(voter)
        )
        return is_bot, bot_confidence, is_manipulated, manipulation_confidence

    def _analyze_policy_context(
        self, policy: Policy, region: Region, voters: List[Voter]
    ) -> Dict[str, Any]:
        print(f"Analyzing policy context for policy: {policy.name} in region: {region.name}")
        """Analyze policy context using LLM and real-world social data for enhanced understanding.

        :param policy: Policy being decided on
        :param region: Region where decision is being made
        :param voters: List of voters in the region
        :return: Dictionary containing LLM-analyzed policy context with real social data
        """
        # Collect real-world social narratives and opinions for this policy topic
        social_data = {}
        try:
            # Collect social narratives and public opinions from free sources
            social_data = self.social_collector.get_comprehensive_social_data(
                topic=policy.name, domain=str(policy.domain)
            )
        except Exception as e:
            print(f"Social data collection warning: {e}")
            social_data = {
                "topic": policy.name,
                "domain": str(policy.domain),
                "collected_at": datetime.now().isoformat(),
                "opinions": [],
                "media_narratives": [],
                "summary": {
                    "total_opinions": 0,
                    "total_narratives": 0,
                    "average_opinion_sentiment": 0.0,
                    "total_engagement": 0,
                    "average_narrative_sentiment": 0.0,
                    "average_media_credibility": 0.0,
                    "data_freshness": "unavailable",
                    "data_sources": [],
                },
            }

        if not self.llm_client.available:
            return {
                "analysis_method": "fallback",
                "context_summary": f"Policy {policy.name} in region {region.name}",
                "social_data_summary": social_data.get("summary", {}),
                "key_factors": [
                    "policy_impact",
                    "voter_demographics",
                    "regional_context",
                    "social_sentiment",
                ],
            }

        try:
            # Prepare context for LLM analysis including real social data
            context_data = {
                "population": region.population,
                "region_type": region.region_type,
                "policy_name": policy.name,
                "policy_description": policy.description,
                "policy_domain": str(policy.domain),
                "voter_count": len(voters),
                "voter_types": list(set([v.voter_type.value for v in voters])),
                "avg_trust_score": sum(
                    [self.trust_scorer.calculate_trust_score(v) for v in voters]
                )
                / max(len(voters), 1),
                # Add real-world social context
                "social_sentiment_summary": {
                    "opinion_count": len(social_data.get("opinions", [])),
                    "narrative_count": len(social_data.get("media_narratives", [])),
                    "avg_opinion_sentiment": social_data.get("summary", {}).get(
                        "average_opinion_sentiment", 0.0
                    ),
                    "avg_narrative_sentiment": social_data.get("summary", {}).get(
                        "average_narrative_sentiment", 0.0
                    ),
                    "total_engagement": social_data.get("summary", {}).get(
                        "total_engagement", 0
                    ),
                    "data_sources": social_data.get("summary", {}).get(
                        "data_sources", []
                    ),
                },
                # Include sample of real social data for LLM to analyze
                "sample_opinions": [
                    {
                        "text": op.get("text", "")[:200],
                        "perspective": op.get("perspective", "unknown"),
                        "source": op.get("source", "unknown"),
                        "sentiment": op.get("sentiment_score", 0.0),
                    }
                    for op in social_data.get("opinions", [])[:5]  # Top 5 opinions
                ],
                "sample_narratives": [
                    {
                        "title": nar.get("title", ""),
                        "text": nar.get("text", "")[:200],
                        "outlet": nar.get("outlet", "unknown"),
                        "sentiment": nar.get("sentiment_score", 0.0),
                        "credibility": nar.get("credibility_score", 0.0),
                    }
                    for nar in social_data.get("media_narratives", [])[:3]  # Top 3 narratives
                ],
            }

            research_questions = [
                f"What are the key implications of policy '{policy.name}' for region {region.name} based on current social narratives?",
                f"How do real-world public opinions and media narratives reflect the potential impact of this policy on different voter groups?",
                f"What social media and news narratives reveal about historical precedents for similar policies in similar contexts?",
                f"What are the potential benefits and drawbacks of this policy for this specific region based on current public discourse?",
                f"How should decision-makers weigh expert analysis against real-world social sentiment from Reddit and news sources?",
            ]

            principles = [
                "Inclusivity: Ensure all voter groups have fair representation",
                "Transparency: Make decision-making process open and understandable",
                "Accountability: Ensure decision-makers are responsible for outcomes",
                "Adaptability: Allow policies to evolve based on results and feedback",
                "Equity: Fair distribution of benefits and burdens across all groups",
                "Evidence-Based: Incorporate real-world social data and public sentiment into decision-making",
                "Context-Aware: Consider current social narratives and media discourse in policy analysis",
            ]

            reasoning = self.llm_client.generate_reasoning(  # Add type hint here
                context=context_data,
                research_questions=research_questions,
                principles=principles,
                max_tokens=1500,  # Increased for richer analysis with social data
            )

            return {
                "analysis_method": "llm_enhanced_with_social_data",
                "reasoning": reasoning,
                "context_data": context_data,
                "social_data": social_data,  # Include full social data for transparency
                "key_insights": self._extract_key_insights(reasoning),
                "confidence": 0.90,  # Higher confidence due to real data integration
            }
        except Exception as e:
            print(f"LLM policy context analysis error: {e}")
            return {
                "analysis_method": "fallback_error",
                "error": str(e),
                "context_summary": f"Policy {policy.name} in region {region.name}",
                "social_data_summary": social_data.get("summary", {}),
            }

        insights = []
        lines = reasoning.split("\n")

        for line in lines:
            line = line.strip()
            # Look for bullet points, numbered lists, or strong statements
            if (
                line.startswith("- ")
                or line.startswith("* ")
                or any(line.startswith(f"{i}.") for i in range(1, 10))
                or (line.endswith(":") and len(line) > 10)
            ):
                insight = line.lstrip("- *0123456789. ")
                if insight and len(insight) > 10:
                    insights.append(insight)
            elif len(line) > 20 and (
                "key" in line.lower()
                or "important" in line.lower()
                or "crucial" in line.lower()
                or "essential" in line.lower()
            ):
                # Extract sentences that seem important
                if line.endswith(".") and len(line) > 15:
                    insights.append(line)

        # Limit to top 5 insights
        return insights[:5]
