from dataclasses import dataclass, field
from typing import Dict, List

from core.models.item_effect import ItemEffect
from core.models.sc_effect import SCEffect


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
    mdef_: int = 0      # bMdef (hard MDEF)

    # Status bonuses
    maxhp: int = 0      # bMaxHP
    maxsp: int = 0      # bMaxSP
    maxhp_rate: int = 0  # bMaxHPrate — % rate bonus to MaxHP (S-2)
    matk_rate: int = 0   # bMatkRate  — % rate bonus to MATK  (S-2)

    # Element overrides from scripts — int 0-9 or None if not overridden (S-3 wiring)
    script_atk_ele: int | None = None  # bAtkEle — weapon element from script
    script_def_ele: int | None = None  # bDefEle — armor element from script

    # ASPD
    aspd_percent: int = 0   # bAspdRate
    aspd_add: int = 0       # bAspd (flat amotion reduction)

    # All parsed bonus effects across all equipped items (for tooltips)
    all_effects: List[ItemEffect] = field(default_factory=list)

    # SC effects from sc_start/sc_start2/sc_start4 calls across all items (S-4)
    # Routed to StatusCalculator via build_applicator in S-5.
    sc_effects: List[SCEffect] = field(default_factory=list)

    # E2 stubs: race/size/element multipliers (not yet wired into pipeline)
    # Stored raw for future implementation
    add_race: Dict[str, int] = field(default_factory=dict)   # {race: bonus%}
    sub_ele: Dict[str, int] = field(default_factory=dict)    # {ele: resist%}
    sub_race: Dict[str, int] = field(default_factory=dict)   # {race: resist%}
    add_size: Dict[str, int] = field(default_factory=dict)   # {size: bonus%}
    add_ele: Dict[str, int] = field(default_factory=dict)    # {ele: bonus%}
    ignore_def_rate: Dict[str, int] = field(default_factory=dict)   # {race: %}
    ignore_mdef_rate: Dict[str, int] = field(default_factory=dict)  # {race: %}
    skill_atk: Dict[str, int] = field(default_factory=dict)  # {skill: %}

    # Incoming damage rate modifiers (for target-side CardFix / PvP)
    near_atk_def_rate: int = 0   # bNearAtkDef — % reduction vs melee
    long_atk_def_rate: int = 0   # bLongAtkDef — % reduction vs ranged
    magic_def_rate:    int = 0   # bMagicDefRate — % reduction vs magic
    atk_rate:          int = 0   # bAtkRate — flat % bonus to physical ATK

    # Skill timing (G59)
    # castrate: sum of bCastrate / bVarCastrate val deltas.
    #   sd->castrate in Hercules starts at 100; gear_bonuses.castrate is the delta.
    #   Applied as: time = time * (100 + castrate) // 100  (pc.c:2639; skill.c:~17197)
    castrate: int = 0
    # delayrate: sum of bDelayrate val deltas. Same delta-from-100 convention.
    #   Applied as: time = time * (100 + delayrate) // 100  (pc.c:3020; skill.c:~17506)
    delayrate: int = 0
    # skill_castrate: per-skill cast reduction from bonus2 bCastrate,skill_name,val.
    #   Keys are skill constant name strings (e.g. "AL_HOLYLIGHT").  (pc.c:3607)
    skill_castrate: Dict[str, int] = field(default_factory=dict)
