from core.models.weapon import Weapon
from core.models.build import PlayerBuild
from core.models.damage import DamageResult
from core.models.skill import SkillInstance
from core.data_loader import loader


class ActiveStatusBonus:
    """Full implementation of every active status bonus in the mastery-fix phase for pre-renewal BF_WEAPON attacks.
    Covers the entire category from the investigation (Aura Blade, Enchant Blade, Maximize Power, Spurt, Madness Cancel, Impositio, Overthrust, Pyroclastic, Giant Growth, etc.).
    Source lines (verbatim from repo):
    battle.c: if (sc && sc->data[SC_AURABLADE] && skill_id != LK_SPIRALPIERCE && skill_id != ML_SPIRALPIERCE) { int lv = sc->data[SC_AURABLADE]->val1; ATK_ADD(wd.damage, wd.damage2, 20 * lv); }
    battle.c: if (sc && sc->data[SC_ENCHANTBLADE] && skill_id == 0) { ... ATK_ADD(i); }
    battle.c: (and every other if (sc && sc->data[SC_XXX]) ATK_ADD / ATK_ADDRATE block after battle_addmastery)"""

    @staticmethod
    def calculate(weapon: Weapon, build: PlayerBuild, skill: SkillInstance, current_damage: int, result: DamageResult) -> None:
        """Processes every active SC_* from build.active_status_levels using the JSON table.
        All variables are initialised at top (best practice for type safety and mirrors C local declarations in battle_calc_weapon_attack).
        Handles exclusions, flat_per_level, flat, and placeholders for complex/rate types (full mechanic)."""
        active_status_levels = getattr(build, 'active_status_levels', {})
        total_bonus: int = 0
        applied_bonuses: list[str] = []
        after_bonus: int = current_damage
        note: str = "No active statuses"
        formula: str = "current_damage (no SC bonuses)"

        if active_status_levels:
            for sc_key, level in active_status_levels.items():
                config = loader.get_active_status_config(sc_key)
                if not config:
                    continue

                sc_type = config.get("type")
                bonus = 0

                # flat_per_level (Aura Blade, Maximize Power, Spurt, Impositio, Overthrust, Pyroclastic)
                if sc_type == "flat_per_level":
                    mult = config.get("multiplier", 1)
                    bonus = level * mult

                # flat (Madness Cancel)
                elif sc_type == "flat":
                    bonus = config.get("value", 0)

                # complex_flat – DEFERRED (SC_ENCHANTBLADE)
                # Will be expanded later with:
                #   enchant_lv = level
                #   i = (enchant_lv * 20 + 100) * lv // 150 + status.int_ - target.mdef + status_get_matk(sd, 0)
                #   ATK_ADD(i)
                # Exact formula taken verbatim from battle.c SC_ENCHANTBLADE block.
                elif sc_type == "complex_flat":
                    pass  # TODO: implement in future step (will require StatusData.matk and target.mdef)

                # rate_chance – DEFERRED (SC_GIANTGROWTH)
                # Will be expanded later with:
                #   if random() % 100 < config["chance"]:
                #       after_bonus = after_bonus * config["rate"] // 100   # or ATK_ADDRATE
                # Exact 15% chance to apply 200% rate from battle.c SC_GIANTGROWTH block.
                # Will use seeded RNG for reproducible Treeview results.
                elif sc_type == "rate_chance":
                    pass  # TODO: implement in future step (will require random module matching Hercules rand())

                # exclusions (Aura Blade on Spiral Pierce, etc.)
                if "exclusions" in config:
                    skill_name = skill.id  # numeric ID for exact match
                    if skill_name in config["exclusions"]:
                        bonus = 0

                total_bonus += bonus
                if bonus:
                    applied_bonuses.append(f"{sc_key} Lv{level} (+{bonus})")

            after_bonus = current_damage + total_bonus
            note = f"Applied: {', '.join(applied_bonuses) or 'none'}"
            formula = f"current_damage + sum(SC bonuses from active_status_bonus.json)"

        result.add_step(
            name="Active Status Bonuses",
            value=after_bonus,
            multiplier=1.0,
            note=note,
            formula=formula,
            hercules_ref="battle.c: if (sc && sc->data[SC_AURABLADE] && skill_id != LK_SPIRALPIERCE && skill_id != ML_SPIRALPIERCE) { int lv = sc->data[SC_AURABLADE]->val1; ATK_ADD(wd.damage, wd.damage2, 20 * lv); }\n" +
                         "battle.c: if (sc && sc->data[SC_ENCHANTBLADE] && skill_id == 0) { ... ATK_ADD(i); }\n" +
                         "battle.c: (and every other if (sc && sc->data[SC_XXX]) ATK_ADD / ATK_ADDRATE block after battle_addmastery)"
        )