from core.models.build import PlayerBuild
from core.models.damage import DamageResult
from core.config import BattleConfig


class FinalRateBonus:
    """Exact pre-renewal final rate multipliers (weapon/short/long) applied at the very end.
    Source lines (verbatim from repo):
    battle.c: if (wd.flag&BF_SHORT) damage = damage * battle_config.short_attack_damage_rate / 100;
    battle.c: else damage = damage * battle_config.long_attack_damage_rate / 100;
    battle.c: damage = damage * battle_config.weapon_damage_rate / 100;"""

    @staticmethod
    def calculate(build: PlayerBuild, current_damage: int, config: BattleConfig, result: DamageResult) -> None:
        # Step 1: short/long attack rate (Hercules applies this first)
        if build.is_ranged:
            sl_rate = config.long_attack_damage_rate
            sl_label = "Long"
        else:
            sl_rate = config.short_attack_damage_rate
            sl_label = "Short"

        after_sl = current_damage * sl_rate // 100
        result.add_step(
            name=f"Final Rate Bonus ({sl_label})",
            value=after_sl,
            multiplier=sl_rate / 100.0,
            note=f"{sl_label} attack damage rate: {sl_rate}%",
            formula=f"current * {sl_rate} // 100 (battle_config.{sl_label.lower()}_attack_damage_rate)",
            hercules_ref="battle.c: if (wd.flag&BF_SHORT) damage = damage * battle_config.short_attack_damage_rate / 100;\n"
                         "battle.c: else damage = damage * battle_config.long_attack_damage_rate / 100;"
        )

        # Step 2: weapon_damage_rate (Hercules applies this after short/long)
        after_weapon = after_sl * config.weapon_damage_rate // 100
        final_dmg = max(1, after_weapon)
        result.add_step(
            name="Final Rate Bonus (Weapon)",
            value=final_dmg,
            multiplier=config.weapon_damage_rate / 100.0,
            note=f"Weapon damage rate: {config.weapon_damage_rate}%",
            formula=f"current * {config.weapon_damage_rate} // 100 (battle_config.weapon_damage_rate)",
            hercules_ref="battle.c: damage = damage * battle_config.weapon_damage_rate / 100;"
        )