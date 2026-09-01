from __future__ import annotations

import argparse
import copy
from collections.abc import Iterable

# The run parser remains the single source of truth for names, types, defaults,
# choices and help text. This set only classifies which run options have valid
# semantics during clean regeneration.
REGENERATE_RUN_OPTIONS = frozenset(
    {
        "--provider",
        "--source",
        "--target",
        "--no-name-migration",
        "--parallel-videos",
        "--translation-batch-size",
        "--whisper-beam-size",
        "--whisper-cpu-threads",
        "--no-ffmpeg-copy",
        "--generate-webm",
        "--no-webm",
    }
)

RUN_ONLY_OPTIONS = frozenset(
    {
        "--scheduled",
        "--dry-run",
        "--no-retain-sources",
        "--no-resume",
    }
)


def _run_parser() -> argparse.ArgumentParser:
    """Return the run parser from main.py without duplicating its definitions."""
    from main import build_parser

    parser = build_parser()
    subparsers_action = parser._subparsers._group_actions[0]
    return subparsers_action.choices["run"]


def _iter_run_actions() -> Iterable[argparse.Action]:
    yield from _run_parser()._actions


def add_regenerate_run_options(parser: argparse.ArgumentParser) -> None:
    """Reuse run argparse actions whose semantics remain valid for regeneration."""
    actions = list(_iter_run_actions())
    by_option = {
        option: action
        for action in actions
        for option in action.option_strings
        if option in REGENERATE_RUN_OPTIONS
    }

    webm_actions = [by_option[option] for option in ("--generate-webm", "--no-webm") if option in by_option]
    if webm_actions:
        group = parser.add_mutually_exclusive_group()
        for action in webm_actions:
            group._add_action(copy.deepcopy(action))

    added: set[str] = set()
    for action in actions:
        selected = [option for option in action.option_strings if option in REGENERATE_RUN_OPTIONS]
        if not selected or any(option in added for option in selected) or action in webm_actions:
            continue
        parser._add_action(copy.deepcopy(action))
        added.update(selected)


def apply_shared_run_overrides(settings, args):
    """Apply the exact override implementation used by the normal run path."""
    from main import _apply_run_overrides

    return _apply_run_overrides(settings, args)
