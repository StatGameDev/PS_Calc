from dataclasses import dataclass

@dataclass
class BattleConfig:
    """Exact tunables from conf/battle/battle.conf"""
    weapon_damage_rate: int = 100
    short_attack_damage_rate: int = 100
    long_attack_damage_rate: int = 100
    critical_rate: int = 100
    enable_critical: bool = True
    max_aspd: int = 190
    vit_penalty_target: int = 0
    vit_penalty_value: int = 0
    enable_perfect_flee: bool = True