"""
D5 — Item script parser.
Parses Hercules AtCommands-style scripts: bonus/bonus2/bonus3 calls.

Only bonus types relevant to the damage calculator or tooltips are handled.
Unknown types produce an ItemEffect with description="[{bonus_type} effect]".

Source: Hercules/src/map/script.c (bonus registration table)

S-1: Description logic moved to core/bonus_definitions.py (BONUS1/2/3 tables).
     Adding a new bonus type requires only one entry there.
"""
from __future__ import annotations

import re

from core.bonus_definitions import BONUS1, BONUS2, BONUS3
from core.models.item_effect import ItemEffect

# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

# Matches: bonus bXxx,val | bonus2 bXxx,a,b | bonus3 bXxx,a,b,c
# Also handles: bonus bXxx val  (space-separated)
_BONUS_RE = re.compile(
    r'\bbonus(2|3)?\s+'       # "bonus", "bonus2", or "bonus3"
    r'(b\w+)'                  # bonus type e.g. bStr
    r'(?:[,\s](.+?))?'         # optional params (lazy, to next semicolon or end)
    r'(?=;|$)',                # lookahead: ends at semicolon or EOL
    re.MULTILINE,
)


def _coerce(s: str):
    """Try to convert a param string to int; leave as str if not numeric."""
    s = s.strip()
    try:
        return int(s)
    except ValueError:
        return s


def parse_script(script: str) -> list[ItemEffect]:
    """Parse a Hercules item script string into a list of ItemEffect objects."""
    if not script:
        return []

    effects: list[ItemEffect] = []

    for m in _BONUS_RE.finditer(script):
        arity_suffix = m.group(1)  # None, "2", or "3"
        arity = int(arity_suffix) if arity_suffix else 1
        bonus_type = m.group(2)
        raw_params = m.group(3) or ""

        # Split params on comma; first param for arity-1 may be the only token
        parts = [p.strip() for p in raw_params.split(",") if p.strip()]
        params = [_coerce(p) for p in parts]

        description = _make_description(bonus_type, arity, params)

        effects.append(ItemEffect(
            bonus_type=bonus_type,
            arity=arity,
            params=params,
            description=description,
        ))

    return effects


def _make_description(bonus_type: str, arity: int, params: list) -> str:
    defn = {1: BONUS1, 2: BONUS2, 3: BONUS3}.get(arity, {}).get(bonus_type)
    if defn is None or len(params) < arity:
        return f"[{bonus_type} effect]"
    try:
        return defn.description(*params[:arity])
    except Exception:
        return f"[{bonus_type} effect]"
