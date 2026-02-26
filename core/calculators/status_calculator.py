from ..config import BattleConfig
from ..models.build import PlayerBuild
from ..models.status import StatusData

class StatusCalculator:
    """Exact pre-renewal port from status.c (status_calc_pc_ + status_calc_misc)"""

    def __init__(self, config: BattleConfig):
        self.config = config

    def calculate(self, build: PlayerBuild) -> StatusData:
        status = StatusData()

        # Total stats
        status.str = build.base_str + build.bonus_str
        status.agi = build.base_agi + build.bonus_agi
        status.vit = build.base_vit + build.bonus_vit
        status.int = build.base_int + build.bonus_int
        status.dex = build.base_dex + build.bonus_dex
        status.luk = build.base_luk + build.bonus_luk

        # Base ATK – confirmed exact (status_base_atk + PR quadratic term)
        str_val = status.str
        dex_val = status.dex
        if build.is_ranged:
            str_val, dex_val = dex_val, str_val
        dstr = str_val // 10
        status.batk = str_val + (dstr * dstr) + (dex_val // 5) + (status.luk // 5)
        status.batk += build.bonus_batk

        # === DEFENSE – NOW EXACTLY AS SOURCE ===
        # Hard DEF (def_)
        status.def_ = build.equip_def

        # Soft DEF (def2 / vit_def) = VIT + bonuses
        status.def2 = status.vit + build.bonus_def2

        # Critical (LUK * 10 / 3 = classic 0.33% per LUK)
        status.cri = (status.luk * 10 // 3) + (build.bonus_cri * 10)
        if build.is_katar:
            status.cri = int(status.cri * 1.4)   # katar bonus in PR

        # HIT / FLEE (base_level + stat + bonus – exact PR)
        status.hit = build.base_level + status.dex + build.bonus_hit
        status.flee = build.base_level + status.agi + build.bonus_flee
        status.flee2 = status.luk + 10 if self.config.enable_perfect_flee else 0

        # Placeholders (full ASPD/HP/SP tables in Phase 3)
        status.aspd = 2000 - (build.bonus_aspd_percent * 10)
        status.max_hp = 3000 + status.vit * 30
        status.max_sp = 300 + status.int * 5

        return status