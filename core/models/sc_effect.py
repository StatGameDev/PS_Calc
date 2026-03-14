"""
S-4 — SCEffect model.

Represents a single sc_start/sc_start2/sc_start4 call parsed from an item script.
Stored in GearBonuses.sc_effects; routed to StatusCalculator in S-5.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SCEffect:
    """One parsed sc_start call from an item script."""
    sc_name:     str   # SC_* constant name, e.g. "SC_FOOD_STR"
    duration_ms: int   # duration in milliseconds; -1 = permanent
    val1: int = 0
    val2: int = 0
    val3: int = 0
    val4: int = 0
