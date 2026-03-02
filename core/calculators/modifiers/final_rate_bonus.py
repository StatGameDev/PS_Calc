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
        rate = config.weapon_damage_rate
        if build.is_ranged:
            rate = config.long_attack_damage_rate
        else:
            rate = config.short_attack_damage_rate

        after_rate = current_damage * rate // 100
        final_dmg = max(1, after_rate)

        result.add_step(
            name="Final Rate Bonus",
            value=final_dmg,
            multiplier=rate / 100.0,
            note=f"Weapon rate {config.weapon_damage_rate}% + {'Long' if build.is_ranged else 'Short'} rate {rate}%",
            formula=f"current * {rate} // 100 (BattleConfig rates)",
            hercules_ref="battle.c: if (wd.flag&BF_SHORT) damage = damage * battle_config.short_attack_damage_rate / 100;\n" +
                         "battle.c: else damage = damage * battle_config.long_attack_damage_rate / 100;\n" +
                         "battle.c: damage = damage * battle_config.weapon_damage_rate / 100;"
        )