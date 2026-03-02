from core.models.damage import DamageResult
from core.models.build import PlayerBuild
from core.models.status import StatusData
from core.models.weapon import Weapon
from core.models.skill import SkillInstance
from core.models.target import Target
from core.config import BattleConfig
from core.data_loader import loader
from core.calculators.modifiers.base_damage import BaseDamage
from core.calculators.modifiers.skill_ratio import SkillRatio
from core.calculators.modifiers.size_fix import SizeFix
from core.calculators.modifiers.attr_fix import AttrFix
from core.calculators.modifiers.defense_fix import DefenseFix
from core.calculators.modifiers.mastery_fix import MasteryFix
from core.calculators.modifiers.active_status_bonus import ActiveStatusBonus
from core.calculators.modifiers.final_rate_bonus import FinalRateBonus

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

        # Step 0 & 1 – input logging (always first) – explicit Weapon + Refine for GUI clarity
        result.add_step("Status BATK", status.batk,
                        note=f"STR={status.str} DEX={status.dex}")
        result.add_step("Weapon ATK", weapon.atk,
                        note="Raw weapon attack (from item data)",
                        formula="weapon.atk",
                        hercules_ref="battle.c: wd.damage = battle_calc_base_damage2(sstatus, &sstatus->rhw, sc, tstatus->size, sd, i);")
        refine_bonus = loader.get_refine_bonus(weapon.level, weapon.refine)
        result.add_step("Refine Bonus", refine_bonus,
                        note=f"+{weapon.refine} refine on Lv {weapon.level} weapon",
                        formula=f"get_refine_bonus({weapon.level}, {weapon.refine})",
                        hercules_ref="battle.c: ATK_ADD2(wd.damage, sstatus->rhw.atk2);\n" +
                                     "status.c: if (r) wa->atk2 = refine->get_bonus(wlv, r) / 100;")

        # Load skill data from JSON (used by skill_ratio and NK checks later)
        skill_data = loader.get_skill(skill.id)

        # === BASE DAMAGE ===
        BaseDamage.calculate(status, weapon, result)

        # === SKILL RATIO ===
        # Called immediately after Base Damage, exactly as in battle_calc_weapon_attack
        base_dmg = result.steps[-1].value   # Base Damage step (always present)
        SkillRatio.calculate(skill, base_dmg, build, result)

        # === SIZE FIX ===
        current_damage = result.steps[-1].value
        SizeFix.calculate(weapon, build, target, current_damage, skill, result)

        # === DEFENSE FIX ===
        current_damage = result.steps[-1].value
        DefenseFix.calculate(target, build, current_damage, self.config, result)

        # === MASTERY FIX ===
        current_damage = result.steps[-1].value
        MasteryFix.calculate(weapon, build, target, current_damage, result)

        # === ACTIVE STATUS BONUSES ===
        current_damage = result.steps[-1].value
        ActiveStatusBonus.calculate(weapon, build, skill, current_damage, result)

        # === ATTR FIX ===
        current_damage = result.steps[-1].value
        AttrFix.calculate(weapon, target, current_damage, result)

        # === FINAL RATE BONUS (Phase 2.10 – weapon/short/long rates) ===
        current_damage = result.steps[-1].value
        FinalRateBonus.calculate(build, current_damage, self.config, result)

        # Final values (min/max/avg identical until variance + crit in Phase 2.11)
        final_dmg = result.steps[-1].value

        result.add_step("Final Damage", final_dmg)

        result.min_damage = final_dmg
        result.max_damage = final_dmg
        result.avg_damage = final_dmg

        return result