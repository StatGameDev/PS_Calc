from dataclasses import dataclass

@dataclass
class Weapon:
    atk: int = 0
    refine: int = 0
    level: int = 1
    element: int = 0        # 0=Neutral, 1=Water, ...