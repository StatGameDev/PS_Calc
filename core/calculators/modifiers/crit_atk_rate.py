from core.models.build import PlayerBuild
from core.models.damage import DamageResult
from pmf.operations import _scale_floor, pmf_stats


class CritAtkRate:
    """Applies sd->bonus.crit_atk_rate to the crit branch only, pre-defense.

    Source: battle.c lines 5333-5334 (#ifndef RENEWAL, inside switch-default,
    before calc_defense is called — i.e. pre-defense):

        if(flag.cri && sd->bonus.crit_atk_rate)
            ATK_ADDRATE(sd->bonus.crit_atk_rate);

    Since crits bypass defense entirely (flag.idef = flag.idef2 = 1), the
    pre-defense vs. post-defense position is irrelevant for final output, but
    this matches the exact Hercules source position.

    Only called on the crit branch by BattlePipeline._run_branch(is_crit=True).
    """

    @staticmethod
    def calculate(build: PlayerBuild, pmf: dict, result: DamageResult) -> dict:
        rate = getattr(build, "bonus_crit_atk_rate", 0)
        mn, mx, av = pmf_stats(pmf)
        if rate == 0:
            result.add_step(
                name="Crit ATK Rate",
                value=av,
                min_value=mn,
                max_value=mx,
                note="bonus.crit_atk_rate = 0 (no bCriticalDamage bonus)",
                formula="no change",
                hercules_ref="battle.c:5333: if(flag.cri && sd->bonus.crit_atk_rate) ATK_ADDRATE(sd->bonus.crit_atk_rate);",
            )
            return pmf

        pmf = _scale_floor(pmf, 100 + rate, 100)
        mn, mx, av = pmf_stats(pmf)
        result.add_step(
            name="Crit ATK Rate",
            value=av,
            min_value=mn,
            max_value=mx,
            multiplier=(100 + rate) / 100.0,
            note=f"bonus.crit_atk_rate = {rate}% (from bCriticalDamage card/gear effect)",
            formula=f"damage * (100 + {rate}) / 100",
            hercules_ref="battle.c:5333: if(flag.cri && sd->bonus.crit_atk_rate) ATK_ADDRATE(sd->bonus.crit_atk_rate);",
        )
        return pmf
