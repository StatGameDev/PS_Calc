from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class PlayerBuild:
    """Everything you type manually from @status / equipment windows.
    active_status_levels added to support the full active status bonus mechanic (all SC_* from the investigation)."""
    base_level: int = 1
    job_level: int = 1
    job_id: int = 0

    base_str: int = 1
    base_agi: int = 1
    base_vit: int = 1
    base_int: int = 1
    base_dex: int = 1
    base_luk: int = 1

    bonus_str: int = 0
    bonus_agi: int = 0
    bonus_vit: int = 0
    bonus_int: int = 0
    bonus_dex: int = 0
    bonus_luk: int = 0

    equip_def: int = 0          # Hard DEF
    bonus_def2: int = 0         # Extra soft DEF from items / foods / SCs

    bonus_batk: int = 0
    bonus_cri: int = 0
    bonus_hit: int = 0
    bonus_flee: int = 0
    bonus_aspd_percent: int = 0

    # None = derive from equipped weapon's weapon_type at calc time.
    # Set True/False explicitly to override (e.g. musical instrument played melee).
    is_ranged_override: Optional[bool] = None

    no_sizefix: bool = False    # sd->special_state.no_sizefix – exact bypass for size fix

    # Conditional mastery support – exact flags needed for KN_SPEARMASTERY etc.
    # (pre-renewal only, mirrors pc_isridingpeco / pc_isridingdragon)
    is_riding_peco: bool = False

    # Full active status bonus support – all SC_* levels from the investigation
    active_status_levels: Dict[str, int] = field(default_factory=dict)
    # Key = "SC_AURABLADE", "SC_MAXIMIZEPOWER", etc.
    # Value = skill/level that set the status

    mastery_levels: Dict[str, int] = field(default_factory=dict)
    # Key = mastery skill name (e.g. "SM_SWORD", "KN_SPEARMASTERY")
    # Value = skill level

    # Save/load identity and equipment slots
    name: str = ""
    equipped: Dict[str, Optional[int]] = field(default_factory=dict)
    # Key = slot name (e.g. "right_hand", "ammo"), value = item ID or None
    refine_levels: Dict[str, int] = field(default_factory=dict)
    # Key = slot name, value = refine count for that slot
    weapon_elements: Dict[str, int] = field(default_factory=dict)
    # Key = slot name, value = element int (0-9). Overrides item_db element.
    # Used until a proper weapon-imbue item/SC system is implemented.
    target_mob_id: Optional[int] = None
    # When set, pipeline resolves target via loader.get_monster(target_mob_id).
    # None = caller supplies Target manually (used by GUI inputs once built).