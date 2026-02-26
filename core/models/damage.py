from dataclasses import dataclass
from typing import List

@dataclass
class DamageStep:
    name: str
    value: int
    multiplier: float = 1.0
    note: str = ""

@dataclass
class DamageResult:
    min_damage: int = 0
    max_damage: int = 0
    avg_damage: int = 0
    crit_chance: float = 0.0
    hit_chance: float = 0.0
    steps: List[DamageStep] = None

    def __post_init__(self):
        if self.steps is None:
            self.steps = []