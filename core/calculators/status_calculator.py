from core.build_manager import effective_is_ranged
from core.config import BattleConfig
from core.models.build import PlayerBuild
from core.models.status import StatusData
from core.models.weapon import Weapon

class StatusCalculator:
    """Exact pre-renewal port from status.c (status_calc_pc_ + status_calc_misc)"""

    def __init__(self, config: BattleConfig):
        self.config = config

    def calculate(self, build: PlayerBuild, weapon: Weapon) -> StatusData:
        status = StatusData()

        # Total stats (base + equipment/cards/buffs)
        status.str = build.base_str + build.bonus_str
        status.agi = build.base_agi + build.bonus_agi
        status.vit = build.base_vit + build.bonus_vit
        status.int_ = build.base_int + build.bonus_int
        status.dex = build.base_dex + build.bonus_dex
        status.luk = build.base_luk + build.bonus_luk

        # === BASE ATK ===
        # Ranged weapons (W_BOW etc.) swap STR/DEX roles in BATK.
        # is_ranged_override overrides; otherwise derived from weapon_type.
        str_val = status.str
        dex_val = status.dex
        if effective_is_ranged(build, weapon):
            str_val, dex_val = dex_val, str_val
        dstr = str_val // 10
        status.batk = str_val + (dstr * dstr) + (dex_val // 5) + (status.luk // 5)
        status.batk += build.bonus_batk

        # === DEFENSE ===
        status.def_ = build.equip_def                    # Hard DEF (def1) = equipment only
        status.def2 = status.vit + build.bonus_def2      # Soft DEF (vit_def) = VIT + bonuses

        # === CRITICAL ===
        status.cri = 10 + (status.luk * 10 // 3) + (build.bonus_cri * 10)  # base 1.0% + 0.333% per LUK
        if weapon.weapon_type == "Katar":
            status.cri *= 2                              # katar double-crit (W_KATAR, status.c)

        # === HIT / FLEE ===
        status.hit = build.base_level + status.dex + build.bonus_hit
        status.flee = build.base_level + status.agi + build.bonus_flee
        status.flee2 = status.luk + 10 if self.config.enable_perfect_flee else 0

        # Placeholders (full job tables + ASPD in Phase 3)
        status.aspd = 2000 - (build.bonus_aspd_percent * 10)
        status.max_hp = 3000 + status.vit * 30
        status.max_sp = 300 + status.int_ * 5

        return status