from dataclasses import dataclass

@dataclass
class StatusData:
    """Mirror of struct status_data used in battle.c / status.c"""
    str: int = 0
    agi: int = 0
    vit: int = 0
    int_: int = 0
    dex: int = 0
    luk: int = 0

    batk: int = 0      # Base ATK
    def_: int = 0      # Hard DEF (def1)
    def2: int = 0      # Soft DEF (vit_def)
    cri: int = 0       # in 0.1% units (100 = 10.0%)
    hit: int = 0
    flee: int = 0
    flee2: int = 0
    aspd: int = 0
    max_hp: int = 0
    max_sp: int = 0