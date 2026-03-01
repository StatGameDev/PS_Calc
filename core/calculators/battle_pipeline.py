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

        # === BASE DAMAGE (exact position in battle_calc_weapon_attack) ===
        BaseDamage.calculate(status, weapon, result)

        # === SKILL RATIO (Phase 2.5 – full registry from skills.json) ===
        # Called immediately after Base Damage, exactly as in battle_calc_weapon_attack
        base_dmg = result.steps[-1].value   # Base Damage step (always present)
        SkillRatio.calculate(skill, base_dmg, result)

        # Temporary final until size / mastery / defense modifiers (next phases)
        final_dmg = max(1, result.steps[-1].value)   # min-damage rule (Hercules behaviour)

        result.add_step("Final Damage (placeholder)", final_dmg)

        # Output values (variance/crit added later)
        result.min_damage = final_dmg
        result.max_damage = final_dmg
        result.avg_damage = final_dmg

        return result