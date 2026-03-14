"""
D5 — Item script parser.
Parses Hercules AtCommands-style scripts: bonus/bonus2/bonus3 calls.

Only bonus types relevant to the damage calculator or tooltips are handled.
Unknown types produce an ItemEffect with description="[{bonus_type} effect]".

Source: Hercules/src/map/script.c (bonus registration table)

S-1: Description logic moved to core/bonus_definitions.py (BONUS1/2/3 tables).
     Adding a new bonus type requires only one entry there.
S-4: parse_sc_start() added — parses sc_start/sc_start2/sc_start4 calls
     into SCEffect objects. Used by GearBonusAggregator for consumable items.
"""
from __future__ import annotations

import re

from core.bonus_definitions import BONUS1, BONUS2, BONUS3
from core.models.item_effect import ItemEffect
from core.models.sc_effect import SCEffect

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


# ---------------------------------------------------------------------------
# sc_start parser
# ---------------------------------------------------------------------------

# Matches sc_start / sc_start2 / sc_start4 in both forms:
#   sc_start  SC_NAME, dur, v1, ...;
#   sc_start4(SC_NAME, dur, v1, ...);
# Captures the variant suffix and the SC_NAME; remaining tokens parsed below.
_SC_START_RE = re.compile(
    r'\bsc_start(2|4)?\s*\(?\s*'   # sc_start, sc_start2, sc_start4; optional '('
    r'(SC_\w+)'                      # SC_NAME constant
    r'((?:\s*,\s*-?[\w.]+)*)',       # zero or more comma-separated tokens
    re.MULTILINE,
)


def parse_sc_start(script: str) -> list[SCEffect]:
    """
    Parse all sc_start / sc_start2 / sc_start4 calls in a Hercules item script.

    Returns a list of SCEffect objects.  Non-numeric tokens (e.g. SCFLAG_NONE,
    Ele_Neutral) are silently skipped when collecting val1–val4.

    Duration of -1 means permanent (OnEquip).  For val ordering:
    - sc_start  args: sc_name, duration, val1[, val2][, val3]
    - sc_start2 args: sc_name, duration, val1, val2  (same storage, different internal route)
    - sc_start4 args: sc_name, duration, val1, val2, val3, val4
    """
    if not script:
        return []

    effects: list[SCEffect] = []

    for m in _SC_START_RE.finditer(script):
        sc_name = m.group(2)
        raw_tokens = m.group(3) or ""

        # Split on commas; convert numeric tokens; skip non-numeric (flags, ele names)
        numeric: list[int] = []
        for tok in raw_tokens.split(","):
            tok = tok.strip()
            if not tok:
                continue
            try:
                numeric.append(int(tok))
            except ValueError:
                pass  # SCFLAG_NONE, Ele_Neutral, etc.

        if not numeric:
            # No duration found — malformed; skip
            continue

        duration_ms = numeric[0]
        vals = numeric[1:]  # val1..val4
        effects.append(SCEffect(
            sc_name=sc_name,
            duration_ms=duration_ms,
            val1=vals[0] if len(vals) > 0 else 0,
            val2=vals[1] if len(vals) > 1 else 0,
            val3=vals[2] if len(vals) > 2 else 0,
            val4=vals[3] if len(vals) > 3 else 0,
        ))

    return effects
