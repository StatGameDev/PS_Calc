from core.models.weapon import Weapon
from core.models.build import PlayerBuild
from core.models.damage import DamageRange, DamageResult
from core.models.skill import SkillInstance
from core.data_loader import loader


class ActiveStatusBonus:
    """Pre-renewal flat ATK bonuses from SC_* in the weapon-attack phase.
    Only SC_AURABLADE is implemented here (flat_per_level, no renewal guard).
    SC_ENCHANTBLADE (complex_flat) and SC_GIANTGROWTH (rate_chance) are deferred.
    Removed entries (see active_status_bonus.json comment for reasons):
      SC_MAXIMIZEPOWER — variance collapse only; handled in base_damage.py
      SC_SPURT         — hallucinated; not present in Hercules source
      SC_GS_MADNESSCANCEL, SC_IMPOSITIO — #ifdef RENEWAL in battle_calc_masteryfix
      SC_OVERTHRUST, SC_OVERTHRUSTMAX   — skillratio bonus; handled in skill_ratio.py
    Source: battle.c battle_calc_weapon_attack, after battle_addmastery call."""

    @staticmethod
    def calculate(weapon: Weapon, build: PlayerBuild, skill: SkillInstance, dmg: DamageRange, result: DamageResult) -> DamageRange:
        """Applies flat SC_* bonuses to the full DamageRange."""
        active_status_levels = getattr(build, 'active_status_levels', {})
        total_bonus: int = 0
        applied_bonuses: list[str] = []
        note: str = "No active statuses"
        formula: str = "dmg (no SC bonuses)"

        if active_status_levels:
            for sc_key, level in active_status_levels.items():
                config = loader.get_active_status_config(sc_key)
                if not config:
                    continue

                sc_type = config.get("type")
                bonus = 0

                # flat_per_level (Aura Blade; others removed — see class docstring)
                if sc_type == "flat_per_level":
                    mult = config.get("multiplier", 1)
                    bonus = level * mult

                # flat (Madness Cancel)
                elif sc_type == "flat":
                    bonus = config.get("value", 0)

                # complex_flat – DEFERRED (SC_ENCHANTBLADE)
                # i = (enchant_lv*20+100)*lv//150 + status.int_ - target.mdef + status_get_matk(sd,0)
                # Exact formula from battle.c SC_ENCHANTBLADE block.
                elif sc_type == "complex_flat":
                    pass  # TODO: requires StatusData.matk and target.mdef

                # rate_chance – DEFERRED (SC_GIANTGROWTH)
                # 15% chance to apply 200% rate from battle.c SC_GIANTGROWTH block.
                elif sc_type == "rate_chance":
                    pass  # TODO: requires seeded RNG matching Hercules rand()

                # exclusions (Aura Blade on Spiral Pierce, etc.)
                if "exclusions" in config:
                    if skill.id in config["exclusions"]:
                        bonus = 0

                total_bonus += bonus
                if bonus:
                    applied_bonuses.append(f"{sc_key} Lv{level} (+{bonus})")

            note = f"Applied: {', '.join(applied_bonuses) or 'none'}"
            formula = "dmg + sum(SC bonuses from active_status_bonus.json)"

        dmg = dmg.add(total_bonus)

        result.add_step(
            name="Active Status Bonuses",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=1.0,
            note=note,
            formula=formula,
            hercules_ref="battle.c: if (sc && sc->data[SC_AURABLADE] && skill_id != LK_SPIRALPIERCE && skill_id != ML_SPIRALPIERCE) { int lv = sc->data[SC_AURABLADE]->val1; ATK_ADD(wd.damage, wd.damage2, 20 * lv); }\n"
                         "battle.c: if (sc && sc->data[SC_ENCHANTBLADE] && skill_id == 0) { ... ATK_ADD(i); }\n"
                         "battle.c: (and every other if (sc && sc->data[SC_XXX]) ATK_ADD / ATK_ADDRATE block after battle_addmastery)"
        )
        return dmg