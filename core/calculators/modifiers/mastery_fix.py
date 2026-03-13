from core.models.weapon import Weapon
from core.models.build import PlayerBuild
from core.models.damage import DamageResult
from core.models.target import Target
from core.models.skill import SkillInstance
from core.data_loader import loader
from pmf.operations import _add_flat, _scale_floor, pmf_stats


# battle.c:838-842: battle_calc_masteryfix returns early (no mastery bonus) for these skills.
_MASTERY_EXEMPT_SKILLS: frozenset = frozenset({
    "MO_INVESTIGATE", "MO_EXTREMITYFIST", "CR_GRANDCROSS",
    "NJ_ISSEN", "CR_ACIDDEMONSTRATION",
})


class MasteryFix:
    """Exact Mastery Fix step for BF_WEAPON attacks in pre-renewal.
    Source lines (verbatim from repo):
    battle.c: damage = battle->add_mastery(sd, target, damage, left_hand);"""

    @staticmethod
    def calculate(weapon: Weapon, build: PlayerBuild, target: Target, pmf: dict, result: DamageResult,
                  skill: SkillInstance = None) -> dict:
        """Adds the flat mastery bonus to the PMF."""
        # battle.c:838-842: return early from battle_calc_masteryfix for exempt skills.
        if skill is not None and skill.name in _MASTERY_EXEMPT_SKILLS:
            mn, mx, av = pmf_stats(pmf)
            result.add_step(
                name="Mastery Fix",
                value=av, min_value=mn, max_value=mx,
                multiplier=1.0,
                note=f"BYPASSED — {skill.name} is exempt (battle.c:838-842)",
                formula="no change (mastery skipped)",
                hercules_ref="battle.c:838-842: battle_calc_masteryfix returns early for these skills",
            )
            return pmf

        mastery_key = loader.get_mastery_weapon_map().get(weapon.weapon_type)

        bonus: int = 0
        note: str = f"No mastery defined for {weapon.weapon_type}"
        formula: str = "dmg (no mastery)"

        if mastery_key is not None:
            mastery_level = build.mastery_levels.get(mastery_key, 0)
            mult = loader.get_mastery_multiplier(mastery_key, build)

            # Target-dependent masteries (AL_DEMONBANE / HT_BEASTBANE)
            if mastery_key == "AL_DEMONBANE" and target.race in ("Undead", "Demon"):
                bonus = mastery_level * (3 + build.base_level // 20)
            elif mastery_key == "HT_BEASTBANE" and target.race in ("Brute", "Insect"):
                bonus = mastery_level * 4
            else:
                bonus = mastery_level * mult

            note = f"{mastery_key} Lv {mastery_level} for {weapon.weapon_type} ({weapon.hand} hand) (+{bonus})"
            formula = f"dmg + (mastery_level * {mult} from tables/mastery_fix.json)"

        pmf = _add_flat(pmf, bonus)

        mn, mx, av = pmf_stats(pmf)
        result.add_step(
            name="Mastery Fix",
            value=av,
            min_value=mn,
            max_value=mx,
            multiplier=1.0,
            note=note,
            formula=formula,
            hercules_ref="battle.c: damage = battle->add_mastery(sd, target, damage, left_hand);"
        )

        # ASC_KATAR: Advanced Katar Mastery — percentage bonus on top of flat AS_KATAR.
        # Source: battle.c:927-929 #else (pre-renewal):
        #   if (weapontype == W_KATAR && skill_id != ASC_BREAKER && weapon)
        #       damage += damage * (10 + 2 * skill2_lv) / 100;
        asc_katar_lv = build.mastery_levels.get("ASC_KATAR", 0)
        if weapon.weapon_type == "Katar" and asc_katar_lv > 0:
            ratio = 100 + 10 + 2 * asc_katar_lv   # e.g. lv5 → 120, lv10 → 130
            pmf = _scale_floor(pmf, ratio, 100)
            mn, mx, av = pmf_stats(pmf)
            result.add_step(
                name="Adv. Katar Mastery",
                value=av,
                min_value=mn,
                max_value=mx,
                multiplier=ratio / 100,
                note=f"ASC_KATAR Lv {asc_katar_lv}: ×{ratio / 100:.2f}",
                formula=f"dmg * (100 + 10 + 2 × {asc_katar_lv}) / 100",
                hercules_ref="battle.c:927-929 #else: damage += damage * (10 + 2 * skill2_lv) / 100"
            )

        # NJ_TOBIDOUGU: skill-based mastery for NJ_SYURIKEN — flat +3*lv damage.
        # battle.c:843-850: case NJ_SYURIKEN: if (NJ_TOBIDOUGU > 0 && weapon) damage += 3 * skill2_lv;
        # The check is on the skill being NJ_SYURIKEN, NOT on weapon_type.
        nj_tobi_lv = build.mastery_levels.get("NJ_TOBIDOUGU", 0)
        if skill is not None and skill.name == "NJ_SYURIKEN" and nj_tobi_lv > 0:
            pmf = _add_flat(pmf, 3 * nj_tobi_lv)
            mn, mx, av = pmf_stats(pmf)
            result.add_step(
                name="Throw Mastery",
                value=av,
                min_value=mn,
                max_value=mx,
                multiplier=1.0,
                note=f"NJ_TOBIDOUGU Lv {nj_tobi_lv}: +{3 * nj_tobi_lv}",
                formula=f"dmg + 3 × {nj_tobi_lv}",
                hercules_ref="battle.c:843-850 case NJ_SYURIKEN: if(NJ_TOBIDOUGU>0 && weapon) damage += 3 * skill2_lv",
            )

        # NJ_KUNAI: flat +60 mastery pre-renewal.
        # battle.c:852-855 #ifndef RENEWAL: case NJ_KUNAI: if(weapon) damage += 60;
        if skill is not None and skill.name == "NJ_KUNAI":
            pmf = _add_flat(pmf, 60)
            mn, mx, av = pmf_stats(pmf)
            result.add_step(
                name="Kunai Mastery",
                value=av,
                min_value=mn,
                max_value=mx,
                multiplier=1.0,
                note="NJ_KUNAI: +60 flat (pre-renewal)",
                formula="dmg + 60",
                hercules_ref="battle.c:852-855 #ifndef RENEWAL: case NJ_KUNAI: if(weapon) damage += 60",
            )

        return pmf