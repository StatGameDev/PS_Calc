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
    equip_mdef: int = 0         # Hard MDEF (from bMdef scripts)
    bonus_def2: int = 0         # Extra soft DEF from items / foods / SCs

    bonus_batk: int = 0
    bonus_cri: int = 0
    bonus_hit: int = 0
    bonus_flee: int = 0
    bonus_aspd_percent: int = 0
    bonus_aspd_add: int = 0      # flat amotion reduction from bAspd (Session 4 stub)
    bonus_maxhp: int = 0         # flat MaxHP addend from items/cards (Session 4 stub)
    bonus_maxsp: int = 0         # flat MaxSP addend from items/cards (Session 4 stub)

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

    server: str = "standard"    # "standard" or "payon_stories"

    # Save/load identity and equipment slots
    name: str = ""
    equipped: Dict[str, Optional[int]] = field(default_factory=dict)
    # Key = slot name (e.g. "right_hand", "ammo"), value = item ID or None
    refine_levels: Dict[str, int] = field(default_factory=dict)
    # Key = slot name, value = refine count for that slot
    weapon_element: Optional[int] = None
    # Element override for right_hand weapon (int 0-9). None = use item_db element.
    # Used for elemental imbues until a proper SC/item imbue system is implemented.
    armor_element: int = 0
    # Element of worn armor (int 0-9). Default 0 = Neutral (no armor element card).
    # Used for incoming damage pipeline: attr_fix(attacker.element, player.armor_element).
    target_mob_id: Optional[int] = None
    # When set, pipeline resolves target via loader.get_monster(target_mob_id).
    # None = caller supplies Target manually (used by GUI inputs once built).

    # G46: Active Items bonuses (consumable/food effects — temporary catch-all).
    # Keys: "str","agi","vit","int","dex","luk","batk","hit","flee","cri","def","mdef","aspd_pct","maxhp","maxsp"
    active_items_bonuses: Dict[str, int] = field(default_factory=dict)

    # G47: Manual Stat Adjustments (pure numeric escape hatch — no source attribution).
    # Same key set as active_items_bonuses.
    manual_adj_bonuses: Dict[str, int] = field(default_factory=dict)

    # G17: Forged weapon properties — right_hand.
    # is_forged=True hides card slots and activates forge_element in resolve_weapon.
    # forge_element: element from forge process (int 0-9); overridden by weapon_element if set.
    is_forged: bool = False
    forge_sc_count: int = 0    # star crumb count (0–3)
    forge_ranked: bool = False  # forger was ranked blacksmith (+10 star)
    forge_element: int = 0     # element from elemental stone (0=Neutral/none)

    # G52: Forged weapon properties — left_hand (dual-wield only).
    # Same semantics as above; no weapon_element override for LH (uses item_db / forge_element).
    lh_is_forged: bool = False
    lh_forge_sc_count: int = 0
    lh_forge_ranked: bool = False
    lh_forge_element: int = 0

    # M0: Party/outgoing buffs and target-applied debuffs received by the player's team.
    # Keys added per-session as sub-groups are implemented (M, M2, O, R).
    support_buffs: Dict[str, object] = field(default_factory=dict)
    # e.g. {"SC_ADRENALINE": 0, "SC_BLESSING": 0, "SC_IMPOSITIOMANUS": 0, ...}

    # M0: Debuffs the enemy has applied TO the player (affects incoming damage calcs).
    # Keys added in Session R when player_debuffs_section gets actual toggles.
    player_active_scs: Dict[str, object] = field(default_factory=dict)
    # e.g. {"SC_ETERNALCHAOS": False, "SC_CURSE": False, ...}

    # M2: Bard/Dancer song state — caster stats + per-song levels + per-stat overrides.
    # Bard keys: "caster_agi/dex/vit/int/luk", "mus_lesson", "SC_ASSNCROS" (level), "SC_ASSNCROS_agi" (None=shared), etc.
    # Dancer keys: "dancer_agi/dex/vit/int/luk", "dance_lesson", "SC_HUMMING" (level), etc.
    # Ensemble keys: "SC_DRUMBATTLE", "SC_NIBELUNGEN", "SC_SIEGFRIED" (level only).
    # None for override key = use shared caster stat. int = use that value.
    song_state: Dict[str, object] = field(default_factory=dict)