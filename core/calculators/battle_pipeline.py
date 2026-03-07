from core.build_manager import effective_is_ranged
from core.models.damage import DamageResult, BattleResult
from pmf.operations import _scale_floor, pmf_stats
from core.calculators.magic_pipeline import MagicPipeline
from core.models.build import PlayerBuild
from core.models.status import StatusData
from core.models.weapon import Weapon
from core.models.skill import SkillInstance
from core.models.target import Target
from core.config import BattleConfig
from core.data_loader import loader
from core.gear_bonus_aggregator import GearBonusAggregator
from core.calculators.status_calculator import StatusCalculator
from core.calculators.modifiers.base_damage import BaseDamage
from core.calculators.modifiers.skill_ratio import SkillRatio
from core.calculators.modifiers.attr_fix import AttrFix
from core.calculators.modifiers.card_fix import CardFix
from core.calculators.modifiers.defense_fix import DefenseFix
from core.calculators.modifiers.mastery_fix import MasteryFix
from core.calculators.modifiers.active_status_bonus import ActiveStatusBonus
from core.calculators.modifiers.refine_fix import RefineFix
from core.calculators.modifiers.final_rate_bonus import FinalRateBonus
from core.calculators.modifiers.crit_chance import calculate_crit_chance, CRIT_ELIGIBLE_SKILLS
from core.calculators.modifiers.crit_atk_rate import CritAtkRate
from core.calculators.modifiers.hit_chance import calculate_hit_chance


class BattlePipeline:
    """
    Orchestrator for the full pre-renewal BF_WEAPON damage calculation.
    Returns a BattleResult containing both normal and crit branches.

    Correct step order (per battle_calc_weapon_attack source, #ifndef RENEWAL):
      BaseDamage         ← battle_calc_base_damage2 (SizeFix INTERNAL, before batk)
      SkillRatio         ← battle_calc_skillratio
      [CritAtkRate]      ← ATK_ADDRATE(crit_atk_rate) — crit branch only, pre-defense (line 5333)
      DefenseFix         ← battle->calc_defense (~lines 5720-5738) — skipped on crit
      ActiveStatusBonus  ← SC_AURABLADE etc., POST-defense (lines 5770-5795)
      RefineFix          ← ATK_ADD2(sstatus->rhw.atk2, ...) lines 5803-5805 — BOTH branches
      MasteryFix         ← battle->calc_masteryfix (#ifndef RENEWAL, lines 5812-5818)
      AttrFix            ← calc_elefix (after mastery in pre-renewal)
      FinalRateBonus
    """

    def __init__(self, config: BattleConfig):
        self.config = config

    def calculate(self,
                  status: StatusData,
                  weapon: Weapon,
                  skill: SkillInstance,
                  target: Target,
                  build: PlayerBuild) -> BattleResult:
        """Run both normal and crit branches. Returns BattleResult.

        If the skill's attack_type is 'Magic' (from skills.json), routes to MagicPipeline.
        Magic result is stored in BattleResult.magic and also mirrored to .normal so
        the existing GUI StepsBar / summary display shows it without changes.
        """
        skill_data = loader.get_skill(skill.id)
        attack_type = skill_data.get("attack_type", "Weapon") if skill_data else "Weapon"

        if attack_type == "Magic":
            magic_result = MagicPipeline(self.config).calculate(status, skill, target, build)
            hit_chance, perfect_dodge = calculate_hit_chance(status, target, self.config)
            return BattleResult(
                normal=magic_result,   # mirrored so GUI shows steps without changes
                magic=magic_result,
                crit=None,
                crit_chance=0.0,
                hit_chance=hit_chance,
                perfect_dodge=perfect_dodge,
            )

        # Load skill data early (used by SkillRatio and NK checks)
        loader.get_skill(skill.id)

        # Crit eligibility and chance
        is_eligible, crit_chance = calculate_crit_chance(status, weapon, skill, target, self.config)

        hit_chance, perfect_dodge = calculate_hit_chance(status, target, self.config)

        normal = self._run_branch(status, weapon, skill, target, build, is_crit=False)
        crit = (self._run_branch(status, weapon, skill, target, build, is_crit=True)
                if is_eligible else None)

        return BattleResult(
            normal=normal,
            crit=crit,
            crit_chance=crit_chance,
            hit_chance=hit_chance,
            perfect_dodge=perfect_dodge,
        )

    def _run_branch(self,
                    status: StatusData,
                    weapon: Weapon,
                    skill: SkillInstance,
                    target: Target,
                    build: PlayerBuild,
                    is_crit: bool) -> DamageResult:
        """Run a single damage branch (normal or crit) through the full modifier chain."""
        result = DamageResult()
        gear_bonuses = GearBonusAggregator.compute(build.equipped, build.refine_levels)
        is_ranged = effective_is_ranged(build, weapon)

        # Informational input steps — show values entering the pipeline
        result.add_step(
            "Status BATK", status.batk,
            note=f"STR={status.str} DEX={status.dex}",
            formula="str + (str//10)^2 + dex//5 + luk//5",
            hercules_ref="status.c: status_calc_batk (pre-renewal)",
        )
        result.add_step(
            "Weapon ATK", weapon.atk,
            note=f"Raw weapon ATK from item_db (wa->atk); refine bonus applied post-defense as RefineFix",
            formula="weapon.atk",
            hercules_ref="battle.c: atkmax = wa->atk (inside battle_calc_base_damage2 for PC)",
        )
        if is_crit:
            result.add_step(
                "Branch", 0,
                note="CRIT BRANCH — damage=atkmax, DEF bypassed",
                formula="flag.cri=1",
                hercules_ref="battle.c:4988-4989 (#ifndef RENEWAL): flag.idef=flag.idef2=flag.hit=1",
            )

        # === BASE DAMAGE — mirrors battle_calc_base_damage2 exactly ===
        # SizeFix is applied inside this step before batk (A4 fix).
        # Crit branch: damage = atkmax (no roll). Overrefine still randomizes.
        pmf: dict = BaseDamage.calculate(status, weapon, build, target, skill, result,
                                         is_crit=is_crit)

        # === bAtkRate — #ifndef RENEWAL, battle.c:5330 (pre-skill-ratio) ===
        # ATK_ADDRATE(sd->bonus.atk_rate) applied before SkillRatio in the default case.
        if gear_bonuses.atk_rate:
            pmf = _scale_floor(pmf, 100 + gear_bonuses.atk_rate, 100)
            mn, mx, av = pmf_stats(pmf)
            result.add_step(
                "bAtkRate",
                value=av,
                min_value=mn,
                max_value=mx,
                multiplier=(100 + gear_bonuses.atk_rate) / 100,
                note=f"bAtkRate +{gear_bonuses.atk_rate}% (from gear — applied before Skill Ratio)",
                formula=f"dmg * (100 + {gear_bonuses.atk_rate}) // 100",
                hercules_ref="battle.c:5330 #ifndef RENEWAL: ATK_ADDRATE(sd->bonus.atk_rate)",
            )

        # === SKILL RATIO ===
        pmf = SkillRatio.calculate(skill, pmf, build, result)

        # === CRIT ATK RATE — pre-defense, crit branch only (battle.c:5333) ===
        if is_crit:
            pmf = CritAtkRate.calculate(build, pmf, result)

        # === DEFENSE FIX — skipped entirely on crit (flag.idef=flag.idef2=1) ===
        pmf = DefenseFix.calculate(target, build, gear_bonuses, pmf, self.config, result, is_crit=is_crit)

        # === ACTIVE STATUS BONUSES — POST-defense (lines 5770-5795) ===
        pmf = ActiveStatusBonus.calculate(weapon, build, skill, pmf, result)

        # === REFINE BONUS (atk2) — POST-defense, PRE-mastery (lines 5803-5805) ===
        # A6 fix: moved out of BaseDamage to its correct Hercules position.
        # Applies to BOTH branches.
        pmf = RefineFix.calculate(weapon, skill, pmf, result)

        # === MASTERY FIX — #ifndef RENEWAL, lines 5812-5818 ===
        pmf = MasteryFix.calculate(weapon, build, target, pmf, result)

        # === ATTR FIX ===
        pmf = AttrFix.calculate(weapon, target, pmf, result)

        # === CARD FIX — race/ele/size/long_atk bonuses; target resist (PvP) ===
        pmf = CardFix.calculate(build, gear_bonuses, weapon, target, is_ranged, pmf, result)

        # === FINAL RATE BONUS ===
        pmf = FinalRateBonus.calculate(is_ranged, pmf, self.config, result)

        # Final summary step
        mn, mx, av = pmf_stats(pmf)
        result.add_step(
            "Final Damage",
            value=av,
            min_value=mn,
            max_value=mx,
            note=("CRIT branch" if is_crit else "Normal branch"),
            formula="",
            hercules_ref="",
        )

        result.min_damage = mn
        result.max_damage = mx
        result.avg_damage = av
        result.pmf = pmf

        return result
