from dataclasses import dataclass

@dataclass
class BattleConfig:
    """Exact tunables from conf/battle/battle.conf (pre-renewal only – full clean structure)."""
    weapon_damage_rate: int = 100
    short_attack_damage_rate: int = 100
    long_attack_damage_rate: int = 100
    critical_rate: int = 100
    enable_critical: bool = True
    max_aspd: int = 190
    enable_perfect_flee: bool = True

    # Full VIT penalty support (pure mechanics, no legacy fields)
    vit_penalty_target: int = 0      # bitmask: 1=PC, 2=MOB, 4=BOSS, etc.
    vit_penalty_count: int = 3       # hits before penalty starts
    vit_penalty_num: int = 5         # % or flat reduction per extra hit
    vit_penalty_type: int = 0        # 0=off, 1=percentage, 2=flat