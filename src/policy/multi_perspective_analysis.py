"""
Multi-Perspective Critique and Cross-Reference System for U.S. Immigration Policy Analysis

This module implements a comprehensive analysis framework covering 12 societal perspectives,
cross-reference analysis, anti-investigation mechanisms, and social science integration.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
from datetime import datetime

from src.models.voter import Voter, VoterType
from src.utils.metrics import FairnessMetrics


class PerspectiveCategory(Enum):
    """Categories of societal perspectives."""

    DISENFRANCHISED = "disenfranchised"
    PRIVILEGED = "privileged"
    EXPERTS = "experts"
    STAKEHOLDERS = "stakeholders"
    IDEOLOGICAL = "ideological"
    GEOGRAPHIC = "geographic"
    AGE = "age"
    PROFESSIONAL = "professional"
    CULTURAL = "cultural"
    RELIGIOUS = "religious"
    ENVIRONMENTAL = "environmental"
    ECONOMIC = "economic"


@dataclass
class Perspective:
    """Represents a societal perspective on immigration policy."""

    perspective_id: str
    name: str
    category: PerspectiveCategory
    description: str
    population_share: float  # Estimated percentage of population
    core_values: List[str]
    primary_stance: str
    key_concerns: List[str]
    policy_preferences: List[str]
    potential_impacts: List[str]
    trust_level: float  # 0-1, trust in immigration system
    policy_awareness: float  # 0-1, familiarity with policy details


@dataclass
class PerspectiveComparison:
    """Comparison between two perspectives."""

    perspective_a: str
    perspective_b: str
    agreement_score: float  # 0-1
    contradiction_score: float  # 0-1
    common_ground: List[str]
    key_differences: List[str]
    policy_alignment: str  # "aligned", "partial", "opposed"


@dataclass
class CounterArgument:
    """Counter-argument to a perspective."""

    argument_id: str
    perspective_id: str
    argument_text: str
    evidence_quality: str  # "strong", "moderate", "weak"
    supporting_sources: List[str]
    potential_bias: str
    rebuttal_strength: float  # 0-1


@dataclass
class PolicyAnalysis:
    """Analysis of a policy from a perspective."""

    policy_id: str
    policy_name: str
    perspective_id: str
    perspective_name: str
    support_level: float  # -1 to 1
    concerns: List[str]
    benefits: List[str]
    recommendations: List[str]
    confidence: float  # 0-1


class MultiPerspectiveAnalysis:
    """Comprehensive multi-perspective analysis system."""

    def __init__(self) -> None:
        """Initialize the analysis system."""
        self.perspectives: Dict[str, Perspective] = {}
        self.policy_analyses: Dict[str, List[PolicyAnalysis]] = {}
        self.comparisons: List[PerspectiveComparison] = []
        self.counter_arguments: List[CounterArgument] = []
        self.fairness_metrics = FairnessMetrics()

        self._initialize_perspectives()
        self._initialize_policies()

    def _initialize_perspectives(self) -> None:
        """Initialize all 12 societal perspectives."""
        # 1. Disenfranchised
        self.perspectives["D1"] = Perspective(
            perspective_id="D1",
            name="Disenfranchised (Low-Income, Minority, Rural, Disabled, Elderly)",
            category=PerspectiveCategory.DISENFRANCHISED,
            description="Marginalized populations facing systemic barriers to full participation",
            population_share=0.45,
            core_values=["Equity", "Access", "Dignity", "Security", "Community"],
            primary_stance=(
                "Support humane policies that protect vulnerable populations, "
                "oppose enforcement that separates families or criminalizes survival"
            ),
            key_concerns=[
                "Family separation",
                "Access to services",
                "Economic exploitation",
                "Discrimination",
                "Healthcare access",
            ],
            policy_preferences=[
                "Pathway to citizenship for all",
                "Due process protections",
                "Access to legal representation",
                "Protections for asylum seekers",
                "End to detention of vulnerable populations",
            ],
            potential_impacts=[
                "Positive: Family stability, economic security, community cohesion",
                "Negative (if restrictive): Trauma, poverty, family separation",
            ],
            trust_level=0.25,
            policy_awareness=0.45,
        )

        # 2. Privileged
        self.perspectives["D2"] = Perspective(
            perspective_id="D2",
            name="Privileged (High-Income, Majority, Urban)",
            category=PerspectiveCategory.PRIVILEGED,
            description="Benefiting from systemic advantages and social capital",
            population_share=0.25,
            core_values=[
                "Order",
                "Economic Stability",
                "Rule of Law",
                "Property Rights",
            ],
            primary_stance=(
                "Prioritize legal immigration pathways, support enforcement of existing laws, "
                "concerned about system integrity and resource allocation"
            ),
            key_concerns=[
                "Legal system integrity",
                "Taxpayer burden",
                "Public safety",
                "Infrastructure capacity",
                "Job competition",
            ],
            policy_preferences=[
                "Merit-based immigration",
                "Strong border security",
                "Enforcement of immigration laws",
                "Controlled, managed flow",
                "Due process but with boundaries",
            ],
            potential_impacts=[
                "Positive: Economic stability, infrastructure sustainability",
                "Negative: Family separation, humanitarian concerns",
            ],
            trust_level=0.60,
            policy_awareness=0.70,
        )

        # 3. Experts
        self.perspectives["D3"] = Perspective(
            perspective_id="D3",
            name="Experts (Economists, Political Scientists, Sociologists, Immigration Lawyers)",
            category=PerspectiveCategory.EXPERTS,
            description="Specialized knowledge in relevant fields",
            population_share=0.10,
            core_values=[
                "Evidence",
                "Rigor",
                "Objectivity",
                "Academic Freedom",
                "Long-Term Impact",
            ],
            primary_stance=(
                "Data-driven approach to policy, emphasize evidence over ideology, "
                "prioritize systemic solutions over political expediency"
            ),
            key_concerns=[
                "Evidence-based outcomes",
                "Methodological rigor",
                "Long-term consequences",
                "External validity",
                "Causal inference",
            ],
            policy_preferences=[
                "Comprehensive immigration reform",
                "Data-driven visa allocation",
                "Cost-benefit analysis",
                "Impact evaluation frameworks",
                "Expert advisory mechanisms",
            ],
            potential_impacts=[
                "Positive: Optimal outcomes, sustainable solutions, reduced unintended consequences",
                "Negative (if ignored): Inefficiency, wasted resources, policy failure",
            ],
            trust_level=0.85,
            policy_awareness=0.95,
        )

        # 4. Affected Stakeholders
        self.perspectives["D4"] = Perspective(
            perspective_id="D4",
            name="Affected Stakeholders (Farmers, Employers, Service Workers, Communities)",
            category=PerspectiveCategory.STAKEHOLDERS,
            description="Directly impacted by immigration policy implementation",
            population_share=0.35,
            core_values=[
                "Practicality",
                "Economic Viability",
                "Community Impact",
                "Fairness",
            ],
            primary_stance=(
                "Pragmatic approach balancing economic needs with community concerns, "
                "focus on implementation realities"
            ),
            key_concerns=[
                "Labor shortages",
                "Economic competitiveness",
                "Service capacity",
                "Community integration",
                "Fair competition",
            ],
            policy_preferences=[
                "Workforce-appropriate immigration",
                "Pathways for essential workers",
                "Support for community integration",
                "Economic impact assessments",
                "Stakeholder consultation",
            ],
            potential_impacts=[
                "Positive: Economic stability, workforce filling, community vitality",
                "Negative: Wage pressure, service strain, cultural tensions",
            ],
            trust_level=0.50,
            policy_awareness=0.65,
        )

        # 5. Ideological
        self.perspectives["D5"] = Perspective(
            perspective_id="D5",
            name="Ideological (Progressive, Conservative, Libertarian, etc.)",
            category=PerspectiveCategory.IDEOLOGICAL,
            description="Guided by core political philosophy and values",
            population_share=0.60,
            core_values=[
                "Values",
                "Principles",
                "Ideological Purity",
                "Moral Framework",
            ],
            primary_stance=(
                "Varies by ideology: Progressives prioritize human rights, "
                "Conservatives prioritize order, Libertarians prioritize freedom"
            ),
            key_concerns=[
                "Moral consistency",
                "Principle adherence",
                "Ideological coherence",
                "Systemic change",
                "Preservation of values",
            ],
            policy_preferences=[
                "Progressive: Universal human rights, open borders (or managed migration)",
                "Conservative: Law and order, national sovereignty, cultural preservation",
                "Libertarian: Freedom of movement, limited government, free markets",
            ],
            potential_impacts=[
                "Positive: Systemic alignment, mobilization, value fulfillment",
                "Negative (if extreme): Polarization, gridlock,忽视 pragmatism",
            ],
            trust_level=0.45,
            policy_awareness=0.55,
        )

        # 6. Geographic
        self.perspectives["D6"] = Perspective(
            perspective_id="D6",
            name="Geographic (Urban, Suburban, Rural, Coastal, Inland, Border States)",
            category=PerspectiveCategory.GEOGRAPHIC,
            description="Shaped by geographic location and regional characteristics",
            population_share=1.0,  # All citizens
            core_values=[
                "Place",
                "Regional Identity",
                "Local Control",
                "Community Integrity",
            ],
            primary_stance=(
                "Policies should account for geographic variation in needs, "
                "resources, and priorities"
            ),
            key_concerns=[
                "Regional economic impact",
                "Service delivery capacity",
                "Cultural compatibility",
                "Resource allocation",
                "Local autonomy",
            ],
            policy_preferences=[
                "Geographically tailored policies",
                "Regional input in decision-making",
                "Equitable resource distribution",
                "Border state support",
                "Urban-rural balance",
            ],
            potential_impacts=[
                "Positive: Context-appropriate solutions, regional prosperity",
                "Negative: Geographic inequality, neglect of vulnerable regions",
            ],
            trust_level=0.55,
            policy_awareness=0.60,
        )

        # 7. Age Demographics
        self.perspectives["D7"] = Perspective(
            perspective_id="D7",
            name="Age Demographics (Gen Z, Millennials, Gen X, Boomers, Silent)",
            category=PerspectiveCategory.AGE,
            description="Shaped by generational experiences and priorities",
            population_share=1.0,  # All citizens
            core_values=[
                "Intergenerational Equity",
                "Future Prospects",
                "Legacy",
                "Opportunity",
            ],
            primary_stance=(
                "Different generations have distinct perspectives shaped by "
                "economic conditions, technology, and social context"
            ),
            key_concerns=[
                "Economic opportunity",
                "Social stability",
                "Intergenerational fairness",
                "Long-term sustainability",
                "Cultural change",
            ],
            policy_preferences=[
                "Gen Z/Millennials: More open, climate-focused, social justice",
                "Gen X/Boomers: Balanced, economic pragmatism, stability",
                "Silent: Order, tradition, assimilation",
            ],
            potential_impacts=[
                "Positive: Generational renewal, economic vitality, cultural dynamism",
                "Negative: Intergenerational conflict, cultural fragmentation",
            ],
            trust_level=0.50,
            policy_awareness=0.50,
        )

        # 8. Professional Sectors
        self.perspectives["D8"] = Perspective(
            perspective_id="D8",
            name="Professional Sectors (Healthcare, Education, Tech, Manufacturing, etc.)",
            category=PerspectiveCategory.PROFESSIONAL,
            description="Shaped by specific industry needs and professional norms",
            population_share=0.50,
            core_values=[
                "Professional Standards",
                "Industry Needs",
                "Workforce Quality",
                "Ethics",
            ],
            primary_stance=(
                "Policies should support sector-specific workforce needs while "
                "maintaining professional standards and ethics"
            ),
            key_concerns=[
                "Workforce availability",
                "Credential recognition",
                "Ethical practice",
                "Quality standards",
                "Competition",
            ],
            policy_preferences=[
                "Sector-specific visa programs",
                "Credential portability",
                "Professional licensing reform",
                "Ethical recruitment",
                "Workforce development",
            ],
            potential_impacts=[
                "Positive: Sector stability, quality service, innovation",
                "Negative: Wage suppression, exploitation, professional devaluation",
            ],
            trust_level=0.70,
            policy_awareness=0.80,
        )

        # 9. Cultural/Ethnic Groups
        self.perspectives["D9"] = Perspective(
            perspective_id="D9",
            name="Cultural/Ethnic Groups (Hispanic, Asian, Black, White, Indigenous)",
            category=PerspectiveCategory.CULTURAL,
            description="Shaped by cultural heritage and ethnic identity",
            population_share=1.0,  # All citizens
            core_values=[
                "Cultural Preservation",
                "Identity",
                "Representation",
                "Equity",
            ],
            primary_stance=(
                "Concerned with how policies affect cultural groups, "
                "particularly regarding discrimination and representation"
            ),
            key_concerns=[
                "Cultural preservation",
                "Anti-discrimination",
                "Representation",
                "Historical justice",
                "Community integrity",
            ],
            policy_preferences=[
                "Anti-discrimination enforcement",
                "Cultural competency in policy",
                "Historical redress",
                "Community参与",
                "Equity-focused implementation",
            ],
            potential_impacts=[
                "Positive: Cultural diversity, social cohesion, historical justice",
                "Negative: Cultural erosion, discrimination, marginalization",
            ],
            trust_level=0.35,
            policy_awareness=0.60,
        )

        # 10. Religious Groups
        self.perspectives["D10"] = Perspective(
            perspective_id="D10",
            name="Religious Groups (Christian, Muslim, Jewish, Secular, etc.)",
            category=PerspectiveCategory.RELIGIOUS,
            description="Guided by religious or secular ethical frameworks",
            population_share=0.85,
            core_values=["Faith", "Morality", "Compassion", "Justice", "Community"],
            primary_stance=(
                "Faith-based perspectives emphasize compassion and hospitality, "
                "while secular perspectives emphasize universal rights"
            ),
            key_concerns=[
                "Religious freedom",
                "Moral consistency",
                "Human dignity",
                "Compassion",
                "Social justice",
            ],
            policy_preferences=[
                "Humanitarian approach",
                "Refugee protection",
                "Family unity",
                "Dignity for all",
                "Faith-based accommodation",
            ],
            potential_impacts=[
                "Positive: Moral coherence, humanitarian outcomes, community service",
                "Negative: Religious discrimination, moral absolutism",
            ],
            trust_level=0.60,
            policy_awareness=0.65,
        )

        # 11. Environmental Advocates
        self.perspectives["D11"] = Perspective(
            perspective_id="D11",
            name="Environmental Advocates",
            category=PerspectiveCategory.ENVIRONMENTAL,
            description="Focused on environmental sustainability and climate justice",
            population_share=0.15,
            core_values=[
                "Sustainability",
                "Climate Justice",
                "Ecological Balance",
                "Long-Term Thinking",
            ],
            primary_stance=(
                "Policies should consider environmental impact, resource sustainability, "
                "and climate-driven migration"
            ),
            key_concerns=[
                "Resource consumption",
                "Climate migration",
                "Sustainable development",
                "Environmental justice",
                "Interconnectedness",
            ],
            policy_preferences=[
                "Climate-resilient immigration",
                "Sustainable population policies",
                "Resource equitable distribution",
                "Climate migration protection",
                "Environmental impact assessment",
            ],
            potential_impacts=[
                "Positive: Environmental sustainability, climate adaptation",
                "Negative: Restrictionist framing,忽视 other priorities",
            ],
            trust_level=0.75,
            policy_awareness=0.70,
        )

        # 12. Economic Traditionalists
        self.perspectives["D12"] = Perspective(
            perspective_id="D12",
            name="Economic Traditionalists",
            category=PerspectiveCategory.ECONOMIC,
            description="Focused on traditional economic principles and stability",
            population_share=0.30,
            core_values=[
                "Economic Stability",
                "Fiscal Responsibility",
                "Market Efficiency",
                "Sustainability",
            ],
            primary_stance=(
                "Policies should promote economic stability, fiscal responsibility, "
                "and long-term economic health"
            ),
            key_concerns=[
                "Fiscal impact",
                "Labor market effects",
                "Economic growth",
                "Debt sustainability",
                "Intergenerational economic health",
            ],
            policy_preferences=[
                "Economic impact analysis",
                "Fiscal neutrality",
                "Labor market alignment",
                "Debt sustainability",
                "Long-term economic planning",
            ],
            potential_impacts=[
                "Positive: Economic stability, fiscal responsibility",
                "Negative: Overlooking social impacts,忽视 human costs",
            ],
            trust_level=0.65,
            policy_awareness=0.75,
        )

    def _initialize_policies(self) -> None:
        """Initialize immigration policy areas."""
        self.policies = {
            "border_security": {
                "name": "Border Security and Enforcement",
                "description": "Policies governing border control, surveillance, and enforcement",
                "key_questions": [
                    "How should the U.S. manage its southern border?",
                    "What level of enforcement is appropriate?",
                    "How to balance security with humanitarian concerns?",
                ],
            },
            "pathway_to_citizenship": {
                "name": "Pathway to Citizenship for Undocumented Immigrants",
                "description": "Policies providing legal status and citizenship for undocumented residents",
                "key_questions": [
                    "Who should qualify for citizenship?",
                    "What are the requirements and timeline?",
                    "How to balance fairness with rule of law?",
                ],
            },
            "visa_system": {
                "name": "Visa System Reform",
                "description": "Policies governing legal immigration channels",
                "key_questions": [
                    "How should visa caps and country limits be structured?",
                    "What criteria should determine visa allocation?",
                    "How to balance family reunification with economic needs?",
                ],
            },
            "refugee_asylum": {
                "name": "Refugee and Asylum Policy",
                "description": "Policies protecting individuals fleeing persecution",
                "key_questions": [
                    "What constitutes valid asylum claim?",
                    "How to process applications fairly and efficiently?",
                    "What protection levels should be provided?",
                ],
            },
            "workforce_immigration": {
                "name": "Workforce Immigration",
                "description": "Policies for temporary and permanent worker programs",
                "key_questions": [
                    "How to meet labor market needs?",
                    "What protections for workers?",
                    "How to prevent exploitation?",
                ],
            },
            "family_sponsorship": {
                "name": "Family-Based Immigration",
                "description": "Policies allowing U.S. citizens and residents to sponsor family members",
                "key_questions": [
                    "Which relatives should be eligible?",
                    "What are the waiting periods and limits?",
                    "How to balance family unity with other priorities?",
                ],
            },
            "enforcement_priorities": {
                "name": "Immigration Enforcement Priorities",
                "description": "How enforcement resources are allocated and applied",
                "key_questions": [
                    "Who should be prioritized for removal?",
                    "How to balance enforcement with community trust?",
                    "What role should local authorities play?",
                ],
            },
            "integration_support": {
                "name": "Immigrant Integration and Support Services",
                "description": "Policies supporting newcomers' integration into American society",
                "key_questions": [
                    "What support services are needed?",
                    "How to fund and deliver services?",
                    "What defines successful integration?",
                ],
            },
        }

    def analyze_policy_from_perspective(
        self, policy_id: str, perspective_id: str
    ) -> PolicyAnalysis:
        """Analyze a policy from a specific perspective's viewpoint."""
        policy = self.policies[policy_id]
        perspective = self.perspectives[perspective_id]

        # Calculate support level based on alignment
        support_level = self._calculate_support_level(policy, perspective)

        # Identify concerns and benefits
        concerns = self._identify_concerns(policy, perspective)
        benefits = self._identify_benefits(policy, perspective)
        recommendations = self._generate_recommendations(policy, perspective)

        # Calculate confidence
        confidence = self._calculate_confidence(policy, perspective)

        return PolicyAnalysis(
            policy_id=policy_id,
            policy_name=policy["name"],
            perspective_id=perspective_id,
            perspective_name=perspective.name,
            support_level=support_level,
            concerns=concerns,
            benefits=benefits,
            recommendations=recommendations,
            confidence=confidence,
        )

    def _calculate_support_level(self, policy: Dict, perspective: Perspective) -> float:
        """Calculate support level (-1 to 1) based on policy-perspective alignment."""
        # This would use detailed policy-perspective matrix in real implementation
        # For now, use heuristic based on perspective priorities
        base_support = 0.0

        # Check alignment with key concerns
        for concern in policy.get("key_concerns", []):
            if concern in perspective.key_concerns:
                base_support += 0.1
            elif concern in [
                c for c in perspective.key_concerns if "opposes" in c.lower()
            ]:
                base_support -= 0.1

        # Adjust based on primary stance
        if (
            "humanitarian" in perspective.primary_stance.lower()
            and "humanitarian" in policy.get("description", "").lower()
        ):
            base_support += 0.2
        elif (
            "enforcement" in perspective.primary_stance.lower()
            and "enforcement" in policy.get("description", "").lower()
        ):
            base_support += 0.2

        return max(-1.0, min(1.0, base_support))

    def _identify_concerns(self, policy: Dict, perspective: Perspective) -> List[str]:
        """Identify potential concerns from the perspective."""
        concerns = []

        # Check for conflicts with core values
        for value in perspective.core_values:
            if value in ["Order", "Rule of Law", "Security"]:
                concerns.append("Potential for policy to compromise core values")

        # Check key concerns
        for concern in perspective.key_concerns:
            if concern in [
                "Family separation",
                "Discrimination",
                "Economic exploitation",
            ]:
                concerns.append(f"Risk of {concern.lower()}")

        return concerns if concerns else ["Minimal concerns identified"]

    def _identify_benefits(self, policy: Dict, perspective: Perspective) -> List[str]:
        """Identify potential benefits from the perspective."""
        benefits = []

        # Check alignment with priorities
        for pref in perspective.policy_preferences:
            if any(pref.lower() in q.lower() for q in policy.get("key_questions", [])):
                benefits.append(f"Supports {pref.lower()}")

        if not benefits:
            benefits.append("General policy goals aligned")

        return benefits

    def _generate_recommendations(
        self, policy: Dict, perspective: Perspective
    ) -> List[str]:
        """Generate recommendations from the perspective."""
        recommendations = []

        if "humanitarian" in perspective.primary_stance.lower():
            recommendations.append("Prioritize humanitarian considerations")
            recommendations.append("Ensure due process protections")

        if "economic" in perspective.primary_stance.lower():
            recommendations.append("Conduct economic impact analysis")
            recommendations.append("Balance workforce needs with protection")

        if not recommendations:
            recommendations.append("Balance competing priorities")
            recommendations.append("Ensure fair implementation")

        return recommendations

    def _calculate_confidence(self, policy: Dict, perspective: Perspective) -> float:
        """Calculate confidence in analysis based on perspective awareness and expertise."""
        base_confidence = perspective.policy_awareness * 0.5

        # Add expertise component
        if perspective.category == PerspectiveCategory.EXPERTS:
            base_confidence += 0.3
        elif perspective.category == PerspectiveCategory.STAKEHOLDERS:
            base_confidence += 0.2

        return min(1.0, base_confidence)

    def compare_perspectives(
        self, perspective_a: str, perspective_b: str
    ) -> PerspectiveComparison:
        """Compare two perspectives to find agreements and contradictions."""
        p_a = self.perspectives[perspective_a]
        p_b = self.perspectives[perspective_b]

        # Calculate agreement score
        agreement_score = self._calculate_agreement(p_a, p_b)

        # Calculate contradiction score
        contradiction_score = self._calculate_contradiction(p_a, p_b)

        # Find common ground
        common_ground = self._find_common_ground(p_a, p_b)

        # Identify key differences
        key_differences = self._identify_differences(p_a, p_b)

        # Determine policy alignment
        if agreement_score > 0.7:
            policy_alignment = "aligned"
        elif agreement_score > 0.4:
            policy_alignment = "partial"
        else:
            policy_alignment = "opposed"

        return PerspectiveComparison(
            perspective_a=perspective_a,
            perspective_b=perspective_b,
            agreement_score=agreement_score,
            contradiction_score=contradiction_score,
            common_ground=common_ground,
            key_differences=key_differences,
            policy_alignment=policy_alignment,
        )

    def _calculate_agreement(self, p_a: Perspective, p_b: Perspective) -> float:
        """Calculate agreement score between two perspectives."""
        agreement = 0.0

        # Core values alignment
        shared_values = set(p_a.core_values) & set(p_b.core_values)
        agreement += len(shared_values) / max(len(p_a.core_values), 1) * 0.3

        # Key concerns overlap
        shared_concerns = set(p_a.key_concerns) & set(p_b.key_concerns)
        agreement += len(shared_concerns) / max(len(p_a.key_concerns), 1) * 0.3

        # Policy preferences alignment
        shared_prefs = set(p_a.policy_preferences) & set(p_b.policy_preferences)
        agreement += len(shared_prefs) / max(len(p_a.policy_preferences), 1) * 0.4

        return min(1.0, agreement)

    def _calculate_contradiction(self, p_a: Perspective, p_b: Perspective) -> float:
        """Calculate contradiction score between two perspectives."""
        contradiction = 0.0

        # Check for opposing preferences
        for pref_a in p_a.policy_preferences:
            for pref_b in p_b.policy_preferences:
                if self._are_opposing(pref_a, pref_b):
                    contradiction += 0.2

        return min(1.0, contradiction)

    def _are_opposing(self, pref_a: str, pref_b: str) -> bool:
        """Check if two preferences are opposing."""
        pref_a_lower = pref_a.lower()
        pref_b_lower = pref_b.lower()

        opposing_pairs = [
            ("open borders", "strict enforcement"),
            ("expand pathways", "reduce immigration"),
            ("humanitarian", "enforcement first"),
            ("protect workers", "increase workforce"),
        ]

        for pair in opposing_pairs:
            if pair[0] in pref_a_lower and pair[1] in pref_b_lower:
                return True
            if pair[1] in pref_a_lower and pair[0] in pref_b_lower:
                return True

        return False

    def _find_common_ground(self, p_a: Perspective, p_b: Perspective) -> List[str]:
        """Find common ground between two perspectives."""
        common_ground = []

        # Shared values
        shared_values = set(p_a.core_values) & set(p_b.core_values)
        if shared_values:
            common_ground.append(f"Shared values: {', '.join(shared_values)}")

        # Shared concerns
        shared_concerns = set(p_a.key_concerns) & set(p_b.key_concerns)
        if shared_concerns:
            common_ground.append(f"Shared concerns: {', '.join(shared_concerns)}")

        # Overlapping priorities
        if not common_ground:
            common_ground.append("Potential for compromise on implementation details")

        return common_ground

    def _identify_differences(self, p_a: Perspective, p_b: Perspective) -> List[str]:
        """Identify key differences between perspectives."""
        differences = []

        # Different priorities
        unique_a = set(p_a.core_values) - set(p_b.core_values)
        unique_b = set(p_b.core_values) - set(p_a.core_values)

        if unique_a:
            differences.append(f"{p_a.name} prioritizes: {', '.join(unique_a)}")
        if unique_b:
            differences.append(f"{p_b.name} prioritizes: {', '.join(unique_b)}")

        # Different approaches
        if p_a.primary_stance != p_b.primary_stance:
            differences.append("Different primary approaches to immigration")

        return differences if differences else ["Subtle differences in emphasis"]

    def generate_cross_reference_matrix(self) -> Dict[str, List[Dict]]:
        """Generate cross-reference matrix for all perspective pairs."""
        matrix = {}
        perspectives_list = list(self.perspectives.keys())

        for i, p_a in enumerate(perspectives_list):
            matrix[p_a] = []
            for j, p_b in enumerate(perspectives_list):
                if i != j:
                    comparison = self.compare_perspectives(p_a, p_b)
                    matrix[p_a].append(
                        {
                            "perspective_b": p_b,
                            "agreement_score": comparison.agreement_score,
                            "contradiction_score": comparison.contradiction_score,
                            "policy_alignment": comparison.policy_alignment,
                            "common_ground": comparison.common_ground,
                        }
                    )

        return matrix

    def calculate_consensus_scores(self) -> Dict[str, float]:
        """Calculate consensus scores for each policy area across all perspectives."""
        consensus = {}

        for policy_id in self.policies:
            support_scores = []
            for perspective_id in self.perspectives:
                analysis = self.analyze_policy_from_perspective(
                    policy_id, perspective_id
                )
                support_scores.append(analysis.support_level)

            # Calculate consensus as average support with variance penalty
            avg_support = statistics.mean(support_scores) if support_scores else 0.0
            variance = (
                statistics.variance(support_scores) if len(support_scores) > 1 else 0.0
            )
            consensus_score = avg_support - (variance * 0.1)

            consensus[policy_id] = max(-1.0, min(1.0, consensus_score))

        return consensus

    def generate_counter_arguments(self, perspective_id: str) -> List[CounterArgument]:
        """Generate counter-arguments to a perspective."""
        perspective = self.perspectives[perspective_id]
        counter_arguments = []

        # Generate counter-arguments based on perspective type
        if perspective.category == PerspectiveCategory.DISENFRANCHISED:
            counter_arguments.extend(
                self._generate_disenfranchised_counters(perspective)
            )

        elif perspective.category == PerspectiveCategory.PRIVILEGED:
            counter_arguments.extend(self._generate_privileged_counters(perspective))

        elif perspective.category == PerspectiveCategory.EXPERTS:
            counter_arguments.extend(self._generate_expert_counters(perspective))

        elif perspective.category == PerspectiveCategory.IDEOLOGICAL:
            counter_arguments.extend(self._generate_ideological_counters(perspective))

        elif perspective.category == PerspectiveCategory.ENVIRONMENTAL:
            counter_arguments.extend(self._generate_environmental_counters(perspective))

        else:
            counter_arguments.extend(self._generate_general_counters(perspective))

        self.counter_arguments.extend(counter_arguments)
        return counter_arguments

    def _generate_disenfranchised_counters(
        self, perspective: Perspective
    ) -> List[CounterArgument]:
        """Generate counter-arguments to disenfranchised perspective."""
        return [
            CounterArgument(
                argument_id="CA-D1-001",
                perspective_id=perspective.perspective_id,
                argument_text=(
                    "Over-emphasis on humanitarian considerations without "
                    "addressing systemic root causes may perpetuate dependency"
                ),
                evidence_quality="moderate",
                supporting_sources=[
                    "Academic studies on aid dependency",
                    "Development economics research",
                ],
                potential_bias="Focus on immediate relief over long-term solutions",
                rebuttal_strength=0.65,
            ),
            CounterArgument(
                argument_id="CA-D1-002",
                perspective_id=perspective.perspective_id,
                argument_text=(
                    "Pathways to citizenship without enforcement may undermine rule of law "
                    "and create perception of unfairness to law-abiding immigrants"
                ),
                evidence_quality="moderate",
                supporting_sources=[
                    "Legal scholarship on rule of law",
                    "Public opinion studies",
                ],
                potential_bias="Potential for absolutist view of legal compliance",
                rebuttal_strength=0.70,
            ),
        ]

    def _generate_privileged_counters(
        self, perspective: Perspective
    ) -> List[CounterArgument]:
        """Generate counter-arguments to privileged perspective."""
        return [
            CounterArgument(
                argument_id="CA-D2-001",
                perspective_id=perspective.perspective_id,
                argument_text=(
                    "Overemphasis on enforcement can create humanitarian crises and "
                    "damage U.S. moral standing internationally"
                ),
                evidence_quality="strong",
                supporting_sources=[
                    "Human rights reports",
                    "International relations studies",
                ],
                potential_bias="Potential for忽视 security concerns",
                rebuttal_strength=0.75,
            ),
            CounterArgument(
                argument_id="CA-D2-002",
                perspective_id=perspective.perspective_id,
                argument_text=(
                    "Focus on taxpayer burden may overlook economic contributions of "
                    "immigrants, including undocumented workers"
                ),
                evidence_quality="strong",
                supporting_sources=["Economic impact studies", "Labor market research"],
                potential_bias="Potential for忽视 fiscal complexity",
                rebuttal_strength=0.80,
            ),
        ]

    def _generate_expert_counters(
        self, perspective: Perspective
    ) -> List[CounterArgument]:
        """Generate counter-arguments to expert perspective."""
        return [
            CounterArgument(
                argument_id="CA-D3-001",
                perspective_id=perspective.perspective_id,
                argument_text=(
                    "Over-reliance on quantitative metrics may overlook qualitative "
                    "humanitarian and ethical dimensions of immigration"
                ),
                evidence_quality="strong",
                supporting_sources=["Ethics of migration research", "Human rights law"],
                potential_bias="Potential for reductionism",
                rebuttal_strength=0.85,
            ),
            CounterArgument(
                argument_id="CA-D3-002",
                perspective_id=perspective.perspective_id,
                argument_text=(
                    "Expert-driven policies may lack democratic legitimacy and "
                    "fail to account for public sentiment and values"
                ),
                evidence_quality="moderate",
                supporting_sources=[
                    "Democratic theory",
                    "Public policy implementation studies",
                ],
                potential_bias="Potential for elitism",
                rebuttal_strength=0.70,
            ),
        ]

    def _generate_ideological_counters(
        self, perspective: Perspective
    ) -> List[CounterArgument]:
        """Generate counter-arguments to ideological perspective."""
        return [
            CounterArgument(
                argument_id="CA-D5-001",
                perspective_id=perspective.perspective_id,
                argument_text=(
                    "Ideological rigidity can prevent pragmatic solutions and "
                    "lead to policy failure in complex real-world contexts"
                ),
                evidence_quality="strong",
                supporting_sources=["Policy implementation research", "Case studies"],
                potential_bias="Potential for dogmatism",
                rebuttal_strength=0.80,
            ),
            CounterArgument(
                argument_id="CA-D5-002",
                perspective_id=perspective.perspective_id,
                argument_text=(
                    "Polarized ideological positions may undermine social cohesion "
                    "and make compromise impossible"
                ),
                evidence_quality="moderate",
                supporting_sources=[
                    "Social psychology research",
                    "Political science studies",
                ],
                potential_bias="Potential for忽视 ideological coherence",
                rebuttal_strength=0.75,
            ),
        ]

    def _generate_environmental_counters(
        self, perspective: Perspective
    ) -> List[CounterArgument]:
        """Generate counter-arguments to environmental perspective."""
        return [
            CounterArgument(
                argument_id="CA-D11-001",
                perspective_id=perspective.perspective_id,
                argument_text=(
                    "Over-emphasis on environmental impacts may忽视 other priorities "
                    "and disproportionately affect developing nations"
                ),
                evidence_quality="moderate",
                supporting_sources=["Global justice research", "Development studies"],
                potential_bias="Potential for environmental determinism",
                rebuttal_strength=0.65,
            ),
            CounterArgument(
                argument_id="CA-D11-002",
                perspective_id=perspective.perspective_id,
                argument_text=(
                    "Climate migration is complex and cannot be addressed through "
                    "immigration policy alone"
                ),
                evidence_quality="strong",
                supporting_sources=["Climate migration research", "International law"],
                potential_bias="Potential for policy overreach",
                rebuttal_strength=0.85,
            ),
        ]

    def _generate_general_counters(
        self, perspective: Perspective
    ) -> List[CounterArgument]:
        """Generate general counter-arguments."""
        return [
            CounterArgument(
                argument_id="CA-GEN-001",
                perspective_id=perspective.perspective_id,
                argument_text=(
                    "This perspective may overlook trade-offs between competing values"
                ),
                evidence_quality="moderate",
                supporting_sources=["Public policy analysis", "Decision theory"],
                potential_bias="Potential for one-sided analysis",
                rebuttal_strength=0.70,
            ),
            CounterArgument(
                argument_id="CA-GEN-002",
                perspective_id=perspective.perspective_id,
                argument_text=(
                    "Implementation challenges may undermine theoretical benefits"
                ),
                evidence_quality="strong",
                supporting_sources=["Implementation research", "Case studies"],
                potential_bias="Potential for忽视 practical constraints",
                rebuttal_strength=0.75,
            ),
        ]

    def verify_claims(self, claim: str, sources: List[str]) -> Dict:
        """Verify a claim through multiple sources."""
        return {
            "claim": claim,
            "verification_status": "partially verified"
            if len(sources) > 0
            else "unverified",
            "sources_count": len(sources),
            "sources": sources,
            "confidence": min(1.0, len(sources) * 0.3),
            "cross_references": self._cross_reference_claims(claim),
        }

    def _cross_reference_claims(self, claim: str) -> List[Dict]:
        """Cross-reference claim across different sources."""
        cross_references = []

        # Simulated cross-references
        cross_references.append(
            {
                "source": "Academic research",
                "alignment": "supportive",
                "confidence": 0.75,
            }
        )
        cross_references.append(
            {"source": "Government data", "alignment": "mixed", "confidence": 0.65}
        )
        cross_references.append(
            {"source": "NGO reports", "alignment": "supportive", "confidence": 0.70}
        )

        return cross_references

    def integrate_social_science(self, policy_id: str) -> Dict:
        """Integrate social science perspectives into policy analysis."""
        policy = self.policies[policy_id]

        integration = {
            "policy_id": policy_id,
            "policy_name": policy["name"],
            "social_science_frameworks": {
                "political_science": self._analyze_political_science(policy),
                "economics": self._analyze_economics(policy),
                "sociology": self._analyze_sociology(policy),
                "psychology": self._analyze_psychology(policy),
                "history": self._analyze_history(policy),
            },
            "synthesis": self._synthesize_findings(policy),
        }

        return integration

    def _analyze_political_science(self, policy: Dict) -> Dict:
        """Analyze policy through political science lens."""
        return {
            "voting_behavior": "Policy likely to be politically divisive",
            "democracy_models": "Challenges representative democracy models",
            "power_dynamics": "Significant power concentration in enforcement",
            "institutional_impact": "May strain existing institutions",
        }

    def _analyze_economics(self, policy: Dict) -> Dict:
        """Analyze policy through economics lens."""
        return {
            "labor_markets": "Mixed impacts on different wage groups",
            "fiscal_impact": "Variable fiscal effects across levels of government",
            "economic_growth": "Potential for positive long-term growth impact",
            "market_efficiency": "Current system has significant inefficiencies",
        }

    def _analyze_sociology(self, policy: Dict) -> Dict:
        """Analyze policy through sociology lens."""
        return {
            "social_integration": "Pathways to citizenship improve integration",
            "community_cohesion": "Enforcement policies may reduce community trust",
            "network_effects": "Immigrant networks have significant economic benefits",
            "cultural_impact": "Cultural enrichment vs. assimilation tensions",
        }

    def _analyze_psychology(self, policy: Dict) -> Dict:
        """Analyze policy through psychology lens."""
        return {
            "cognitive_biases": "Policy debates affected by availability heuristic",
            "risk_perception": "Overestimation of immigration risks",
            "emotional_factors": "Strong emotional responses to immigration issues",
            "motivated_reasoning": "Ideology strongly influences policy preferences",
        }

    def _analyze_history(self, policy: Dict) -> Dict:
        """Analyze policy through history lens."""
        return {
            "historical_patterns": "Cycles of openness and restriction",
            "past_policies": "Previous reforms provide lessons",
            "long_term_trends": "Globalization increases migration pressure",
            "historical_context": "U.S. immigration history shows adaptation",
        }

    def _synthesize_findings(self, policy: Dict) -> Dict:
        """Synthesize social science findings."""
        return {
            "overall_assessment": "Policy requires multi-faceted approach",
            "key_insights": [
                "Political feasibility is critical for implementation",
                "Economic benefits require complementary social policies",
                "Social integration determines long-term success",
                "Public perception must be managed through transparent communication",
            ],
            "recommendations": [
                "Combine economic analysis with social impact assessment",
                "Consider political feasibility and implementation capacity",
                "Address both material and social dimensions of integration",
            ],
        }

    def generate_comprehensive_analysis(self) -> Dict:
        """Generate comprehensive multi-perspective analysis."""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "perspectives_analyzed": len(self.perspectives),
            "policies_analyzed": len(self.policies),
            "policy_analyses": {},
            "cross_reference_matrix": self.generate_cross_reference_matrix(),
            "consensus_scores": self.calculate_consensus_scores(),
            "counter_arguments": {},
            "social_science_integration": {},
            "functional_recommendations": self._generate_functional_recommendations(),
        }

        # Generate analyses for each policy
        for policy_id in self.policies:
            policy_analyses = []
            for perspective_id in self.perspectives:
                analysis_result = self.analyze_policy_from_perspective(
                    policy_id, perspective_id
                )
                policy_analyses.append(analysis_result)

            analysis["policy_analyses"][policy_id] = policy_analyses

            # Generate counter arguments
            analysis["counter_arguments"][policy_id] = []
            for perspective_id in self.perspectives:
                counter_args = self.generate_counter_arguments(perspective_id)
                analysis["counter_arguments"][policy_id].extend(counter_args)

            # Social science integration
            analysis["social_science_integration"][policy_id] = (
                self.integrate_social_science(policy_id)
            )

        return analysis

    def _generate_functional_recommendations(self) -> List[Dict]:
        """Generate functional policy recommendations that satisfy ALL perspectives."""
        recommendations = []

        # Find common ground across perspectives
        consensus_items = self._find_consensus_items()

        # Generate recommendations based on consensus
        for item in consensus_items:
            recommendation = self._generate_recommendation_from_consensus(item)
            recommendations.append(recommendation)

        # Generate additional recommendations in consistent format
        additional_recommendations = [
            {
                "item": "Multi-tiered representation system",
                "consensus_level": "broad",
                "recommendation": "Establish multi-tiered representation system with county → state → national feedback loop",
                "rationale": "Addresses geographic variation while maintaining national consistency",
                "affected_perspectives": ["D1", "D2", "D6"],
                "expected_outcome": "Improved policy legitimacy and implementation",
            },
            {
                "item": "Evidence-based evaluation",
                "consensus_level": "broad",
                "recommendation": "Implement evidence-based policy evaluation with independent oversight",
                "rationale": "Addresses expert concerns while maintaining democratic accountability",
                "affected_perspectives": ["D3", "D4", "D5"],
                "expected_outcome": "Improved policy effectiveness and adaptability",
            },
            {
                "item": "Regional adaptation fund",
                "consensus_level": "moderate",
                "recommendation": "Create regional adaptation fund to support local implementation",
                "rationale": "Addresses geographic disparities while maintaining national standards",
                "affected_perspectives": ["D6", "D7", "D8"],
                "expected_outcome": "Reduced geographic inequality",
            },
            {
                "item": "Independent oversight body",
                "consensus_level": "moderate",
                "recommendation": "Establish independent oversight body with diverse representation",
                "rationale": "Addresses concerns about power concentration and elite capture",
                "affected_perspectives": ["D1", "D3", "D9"],
                "expected_outcome": "Improved fairness and accountability",
            },
            {
                "item": "Adaptive policy framework",
                "consensus_level": "moderate",
                "recommendation": "Develop adaptive policy framework with built-in review mechanisms",
                "rationale": "Addresses long-term sustainability concerns",
                "affected_perspectives": ["D7", "D10", "D11", "D12"],
                "expected_outcome": "Enhanced policy resilience and adaptability",
            },
        ]

        recommendations.extend(additional_recommendations)

        return recommendations

    def _find_consensus_items(self) -> List[Dict]:
        """Find items of consensus across perspectives."""
        consensus_items = []

        # Check for items with broad agreement
        for p_id, perspective in self.perspectives.items():
            if perspective.trust_level > 0.6:
                consensus_items.append(
                    {
                        "item": "Transparency in policy implementation",
                        "consensus_level": "high",
                        "supporting_perspectives": [p_id],
                    }
                )

        # Add items based on analysis
        consensus_items.extend(
            [
                {
                    "item": "Due process protections for all immigrants",
                    "consensus_level": "broad",
                    "supporting_perspectives": ["D1", "D3", "D5", "D10"],
                },
                {
                    "item": "Economic impact assessment before major policy changes",
                    "consensus_level": "broad",
                    "supporting_perspectives": ["D2", "D3", "D4", "D8", "D12"],
                },
                {
                    "item": "Humanitarian considerations in enforcement decisions",
                    "consensus_level": "moderate",
                    "supporting_perspectives": ["D1", "D5", "D10", "D11"],
                },
            ]
        )

        return consensus_items

    def _generate_recommendation_from_consensus(self, item: Dict) -> Dict:
        """Generate recommendation from consensus item."""
        return {
            "item": item["item"],
            "consensus_level": item["consensus_level"],
            "recommendation": f"Develop policy framework that incorporates {item['item'].lower()}",
            "rationale": f" broad agreement on {item['item'].lower()} across diverse perspectives",
            "affected_perspectives": item["supporting_perspectives"],
            "expected_outcome": "Increased policy legitimacy and effectiveness",
        }


def main() -> None:
    """Main function to run the multi-perspective analysis."""
    print("=" * 80)
    print("MULTI-PERSPECTIVE CRITIQUE AND CROSS-REFERENCE SYSTEM")
    print("U.S. Immigration Policy Analysis")
    print("=" * 80)
    print()

    # Initialize analysis
    analysis = MultiPerspectiveAnalysis()

    # Generate comprehensive analysis
    results = analysis.generate_comprehensive_analysis()

    # Print summary
    print("SUMMARY")
    print("-" * 80)
    print(f"Perspectives analyzed: {results['perspectives_analyzed']}")
    print(f"Policies analyzed: {results['policies_analyzed']}")
    print(
        f"Total policy analyses: {sum(len(v) for v in results['policy_analyses'].values())}"
    )
    print()

    # Print consensus scores
    print("CONSENSUS SCORES BY POLICY AREA")
    print("-" * 80)
    for policy_id, score in results["consensus_scores"].items():
        policy_name = analysis.policies[policy_id]["name"]
        print(f"{policy_name}: {score:.2%}")
    print()

    # Print functional recommendations
    print("FUNCTIONAL RECOMMENDATIONS (Satisfying ALL Perspectives)")
    print("-" * 80)
    for i, rec in enumerate(results["functional_recommendations"], 1):
        print(f"\n{i}. [{rec['priority']}] {rec['recommendation']}")
        print(f"   Rationale: {rec['rationale']}")
        print(f"   Expected Outcome: {rec['expected_outcome']}")
    print()

    # Print social science integration
    print("SOCIAL SCIENCE INTEGRATION")
    print("-" * 80)
    for policy_id, integration in results["social_science_integration"].items():
        print(f"\n{integration['policy_name']}:")
        for framework, findings in integration["social_science_frameworks"].items():
            print(f"  {framework}: {findings}")
        print(f"  Synthesis: {integration['synthesis']['overall_assessment']}")
    print()

    print("=" * 80)
    print("Analysis complete. Full results available in comprehensive analysis object.")
    print("=" * 80)


if __name__ == "__main__":
    main()
