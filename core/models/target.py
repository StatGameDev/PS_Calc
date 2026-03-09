from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Target:
    """Mirror of struct status_data for target side in battle_calc_damage / battle_calc_defense."""
    def_: int = 0
    vit: int = 0
    size: str = "Medium"    # Small / Medium / Large
    race: str = "Formless"
    element: int = 0
    element_level: int = 1   # 1-4 for attr_fix table
    is_boss: bool = False
    level: int = 1
    luk: int = 0              # tstatus->luk — used in crit roll: cri -= luk*2 (battle.c:4957)
    agi: int = 0              # tstatus->agi — used in FLEE calc: flee = level + agi (status.c)
    is_pc: bool = False
    targeted_count: int = 1   # unit_counttargeted(bl) value for VIT penalty (pre-renewal exact)
    sub_race: Dict[str, int] = field(default_factory=dict)   # RC_* keys — player's race resistance
    sub_ele:  Dict[str, int] = field(default_factory=dict)   # Ele_* keys — element resistance
    sub_size: Dict[str, int] = field(default_factory=dict)   # Size_* keys — size resistance
    near_attack_def_rate: int = 0   # % reduction vs melee
    long_attack_def_rate: int = 0   # % reduction vs ranged
    magic_def_rate: int = 0         # % reduction vs magic
    mdef_: int = 0                  # tstatus->mdef (hard MDEF)
    int_:  int = 0                  # tstatus->int (soft MDEF)
    armor_element: int = 0          # 0 = Neutral
    flee:  int = 0                  # tstatus->flee
    def_percent: int = 100          # st->def_percent: multiplier on vit_def for PC targets (battle.c:1492)