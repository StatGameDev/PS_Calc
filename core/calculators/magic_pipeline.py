from core.models.damage import DamageRange, DamageResult, BattleResult
from core.models.build import PlayerBuild
from core.models.status import StatusData
from core.models.skill import SkillInstance
from core.models.target import Target
from core.config import BattleConfig
from core.data_loader import loader
from core.gear_bonus_aggregator import GearBonusAggregator
from core.calculators.modifiers.skill_ratio import SkillRatio
from core.calculators.modifiers.defense_fix import DefenseFix
from core.calculators.modifiers.attr_fix import AttrFix
from core.calculators.modifiers.card_fix import CardFix
from core.calculators.modifiers.final_rate_bonus import FinalRateBonus


class MagicPipeline:
    """
    Orchestrator for pre-renewal BF_MAGIC outgoing damage (player → any target).

    Step order (battle_calc_magic_attack, #else not RENEWAL):
      MATK roll       — random in [matk_min, matk_max]; matk_max on SC_MAXIMIZEPOWER
      SkillRatio      — battle_calc_skillratio BF_MAGIC (per-hit ratio)
      DefenseFix      — damage*(100-mdef)/100 - mdef2  (magic_defense_type=0, per-hit)
      AttrFix         — skill element vs target element (attr_fix table, per-hit)
      Hit count ×N    — ad.div_ multiplication after defense+attr_fix
      CardFix(magic)  — target-side only if is_pc (sub_ele/sub_race/magic_def_rate)
      FinalRateBonus  — weapon_damage_rate

    Note: matk_percent and skillatk_bonus steps are stubs (gear fields not yet wired).
    Source: battle.c:3828 battle_calc_magic_attack (#else not RENEWAL).
    """

    def __init__(self, config: BattleConfig):
        self.config = config

    def calculate(self,
                  status: StatusData,
                  skill: SkillInstance,
                  target: Target,
                  build: PlayerBuild) -> DamageResult:
        result = DamageResult()
        gear_bonuses = GearBonusAggregator.compute(build.equipped)
        active = getattr(build, 'active_status_levels', {})

        # --- MATK base roll ---
        # status.c:3783/3790 #else not RENEWAL (already computed in StatusData)
        maximize = "SC_MAXIMIZEPOWER" in active
        if maximize:
            matk = status.matk_max
            matk_note = f"MATK {matk} (SC_MAXIMIZEPOWER: use max)"
        else:
            matk = (status.matk_min + status.matk_max) // 2  # avg for display
            matk_note = f"MATK roll [{status.matk_min}–{status.matk_max}]"

        dmg = DamageRange(
            status.matk_min if not maximize else status.matk_max,
            status.matk_max,
            matk,
        )

        result.add_step(
            name="MATK Base",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            note=matk_note,
            formula="int_ + (int_//7)^2 to int_ + (int_//5)^2",
            hercules_ref="status.c:3783-3792 status_base_matk_min/max (#else not RENEWAL)\n"
                         "battle_calc_magic_attack: MATK_ADD(status->get_matk(src, 2))",
        )

        # --- Skill Ratio (BF_MAGIC): ratio only (per-hit). hit_count returned separately. ---
        # battle_calc_magic_attack: MATK_RATE(skillratio) on per-hit ad.damage,
        # then calc_defense and attr_fix on per-hit, THEN × ad.div_ at damage dealing.
        dmg, hit_count = SkillRatio.calculate_magic(skill, dmg, build, target, result)

        # --- Defense Fix (BF_MAGIC) — per-hit ---
        # damage = damage * (100 - mdef) / 100 - mdef2   (magic_defense_type=0)
        dmg = DefenseFix.calculate_magic(target, gear_bonuses, dmg, result)

        # --- Attr Fix (magic element from skills.json) — per-hit ---
        skill_data = loader.get_skill(skill.id)
        skill_ele_raw = None
        if skill_data:
            ele_list = skill_data.get("element")
            if ele_list and skill.level <= len(ele_list):
                skill_ele_raw = ele_list[skill.level - 1]   # e.g. "Ele_Fire"

        # Map "Ele_Fire" → "Fire" for attr_fix table lookup
        if skill_ele_raw and skill_ele_raw.startswith("Ele_"):
            magic_ele_name = skill_ele_raw[4:]   # strip "Ele_"
        else:
            magic_ele_name = "Neutral"

        defending = loader.get_element_name(target.element)
        multiplier = loader.get_attr_fix_multiplier(magic_ele_name, defending, target.element_level or 1)
        if multiplier != 100:
            dmg = dmg.scale(multiplier, 100)
        result.add_step(
            name="Attr Fix (Magic)",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=multiplier / 100.0,
            note=f"{magic_ele_name} vs {defending} Lv{target.element_level or 1} ({multiplier}%)",
            formula=f"dmg * {multiplier} // 100",
            hercules_ref="battle_calc_magic_attack: battle->attr_fix(src,target,ad.damage,s_ele,...)",
        )

        # --- Hit count — applied after defense+attr_fix, per source order ---
        # damage_div_fix(dmg, div): positive div > 1 → dmg *= div (actual multi-hit)
        #                            negative div    → div = abs(div), dmg unchanged (cosmetic)
        # Source: battle.c:3823 #define damage_div_fix
        if hit_count > 1:
            dmg = dmg.scale(hit_count, 1)
            result.add_step(
                name=f"Hit Count ×{hit_count}",
                value=dmg.avg,
                min_value=dmg.min,
                max_value=dmg.max,
                multiplier=float(hit_count),
                note=f"{hit_count} actual hits × per-hit damage",
                formula=f"per_hit_dmg × {hit_count}",
                hercules_ref="battle.c:3823: damage_div_fix: div>1 → dmg*=div",
            )
        elif hit_count < 0:
            # Cosmetic multi-hit: animation only, damage is per single hit (not multiplied)
            result.add_step(
                name=f"Hit Count ×{abs(hit_count)} (cosmetic)",
                value=dmg.avg,
                min_value=dmg.min,
                max_value=dmg.max,
                multiplier=1.0,
                note=f"{abs(hit_count)} cosmetic hits — damage not multiplied",
                formula="no change (cosmetic multi-hit)",
                hercules_ref="battle.c:3823: damage_div_fix: div<0 → div=abs(div), dmg unchanged",
            )

        # --- Card Fix (magic, target-side only) ---
        dmg = CardFix.calculate_magic(target, "Ele_" + magic_ele_name, dmg, result)

        # --- Final Rate Bonus ---
        # weapon_damage_rate also applies to magic in the source (same final multiplier)
        dmg = FinalRateBonus.calculate(is_ranged=False, dmg=dmg, config=self.config, result=result)

        result.add_step(
            "Final Magic Damage",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            note="BF_MAGIC branch",
            formula="",
            hercules_ref="",
        )

        result.min_damage = dmg.min
        result.max_damage = dmg.max
        result.avg_damage = dmg.avg

        return result
