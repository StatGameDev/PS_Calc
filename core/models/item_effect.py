from dataclasses import dataclass, field


@dataclass
class ItemEffect:
    """One parsed effect from an item script."""
    bonus_type: str       # e.g. "bStr", "bSubClass", "bAutoSpell"
    arity: int            # 1 = bonus, 2 = bonus2, 3 = bonus3
    params: list          # e.g. [3] or ["RC_Boss", 40]
    description: str = ""  # human-readable, generated from template or manual override
