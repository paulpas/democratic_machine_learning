"""Skill definitions for the democratic machine learning system.

Each skill defines a discrete capability that the LLM can use to perform
specific functions within the democratic decision-making system.
"""

from abc import abstractmethod
from typing import Dict, List, Protocol

# ============================================================================
# DATA ACQUISITION SKILLS
# ============================================================================


class SkillDataLoading(Protocol):
    """Skill: Load and parse data from various sources."""

    @abstractmethod
    def load_voter_data(self, filepath: str, format: str = "json") -> List[Dict]:
        """Load voter data from file."""
        ...

    @abstractmethod
    def load_policy_data(self, filepath: str) -> List[Dict]:
        """Load policy data from file."""
        ...

    @abstractmethod
    def load_region_data(self, filepath: str) -> List[Dict]:
        """Load region data from file."""
        ...

    @abstractmethod
    def fetch_realtime_polling(self, region_id: str) -> Dict:
        """Fetch real-time polling data for a region."""
        ...


class SkillDataValidation(Protocol):
    """Skill: Validate data quality and detect anomalies."""

    @abstractmethod
    def validate_voter_preferences(self, preferences: Dict[str, float]) -> bool:
        """Validate voter preference values are within range."""
        ...

    @abstractmethod
    def detect_preference_anomalies(self, preferences: Dict[str, float]) -> List[str]:
        """Detect anomalous preference patterns."""
        ...

    @abstractmethod
    def verify_data_provenance(self, source_id: str) -> Dict:
        """Verify data source legitimacy."""
        ...


# ============================================================================
# TRUST & SECURITY SKILLS
# ============================================================================


class SkillBotDetection(Protocol):
    """Skill: Detect bot and automated account behavior."""

    @abstractmethod
    def calculate_bot_score(self, voter: Dict) -> float:
        """Calculate bot probability score for a voter."""
        ...

    @abstractmethod
    def detect_synchronized_behavior(self, voters: List[Dict]) -> List[List[str]]:
        """Detect groups of voters with synchronized behavior (potential bots)."""
        ...

    @abstractmethod
    def analyze_timing_patterns(self, voting_timestamps: List[float]) -> float:
        """Analyze voting timing for automated patterns."""
        ...


class SkillManipulationDetection(Protocol):
    """Skill: Detect coordinated manipulation campaigns."""

    @abstractmethod
    def detect_manipulation_patterns(self, preferences: Dict[str, List[float]]) -> Dict:
        """Detect manipulation patterns in preference data."""
        ...

    @abstractmethod
    def analyze_influence_network(self, connections: List[Dict]) -> Dict:
        """Analyze social influence network for manipulation hubs."""
        ...

    @abstractmethod
    def identify_coordinated_campaigns(self, voters: List[Dict]) -> List[List[str]]:
        """Identify groups of voters acting in coordinated campaigns."""
        ...


class SkillTrustScoring(Protocol):
    """Skill: Calculate and maintain trust scores for voters."""

    @abstractmethod
    def calculate_trust_score(self, voter: Dict) -> float:
        """Calculate overall trust score for a voter."""
        ...

    @abstractmethod
    def assess_expertise(self, voter: Dict, policy_domain: str) -> float:
        """Assess voter expertise in specific policy domain."""
        ...

    @abstractmethod
    def track_consistency(self, voter_id: str, preferences: List[Dict]) -> float:
        """Track voter preference consistency over time."""
        ...


# ============================================================================
# GEOGRAPHIC & CLIMATE ANALYSIS SKILLS
# ============================================================================


class SkillGeographicWeighting(Protocol):
    """Skill: Apply geographic factors to decision weighting."""

    @abstractmethod
    def calculate_proximity_weight(self, voter_region: str, policy_region: str) -> float:
        """Calculate weight based on geographic proximity."""
        ...

    @abstractmethod
    def assess_regional_impact(self, policy_id: str, region_id: str) -> float:
        """Assess how a policy impacts a specific region."""
        ...

    @abstractmethod
    def balance_geographic_representation(self, decisions: List[Dict]) -> float:
        """Calculate geographic representation balance score."""
        ...


class SkillClimateImpactAssessment(Protocol):
    """Skill: Assess climate and environmental factors."""

    @abstractmethod
    def score_climate_vulnerability(self, region_id: str) -> float:
        """Score a region's climate vulnerability."""
        ...

    @abstractmethod
    def analyze_policy_climate_impact(self, policy_id: str, region_id: str) -> float:
        """Analyze environmental impact of policy on region."""
        ...

    @abstractmethod
    def calculate_carbon_footprint(self, policy_id: str) -> float:
        """Calculate policy's carbon footprint estimate."""
        ...


# ============================================================================
# DECISION ENGINE SKILLS
# ============================================================================


class SkillWeightedVoting(Protocol):
    """Skill: Calculate weighted votes."""

    @abstractmethod
    def calculate_voter_weight(self, voter: Dict, policy: Dict, region: Dict) -> float:
        """Calculate weighted voting power for voter-policy-region."""
        ...

    @abstractmethod
    def aggregate_votes(self, votes: List[Dict]) -> Dict:
        """Aggregate individual votes into collective decision."""
        ...

    @abstractmethod
    def calculate_confidence(self, decision: Dict) -> float:
        """Calculate confidence score for a decision."""
        ...


class SkillFairnessAssessment(Protocol):
    """Skill: Assess fairness of decisions."""

    @abstractmethod
    def calculate_fairness_score(self, decision: Dict, voters: List[Dict]) -> float:
        """Calculate fairness score for a decision."""
        ...

    @abstractmethod
    def check_proportional_representation(self, decisions: List[Dict]) -> bool:
        """Check if decisions satisfy proportional representation."""
        ...

    @abstractmethod
    def assess_minority_protection(self, decision: Dict, minority_groups: List[str]) -> float:
        """Assess protection of minority interests."""
        ...


class SkillMultiTieredDecision(Protocol):
    """Skill: Handle multi-tiered decision making."""

    @abstractmethod
    def propagate_decision_tier(self, decision: Dict, from_tier: str, to_tier: str) -> Dict:
        """Propagate decision from one tier to another."""
        ...

    @abstractmethod
    def resolve_tier_conflicts(self, decisions: List[Dict]) -> Dict:
        """Resolve conflicts between decision tiers."""
        ...

    @abstractmethod
    def balance_tier_weights(self, voters: List[Dict]) -> Dict[str, float]:
        """Calculate appropriate weights for each decision tier."""
        ...


# ============================================================================
# FEEDBACK & ADAPTATION SKILLS
# ============================================================================


class SkillFeedbackAnalysis(Protocol):
    """Skill: Analyze decision outcomes and provide feedback."""

    @abstractmethod
    def evaluate_decision_outcome(self, decision: Dict, outcomes: List[Dict]) -> Dict:
        """Evaluate the outcome of a decision."""
        ...

    @abstractmethod
    def calculate_learning_rate(self, feedback_quality: float) -> float:
        """Calculate appropriate learning rate based on feedback."""
        ...

    @abstractmethod
    def detect_trends(self, history: List[Dict], window: int = 10) -> Dict:
        """Detect trends in decision history."""
        ...


class SkillWeightAdaptation(Protocol):
    """Skill: Adapt voter weights based on feedback."""

    @abstractmethod
    def adjust_weight_for_expertise(
        self, voter_id: str, policy_domain: str, adjustment: float
    ) -> None:
        """Adjust voter weight based on expertise demonstration."""
        ...

    @abstractmethod
    def adjust_weight_for_participation(self, voter_id: str, participation_count: int) -> None:
        """Adjust voter weight based on participation history."""
        ...

    @abstractmethod
    def penalize_inconsistent_behavior(self, voter_id: str, penalty: float) -> None:
        """Penalize voter for inconsistent voting behavior."""
        ...


# ============================================================================
# OUTPUT & INTERACTION SKILLS
# ============================================================================


class SkillTUIOutput(Protocol):
    """Skill: Generate text-based user interface output."""

    @abstractmethod
    def format_decision_report(self, decision: Dict) -> str:
        """Format decision as TUI report."""
        ...

    @abstractmethod
    def create_dashboard(self, metrics: Dict) -> str:
        """Create interactive dashboard display."""
        ...

    @abstractmethod
    def display_policy_analysis(self, policy: Dict, decisions: List[Dict]) -> str:
        """Display policy analysis in TUI format."""
        ...


class SkillDataVisualization(Protocol):
    """Skill: Generate visual representations of data."""

    @abstractmethod
    def generate_preference_chart(self, voters: List[Dict]) -> str:
        """Generate preference distribution visualization."""
        ...

    @abstractmethod
    def create_trend_graph(self, history: List[Dict]) -> str:
        """Generate trend visualization."""
        ...

    @abstractmethod
    def display_geographic_map(self, regions: List[Dict]) -> str:
        """Display geographic distribution visualization."""
        ...


# ============================================================================
# CORE SYSTEM SKILLS
# ============================================================================


class SkillDecisionMaking(Protocol):
    """Skill: Core decision-making functionality."""

    @abstractmethod
    def make_decision(self, policy_id: str, region_id: str, voters: List[Dict]) -> Dict:
        """Make a decision on a policy for a region."""
        ...

    @abstractmethod
    def check_fairness_constraints(self, decision: Dict) -> bool:
        """Check if decision meets fairness constraints."""
        ...

    @abstractmethod
    def generate_confidence_score(self, decision: Dict) -> float:
        """Generate confidence score for decision."""
        ...


class SkillPolicyAnalysis(Protocol):
    """Skill: Analyze policy impacts and dependencies."""

    @abstractmethod
    def analyze_policy_impact(self, policy: Dict, regions: List[Dict]) -> Dict:
        """Analyze policy impact across regions."""
        ...

    @abstractmethod
    def identify_policy_dependencies(self, policy: Dict) -> List[str]:
        """Identify other policies that this policy depends on."""
        ...

    @abstractmethod
    def assess_policy_conflicts(self, policies: List[Dict]) -> List[Dict]:
        """Assess conflicts between policies."""
        ...


# ============================================================================
# DATA SCIENCE SKILLS
# ============================================================================


class SkillFeatureEngineering(Protocol):
    """Skill: Engineer features for ML models."""

    @abstractmethod
    def create_voter_features(self, voter: Dict, policy: Dict) -> Dict:
        """Create features for voter-policy pair."""
        ...

    @abstractmethod
    def create_region_features(self, region: Dict, voters: List[Dict]) -> Dict:
        """Create aggregate features for region."""
        ...

    @abstractmethod
    def normalize_features(self, features: List[Dict]) -> List[Dict]:
        """Normalize feature values."""
        ...


class SkillPredictiveModeling(Protocol):
    """Skill: Apply ML predictions to decision-making."""

    @abstractmethod
    def predict_policy_outcome(self, policy: Dict, voters: List[Dict]) -> float:
        """Predict likely outcome of a policy vote."""
        ...

    @abstractmethod
    def predict_voter_preference(self, voter_id: str, policy_id: str) -> float:
        """Predict a voter's preference for a policy."""
        ...

    @abstractmethod
    def optimize_policy_bundle(self, policies: List[Dict]) -> List[Dict]:
        """Optimize policy bundle for maximum acceptance."""
        ...
