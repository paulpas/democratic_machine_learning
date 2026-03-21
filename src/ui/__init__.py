"""
User interface components for the democratic decision-making system.

This module provides TUI (Text User Interface) components for interacting with the system.
"""

from src.ui.tui import (
    parse_args,
    load_data,
    create_entities,
    run_decision,
    display_results,
    display_text,
    display_rich,
    display_json,
    main,
)
from src.ui.display import DecisionDisplay, PolicyDashboard

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
