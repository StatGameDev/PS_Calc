from core.models.weapon import Weapon
from core.models.target import Target
from core.models.damage import DamageResult
from core.data_loader import loader


class AttrFix:
    """Element damage multiplier (after active status bonuses, verbatim position in battle_calc_weapon_attack)."""

    @staticmethod
    def calculate(weapon: Weapon, target: Target, current_damage: int, result: DamageResult) -> None:
        data = loader._load_json("tables/attr_fix.json")
        level = str(target.element_level or 1)
        defending = loader.get_element_name(target.element)
        attacking = loader.get_element_name(weapon.element)

        multiplier = data.get("table", {}).get(defending, {}).get(level, {}).get(attacking, 100)

        after = current_damage * multiplier // 100

        result.add_step(
            name="Attr Fix",
            value=after,
            multiplier=multiplier / 100.0,
            note=f"{attacking} vs {defending} Lv{level} ({multiplier}%)",
            formula=f"current * {multiplier} // 100 (from attr_fix table)",
            hercules_ref="battle.c: if (tstatus->ele) wd.damage = battle_calc_elem_damage(...);"
        )