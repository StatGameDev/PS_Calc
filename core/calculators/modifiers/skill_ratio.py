from core.models.skill import SkillInstance
from core.models.damage import DamageRange, DamageResult
from core.models.build import PlayerBuild
from core.data_loader import loader

# Pre-renewal magic skill ratios from battle_calc_skillratio BF_MAGIC switch.
# Source: battle.c:1631-1785 #else not RENEWAL.
# All unlisted skills use default ratio = 100.
# ELE_UNDEAD = 9 (map.h). Default undead_detect_type=0 → element check only.
_BF_MAGIC_RATIOS = {
    "MG_NAPALMBEAT":   lambda lv, tgt: 70 + 10 * lv,
    "MG_FIREBALL":     lambda lv, tgt: 70 + 10 * lv,   # pre-re: same formula as napalmbeat
    "MG_SOULSTRIKE":   lambda lv, tgt: 100 + (5 * lv if (tgt and tgt.element == 9) else 0),
    "MG_FIREWALL":     lambda lv, tgt: 50,
    "MG_THUNDERSTORM": lambda lv, tgt: 80,              # pre-re: skillratio -= 20
    "MG_FROSTDIVER":   lambda lv, tgt: 100 + 10 * lv,
    "AL_HOLYLIGHT":    lambda lv, tgt: 125,
    "AL_RUWACH":       lambda lv, tgt: 145,
    "WZ_FROSTNOVA":    lambda lv, tgt: (100 + 10 * lv) * 2 // 3,
    "WZ_FIREPILLAR":   lambda lv, tgt: 40 + 20 * lv,   # lv <= 10; lv > 10 not in pre-re
    "WZ_SIGHTRASHER":  lambda lv, tgt: 100 + 20 * lv,
    "WZ_WATERBALL":    lambda lv, tgt: 100 + 30 * lv,
    "WZ_STORMGUST":    lambda lv, tgt: 100 + 40 * lv,
    "HW_NAPALMVULCAN": lambda lv, tgt: 70 + 10 * lv,
    "WZ_VERMILION":    lambda lv, tgt: 80 + 20 * lv,   # pre-re: #else RENEWAL (20*lv-20)
}


class SkillRatio:
    """Exact Skill Ratio step.
    Source lines (verbatim from repo):
    battle.c: int ratio = battle_calc_skillratio(src, bl, skill_id, skill_lv,
    (skill_get_type(skill_id) == BF_WEAPON) ?
    skill_get_damage(skill_id, skill_lv) : 100);
    battle.c: wd.damage = (int64)wd.damage * ratio / 100;"""

    @staticmethod
    def calculate(skill: SkillInstance, dmg: DamageRange, build: PlayerBuild, result: DamageResult) -> DamageRange:
        """Applies skill ratio and hit count to the full DamageRange."""
        skill_data = loader.get_skill(skill.id)

        if skill_data and skill_data.get("ratio_per_level"):
            ratio_list = skill_data["ratio_per_level"]
            ratio = ratio_list[skill.level - 1] if skill.level <= len(ratio_list) else skill_data.get("ratio_base", 100)
        else:
            ratio = skill_data.get("ratio_base", 100) if skill_data else 100

        # SC_MAXIMIZEPOWER forces ratio = 100 (exact rule from battle_calc_skillratio)
        active = getattr(build, 'active_status_levels', {})
        if "SC_MAXIMIZEPOWER" in active:
            ratio = 100

        # SC_OVERTHRUST / SC_OVERTHRUSTMAX add to skillratio (not flat ATK).
        # status.c: SC_OVERTHRUST val3 = 5*val1 (self-cast, pre-renewal)
        # status.c: SC_OVERTHRUSTMAX val2 = 20*val1
        # SC_OVERTHRUSTMAX cancels SC_OVERTHRUST in the emulator — both can't be active.
        # battle.c:2919-2922 inside battle_calc_skillratio (no RENEWAL guard):
        #   if(sc->data[SC_OVERTHRUST])    skillratio += sc->data[SC_OVERTHRUST]->val3;
        #   if(sc->data[SC_OVERTHRUSTMAX]) skillratio += sc->data[SC_OVERTHRUSTMAX]->val2;
        if "SC_OVERTHRUST" in active:
            ratio += 5 * active["SC_OVERTHRUST"]
        if "SC_OVERTHRUSTMAX" in active:
            ratio += 20 * active["SC_OVERTHRUSTMAX"]

        # NK flags (loaded here – ready for future NK_IGNORE_DEF etc. checks)
        nk_flags = skill_data.get("nk_flags", []) if skill_data else []  # noqa: F841

        # Multi-hit support (hit_count from skills.json)
        hit_count = skill_data.get("hit_count", 1) if skill_data else 1

        # Two sequential scale() calls — keep separate to preserve Hercules integer rounding
        # battle.c: wd.damage = (int64)wd.damage * ratio / 100;  (then * hit_count separately)
        dmg = dmg.scale(ratio, 100)
        dmg = dmg.scale(hit_count, 1)

        if skill_data and skill_data.get("ratio_per_level"):
            src = f"ratio_per_level[lv{skill.level}]"
        else:
            src = "ratio_base"

        result.add_step(
            name=f"Skill Ratio (ID {skill.id} Lv {skill.level})",

            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=ratio / 100.0,
            note=skill_data.get("note", "") if skill_data else "",
            formula=f"dmg * {ratio} // 100 * {hit_count}   (from skills.json {src})",
            hercules_ref="battle.c: battle_calc_skillratio — base ratio from skill_get_damage\n"
                         "battle.c:2919-2922: if(sc->data[SC_OVERTHRUST]) skillratio += sc->data[SC_OVERTHRUST]->val3;\n"
                         "battle.c:2921-2922: if(sc->data[SC_OVERTHRUSTMAX]) skillratio += sc->data[SC_OVERTHRUSTMAX]->val2;\n"
                         "battle.c: wd.damage = (int64)wd.damage * ratio / 100;"
        )
        return dmg

    @staticmethod
    def calculate_magic(skill: SkillInstance, dmg: DamageRange, build: PlayerBuild, target,
                        result: DamageResult) -> tuple:
        """Applies BF_MAGIC skill ratio (per-hit only). Returns (dmg, hit_count).

        hit_count is returned separately so the caller can apply it AFTER defense and
        attr_fix, matching the exact Hercules source order:
          MATK_RATE(skillratio) → calc_defense → attr_fix → × ad.div_
        Source: battle_calc_magic_attack, battle.c:1631-1785 (#else not RENEWAL).
        """
        skill_data = loader.get_skill(skill.id)
        skill_name = skill_data.get("name", "") if skill_data else ""

        ratio_fn = _BF_MAGIC_RATIOS.get(skill_name)
        ratio = ratio_fn(skill.level, target) if ratio_fn else 100

        # Raw hit count from skills.json number_of_hits — sign is significant:
        #   positive (e.g. +5): actual multi-hit — caller multiplies dmg × n after defense+attrfix
        #   negative (e.g. -3): cosmetic multi-hit — animation shows n hits, dmg is NOT multiplied
        # Source: battle.c:3823 damage_div_fix macro:
        #   if (div > 1) dmg *= div;          ← actual multi-hit
        #   else if (div < 0) div *= -1;      ← cosmetic: just flip sign for display, dmg unchanged
        hit_count_raw = 1
        if skill_data:
            noh = skill_data.get("number_of_hits")
            if noh and skill.level <= len(noh):
                hit_count_raw = noh[skill.level - 1]   # raw, NOT abs()

        dmg = dmg.scale(ratio, 100)

        display_hits = abs(hit_count_raw)
        cosmetic = hit_count_raw < 0
        result.add_step(
            name=f"Magic Skill Ratio (ID {skill.id} Lv {skill.level})",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=ratio / 100.0,
            note=skill_data.get("description", "") if skill_data else "",
            formula=(f"MATK × {ratio}%  ({display_hits} cosmetic hits — dmg not multiplied)"
                     if cosmetic else
                     f"MATK × {ratio}%  ({display_hits} hits applied after defense)"),
            hercules_ref="battle.c:1631-1785: battle_calc_skillratio BF_MAGIC switch (#else not RENEWAL)\n"
                         "battle.c:3823: damage_div_fix: div>1 → dmg*=div; div<0 → cosmetic (div negated, dmg unchanged)"
        )
        return dmg, hit_count_raw