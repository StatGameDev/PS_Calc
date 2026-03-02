from dataclasses import dataclass

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
    is_pc: bool = False
    targeted_count: int = 1   # NEW: unit_counttargeted(bl) value for VIT penalty (pre-renewal exact)