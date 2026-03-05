from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DamageRange:
    """Carries (min, max, avg) through the damage pipeline.
    All arithmetic uses floor division to match Hercules C integer behaviour.
    Never mutate in place — every method returns a new DamageRange."""
    min: int
    max: int
    avg: int

    def scale(self, num: int, denom: int) -> "DamageRange":
        """Multiplicative step: floor-divide per component.
        Do NOT batch sequential calls — Hercules truncates at each step."""
        return DamageRange(self.min * num // denom,
                           self.max * num // denom,
                           self.avg * num // denom)

    def add(self, flat: int) -> "DamageRange":
        """Deterministic flat addend — same value applied to all three components."""
        return DamageRange(self.min + flat, self.max + flat, self.avg + flat)

    def add_range(self, min_add: int, max_add: int, avg_add: int) -> "DamageRange":
        """Asymmetric flat addend — each component has a different addend.
        Used for overrefine (range [1, overrefine]) and arrow ATK variance."""
        return DamageRange(self.min + min_add, self.max + max_add, self.avg + avg_add)

    def subtract(self, min_sub: int, max_sub: int, avg_sub: int) -> "DamageRange":
        """Crossed asymmetric subtraction for independent VIT DEF variance.
        Because weapon ATK and VIT DEF rolls are independent:
          min output = self.min - max_sub  (low weapon roll, high DEF roll — worst case)
          max output = self.max - min_sub  (high weapon roll, low DEF roll — best case)
        min_sub/max_sub/avg_sub are the VIT DEF roll range, NOT the output range."""
        return DamageRange(self.min - max_sub,
                           self.max - min_sub,
                           self.avg - avg_sub)

    def floor_at(self, n: int = 1) -> "DamageRange":
        """Clamp every component to a minimum value (mirrors max(1, damage) in Hercules)."""
        return DamageRange(max(n, self.min), max(n, self.max), max(n, self.avg))


@dataclass
class DamageStep:
    """Single step in the damage pipeline – includes min/max/avg and source-accurate debug strings."""
    name: str
    value: int          # avg — used by GUI display
    min_value: int = 0  # populated when variance is known; 0 = informational step only
    max_value: int = 0  # populated when variance is known; 0 = informational step only
    multiplier: float = 1.0
    note: str = ""
    formula: str = ""          # e.g. "status.batk + weapon.atk + refine_bonus"
    hercules_ref: str = ""     # e.g. "battle.c: battle_calc_base_damage2 (pre-renewal)"

    def __post_init__(self):
        # Auto-fill only when BOTH are 0, meaning neither was explicitly provided
        # (informational step). If min_value=0 but max_value≠0, the zero is a
        # legitimate minimum damage value (e.g. size fix flooring a low-DEX roll).
        if self.min_value == 0 and self.max_value == 0:
            self.min_value = self.value
            self.max_value = self.value
        if not self.formula:
            self.formula = "N/A (legacy step)"
        if not self.hercules_ref:
            self.hercules_ref = "N/A (legacy step)"


@dataclass
class DamageResult:
    """Full damage result – steps carry formula + hercules_ref for Treeview debugging."""
    min_damage: int = 0
    max_damage: int = 0
    avg_damage: int = 0
    crit_chance: float = 0.0
    hit_chance: float = 0.0
    steps: List[DamageStep] = field(default_factory=list)

    def add_step(self,
                 name: str,
                 value: int,
                 min_value: int = 0,
                 max_value: int = 0,
                 multiplier: float = 1.0,
                 note: str = "",
                 formula: str = "",
                 hercules_ref: str = ""):
        """Add step with full debug strings and optional min/max range."""
        self.steps.append(DamageStep(
            name=name,
            value=value,
            min_value=min_value,
            max_value=max_value,
            multiplier=multiplier,
            note=note,
            formula=formula,
            hercules_ref=hercules_ref,
        ))


@dataclass
class BattleResult:
    """Full output of BattlePipeline.calculate() — carries both normal and crit branches.

    normal:      Always present. Full DamageResult for the non-crit hit path.
    crit:        None when the skill/attack is ineligible for crits (e.g. SM_BASH).
                 Otherwise a full DamageResult for the crit hit path.
    crit_chance: Probability (percent, 0-100) that a single hit is a crit.
                 0.0 when crit is None.
    hit_chance:  Placeholder — E1 (hit/miss system) not yet implemented.
                 Always 100.0 until E1 is done.
    """
    normal: "DamageResult" = field(default_factory=lambda: DamageResult())
    crit: Optional["DamageResult"] = None
    crit_chance: float = 0.0
    hit_chance: float = 100.0      # basic hit% (80 + HIT - FLEE, clamped to [min, max])
    perfect_dodge: float = 0.0    # target's perfect dodge chance (luk+10)/10 %
