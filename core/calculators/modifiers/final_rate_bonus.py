from core.models.damage import DamageRange, DamageResult
from core.config import BattleConfig


class FinalRateBonus:
    """Exact pre-renewal final rate multipliers (weapon/short/long) applied at the very end.
    Source lines (verbatim from repo):
    battle.c: if (wd.flag&BF_SHORT) damage = damage * battle_config.short_attack_damage_rate / 100;
    battle.c: else damage = damage * battle_config.long_attack_damage_rate / 100;
    battle.c: damage = damage * battle_config.weapon_damage_rate / 100;"""

    @staticmethod
    def calculate(is_ranged: bool, dmg: DamageRange, config: BattleConfig, result: DamageResult) -> DamageRange:
        # Step 1: short/long attack rate (Hercules applies this first)
        if is_ranged:
            sl_rate = config.long_attack_damage_rate
            sl_label = "Long"
        else:
            sl_rate = config.short_attack_damage_rate
            sl_label = "Short"

        dmg = dmg.scale(sl_rate, 100)
        result.add_step(
            name=f"Final Rate Bonus ({sl_label})",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=sl_rate / 100.0,
            note=f"{sl_label} attack damage rate: {sl_rate}%",
            formula=f"dmg * {sl_rate} // 100 (battle_config.{sl_label.lower()}_attack_damage_rate)",
            hercules_ref="battle.c: if (wd.flag&BF_SHORT) damage = damage * battle_config.short_attack_damage_rate / 100;\n"
                         "battle.c: else damage = damage * battle_config.long_attack_damage_rate / 100;"
        )

        # Step 2: weapon_damage_rate (Hercules applies this after short/long)
        dmg = dmg.scale(config.weapon_damage_rate, 100)
        dmg = dmg.floor_at(1)
        result.add_step(
            name="Final Rate Bonus (Weapon)",
            value=dmg.avg,
            min_value=dmg.min,
            max_value=dmg.max,
            multiplier=config.weapon_damage_rate / 100.0,
            note=f"Weapon damage rate: {config.weapon_damage_rate}%",
            formula=f"dmg * {config.weapon_damage_rate} // 100 (battle_config.weapon_damage_rate)",
            hercules_ref="battle.c: damage = damage * battle_config.weapon_damage_rate / 100;"
        )
        return dmg