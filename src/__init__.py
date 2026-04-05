"""
democratic_machine_learning - A machine learning system for adaptive democratic decision-making.

This package implements a multi-tiered democratic decision-making algorithm that scales
with society and adapts to the needs of individuals and communities.
"""

__version__ = "0.1.0"
__author__ = "Paul Pas"

from src.core.decision_engine import DecisionEngine
from src.core.policy_cell import PolicyCell
from src.data.data_loader import DataLoader
from src.models.policy import Policy
from src.models.voter import Voter
from src.utils.metrics import FairnessMetrics

__all__ = [
    "DecisionEngine",
    "PolicyCell",
    "Voter",
    "Policy",
    "DataLoader",
    "FairnessMetrics",
]
