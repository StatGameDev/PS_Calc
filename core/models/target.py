from dataclasses import dataclass

@dataclass
class Target:
    def_: int = 0
    vit: int = 0
    size: str = "Medium"    # Small / Medium / Large
    race: str = "Formless"
    element: int = 0
    is_boss: bool = False
    level: int = 1