from core.models.weapon import Weapon
from core.models.build import PlayerBuild
from core.models.damage import DamageRange, DamageResult
from core.models.target import Target
from core.data_loader import loader



class MasteryFix:
    """Exact Mastery Fix step for BF_WEAPON attacks in pre-renewal.
    Source lines (verbatim from repo):
    battle.c: damage = battle->add_mastery(sd, target, damage, left_hand);"""

    @staticmethod
    def calculate(weapon: Weapon, build: PlayerBuild, target: Target, dmg: DamageRange, result: DamageResult) -> DamageRange:
        """Adds the flat mastery bonus to the full DamageRange."""
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

        dmg = dmg.add(bonus)

        result.add_step(
            name="Mastery Fix",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
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
            dmg = dmg.scale(ratio, 100)
            result.add_step(
                name="Adv. Katar Mastery",
                value=dmg.avg,
                min_value=dmg.min,
                max_value=dmg.max,
                multiplier=ratio / 100,
                note=f"ASC_KATAR Lv {asc_katar_lv}: ×{ratio / 100:.2f}",
                formula=f"dmg * (100 + 10 + 2 × {asc_katar_lv}) / 100",
                hercules_ref="battle.c:927-929 #else: damage += damage * (10 + 2 * skill2_lv) / 100"
            )

        return dmg