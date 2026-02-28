from core.models.damage import DamageResult
from core.models.build import PlayerBuild
from core.models.status import StatusData
from core.models.weapon import Weapon
from core.models.skill import SkillInstance
from core.models.target import Target
from core.config import BattleConfig
from core.data_loader import loader
from core.calculators.modifiers.base_damage import BaseDamage

class BattlePipeline:
    """
    Orchestrator for the full pre-renewal BF_WEAPON damage calculation.
    Calls modifiers in the exact order of Hercules battle_calc_weapon_attack.
    """

    def __init__(self, config: BattleConfig):
        self.config = config

    def calculate(self,
                  status: StatusData,
                  weapon: Weapon,
                  skill: SkillInstance,
                  target: Target,
                  build: PlayerBuild) -> DamageResult:
        result = DamageResult()

        # Step 0 & 1 – input logging (always first)
        result.add_step("Status BATK", status.batk,
                        note=f"STR={status.str} DEX={status.dex}")
        result.add_step("Weapon ATK", weapon.atk,
                        note=f"Refine +{weapon.refine} Level {weapon.level}")

        # Load skill data from JSON (used by skill_ratio and NK checks later)
        skill_data = loader.get_skill(skill.id)

        # === BASE DAMAGE (exact position in battle_calc_weapon_attack) ===
        BaseDamage.calculate(status, weapon, result)

        # === PLACEHOLDERS (real modifiers replace these one by one) ===

        # Placeholder for skill_ratio.py (Sub-step 2.5) — temporary until full modifier
        if skill_data and skill_data.get("ratio_per_level"):
            ratio_list = skill_data["ratio_per_level"]
            ratio = ratio_list[skill.level - 1] if skill.level <= len(ratio_list) else 100
        else:
            ratio = 100
        # Use the value from the Base Damage step we just added (exact Hercules order)
        base_dmg = result.steps[-1].value
        dmg_after_ratio = base_dmg * ratio // 100
        result.add_step(f"Skill Ratio (ID {skill.id} Lv {skill.level})",
                        dmg_after_ratio, multiplier=ratio / 100.0,
                        note=skill_data["note"] if skill_data else "")

        # Placeholder for all remaining modifiers (size, ele, card, defense)
        final_dmg = max(1, dmg_after_ratio)   # temporary min-damage rule

        result.add_step("Final Damage (placeholder)", final_dmg)

        # Output values (variance/crit added later)
        result.min_damage = final_dmg
        result.max_damage = final_dmg
        result.avg_damage = final_dmg

        return result