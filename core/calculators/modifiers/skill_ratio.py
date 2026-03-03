from core.models.skill import SkillInstance
from core.models.damage import DamageRange, DamageResult
from core.models.build import PlayerBuild
from core.data_loader import loader


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