from typing import Optional

from core.models.damage import DamageRange, DamageResult
from core.models.target import Target
from core.models.build import PlayerBuild
from core.models.gear_bonuses import GearBonuses
from core.models.skill import SkillInstance
from core.config import BattleConfig
from core.data_loader import loader
from core.calculators.modifiers.skill_ratio import SkillRatio
from core.calculators.modifiers.defense_fix import DefenseFix
from core.calculators.modifiers.card_fix import CardFix


class IncomingMagicPipeline:
    """
    Pre-renewal incoming magic damage pipeline (mob → player).

    Step order (battle.c:3828 battle_calc_magic_attack #else not RENEWAL):
      MobMATKRoll    — [matk_min, matk_max] from mob int_; mob_matk_bonus_rate for buffs/debuffs
      SkillRatio     — if a named skill is used (BF_MAGIC ratio, per-hit)
      AttrFix        — skill/mob element vs player armor element
      DefenseFix     — player MDEF: damage*(100-mdef)/100 - mdef2
      CardFix        — target-side only (player magic resist cards; mob has no gear)

    mob_matk_bonus_rate mirrors SC effects that change mob MATK post-spawn (e.g. buffs
    from SC_BLESSING, SC_INC_AGI-type effects on mob INT). Default 0 = unmodified.

    Source: status.c:3783-3792 status_base_matk_min/max (#else not RENEWAL);
            battle.c:3828 battle_calc_magic_attack.
    """

    def __init__(self, config: BattleConfig):
        self.config = config

    def calculate(
        self,
        mob_id: int,
        player_target: Target,
        gear_bonuses: GearBonuses,
        build: PlayerBuild,
        skill: Optional[SkillInstance] = None,
        mob_matk_bonus_rate: int = 0,   # % modifier to mob MATK (buffs/debuffs)
    ) -> DamageResult:
        result = DamageResult()

        mob_data = loader.get_monster_data(mob_id)
        if mob_data is None:
            return result

        mob_name    = mob_data.get("name", f"Mob {mob_id}")
        mob_element = mob_data.get("element", 0)
        mob_race    = mob_data.get("race", "Formless")
        mob_int_    = mob_data.get("stats", {}).get("int", 0)

        # --- Mob MATK Roll ---
        # Pre-renewal formula (status.c:3783-3792 #else not RENEWAL):
        #   matk_min = int_ + (int_//7)^2
        #   matk_max = int_ + (int_//5)^2
        # mob_matk_bonus_rate applies uniformly to both bounds (mirrors SC buff effects).
        base_matk_min = mob_int_ + (mob_int_ // 7) ** 2
        base_matk_max = mob_int_ + (mob_int_ // 5) ** 2

        if mob_matk_bonus_rate:
            matk_min = base_matk_min * (100 + mob_matk_bonus_rate) // 100
            matk_max = base_matk_max * (100 + mob_matk_bonus_rate) // 100
        else:
            matk_min = base_matk_min
            matk_max = base_matk_max

        matk_max = max(matk_min, matk_max)
        matk_avg = (matk_min + matk_max) // 2

        modifier_note = f" ×{100 + mob_matk_bonus_rate}%" if mob_matk_bonus_rate else ""
        dmg = DamageRange(matk_min, matk_max, matk_avg)

        result.add_step(
            name="Mob MATK Roll",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            note=(f"{mob_name}: int_ {mob_int_}{modifier_note}"
                  f" → MATK [{matk_min}, {matk_max}]"),
            formula="int_ + (int_//7)^2  to  int_ + (int_//5)^2",
            hercules_ref="status.c:3783-3792 status_base_matk_min/max (#else not RENEWAL)",
        )

        # --- Skill Ratio (BF_MAGIC) — optional ---
        # SkillRatio.calculate_magic returns (dmg, hit_count); build=None is safe (unused).
        hit_count = 1
        if skill is not None and skill.id != 0:
            dmg, hit_count = SkillRatio.calculate_magic(skill, dmg, None, player_target, result)

        # --- Attr Fix: mob/skill element vs player armor element ---
        # Resolve element: skill element takes priority over mob natural element.
        magic_ele_name = "Neutral"
        if skill is not None and skill.id != 0:
            skill_data = loader.get_skill(skill.id)
            if skill_data:
                ele_list = skill_data.get("element")
                if ele_list and skill.level <= len(ele_list):
                    raw = ele_list[skill.level - 1]   # e.g. "Ele_Fire"
                    if raw and raw.startswith("Ele_"):
                        magic_ele_name = raw[4:]       # strip "Ele_" → "Fire"
        if magic_ele_name == "Neutral":
            # Fall back to mob's natural element
            magic_ele_name = loader.get_element_name(mob_element)

        player_ele_name = loader.get_element_name(player_target.armor_element)
        multiplier = loader.get_attr_fix_multiplier(
            magic_ele_name, player_ele_name, player_target.element_level or 1
        )
        if multiplier != 100:
            dmg = dmg.scale(multiplier, 100)
        result.add_step(
            name="Attr Fix (Magic)",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=multiplier / 100.0,
            note=f"{magic_ele_name} vs {player_ele_name} Lv{player_target.element_level or 1} ({multiplier}%)",
            formula=f"dmg * {multiplier} // 100",
            hercules_ref="battle_calc_magic_attack: battle->attr_fix(src,target,ad.damage,s_ele,...)",
        )

        # --- Hit count — applied after defense+attr_fix (per source order) ---
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

        # --- Defense Fix (magic): player MDEF ---
        # Mob has no ignore_mdef gear → empty GearBonuses (ignore_mdef_rate all zero).
        dmg = DefenseFix.calculate_magic(player_target, GearBonuses(), dmg, result)

        # --- Card Fix (magic, target-side): player's magic resist cards vs mob attacker ---
        magic_ele_key = f"Ele_{magic_ele_name}"
        dmg = CardFix.calculate_incoming_magic(
            mob_race=mob_race,
            magic_ele_name=magic_ele_key,
            player_target=player_target,
            dmg=dmg,
            result=result,
        )

        result.add_step(
            "Final Incoming Magic Damage",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            note="mob → player, pre-renewal BF_MAGIC",
            formula="",
            hercules_ref="",
        )

        result.min_damage = dmg.min
        result.max_damage = dmg.max
        result.avg_damage = dmg.avg

        return result
