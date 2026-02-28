from dataclasses import dataclass, field
from typing import List

@dataclass
class DamageStep:
    """Single step in the damage pipeline – now includes source-accurate debug strings."""
    name: str
    value: int
    multiplier: float = 1.0
    note: str = ""
    formula: str = ""          # e.g. "status.batk + weapon.atk + refine_bonus"
    hercules_ref: str = ""     # e.g. "battle.c: battle_calc_base_damage2 (pre-renewal)"

    # For backwards compatibility with existing code (Phase 2.2/2.3) REMOVE LATER?
    def __post_init__(self):
        if not self.formula:
            self.formula = "N/A (legacy step)"
        if not self.hercules_ref:
            self.hercules_ref = "N/A (legacy step)"


@dataclass
class DamageResult:
    """Full damage result – steps now carry formula + hercules_ref for Treeview debugging."""
    min_damage: int = 0
    max_damage: int = 0
    avg_damage: int = 0
    crit_chance: float = 0.0
    hit_chance: float = 0.0
    steps: List[DamageStep] = field(default_factory=list)   # ← FIXED: no more type error

    def add_step(self,
                 name: str,
                 value: int,
                 multiplier: float = 1.0,
                 note: str = "",
                 formula: str = "",
                 hercules_ref: str = ""):
        """Add step with full debug strings (used by all modifiers from 2.4 onward)."""
        self.steps.append(DamageStep(
            name=name,
            value=value,
            multiplier=multiplier,
            note=note,
            formula=formula,
            hercules_ref=hercules_ref
        ))