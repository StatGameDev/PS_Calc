from dataclasses import dataclass, field
from typing import Dict, List

from core.models.item_effect import ItemEffect


@dataclass
class GearBonuses:
    """
    Aggregated numeric bonuses parsed from all equipped item scripts.
    These are added on top of the manually-entered bonus_* fields in PlayerBuild.
    Not saved to disk — recomputed each time equipment changes.

    Fields mirror the PlayerBuild bonus_* stubs they feed into.
    race/size/element multipliers are stored as effect lists for E2 (future).
    """
    # Flat stat bonuses
    str_: int = 0
    agi: int = 0
    vit: int = 0
    int_: int = 0
    dex: int = 0
    luk: int = 0

    # Combat bonuses
    batk: int = 0       # bBaseAtk
    hit: int = 0        # bHit
    flee: int = 0       # bFlee
    flee2: int = 0      # bFlee2 (perfect dodge)
    cri: int = 0        # bCritical
    crit_atk_rate: int = 0  # bCritAtkRate (%)
    long_atk_rate: int = 0  # bLongAtkRate (%)

    # Defensive
    def_: int = 0       # bDef (hard DEF)

    # Status bonuses
    maxhp: int = 0      # bMaxHP
    maxsp: int = 0      # bMaxSP

    # ASPD
    aspd_percent: int = 0   # bAspdRate
    aspd_add: int = 0       # bAspd (flat amotion reduction)

    # All parsed effects across all equipped items (for tooltips)
    all_effects: List[ItemEffect] = field(default_factory=list)

    # E2 stubs: race/size/element multipliers (not yet wired into pipeline)
    # Stored raw for future implementation
    add_race: Dict[str, int] = field(default_factory=dict)   # {race: bonus%}
    sub_ele: Dict[str, int] = field(default_factory=dict)    # {ele: resist%}
    sub_race: Dict[str, int] = field(default_factory=dict)   # {race: resist%}
    add_size: Dict[str, int] = field(default_factory=dict)   # {size: bonus%}
    add_ele: Dict[str, int] = field(default_factory=dict)    # {ele: bonus%}
    ignore_def_rate: Dict[str, int] = field(default_factory=dict)  # {race: %}
    skill_atk: Dict[str, int] = field(default_factory=dict)  # {skill: %}

    # Incoming damage rate modifiers (for target-side CardFix / PvP)
    near_atk_def_rate: int = 0   # bNearAtkDef — % reduction vs melee
    long_atk_def_rate: int = 0   # bLongAtkDef — % reduction vs ranged
    magic_def_rate:    int = 0   # bMagicDefRate — % reduction vs magic
    atk_rate:          int = 0   # bAtkRate — flat % bonus to physical ATK
