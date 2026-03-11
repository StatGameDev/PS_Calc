from core.build_manager import BuildManager, effective_is_ranged

# G52: Jobs that can dual-wield (Assassin, Assassin Cross).
# Source: battle.c:4855-4859 — skills always use RH only; dual-wield is normal attack only.
_DUAL_WIELD_JOBS: frozenset = frozenset({12, 4013})
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
from core.calculators.modifiers.forge_bonus import ForgeBonus
from core.calculators.modifiers.card_fix import CardFix
from core.calculators.modifiers.defense_fix import DefenseFix
from core.calculators.modifiers.mastery_fix import MasteryFix
from core.calculators.modifiers.active_status_bonus import ActiveStatusBonus
from core.calculators.modifiers.refine_fix import RefineFix
from core.calculators.modifiers.final_rate_bonus import FinalRateBonus
from core.calculators.modifiers.crit_chance import calculate_crit_chance, CRIT_ELIGIBLE_SKILLS
from core.calculators.modifiers.crit_atk_rate import CritAtkRate
from core.calculators.modifiers.hit_chance import calculate_hit_chance
from core.models.attack_definition import AttackDefinition
from core.calculators.dps_calculator import calculate_dps, FormulaSelectionStrategy
from core.calculators.skill_timing import calculate_skill_timing
from core.calculators.modifiers.skill_ratio import IMPLEMENTED_BF_WEAPON_SKILLS, IMPLEMENTED_BF_MAGIC_SKILLS


def _resolve_is_ranged(build: PlayerBuild, weapon: Weapon, skill: SkillInstance) -> bool:
    """Determine BF_SHORT (False) vs BF_LONG (True) for a skill attack.

    Skills with an explicit non-negative range in skill_db override the weapon-derived flag.
    Negative range values mean 'use weapon range' and fall back to effective_is_ranged.
    Source: battle.c:3789-3792 battle_range_type:
        skill_get_range2 < 5 → BF_SHORT; else BF_LONG
    """
    if skill.id != 0:
        skill_data = loader.get_skill(skill.id)
        if skill_data:
            range_list = skill_data.get("range", [])
            if range_list:
                idx = min(skill.level - 1, len(range_list) - 1)
                r = range_list[idx]
                if r >= 0:
                    return r >= 5   # BF_LONG threshold from battle_range_type
    return effective_is_ranged(build, weapon)


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
        skill_name: str = skill_data.get("name", "") if skill_data else ""

        # amotion = 2000 - aspd*10  (status.c:2112; status.c:2134: adelay = 2 × amotion)
        # Floored at 100 to match cap_value(i, pc_max_aspd(sd), 2000) in Hercules.
        amotion: int = max(100, int(2000 - status.aspd * 10))

        if attack_type == "Magic":
            magic_result = MagicPipeline(self.config).calculate(status, skill, target, build)
            hit_chance, perfect_dodge = calculate_hit_chance(status, target, self.config)
            # Monsters do not have perfect dodge vs player attacks; only player characters do.
            if build.target_mob_id is not None:
                perfect_dodge = 0.0
            # G56: compute period and DPS for magic skills.
            # dps_valid=True only for skills with a confirmed ratio in IMPLEMENTED_BF_MAGIC_SKILLS.
            if skill_data:
                gb = GearBonusAggregator.compute(build.equipped, build.refine_levels)
                GearBonusAggregator.apply_passive_bonuses(gb, build.mastery_levels)
                cast_ms, delay_ms = calculate_skill_timing(
                    skill_name, skill.level, skill_data, status, gb, build.support_buffs,
                )
                magic_period = max(cast_ms + delay_ms, amotion)
            else:
                magic_period = amotion
            magic_dps = (magic_result.avg_damage / magic_period * 1000
                         if magic_period > 0 else 0.0)
            return BattleResult(
                normal=magic_result,   # mirrored so GUI shows steps without changes
                magic=magic_result,
                crit=None,
                crit_chance=0.0,
                hit_chance=hit_chance,
                perfect_dodge=perfect_dodge,
                dps=magic_dps,
                period_ms=float(magic_period),
                dps_valid=skill_name in IMPLEMENTED_BF_MAGIC_SKILLS,
            )

        # skill_data above is used for attack_type / skill_name / skill timing.
        # _run_branch loads it again independently for ForgeBonus div.

        # Crit eligibility and chance
        is_eligible, crit_chance = calculate_crit_chance(status, weapon, skill, target, self.config)

        hit_chance, perfect_dodge = calculate_hit_chance(status, target, self.config)
        # Monsters do not have perfect dodge vs player attacks; only player characters do.
        if build.target_mob_id is not None:
            perfect_dodge = 0.0

        normal = self._run_branch(status, weapon, skill, target, build, is_crit=False)
        crit = (self._run_branch(status, weapon, skill, target, build, is_crit=True)
                if is_eligible else None)

        # G16: Katar second hit — normal attacks only (skill_id == 0).
        # Source: battle.c:5941-5952 (#ifndef RENEWAL):
        #   temp = pc->checkskill(sd, TF_DOUBLE)
        #   wd.damage2 = wd.damage * (1 + (temp * 2)) / 100
        #   if (wd.damage && !wd.damage2) wd.damage2 = 1;   // pre-renewal minimum
        # Applied AFTER full pipeline (post-CardFix wd.damage); CardFix does NOT run on damage2
        # because flag.lh is set after the CardFix block.
        katar_second = None
        katar_second_crit = None
        if weapon.weapon_type == "Katar" and skill.id == 0:
            tf_level = build.mastery_levels.get("TF_DOUBLE", 0)
            katar_second = self._katar_second_hit(normal, tf_level)
            if crit is not None:
                katar_second_crit = self._katar_second_hit(crit, tf_level)

        # G54: TF_DOUBLE (Knife) / GS_CHAINACTION (Revolver) double-hit proc branches.
        # Only eligible on normal auto-attacks (skill.id == 0).
        # Crit and proc are mutually exclusive (battle.c:4926).
        # proc_chance = 5 * skill_level  (percent).
        # Source: pc.c pc_checkskill; battle.c:4926 proc vs crit mutex.
        proc_chance = 0.0
        double_hit = None
        double_hit_crit = None
        if skill.id == 0:
            tf_level = build.mastery_levels.get("TF_DOUBLE", 0)
            gs_level = build.mastery_levels.get("GS_CHAINACTION", 0)
            if weapon.weapon_type == "Knife" and tf_level > 0:
                proc_chance = 5.0 * tf_level
            elif weapon.weapon_type == "Revolver" and gs_level > 0:
                proc_chance = 5.0 * gs_level
            if proc_chance > 0:
                double_hit = self._run_branch(
                    status, weapon, skill, target, build, is_crit=False, proc_hit_count=2)
                if is_eligible:
                    double_hit_crit = self._run_branch(
                        status, weapon, skill, target, build, is_crit=True, proc_hit_count=2)

        # G52: Dual-wield branch — normal attack only, Assassin / Assassin Cross.
        # ATK_RATER: RH damage *= (50 + AS_RIGHT_lv*10) / 100  (battle.c:5923-5926)
        # ATK_RATEL: LH damage *= (30 + AS_LEFT_lv*10) / 100   (battle.c:5929-5932)
        # Both have pre-renewal floor of 1 (battle.c:5937-5938, #else branch).
        # LH active when lhw.atk != 0 (battle.c:4861) → Unarmed fallback means atk=0 → skip.
        lh_normal = None
        lh_crit   = None
        if build.job_id in _DUAL_WIELD_JOBS and skill.id == 0:
            as_right_lv = build.mastery_levels.get("AS_RIGHT", 0)
            as_left_lv  = build.mastery_levels.get("AS_LEFT", 0)
            lh_weapon = BuildManager.resolve_weapon(
                build.equipped.get("left_hand"),
                build.refine_levels.get("left_hand", 0),
                element_override=None,
                is_forged=build.lh_is_forged,
                forge_sc_count=build.lh_forge_sc_count,
                forge_ranked=build.lh_forge_ranked,
                forge_element=build.lh_forge_element,
            )
            if lh_weapon.weapon_type != "Unarmed":
                # Apply RH penalty rate to existing normal/crit results.
                rh_rate = 50 + as_right_lv * 10
                normal = self._apply_dualwield_rate(normal, rh_rate, "RH", as_right_lv)
                if crit is not None:
                    crit = self._apply_dualwield_rate(crit, rh_rate, "RH", as_right_lv)
                # Compute LH branches and apply LH penalty rate.
                lh_rate = 30 + as_left_lv * 10
                lh_normal_raw = self._run_branch(status, lh_weapon, skill, target, build, is_crit=False)
                lh_normal = self._apply_dualwield_rate(lh_normal_raw, lh_rate, "LH", as_left_lv)
                if is_eligible:
                    lh_crit_raw = self._run_branch(status, lh_weapon, skill, target, build, is_crit=True)
                    lh_crit = self._apply_dualwield_rate(lh_crit_raw, lh_rate, "LH", as_left_lv)
                # Proc branches also need ATK_RATER: damage_div_fix only scales wd.damage (RH),
                # then ATK_RATER/ATK_RATEL are applied on top (battle.c:5567 → 5923-5932).
                # LH is NOT doubled by the proc — it contributes its normal value to the proc swing.
                if double_hit is not None:
                    double_hit = self._apply_dualwield_rate(double_hit, rh_rate, "RH", as_right_lv)
                if double_hit_crit is not None:
                    double_hit_crit = self._apply_dualwield_rate(double_hit_crit, rh_rate, "RH", as_right_lv)

        # DPS calculation.
        # adelay = 2 × amotion (floored at 200ms = 2×100ms min amotion).
        # TF_DOUBLE / GS_CHAINACTION proc fires within the same swing, same period.
        adelay = float(2 * amotion)  # = max(200, (2000 - aspd*10)*2)

        # G56: skill period — auto-attack uses adelay; skills use max(cast+delay, amotion).
        if skill.id == 0:
            period = adelay
            dps_valid = True
        else:
            gb_timing = GearBonusAggregator.compute(build.equipped, build.refine_levels)
            GearBonusAggregator.apply_passive_bonuses(gb_timing, build.mastery_levels)
            cast_ms, delay_ms = calculate_skill_timing(
                skill_name, skill.level, skill_data, status, gb_timing, build.support_buffs,
            ) if skill_data else (0, 0)
            period = float(max(cast_ms + delay_ms, amotion))
            dps_valid = skill_name in IMPLEMENTED_BF_WEAPON_SKILLS

        p        = proc_chance / 100.0
        eff_crit = crit_chance / 100.0 * (1.0 - p)  # crit and proc mutually exclusive
        h        = hit_chance / 100.0

        # Katar: both hits land in the same action — sum for DPS.
        # Dual-wield: both hands land in the same swing — sum RH + LH.
        normal_avg = (float(normal.avg_damage) + (float(katar_second.avg_damage) if katar_second else 0.0)
                      + (float(lh_normal.avg_damage) if lh_normal else 0.0))
        crit_avg   = ((float(crit.avg_damage) + (float(katar_second_crit.avg_damage) if katar_second_crit else 0.0)
                       + (float(lh_crit.avg_damage) if lh_crit else float(lh_normal.avg_damage) if lh_normal else 0.0))
                      if crit else normal_avg)
        # Proc swing: RH is doubled, LH contributes its normal value (proc does not double LH).
        double_avg = (float(double_hit.avg_damage) + (float(lh_normal.avg_damage) if lh_normal else 0.0)) if double_hit else 0.0

        # Probability tree — sums to 1.0:
        #   crits auto-hit (bypass FLEE), so weight = eff_crit, NOT eff_crit * h.
        #   proc can miss — proc-miss is zero damage but still consumes the full period.
        # Future sessions: append AttackDefinition entries here; do not add named fields.
        attacks = [
            AttackDefinition(normal_avg, 0.0, period, (1.0 - p - eff_crit) * h),        # normal hit
            AttackDefinition(0.0,        0.0, period, (1.0 - p - eff_crit) * (1.0 - h)), # normal miss
            AttackDefinition(crit_avg,   0.0, period, eff_crit),                          # crit (auto-hit)
            AttackDefinition(double_avg, 0.0, period, p * h),                             # proc hit
            AttackDefinition(0.0,        0.0, period, p * (1.0 - h)),                     # proc miss
        ]
        dps = calculate_dps(attacks, FormulaSelectionStrategy())

        return BattleResult(
            normal=normal,
            crit=crit,
            crit_chance=crit_chance,
            hit_chance=hit_chance,
            perfect_dodge=perfect_dodge,
            katar_second=katar_second,
            katar_second_crit=katar_second_crit,
            proc_chance=proc_chance,
            double_hit=double_hit,
            double_hit_crit=double_hit_crit,
            lh_normal=lh_normal,
            lh_crit=lh_crit,
            dps=dps,
            attacks=attacks,
            period_ms=period,
            dps_valid=dps_valid,
        )

    @staticmethod
    def _katar_second_hit(first: DamageResult, tf_level: int) -> DamageResult:
        """Compute katar second-hit DamageResult from the first hit's final PMF.

        Formula: damage2 = max(1, damage1 * (1 + TF_DOUBLE_level * 2) // 100)
        Source: battle.c:5941-5952 (#ifndef RENEWAL)
        """
        factor = 1 + tf_level * 2
        out_pmf: dict = {}
        for dmg, prob in first.pmf.items():
            d2 = max(1, dmg * factor // 100)
            out_pmf[d2] = out_pmf.get(d2, 0.0) + prob
        mn, mx, av = pmf_stats(out_pmf)
        dr = DamageResult()
        dr.pmf = out_pmf
        dr.min_damage = mn
        dr.max_damage = mx
        dr.avg_damage = av
        dr.add_step(
            "Katar 2nd Hit",
            value=av, min_value=mn, max_value=mx,
            note=f"TF_DOUBLE lv{tf_level}: damage × (1+{tf_level}×2)÷100, min 1",
            formula=f"max(1, damage * {factor} // 100)",
            hercules_ref="battle.c:5941-5952 (#ifndef RENEWAL): wd.damage2 = wd.damage*(1+(TF_DOUBLE*2))/100",
        )
        return dr

    @staticmethod
    def _apply_dualwield_rate(source: DamageResult, numerator: int, hand: str, skill_lv: int) -> DamageResult:
        """Scale a branch's PMF by the dual-wield hand rate, floor each output to min 1.

        Formula: damage = damage * numerator / 100  (integer division), then max(1, result).
        RH: numerator = 50 + AS_RIGHT_lv*10 (ATK_RATER macro, battle.c:5923-5926)
        LH: numerator = 30 + AS_LEFT_lv*10  (ATK_RATEL macro, battle.c:5929-5932)
        Pre-renewal floor of 1: battle.c:5937-5938 (#else branch, not RENEWAL).
        """
        out_pmf: dict = {}
        for dmg, prob in source.pmf.items():
            scaled = max(1, dmg * numerator // 100)
            out_pmf[scaled] = out_pmf.get(scaled, 0.0) + prob
        mn, mx, av = pmf_stats(out_pmf)
        dr = DamageResult()
        dr.pmf = out_pmf
        dr.min_damage = mn
        dr.max_damage = mx
        dr.avg_damage = av
        # Copy existing steps so the StepsBar shows the full chain.
        dr.steps = list(source.steps)
        skill_key = "AS_RIGHT" if hand == "RH" else "AS_LEFT"
        dr.add_step(
            f"Dual-Wield {hand} Rate",
            value=av, min_value=mn, max_value=mx,
            multiplier=numerator / 100,
            note=f"{skill_key} lv{skill_lv}: damage × {numerator} ÷ 100, floor 1",
            formula=f"max(1, damage * {numerator} // 100)",
            hercules_ref=(
                "battle.c:5923-5926 ATK_RATER: wd.damage * (50+AS_RIGHT*10)/100"
                if hand == "RH" else
                "battle.c:5929-5932 ATK_RATEL: wd.damage2 * (30+AS_LEFT*10)/100"
            ),
        )
        return dr

    def _run_branch(self,
                    status: StatusData,
                    weapon: Weapon,
                    skill: SkillInstance,
                    target: Target,
                    build: PlayerBuild,
                    is_crit: bool,
                    proc_hit_count: int = 1) -> DamageResult:
        """Run a single damage branch (normal or crit) through the full modifier chain."""
        result = DamageResult()
        gear_bonuses = GearBonusAggregator.compute(build.equipped, build.refine_levels)
        GearBonusAggregator.apply_passive_bonuses(gear_bonuses, build.mastery_levels)
        is_ranged = _resolve_is_ranged(build, weapon, skill)

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
        pmf = SkillRatio.calculate(skill, pmf, build, result, target)

        # === PROC HIT COUNT — mirrors damage_div_fix at battle.c:5567 (#ifndef RENEWAL) ===
        # For TF_DOUBLE / GS_CHAINACTION proc branches: proc_hit_count=2 doubles the total.
        # Normal auto-attacks and skill branches keep the default proc_hit_count=1 (no-op).
        if proc_hit_count > 1:
            pmf = _scale_floor(pmf, proc_hit_count, 1)
            mn, mx, av = pmf_stats(pmf)
            result.add_step(
                "Proc ×2",
                value=av, min_value=mn, max_value=mx,
                multiplier=float(proc_hit_count),
                note=f"Double-hit proc: ×{proc_hit_count} hits",
                formula=f"dmg * {proc_hit_count}",
                hercules_ref="battle.c:5567 (#ifndef RENEWAL): damage_div_fix",
            )

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
        pmf = AttrFix.calculate(weapon, target, pmf, result, build)

        # === FORGE BONUS — flat star ATK × div, after AttrFix, before CardFix ===
        # Source: battle.c:5864 (#ifndef RENEWAL): ATK_ADD2(wd.div_*right_weapon.star, ...)
        skill_data = loader.get_skill(skill.id)
        div = skill_data.get("hit", 1) if skill_data else 1
        pmf = ForgeBonus.calculate(weapon, div, pmf, result)

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
