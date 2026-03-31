"""
User interface components for the democratic decision-making system.

This module provides TUI (Text User Interface) components for interacting with the system.
"""

from src.ui.display import DecisionDisplay, PolicyDashboard
from src.ui.tui import (
    create_entities,
    display_json,
    display_results,
    display_rich,
    display_text,
    load_data,
    main,
    parse_args,
    run_decision,
)

__all__ = [
    "parse_args",
    "load_data",
    "create_entities",
    "run_decision",
    "display_results",
    "display_text",
    "display_rich",
    "display_json",
    "main",
    "DecisionDisplay",
    "PolicyDashboard",
]
