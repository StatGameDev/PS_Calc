from core.models.weapon import Weapon
from core.models.build import PlayerBuild
from core.models.damage import DamageResult
from core.models.target import Target
from core.data_loader import loader



class MasteryFix:
    """Exact Mastery Fix step for BF_WEAPON attacks in pre-renewal.
    Source lines (verbatim from repo):
    battle.c: damage = battle->add_mastery(sd, target, damage, left_hand);"""

    @staticmethod
    def calculate(weapon: Weapon, build: PlayerBuild, target: Target, current_damage: int, result: DamageResult) -> None:
        """Adds the flat mastery bonus using the JSON table (now with build passed for conditionals).
        All variables are initialised at top (best practice for type safety and Hercules-style clarity)."""
        # Mapping now loaded from JSON (data-driven)
        mastery_key = loader.get_mastery_weapon_map().get(weapon.weapon_type)

        # Initialise every post-conditional variable at top – required by static type checkers
        # and mirrors C local declaration style in battle.c
        mastery_level: int = 0
        mult: int = 1
        bonus: int = 0
        after_mastery: int = current_damage
        note: str = f"No mastery defined for {weapon.weapon_type}"
        formula: str = "current_damage (no mastery)"

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

            after_mastery = current_damage + bonus
            note = f"{mastery_key} Lv {mastery_level} for {weapon.weapon_type} ({weapon.hand} hand) (+{bonus})"
            formula = f"current_damage + (mastery_level * {mult} from tables/mastery_fix.json)"

        result.add_step(
            name="Mastery Fix",
            value=after_mastery,
            multiplier=1.0,
            note=note,
            formula=formula,
            hercules_ref="battle.c: damage = battle->add_mastery(sd, target, damage, left_hand);"
        )