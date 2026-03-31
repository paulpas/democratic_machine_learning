#!/usr/bin/env python3
"""Interactive profile selection menu for the Democratic Machine Learning System.

Provides a terminal-based UI (via prompt_toolkit + rich) to:
  - Browse existing profiles
  - Create new profiles with arbitrary topic/domain strings
  - Edit or delete profiles
  - Launch a full analysis run for any selected profile

Usage:
    python3 src/ui/profile_menu.py
    # or, via just:
    just menu
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import (
    checkboxlist_dialog,
    input_dialog,
    message_dialog,
    radiolist_dialog,
    yes_no_dialog,
)
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.config import ProfileConfig
from src.ui.profile_loader import (
    get_default_domains,
    list_available_profiles,
    load_profile,
    profile_exists,
)
from src.ui.profile_manager import (
    create_profile,
    delete_profile,
    update_profile,
)

console = Console()

# ── repo root (two levels up from src/ui/) ────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
_RUN_SCRIPT = _REPO_ROOT / "run_all_domains.py"

# ── Default profile name ───────────────────────────────────────────────────────
DEFAULT_PROFILE_NAME = "default"

# ── prompt_toolkit colour theme ───────────────────────────────────────────────
STYLE = Style.from_dict(
    {
        "dialog": "bg:#1a1a2e",
        "dialog frame.label": "bg:#e94560 #ffffff bold",
        "dialog.body": "bg:#16213e #c8c8d4",
        "dialog.body label": "#e94560 bold",
        "dialog button": "bg:#0f3460 #ffffff",
        "dialog button focused": "bg:#e94560 #ffffff bold",
        "dialog shadow": "bg:#0a0a0a",
        "radio-list": "bg:#16213e",
        "radio-list focused": "bg:#0f3460",
        "checkbox-list": "bg:#16213e",
        "checkbox-list focused": "bg:#0f3460",
    }
)


# ── helpers ───────────────────────────────────────────────────────────────────


def _show_banner() -> None:
    """Print the system banner using rich."""
    console.print(
        Panel(
            "[bold white]Democratic Machine Learning System[/bold white]\n"
            "[dim]Profile-based Topic Selection & Analysis Launcher[/dim]",
            border_style="bright_blue",
            expand=False,
        )
    )


def _profile_table(profiles: List[str]) -> None:
    """Render a rich table of available profiles."""
    if not profiles:
        console.print("[yellow]No profiles found in config/profiles/[/yellow]")
        return

    table = Table(title="Available Profiles", border_style="bright_blue")
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="cyan bold")
    table.add_column("Domains", style="green")
    table.add_column("Depth", justify="right")
    table.add_column("Geo Fan-out", justify="center")

    for i, name in enumerate(profiles, 1):
        try:
            p = load_profile(name)
            domains_str = ", ".join(p.domains[:4])
            if len(p.domains) > 4:
                domains_str += f" +{len(p.domains) - 4}"
            table.add_row(
                str(i),
                name,
                domains_str,
                str(p.depth),
                "✓ all 50 states" if p.geo_fan_out else "✗ national only",
            )
        except Exception as exc:
            table.add_row(str(i), name, f"[red]error: {exc}[/red]", "—", "—")

    console.print(table)


def display_profile_summary(profile: ProfileConfig) -> None:
    """Render a detailed rich summary of *profile*."""
    table = Table(title=f"Profile: [bold cyan]{profile.name}[/bold cyan]", border_style="cyan")
    table.add_column("Field", style="cyan", width=22)
    table.add_column("Value", style="white")

    table.add_row("Name", profile.name)
    table.add_row("Description", profile.description or "[dim]—[/dim]")
    table.add_row("Topics / Domains", "\n".join(f"  • {d}" for d in profile.domains))
    table.add_row("Recursion Depth", str(profile.depth))
    table.add_row("Subtopics / Level", str(profile.subtopics_per_level))
    table.add_row(
        "Geographic Scope",
        "All 50 US states + counties" if profile.geo_fan_out else "National only",
    )

    if profile.expert_allocation:
        alloc = "\n".join(f"  {k}: {v}" for k, v in profile.expert_allocation.items())
        table.add_row("Expert Allocation", alloc)

    if profile.metadata:
        meta = ", ".join(f"{k}={v}" for k, v in profile.metadata.items() if k != "type")
        table.add_row("Metadata", meta or "[dim]—[/dim]")

    console.print(table)


# ── domain / topic selection helpers ─────────────────────────────────────────


def _select_domains_interactive() -> Optional[List[str]]:
    """Collect topics for a profile.

    Flow (free-text first, built-in checkboxes as an optional shortcut):
      1. Free-text entry — type *any* topic(s), comma-separated.
         This is the primary path; no restriction on subject matter.
      2. Optional built-in shortcut — checkbox list of the 6 default
         policy domains, all **unchecked** by default.  Useful when the
         user wants standard domains without typing them out.

    Returns:
        Combined, deduplicated list of topics, or ``None`` if cancelled.
    """
    # ── Step 1: free-text entry (primary path) ────────────────────────────
    custom_raw = input_dialog(
        title=HTML("<b>Enter Topics to Analyse</b>"),
        text=(
            "Type one or more topics separated by commas.\n"
            "Any subject is valid — policy, science, history, recipes, world events.\n\n"
            "Examples:\n"
            "  opioid crisis\n"
            "  AI governance, data privacy\n"
            "  grandmother's apple pie recipe\n"
            "  US immigration, housing affordability, climate\n\n"
            "Leave blank to skip to the built-in domain shortcut list."
        ),
        style=STYLE,
    ).run()

    if custom_raw is None:
        return None  # user pressed Escape

    custom_topics = [t.strip() for t in custom_raw.split(",") if t.strip()]

    # ── Step 2: optional built-in domain shortcuts (all unchecked) ────────
    add_builtin = yes_no_dialog(
        title=HTML("<b>Add Built-in Domain Shortcuts?</b>"),
        text=(
            "Would you like to also pick from the 6 standard policy domains?\n"
            "(economy, healthcare, education, immigration, climate, infrastructure)\n\n"
            "None are selected by default — this is purely a convenience shortcut."
        ),
        yes_text="Show shortcut list",
        no_text="No — use my topics only",
        style=STYLE,
    ).run()

    builtin_selected: list = []
    if add_builtin:
        builtin = get_default_domains()
        builtin_selected = (
            checkboxlist_dialog(
                title=HTML("<b>Built-in Domain Shortcuts  (all optional)</b>"),
                text=HTML(
                    "Space = toggle  ·  Enter = confirm  ·  Esc = skip\n"
                    "None are pre-selected. Pick any you want added to your topic list."
                ),
                values=[(d, d.capitalize().replace("_", " ")) for d in builtin],
                default_values=[],  # ← nothing pre-checked
                style=STYLE,
            ).run()
            or []
        )

    # ── Merge, deduplicate, preserve order ────────────────────────────────
    seen: set = set()
    topics: list = []
    for t in custom_topics + builtin_selected:
        key = t.lower().strip()
        if key and key not in seen:
            seen.add(key)
            topics.append(t)

    if not topics:
        message_dialog(
            title="No Topics Entered",
            text="At least one topic is required.\nPlease enter a topic or select a built-in domain.",
            style=STYLE,
        ).run()
        return None

    return topics


# ── main menu actions ─────────────────────────────────────────────────────────


def _action_select_and_run() -> None:
    """Select a profile from the list and immediately launch analysis."""
    profiles = list_available_profiles()
    if not profiles:
        message_dialog(
            title="No Profiles",
            text="No profiles found.\nCreate one first with 'Create new profile'.",
            style=STYLE,
        ).run()
        return

    chosen = radiolist_dialog(
        title=HTML("<b>Select Profile to Run</b>"),
        text="Arrow keys = navigate  ·  Enter = confirm  ·  Esc = cancel",
        values=[(p, p) for p in profiles],
        default=DEFAULT_PROFILE_NAME if DEFAULT_PROFILE_NAME in profiles else profiles[0],
        style=STYLE,
    ).run()

    if not chosen:
        return

    try:
        profile = load_profile(chosen)
    except Exception as exc:
        message_dialog(title="Error", text=f"Failed to load profile: {exc}", style=STYLE).run()
        return

    display_profile_summary(profile)

    confirmed = yes_no_dialog(
        title=HTML(f"<b>Run Analysis: {profile.name}</b>"),
        text=(
            f"Topics : {', '.join(profile.domains)}\n"
            f"Depth  : {profile.depth}\n"
            f"Geo    : {'All 50 states' if profile.geo_fan_out else 'National only'}\n\n"
            "Launch full analysis pipeline now?"
        ),
        yes_text="Run",
        no_text="Cancel",
        style=STYLE,
    ).run()

    if confirmed:
        _launch_analysis(profile)


def _action_create() -> None:
    """Multi-step wizard to create a new profile.

    Step order is intentional: topics come FIRST so the user thinks in terms
    of *what to analyse* before naming the profile.  Any subject is valid —
    the LLM has no topic restrictions.
    """
    # ── Step 1: what do you want to analyse? ─────────────────────────────
    domains = _select_domains_interactive()
    if not domains:
        return

    # ── Step 2: name the profile ──────────────────────────────────────────
    # Suggest a slug derived from the first topic for convenience
    topic_slug = domains[0].lower().strip().replace(" ", "-")[:24]
    name_raw = input_dialog(
        title=HTML("<b>Create Profile — Name</b>"),
        text=(
            "Give this profile a short name (letters, numbers, hyphens, underscores).\n"
            "It becomes the output sub-directory: output/<name>/"
        ),
        default=topic_slug,
        style=STYLE,
    ).run()

    if not name_raw:
        return

    name = name_raw.strip().lower().replace(" ", "-")

    if profile_exists(name):
        message_dialog(
            title="Name Taken",
            text=f"A profile named '{name}' already exists.\nChoose a different name.",
            style=STYLE,
        ).run()
        return

    # ── Step 3: optional description ─────────────────────────────────────
    description = input_dialog(
        title=HTML("<b>Create Profile — Description  (optional)</b>"),
        text="One-line description — press Enter to use the default:",
        default=", ".join(domains[:3]) + (" …" if len(domains) > 3 else ""),
        style=STYLE,
    ).run()

    # ── Step 4: recursion depth ───────────────────────────────────────────
    depth_raw = input_dialog(
        title=HTML("<b>Create Profile — Recursion Depth</b>"),
        text=(
            "How deep should the LLM investigate each topic?\n\n"
            "  2 = quick exploration   (~6 LLM calls, < 1 min)\n"
            "  4 = full production     (~700 calls per topic, hours)\n"
            "  6 = exhaustive          (very long — research-grade)\n\n"
            "Press Enter to accept the default."
        ),
        default="4",
        style=STYLE,
    ).run()

    depth = 4
    if depth_raw:
        try:
            depth = max(1, int(depth_raw))
        except ValueError:
            depth = 4

    try:
        profile = create_profile(
            name=name,
            domains=domains,
            config_overrides={
                "description": description or "",
                "depth": depth,
                "subtopics_per_level": 5,
                "geo_fan_out": True,
            },
        )
        console.print(
            f"\n[green]Profile '[bold]{profile.name}[/bold]' created successfully.[/green]"
        )
        display_profile_summary(profile)

        run_now = yes_no_dialog(
            title="Run Now?",
            text=f"Profile '{profile.name}' is ready.\nLaunch analysis now?",
            yes_text="Run Now",
            no_text="Later",
            style=STYLE,
        ).run()

        if run_now:
            _launch_analysis(profile)

    except Exception as exc:
        message_dialog(title="Error", text=f"Failed to create profile:\n{exc}", style=STYLE).run()


def _action_edit() -> None:
    """Edit an existing profile's settings."""
    profiles = list_available_profiles()
    if not profiles:
        message_dialog(title="No Profiles", text="No profiles to edit.", style=STYLE).run()
        return

    chosen = radiolist_dialog(
        title=HTML("<b>Edit Profile — Select</b>"),
        text="Choose the profile to edit:",
        values=[(p, p) for p in profiles],
        default=profiles[0],
        style=STYLE,
    ).run()

    if not chosen:
        return

    try:
        profile = load_profile(chosen)
    except Exception as exc:
        message_dialog(title="Error", text=f"Cannot load profile: {exc}", style=STYLE).run()
        return

    display_profile_summary(profile)

    field = radiolist_dialog(
        title=HTML(f"<b>Edit: {chosen}</b>"),
        text="Which field do you want to change?",
        values=[
            ("description", "Description"),
            ("depth", f"Recursion depth  (current: {profile.depth})"),
            ("subtopics", f"Subtopics per level  (current: {profile.subtopics_per_level})"),
            (
                "geo",
                f"Geo fan-out  (current: {'enabled' if profile.geo_fan_out else 'disabled'})",
            ),
            ("domains", f"Topics/Domains  (current: {', '.join(profile.domains)})"),
        ],
        style=STYLE,
    ).run()

    if not field:
        return

    updates: dict = {}

    if field == "description":
        val = input_dialog(
            title="Edit Description",
            text="New description:",
            default=profile.description,
            style=STYLE,
        ).run()
        if val is not None:
            updates["description"] = val

    elif field == "depth":
        val = input_dialog(
            title="Edit Depth",
            text="New recursion depth (1–6):",
            default=str(profile.depth),
            style=STYLE,
        ).run()
        if val:
            try:
                updates["depth"] = max(1, int(val))
            except ValueError:
                pass

    elif field == "subtopics":
        val = input_dialog(
            title="Edit Subtopics",
            text="Subtopics per level (1–10):",
            default=str(profile.subtopics_per_level),
            style=STYLE,
        ).run()
        if val:
            try:
                updates["subtopics_per_level"] = max(1, int(val))
            except ValueError:
                pass

    elif field == "geo":
        new_geo = yes_no_dialog(
            title="Geo Fan-out",
            text="Enable full geographic fan-out (all 50 US states + counties)?",
            yes_text="Enable",
            no_text="Disable",
            style=STYLE,
        ).run()
        updates["geo_fan_out"] = bool(new_geo)

    elif field == "domains":
        new_domains = _select_domains_interactive()
        if new_domains:
            updates["domains"] = new_domains

    if updates:
        try:
            updated = update_profile(chosen, updates)
            console.print(f"\n[green]Profile '[bold]{chosen}[/bold]' updated.[/green]")
            display_profile_summary(updated)
        except Exception as exc:
            message_dialog(title="Error", text=f"Update failed:\n{exc}", style=STYLE).run()


def _action_delete() -> None:
    """Delete a non-system profile."""
    profiles = [p for p in list_available_profiles() if p != DEFAULT_PROFILE_NAME]
    if not profiles:
        message_dialog(
            title="Nothing to Delete",
            text="No custom profiles found.\nThe 'default' profile cannot be deleted.",
            style=STYLE,
        ).run()
        return

    chosen = radiolist_dialog(
        title=HTML("<b>Delete Profile</b>"),
        text="Select the profile to permanently delete:",
        values=[(p, p) for p in profiles],
        default=profiles[0],
        style=STYLE,
    ).run()

    if not chosen:
        return

    confirmed = yes_no_dialog(
        title="Confirm Delete",
        text=f"Permanently delete profile '{chosen}'?\nThis cannot be undone.",
        yes_text="Delete",
        no_text="Cancel",
        style=STYLE,
    ).run()

    if confirmed:
        try:
            delete_profile(chosen)
            console.print(f"\n[red]Profile '[bold]{chosen}[/bold]' deleted.[/red]")
        except Exception as exc:
            message_dialog(title="Error", text=f"Delete failed:\n{exc}", style=STYLE).run()


def _action_view() -> None:
    """Display a summary of an existing profile."""
    profiles = list_available_profiles()
    if not profiles:
        message_dialog(title="No Profiles", text="No profiles found.", style=STYLE).run()
        return

    chosen = radiolist_dialog(
        title=HTML("<b>View Profile Details</b>"),
        text="Choose a profile to inspect:",
        values=[(p, p) for p in profiles],
        default=DEFAULT_PROFILE_NAME if DEFAULT_PROFILE_NAME in profiles else profiles[0],
        style=STYLE,
    ).run()

    if not chosen:
        return

    try:
        profile = load_profile(chosen)
        display_profile_summary(profile)
    except Exception as exc:
        message_dialog(title="Error", text=f"Cannot load profile: {exc}", style=STYLE).run()


# ── analysis launcher ─────────────────────────────────────────────────────────


def _launch_analysis(profile: ProfileConfig) -> None:
    """Invoke run_all_domains.py for the given profile as a subprocess.

    Passes ``--profile <name>`` so all output, checkpoints, and reports are
    routed to ``output/<profile-name>/``.
    """
    console.print(
        f"\n[bold yellow]Launching analysis for profile "
        f"'[cyan]{profile.name}[/cyan]'…[/bold yellow]"
    )
    console.print(f"[dim]  Topics : {', '.join(profile.domains)}[/dim]")
    console.print(f"[dim]  Depth  : {profile.depth}[/dim]")
    console.print(
        f"[dim]  Geo    : "
        f"{'all 50 states + counties' if profile.geo_fan_out else 'national only'}[/dim]\n"
    )

    cmd = [sys.executable, str(_RUN_SCRIPT), "--profile", profile.name]
    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted.[/yellow]")
    except Exception as exc:
        console.print(f"\n[red]Failed to launch analysis: {exc}[/red]")


# ── main menu loop ────────────────────────────────────────────────────────────


def run_menu() -> None:
    """Run the interactive profile menu loop."""
    _show_banner()

    menu_options = [
        ("run", "Select profile and run analysis"),
        ("create", "Create new profile"),
        ("view", "View profile details"),
        ("edit", "Edit existing profile"),
        ("delete", "Delete custom profile"),
        ("list", "List all profiles (table view)"),
        ("exit", "Exit"),
    ]

    while True:
        profiles = list_available_profiles()
        console.print(f"\n[dim]Profiles available: {len(profiles)}[/dim]")

        choice = radiolist_dialog(
            title=HTML(
                "<b>Democratic Machine Learning System</b>\n"
                "<ansiblue>Profile Management Menu</ansiblue>"
            ),
            text="Arrow keys = navigate  ·  Enter = select  ·  Ctrl-C = exit",
            values=menu_options,
            default="run",
            style=STYLE,
        ).run()

        if choice is None or choice == "exit":
            console.print("\n[bold]Goodbye.[/bold]")
            break

        if choice == "run":
            _action_select_and_run()
        elif choice == "create":
            _action_create()
        elif choice == "view":
            _action_view()
        elif choice == "edit":
            _action_edit()
        elif choice == "delete":
            _action_delete()
        elif choice == "list":
            console.print()
            _profile_table(profiles)


if __name__ == "__main__":
    try:
        run_menu()
    except KeyboardInterrupt:
        console.print("\n[bold]Cancelled.[/bold]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"\n[red]Fatal error:[/red] {exc}")
        sys.exit(1)
