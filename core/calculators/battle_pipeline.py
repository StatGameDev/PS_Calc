from core.build_manager import effective_is_ranged
from core.models.damage import DamageRange, DamageResult
from core.models.build import PlayerBuild
from core.models.status import StatusData
from core.models.weapon import Weapon
from core.models.skill import SkillInstance
from core.models.target import Target
from core.config import BattleConfig
from core.data_loader import loader
from core.calculators.modifiers.base_damage import BaseDamage
from core.calculators.modifiers.skill_ratio import SkillRatio
from core.calculators.modifiers.attr_fix import AttrFix
from core.calculators.modifiers.defense_fix import DefenseFix
from core.calculators.modifiers.mastery_fix import MasteryFix
from core.calculators.modifiers.active_status_bonus import ActiveStatusBonus
from core.calculators.modifiers.final_rate_bonus import FinalRateBonus


class BattlePipeline:
    """
    Orchestrator for the full pre-renewal BF_WEAPON damage calculation.
    Calls modifiers in the exact order of Hercules battle_calc_weapon_attack.
    Each modifier receives and returns a DamageRange(min, max, avg) so that
    weapon ATK variance and VIT DEF variance propagate correctly through every step.

    Correct step order (per battle_calc_weapon_attack source):
      BaseDamage    ← battle_calc_base_damage2 (SizeFix is INTERNAL to this, before batk)
      SkillRatio    ← battle_calc_skillratio
      DefenseFix    ← battle->calc_defense (~lines 5725-5738)
      ActiveStatusBonus  ← SC_AURABLADE etc., POST-defense (lines 5770-5795)
      MasteryFix    ← battle->calc_masteryfix (#ifndef RENEWAL, lines 5815-5818)
      AttrFix       ← calc_elefix (after mastery in pre-renewal)
      FinalRateBonus
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

        # Informational input steps — logged before the DamageRange is constructed.
        # min_value/max_value default to value (informational only, no range at this stage).
        result.add_step("Status BATK", status.batk,
                        note=f"STR={status.str} DEX={status.dex}")
        result.add_step("Weapon ATK", weapon.atk,
                        note="Raw weapon attack (from item data)",
                        formula="weapon.atk",
                        hercules_ref="battle.c: wd.damage = battle_calc_base_damage2(sstatus, &sstatus->rhw, sc, tstatus->size, sd, i);")
        refine_bonus = loader.get_refine_bonus(weapon.level, weapon.refine)
        result.add_step("Refine Bonus", refine_bonus,
                        note=f"+{weapon.refine} refine on Lv {weapon.level} weapon (deterministic)",
                        formula=f"get_refine_bonus({weapon.level}, {weapon.refine})",
                        hercules_ref="battle.c: ATK_ADD2(wd.damage, sstatus->rhw.atk2);\n"
                                     "status.c: if (r) wa->atk2 = refine->get_bonus(wlv, r) / 100;")

        if weapon.refineable:
            overrefine = loader.get_overrefine(weapon.level, weapon.refine)
        else:
            overrefine = 0
        if overrefine > 0:
            or_avg = (overrefine + 1) // 2
            result.add_step("Overrefine Bonus", or_avg,
                            min_value=1, max_value=overrefine,
                            note=f"Stochastic: rnd()%{overrefine}+1 → [1,{overrefine}]  avg≈{or_avg}",
                            formula=f"rnd()%{overrefine}+1",
                            hercules_ref="battle.c battle_calc_base_damage2:\n"
                                         "if (sd->right_weapon.overrefine)\n"
                                         "    damage += rnd()%sd->right_weapon.overrefine+1;\n"
                                         "status.c: wd->overrefine = refine->get_randombonus_max(wlv, r) / 100;")
        else:
            result.add_step("Overrefine Bonus", 0,
                            note="No overrefine (refine too low, weapon unrefined, or not refineable)",
                            formula="0",
                            hercules_ref="battle.c: overrefine block skipped (overrefine == 0)")

        # Load skill data (used by skill_ratio and NK checks)
        loader.get_skill(skill.id)

        # === BASE DAMAGE — mirrors battle_calc_base_damage2 exactly ===
        # SizeFix is applied inside this step before batk is added (A4 fix).
        # Two steps are logged: "Size Fix" then "Base Damage" (combined result).
        dmg: DamageRange = BaseDamage.calculate(status, weapon, build, target, skill, result)

        # === SKILL RATIO ===
        dmg = SkillRatio.calculate(skill, dmg, build, result)

        # === DEFENSE FIX ===
        dmg = DefenseFix.calculate(target, build, dmg, self.config, result)

        # === ACTIVE STATUS BONUSES — POST-defense (lines 5770-5795) ===
        dmg = ActiveStatusBonus.calculate(weapon, build, skill, dmg, result)

        # === MASTERY FIX — #ifndef RENEWAL, lines 5815-5818 ===
        dmg = MasteryFix.calculate(weapon, build, target, dmg, result)

        # === ATTR FIX ===
        dmg = AttrFix.calculate(weapon, target, dmg, result)

        # === FINAL RATE BONUS ===
        # is_ranged is pre-computed here so FinalRateBonus has no dependency on build or weapon.
        is_ranged = effective_is_ranged(build, weapon)
        dmg = FinalRateBonus.calculate(is_ranged, dmg, self.config, result)

        # Final summary step — carries the full range
        result.add_step("Final Damage",
                        value=dmg.avg,
                        min_value=dmg.min,
                        max_value=dmg.max)

        result.min_damage = dmg.min
        result.max_damage = dmg.max
        result.avg_damage = dmg.avg

        return result
