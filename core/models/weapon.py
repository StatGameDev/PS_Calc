from dataclasses import dataclass


@dataclass
class Weapon:
    """Exact mirror of struct weapon_data used in status.c / battle.c for BF_WEAPON attacks."""
    atk: int = 0
    refine: int = 0
    level: int = 1
    element: int = 0        # 0=Neutral, 1=Water, ...
    weapon_type: str = "Unarmed"   # exact index into size_fix.json table (and sd->weapontype1)
    hand: str = "right"            # "right" or "left" – selects atkmods[t_size] in battle.c sizefix