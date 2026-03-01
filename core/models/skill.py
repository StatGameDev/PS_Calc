from dataclasses import dataclass

@dataclass
class SkillInstance:
    id: int = 0                     # 0 = Normal Attack, 5 = SM_BASH, ...
    level: int = 1
    is_critical_forced: bool = False
    is_maximize_power: bool = False
    ignore_size_fix: bool = False   # flag&8 – ignores size fix