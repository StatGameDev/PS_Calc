from dataclasses import dataclass

# Weapon types whose BATK uses DEX as the primary stat (long-range attack flag).
# Matches the W_* cases in battle_calc_base_damage2 / battle_calc_weapon_attack.
# Source: battle.c lines 3262-3272, 5282-5287.
RANGED_WEAPON_TYPES: frozenset = frozenset({
    "Bow", "MusicalInstrument", "Whip",
    "Revolver", "Rifle", "Gatling", "Shotgun", "Grenade",
})


@dataclass
class Weapon:
    """Exact mirror of struct weapon_data used in status.c / battle.c for BF_WEAPON attacks."""
    atk: int = 0
    refine: int = 0
    level: int = 1
    element: int = 0        # 0=Neutral, 1=Water, ...
    weapon_type: str = "Unarmed"   # exact index into size_fix.json table (and sd->weapontype1)
    hand: str = "right"            # "right" or "left" – selects atkmods[t_size] in battle.c sizefix
    aegis_name: str = ""           # AegisName from item_db — display only, no calculation effect
    refineable: bool = True        # Refine: false in item_db → suppress overrefine bonus in base_damage.py