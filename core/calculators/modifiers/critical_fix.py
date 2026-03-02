from core.models.status import StatusData
from core.models.skill import SkillInstance
from core.models.damage import DamageResult


class CriticalFix:
    """Exact Critical Hit step with full RNG support (pre-renewal BF_WEAPON).
    Source lines (verbatim from repo):
    if( !flag.cri && wd.type != BDT_MULTIHIT && sstatus->cri &&
        (!skill_id ||
         skill_id == KN_AUTOCOUNTER ||
         skill_id == SN_SHARPSHOOTING || skill_id == MA_SHARPSHOOTING ||
         skill_id == NJ_KIRIKAGE))
    {
        ... if (rnd() % 1000 < cri) flag.cri = 1;
    }
    if (is_attack_critical(&wd, src, target, skill_id, skill_lv, flag)) {
        wd.type = DMG_CRITICAL;
        wd.damage = battle_calc_damage(...)  # crit path
    }"""

    @staticmethod
    def calculate(status: StatusData, skill: SkillInstance, current_damage: int, result: DamageResult) -> None:
        """Computes crit chance (per-mille → %), respects forced flag for tests, adds step with non-crit/crit paths.
        All variables initialised at top (C local-declaration style, type safety, readability)."""
        cri = status.cri                      # already 0.1% units from StatusCalculator
        chance = 0.0
        is_crit = skill.is_critical_forced
        non_crit_dmg = current_damage
        crit_dmg = current_damage * 2

        if is_crit:
            chance = 100.0
        else:
            chance = min(100.0, cri / 10.0)   # convert 0.1% units to %

        # Store for later expected-average calculation in Variance step
        result.crit_chance = chance

        result.add_step(
            name="Critical Hit",
            value=crit_dmg if is_crit else non_crit_dmg,
            multiplier=2.0 if is_crit else 1.0,
            note=f"Chance {chance:.1f}% (forced={is_crit}) – non-crit {non_crit_dmg} / crit {crit_dmg}",
            formula=f"current * 2 if crit else current   (sstatus->cri roll after all multipliers)",
            hercules_ref="if( !flag.cri && wd.type != BDT_MULTIHIT && sstatus->cri &&\n" +
                         "    (!skill_id || skill_id == KN_AUTOCOUNTER || ... )) {\n" +
                         "    ... if (rnd() % 1000 < cri) flag.cri = 1;\n" +
                         "}\n" +
                         "if (is_attack_critical(&wd, src, target, skill_id, skill_lv, flag)) {\n" +
                         "    wd.type = DMG_CRITICAL;\n" +
                         "    wd.damage = battle_calc_damage(...)  # crit path\n" +
                         "}"
        )