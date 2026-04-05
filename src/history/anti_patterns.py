"""Historical anti-patterns for democratic decision-making.

This module contains documented anti-patterns from historical civilizations
that can be detected and avoided in democratic decision-making systems.

Source research: Academic political science, history, and governance studies
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class AntiPatternCategory(Enum):
    """Categories of historical anti-patterns."""

    POWER_CONCENTRATION = "power_concentration"
    ELITE_CAPTURE = "elite_capture"
    POPULIST_DECAY = "populist_decay"
    INSTITUTIONAL_ROT = "institutional_rot"
    FEEDBACK_FAILURE = "feedback_failure"
    GEOGRAPHIC_MISMANAGEMENT = "geographic_mismanagemen"
    CLIMATE_VULNERABILITY = "climate_vulnerability"
    INFORMATION_MANIPULATION = "information_manipulation"


@dataclass
class HistoricalAntiPattern:
    """Represents a historical anti-pattern with documentation."""

    pattern_id: str
    name: str
    description: str
    category: AntiPatternCategory
    historical_examples: List[str]
    warning_signs: List[str]
    mitigation_strategies: List[str]
    modern_equivalents: List[str]
    detection_metrics: Dict[str, float]


# ============================================================================
# POWER CONCENTRATION ANTI-PATTERNS
# ============================================================================

POWER_CONCENTRATION_PATTERNS = [
    HistoricalAntiPattern(
        pattern_id="PP-001",
        name="Dictatorship Emergence",
        description="Gradual concentration of power in single individual",
        category=AntiPatternCategory.POWER_CONCENTRATION,
        historical_examples=[
            "Julius Caesar's rise to perpetual dictator (44 BCE)",
            "Augustus establishing Principate (27 BCE)",
            "Napoleon Bonaparte's coup (1799)",
            "Adolf Hitler's Enabling Act (1933)",
        ],
        warning_signs=[
            "Emergency powers extended beyond crisis",
            "Checks and balances weakened",
            "Opposition suppressed under guise of stability",
            "Cult of personality developed",
        ],
        mitigation_strategies=[
            "Strict term limits with no exceptions",
            "Independent judicial review",
            "Transparent succession planning",
            "Mandatory power rotation",
        ],
        modern_equivalents=[
            "Executive orders bypassing legislature",
            "Packing courts with loyalists",
            "Restricting opposition party access",
        ],
        detection_metrics={
            "power_concentration_ratio": 0.8,
            "checks_balances_score": 0.3,
            "opposition_suppression_rate": 0.7,
        },
    ),
    HistoricalAntiPattern(
        pattern_id="PP-002",
        name="Oligarchic Capture",
        description="Rule by small elite group at expense of majority",
        category=AntiPatternCategory.POWER_CONCENTRATION,
        historical_examples=[
            "Roman Senate dominance (2nd Century BCE)",
            "Venetian Doge oligarchy",
            "Rhodesian white minority rule",
            "Modern corporate lobbying dominance",
        ],
        warning_signs=[
            "Policy favors concentrated wealth",
            "Regulatory capture by industry",
            "Voter suppression of majority",
            "Campaign finance imbalances",
        ],
        mitigation_strategies=[
            "Campaign finance transparency",
            "Lobbying restrictions",
            "Wealth caps on political spending",
            "Proportional representation",
        ],
        modern_equivalents=[
            "Super PACs dominating elections",
            "Revolving door between government and industry",
            "Gerrymandering for partisan advantage",
        ],
        detection_metrics={
            "elite_influence_score": 0.7,
            "wealth_polarization_index": 0.8,
            "policy_elite_alignment": 0.85,
        },
    ),
    HistoricalAntiPattern(
        pattern_id="PP-003",
        name="One-Party State",
        description="Single political party monopolizes power",
        category=AntiPatternCategory.POWER_CONCENTRATION,
        historical_examples=[
            "Soviet Communist Party (1922-1991)",
            "Fascist Italy (1922-1943)",
            "Modern authoritarian regimes",
        ],
        warning_signs=[
            "Opposition parties banned or marginalized",
            "Elections lack real choice",
            "Media controlled by state",
            "Dissent criminalized",
        ],
        mitigation_strategies=[
            "Multi-party system enforcement",
            "Free and fair election oversight",
            "Independent media protection",
            "Dissent rights protection",
        ],
        modern_equivalents=[
            "Banned opposition candidates",
            "Gerrymandered districts",
            "State-controlled media dominance",
        ],
        detection_metrics={
            "party_plurality": 0.9,
            "election_competition_index": 0.2,
            "media_diversity_score": 0.3,
        },
    ),
]


# ============================================================================
# ELITE CAPTURE ANTI-PATTERNS
# ============================================================================

ELITE_CAPTURE_PATTERNS = [
    HistoricalAntiPattern(
        pattern_id="EC-001",
        name="PAC/Corporate Influence",
        description="Special interests dominate policy through lobbying",
        category=AntiPatternCategory.ELITE_CAPTURE,
        historical_examples=[
            "East India Company control of British politics",
            "Robber barons Gilded Age",
            "Modern corporate lobbying",
        ],
        warning_signs=[
            "Policy mirrors donor interests",
            "Regulatory agencies led by industry insiders",
            "Lobbyist access to policymakers",
            "Campaign contributions influence voting",
        ],
        mitigation_strategies=[
            "Lobbying disclosure requirements",
            "Cooling-off periods for officials",
            "Public campaign financing",
            "Donor transparency thresholds",
        ],
        modern_equivalents=[
            "PAC contributions to candidates",
            "Revolving door between government and industry",
            "Industry-funded research bias",
        ],
        detection_metrics={
            "lobbying_spending_ratio": 0.6,
            "donor_policy_alignment": 0.75,
            "regulatory_capture_score": 0.7,
        },
    ),
    HistoricalAntiPattern(
        pattern_id="EC-002",
        name="Political Dynasties",
        description="Power remains within family/clan lines",
        category=AntiPatternCategory.ELITE_CAPTURE,
        historical_examples=[
            "Roman Julian-Claudian dynasty",
            "Chinese imperial dynasties",
            "Modern political dynasties (Kennedy, Bush, Clinton)",
        ],
        warning_signs=[
            "Family members hold consecutive offices",
            "Patronage networks based on kinship",
            "Inheritance of political influence",
            "Limited political mobility",
        ],
        mitigation_strategies=[
            "Term limits enforcement",
            "Anti-nepotism laws",
            "Open primary systems",
            "Leadership rotation requirements",
        ],
        modern_equivalents=[
            "Dynastic succession in politics",
            "Patronage appointments",
            "Family-controlled media empires",
        ],
        detection_metrics={
            "dynastic_influence_score": 0.6,
            "political_mobility_index": 0.4,
            "patronage_network_strength": 0.7,
        },
    ),
]


# ============================================================================
# POPULIST DECAY ANTI-PATTERNS
# ============================================================================

POPULIST_DECAY_PATTERNS = [
    HistoricalAntiPattern(
        pattern_id="PD-001",
        name="Tyranny of Majority",
        description="Majority oppresses minority interests",
        category=AntiPatternCategory.POPULIST_DECAY,
        historical_examples=[
            "Athenian democracy execution of generals (406 BCE)",
            "French Revolution Reign of Terror",
            "Jim Crow laws in US South",
        ],
        warning_signs=[
            "Majority disregard for minority rights",
            "Minority voting rights restricted",
            "Polarization increasing",
            "Compromise seen as weakness",
        ],
        mitigation_strategies=[
            "Constitutional protections for minorities",
            "Supermajority requirements for key decisions",
            "Proportional representation",
            "Minority veto on critical issues",
        ],
        modern_equivalents=[
            "Voter ID laws targeting minorities",
            "Gerrymandering to dilute minority vote",
            "Majority bloc voting ignoring minority needs",
        ],
        detection_metrics={
            "minority_satisfaction_score": 0.3,
            "polarization_index": 0.7,
            "majority_consent_rate": 0.65,
        },
    ),
    HistoricalAntiPattern(
        pattern_id="PD-002",
        name="Populist Demagoguery",
        description="Charismatic leader exploits popular fears",
        category=AntiPatternCategory.POPULIST_DECAY,
        historical_examples=[
            "Cleon in Athenian democracy",
            "Marcus Palm in Roman Republic",
            "Modern populist leaders",
        ],
        warning_signs=[
            "Scapegoating of out-groups",
            "Promises beyond fiscal reality",
            "Discredit of experts and institutions",
            "Emotional appeals over rational debate",
        ],
        mitigation_strategies=[
            "Media literacy education",
            "Fact-checking institutions",
            "Campaign finance reform",
            "Debate format requirements",
        ],
        modern_equivalents=[
            "Social media manipulation",
            "False promises in campaigns",
            "Attacks on expert consensus",
        ],
        detection_metrics={
            "populist_rhetoric_ratio": 0.7,
            "expert_discredit_rate": 0.6,
            "fiscal_impossibility_score": 0.8,
        },
    ),
]


# ============================================================================
# INSTITUTIONAL ROT ANTI-PATTERNS
# ============================================================================

INSTITUTIONAL_ROT_PATTERNS = [
    HistoricalAntiPattern(
        pattern_id="IR-001",
        name="Institutional Decay",
        description="Erosion of institutional integrity",
        category=AntiPatternCategory.INSTITUTIONAL_ROT,
        historical_examples=[
            "Late Roman Empire bureaucracy",
            "Dreyfus Affair France",
            "Modern regulatory capture",
        ],
        warning_signs=[
            "Institutions prioritize self-preservation",
            "Meritocracy replaced with patronage",
            "Rules bent for political advantage",
            "Public trust declining",
        ],
        mitigation_strategies=[
            "Independent oversight bodies",
            "Merit-based appointments",
            "Institutional transparency",
            "Rotation of key positions",
        ],
        modern_equivalents=[
            "Bureaucratic resistance to reform",
            "Patronage hiring",
            "Rule changes for political gain",
        ],
        detection_metrics={
            "institutional_integrity_score": 0.5,
            "meritocracy_index": 0.4,
            "public_trust_index": 0.35,
        },
    ),
    HistoricalAntiPattern(
        pattern_id="IR-002",
        name="Corruption Entrenchment",
        description="Systemic corruption becomes normalized",
        category=AntiPatternCategory.INSTITUTIONAL_ROT,
        historical_examples=[
            "Roman provincial corruption",
            "Habsburg Empire bureaucracy",
            "Modern kleptocracies",
        ],
        warning_signs=[
            "Bribery expected in transactions",
            "Nepotism widespread",
            "Regulatory evasion normalized",
            "Whistleblower retaliation",
        ],
        mitigation_strategies=[
            "Anti-corruption commissions",
            "Whistleblower protection",
            "Transparency requirements",
            "Asset disclosure mandates",
        ],
        modern_equivalents=[
            "Bribery in procurement",
            "Family hiring in government",
            "Regulatory loopholes for elites",
        ],
        detection_metrics={
            "corruption_index": 0.7,
            "bribery_frequency": 0.6,
            "whistleblower_protection_score": 0.3,
        },
    ),
]


# ============================================================================
# FEEDBACK FAILURE ANTI-PATTERNS
# ============================================================================

FEEDBACK_FAILURE_PATTERNS = [
    HistoricalAntiPattern(
        pattern_id="FF-001",
        name="Feedback Loop Breakdown",
        description="System fails to adapt to changing conditions",
        category=AntiPatternCategory.FEEDBACK_FAILURE,
        historical_examples=[
            "Dust Bowl agricultural policies",
            "Soviet collectivization",
            "Modern climate denial",
        ],
        warning_signs=[
            "Data ignored or manipulated",
            "Expert opinions dismissed",
            "Policy not adjusted despite failures",
            "Dissent suppressed",
        ],
        mitigation_strategies=[
            "Independent data collection",
            "Expert advisory boards",
            "Adaptive policy frameworks",
            "Feedback integration mechanisms",
        ],
        modern_equivalents=[
            "Data suppression for political reasons",
            "Expert dismissal in policy debates",
            "Policy rigidity despite evidence",
        ],
        detection_metrics={
            "feedback_integration_rate": 0.3,
            "expert_influence_score": 0.4,
            "policy_adaptation_speed": 0.2,
        },
    ),
    HistoricalAntiPattern(
        pattern_id="FF-002",
        name="Tyranny of Short-Termism",
        description="Focus on immediate results over long-term sustainability",
        category=AntiPatternCategory.FEEDBACK_FAILURE,
        historical_examples=[
            "Roman overreliance on slave labor",
            "Mayan ecological collapse",
            "Modern quarterly earnings focus",
        ],
        warning_signs=[
            "Long-term problems deferred",
            "Sustainability sacrificed for growth",
            "Future generations ignored",
            "Resource depletion accelerated",
        ],
        mitigation_strategies=[
            "Long-term policy frameworks",
            "Intergenerational impact assessments",
            "Sustainability metrics",
            "Future-focused governance bodies",
        ],
        modern_equivalents=[
            "Quarterly profit over sustainability",
            "Deferring climate action",
            "Debt accumulation for short-term gains",
        ],
        detection_metrics={
            "short_termism_index": 0.8,
            "sustainability_score": 0.3,
            "long_term_planning_score": 0.25,
        },
    ),
]


# ============================================================================
# GEOGRAPHIC CLIMATE ANTI-PATTERNS
# ============================================================================

GEOGRAPHIC_CLIMATE_PATTERNS = [
    HistoricalAntiPattern(
        pattern_id="GC-001",
        name="Resource Mismanagement",
        description="Failure to manage geographic resources sustainably",
        category=AntiPatternCategory.GEOGRAPHIC_MISMANAGEMENT,
        historical_examples=[
            "Easter Island deforestation",
            "Mesopotamian salinization",
            "Modern water crises",
        ],
        warning_signs=[
            "Resource depletion accelerating",
            "Environmental degradation ignored",
            "Geographic vulnerability unaddressed",
            "Climate adaptation delayed",
        ],
        mitigation_strategies=[
            "Sustainable resource quotas",
            "Environmental impact assessments",
            "Geographic risk mapping",
            "Climate resilience planning",
        ],
        modern_equivalents=[
            "Over-extraction of aquifers",
            "Deforestation for short-term gain",
            "Coastal development in flood zones",
        ],
        detection_metrics={
            "resource_depletion_rate": 0.7,
            "environmental_health_score": 0.4,
            "geographic_risk_index": 0.6,
        },
    ),
    HistoricalAntiPattern(
        pattern_id="GC-002",
        name="Climate Vulnerability Ignored",
        description="Failure to address climate vulnerability",
        category=AntiPatternCategory.CLIMATE_VULNERABILITY,
        historical_examples=[
            "Akkadian Empire drought collapse",
            "Mayan civilization drought",
            "Modern climate inaction",
        ],
        warning_signs=[
            "Climate data dismissed",
            "Vulnerable populations unprotected",
            "Adaptation infrastructure delayed",
            "Disaster preparedness lacking",
        ],
        mitigation_strategies=[
            "Climate vulnerability mapping",
            "Early warning systems",
            "Resilience infrastructure investment",
            "Vulnerable population protection",
        ],
        modern_equivalents=[
            "Climate denial in policy",
            "Insufficient disaster preparedness",
            "Ignoring sea-level rise projections",
        ],
        detection_metrics={
            "climate_vulnerability_index": 0.7,
            "adaptation_readiness_score": 0.3,
            "vulnerable_population_protection": 0.4,
        },
    ),
]


# ============================================================================
# INFORMATION MANIPULATION ANTI-PATTERNS
# ============================================================================

INFORMATION_MANIPULATION_PATTERNS = [
    HistoricalAntiPattern(
        pattern_id="IM-001",
        name="Propaganda Dominance",
        description="State or group controls narrative through propaganda",
        category=AntiPatternCategory.INFORMATION_MANIPULATION,
        historical_examples=[
            "Roman 'panem et circenses'",
            "Nazi Ministry of Propaganda",
            "Modern social media manipulation",
        ],
        warning_signs=[
            "State-controlled media narrative",
            "Disinformation campaigns",
            "Censorship of dissent",
            "Algorithmic bias in information",
        ],
        mitigation_strategies=[
            "Media diversity requirements",
            "Algorithmic transparency",
            "Digital literacy education",
            "Disinformation detection systems",
        ],
        modern_equivalents=[
            "Social media bot networks",
            "Algorithmic echo chambers",
            "State-sponsored disinformation",
        ],
        detection_metrics={
            "propaganda_exposure_ratio": 0.7,
            "media_diversity_score": 0.3,
            "disinformation_spread_rate": 0.6,
        },
    ),
    HistoricalAntiPattern(
        pattern_id="IM-002",
        name="Data Manipulation for Political Gain",
        description="Data扭曲 to influence decisions",
        category=AntiPatternCategory.INFORMATION_MANIPULATION,
        historical_examples=[
            "Roman census manipulation",
            "Soviet economic statistics",
            "Modern polling manipulation",
        ],
        warning_signs=[
            "Data selectively reported",
            "Methodology changed for desired outcome",
            "Expert analysis suppressed",
            "Evidence ignored when inconvenient",
        ],
        mitigation_strategies=[
            "Independent data verification",
            "Transparent methodology",
            "Data provenance tracking",
            "Expert oversight boards",
        ],
        modern_equivalents=[
            "Cherry-picked data in reports",
            "Methodology changes for favorable results",
            "Expert suppression in policy decisions",
        ],
        detection_metrics={
            "data_integrity_score": 0.4,
            "methodology_transparency": 0.3,
            "expert_suppression_rate": 0.6,
        },
    ),
]


# ============================================================================
# MAIN ANTI-PATTERN DATABASE CLASS
# ============================================================================


class AntiPatternDatabase:
    """Comprehensive database of historical anti-patterns."""

    def __init__(self) -> None:
        """Initialize the anti-pattern database."""
        self.patterns: List[HistoricalAntiPattern] = []

        # Load all categories
        self.patterns.extend(POWER_CONCENTRATION_PATTERNS)
        self.patterns.extend(ELITE_CAPTURE_PATTERNS)
        self.patterns.extend(POPULIST_DECAY_PATTERNS)
        self.patterns.extend(INSTITUTIONAL_ROT_PATTERNS)
        self.patterns.extend(FEEDBACK_FAILURE_PATTERNS)
        self.patterns.extend(GEOGRAPHIC_CLIMATE_PATTERNS)
        self.patterns.extend(INFORMATION_MANIPULATION_PATTERNS)

    def get_patterns_by_category(
        self, category: AntiPatternCategory
    ) -> List[HistoricalAntiPattern]:
        """Get patterns by category."""
        return [p for p in self.patterns if p.category == category]

    def get_pattern_by_id(self, pattern_id: str) -> Optional[HistoricalAntiPattern]:
        """Get pattern by ID."""
        for pattern in self.patterns:
            if pattern.pattern_id == pattern_id:
                return pattern
        return None

    def detect_patterns(self, decision_data: Dict) -> List[HistoricalAntiPattern]:
        """Detect which anti-patterns are present in current decision data."""
        detected = []

        for pattern in self.patterns:
            metrics = pattern.detection_metrics

            # Check if current data matches pattern thresholds
            if self._matches_thresholds(decision_data, metrics):
                detected.append(pattern)

        return detected

    def _matches_thresholds(self, decision_data: Dict, metrics: Dict[str, float]) -> bool:
        """Check if decision data matches pattern thresholds."""
        for metric_name, threshold in metrics.items():
            if metric_name in decision_data:
                if decision_data[metric_name] >= threshold:
                    return True
        return False

    def get_all_warning_signs(self) -> Dict[str, List[str]]:
        """Get all warning signs grouped by category."""
        warning_signs = {}

        for pattern in self.patterns:
            if pattern.category.value not in warning_signs:
                warning_signs[pattern.category.value] = []
            warning_signs[pattern.category.value].extend(pattern.warning_signs)

        return warning_signs

    def get_mitigation_strategies(self) -> List[str]:
        """Get all mitigation strategies."""
        strategies = []

        for pattern in self.patterns:
            strategies.extend(pattern.mitigation_strategies)

        return list(set(strategies))  # Remove duplicates
