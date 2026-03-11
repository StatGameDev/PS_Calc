from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.models.attack_definition import AttackDefinition


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
    """Full damage result – steps carry formula + hercules_ref for Treeview debugging.

    pmf: populated by the pipeline as it runs through modifiers (dict[int, float]).
    min_damage / max_damage / avg_damage: derived from pmf at the end of each pipeline
    branch via pmf_stats(result.pmf); do not set these manually mid-pipeline.
    """
    min_damage: int = 0
    max_damage: int = 0
    avg_damage: int = 0
    crit_chance: float = 0.0
    hit_chance: float = 0.0
    steps: List[DamageStep] = field(default_factory=list)
    pmf: dict = field(default_factory=dict)  # dict[int, float], populated by pipeline

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
    magic: Optional["DamageResult"] = None  # BF_MAGIC result (Session B); also mirrored in normal for GUI
    # G16: Katar normal-attack second hit (battle.c:5941-5952, #ifndef RENEWAL).
    # Computed from final post-pipeline PMF: damage2 = max(1, damage * (1 + TF_DOUBLE*2) // 100).
    # katar_second = second hit of non-crit branch; katar_second_crit = second hit of crit branch.
    katar_second: Optional["DamageResult"] = None
    katar_second_crit: Optional["DamageResult"] = None
    # G54: TF_DOUBLE (Knife) / GS_CHAINACTION (Revolver) proc branches.
    # proc_chance: percent probability per auto-attack swing (0 = not eligible).
    # double_hit / double_hit_crit: full 2-hit pipeline result for the proc swing.
    # Crit and proc are mutually exclusive (battle.c:4926).
    proc_chance: float = 0.0
    double_hit: Optional["DamageResult"] = None
    double_hit_crit: Optional["DamageResult"] = None
    # DPS stat: Σ(chance_i × damage_i) / Σ(chance_i × delay_i) × 1000  (dmg/s)
    dps: float = 0.0
    # Full attack distribution used to compute dps. Stored on BattleResult so:
    #   - future branches (skills, procs) just append without touching this class
    #   - FormulaSelectionStrategy passes through; MarkovSelectionStrategy will
    #     use state_requirement/next_state on each AttackDefinition to solve
    #     steady-state via eigenvector when turn-sequence modelling is added.
    attacks: List["AttackDefinition"] = field(default_factory=list)
