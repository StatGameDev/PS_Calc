from dataclasses import dataclass

@dataclass
class PlayerBuild:
    """Everything you type manually from @status / equipment windows"""
    base_level: int = 1
    job_level: int = 1
    job_id: int = 0

    base_str: int = 1
    base_agi: int = 1
    base_vit: int = 1
    base_int: int = 1
    base_dex: int = 1
    base_luk: int = 1

    bonus_str: int = 0
    bonus_agi: int = 0
    bonus_vit: int = 0
    bonus_int: int = 0
    bonus_dex: int = 0
    bonus_luk: int = 0

    equip_def: int = 0          # Hard DEF
    bonus_def2: int = 0         # Extra soft DEF from items / foods / SCs

    bonus_batk: int = 0
    bonus_cri: int = 0
    bonus_hit: int = 0
    bonus_flee: int = 0
    bonus_aspd_percent: int = 0

    is_ranged: bool = False
    is_katar: bool = False