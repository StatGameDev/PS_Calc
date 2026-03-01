from core.models.skill import SkillInstance
from core.models.damage import DamageResult
from core.data_loader import loader


class SkillRatio:
    """Exact Skill Ratio step.
    Source lines (verbatim from repo):
    battle.c: int ratio = battle_calc_skillratio(src, bl, skill_id, skill_lv,
    (skill_get_type(skill_id) == BF_WEAPON) ?
    skill_get_damage(skill_id, skill_lv) : 100);
    battle.c: wd.damage = (int64)wd.damage * ratio / 100;"""

    @staticmethod
    def calculate(skill: SkillInstance, base_dmg: int, result: DamageResult) -> None:
        """Computes ratio from skills.json registry and adds the step.
        Uses the exact same logic the previous placeholder had, now isolated."""
        skill_data = loader.get_skill(skill.id)

        if skill_data and skill_data.get("ratio_per_level"):
            ratio_list = skill_data["ratio_per_level"]
            ratio = ratio_list[skill.level - 1] if skill.level <= len(ratio_list) else skill_data.get("ratio_base", 100)
        else:
            ratio = skill_data.get("ratio_base", 100) if skill_data else 100

        dmg_after_ratio = base_dmg * ratio // 100

        # Dynamic formula prepared for future JSON expansions (ratio_base, skill_get_damage, etc.)
        if skill_data and skill_data.get("ratio_per_level"):
            src = f"ratio_per_level[lv{skill.level}]"
        else:
            src = "ratio_base"
        formula = f"base_dmg * {ratio} // 100   (from skills.json {src})"

        result.add_step(
            name=f"Skill Ratio (ID {skill.id} Lv {skill.level})",
            value=dmg_after_ratio,
            multiplier=ratio / 100.0,
            note=skill_data.get("note", "") if skill_data else "",
            formula=formula,
            hercules_ref="battle.c: int ratio = battle_calc_skillratio(src, bl, skill_id, skill_lv, (skill_get_type(skill_id) == BF_WEAPON) ? skill_get_damage(skill_id, skill_lv) : 100);\n" +
                         "battle.c: wd.damage = (int64)wd.damage * ratio / 100;"
        )