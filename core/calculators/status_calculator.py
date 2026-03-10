from core.build_manager import effective_is_ranged
from core.config import BattleConfig
from core.data_loader import loader
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

        # === PARTY BUFF SCs (support_buffs) ===
        # SC_BLESSING/SC_INC_AGI/SC_GLORIA stat bonuses are folded into build.bonus_*
        # by _apply_gear_bonuses() in main_window.py before StatusCalculator is called.
        # They therefore already appear in status.str/agi/etc. via base+bonus arithmetic.
        support = build.support_buffs

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

        # SC_ANGELUS: val2=5*level, pre-renewal (status.c:8320-8321, #ifndef RENEWAL at line 4426)
        # Multiplies computed vit_def for PC targets: vit_def *= def_percent/100 (battle.c:1492)
        # Hard DEF (def1) is NOT scaled for PC targets in pre-renewal (only for mob/pet targets).
        angelus_lv = int(support.get("SC_ANGELUS", 0))
        status.def_percent = 100 + 5 * angelus_lv
        # Scale def2 for display (def2 is display-only; DefenseFix uses target.vit directly).
        if angelus_lv:
            status.def2 = status.def2 * status.def_percent // 100

        # === CRITICAL ===
        # status.c:3876 — cri in 0.1% units: base 1.0% (=10) + 0.333% per LUK
        # Katar doubling (cri <<= 1) belongs in the crit roll (crit_chance.py),
        # NOT here, under the default Hercules config (show_katar_crit_bonus = 0).
        # When show_katar_crit_bonus = 1, status.c doubles cri here instead, but
        # that is the non-default path. We implement the default only.
        status.cri = 10 + (status.luk * 10 // 3) + (build.bonus_cri * 10)

        # === HIT / FLEE ===
        status.hit = build.base_level + status.dex + build.bonus_hit
        status.flee = build.base_level + status.agi + build.bonus_flee
        status.flee2 = status.luk + 10 if self.config.enable_perfect_flee else 0

        # === ASPD ===
        # Pre-renewal formula (status.c status_base_amotion_pc, #ifndef RENEWAL_ASPD):
        #   amotion = aspd_base[job][weapon_type]
        #   amotion -= amotion * (4*agi + dex) / 1000
        #   amotion += bonus.aspd_add  (flat from bAspd)
        #   amotion += 500-100*KN_CAVALIERMASTERY if riding peco (#ifndef RENEWAL_ASPD)
        #   clamped to [pc_max_aspd, 2000] = [2000 - max_aspd*10, 2000]
        # Displayed ASPD = (2000 - amotion) / 10  (client conversion)
        base_amotion = loader.get_aspd_base(build.job_id, weapon.weapon_type)
        amotion = base_amotion - base_amotion * (4 * status.agi + status.dex) // 1000
        amotion += build.bonus_aspd_add  # stub: flat amotion reduction from bAspd (Session 4)

        # SC ASPD buffs — source: status.c:5587-5652 status_calc_aspd_rate
        # Comment in source: "Note that the scale of aspd_rate is 1000 = 100%."
        # Formula: aspd_rate -= max(all active SC reductions); amotion = amotion * aspd_rate // 1000
        # Only the highest single reduction applies — no stacking between quicken-type SCs.
        active_sc = build.active_status_levels
        sc_aspd_reduction = 0   # in 1000-scale units (300 = 30% reduction)

        # Fixed-value SCs (val2 constant regardless of level)
        for sc_key in ("SC_TWOHANDQUICKEN", "SC_ONEHANDQUICKEN"):
            if sc_key in active_sc:
                sc_aspd_reduction = max(sc_aspd_reduction, 300)  # val2 = 300

        # SC_ADRENALINE: val3 = 300 (self) or 200 (party member) (status.c:7226-7232)
        # support_buffs stores the actual val3 directly (300 or 200).
        # Weapon restriction (axe/mace only) not enforced here — user's responsibility.
        adrenaline_val = int(support.get("SC_ADRENALINE", 0))
        if adrenaline_val:
            sc_aspd_reduction = max(sc_aspd_reduction, adrenaline_val)
        elif "SC_ADRENALINE" in active_sc:
            # backward-compat: old saves that stored it in active_status_levels
            sc_aspd_reduction = max(sc_aspd_reduction, 300)

        # SC_SPEARQUICKEN: val2 = 200 + 10*val1 (status.c:7822 #ifndef RENEWAL_ASPD)
        if "SC_SPEARQUICKEN" in active_sc:
            spear_lv = active_sc["SC_SPEARQUICKEN"]
            sc_aspd_reduction = max(sc_aspd_reduction, 200 + 10 * spear_lv)

        # SC_ASSNCROS (Assassin's Cross): val2 = (MusLesson/2 + 10 + song_lv + bard_agi/10) * 10
        # skill.c:13296-13307 #else (pre-renewal); weapon restriction (no bow/gun) not enforced here.
        song = build.song_state
        if song.get("SC_ASSNCROS"):
            song_lv   = int(song["SC_ASSNCROS"])
            mus_lv    = int(song.get("mus_lesson", 0))
            s_agi     = int(song.get("SC_ASSNCROS_agi") if song.get("SC_ASSNCROS_agi") is not None
                           else song.get("caster_agi", 1))
            val2 = (mus_lv // 2 + 10 + song_lv + s_agi // 10) * 10
            sc_aspd_reduction = max(sc_aspd_reduction, val2)

        if sc_aspd_reduction:
            amotion = amotion * (1000 - sc_aspd_reduction) // 1000

        # bonus_aspd_percent: percentage aspd_rate bonus (e.g. 10 = 10% faster)
        # Implemented as aspd_rate modifier: amotion *= (1000 - pct*10) / 1000
        # (bAspd_rate from items/skills — Session 4 populates via script parsing)
        if build.bonus_aspd_percent:
            amotion = amotion * (1000 - build.bonus_aspd_percent * 10) // 1000
        if build.is_riding_peco:
            cav_lv = build.mastery_levels.get("KN_CAVALIERMASTERY", 0)
            amotion += 500 - 100 * cav_lv  # status.c #ifndef RENEWAL_ASPD
        min_amotion = 2000 - self.config.max_aspd * 10
        amotion = max(min_amotion, min(2000, amotion))
        status.aspd = (2000 - amotion) / 10  # player-facing display value (float, e.g. 185.3)

        # === MAX HP ===
        # status_calc_pc_ MaxHP (pre-renewal):
        #   hp_base = HPTable[job_id][base_level - 1]
        #   max_hp  = hp_base * (100 + vit) // 100
        #   + bonus_maxhp stub (Session 4)
        hp_base = loader.get_hp_at_level(build.job_id, build.base_level)
        status.max_hp = hp_base * (100 + status.vit) // 100
        status.max_hp += build.bonus_maxhp

        # === MAX SP ===
        # Same pattern: SPTable[job_id][base_level - 1] * (100 + int_) // 100
        sp_base = loader.get_sp_at_level(build.job_id, build.base_level)
        status.max_sp = sp_base * (100 + status.int_) // 100
        status.max_sp += build.bonus_maxsp

        # === MATK ===
        # status.c:3783-3792 #else not RENEWAL (status_base_matk_min / _max)
        status.matk_min = status.int_ + (status.int_ // 7) ** 2
        status.matk_max = status.int_ + (status.int_ // 5) ** 2

        # === MDEF ===
        # Hard MDEF (mdef): from bMdef item scripts, routed through equip_mdef on PlayerBuild
        status.mdef = build.equip_mdef
        # Soft MDEF (mdef2): int_ + vit//2  (status.c:3867 #else not RENEWAL)
        status.mdef2 = status.int_ + (status.vit >> 1)

        # === BARD SONGS (song_state) ===
        # All formulas from skill.c skill_unitsetting (#else pre-renewal blocks).
        # val stored as sg->val1 in skill_unitsetting → becomes SC->val2 when applied.
        # Override key (e.g. "SC_ASSNCROS_agi") not None → use that value; None → shared caster stat.

        def _sv(key: str, shared_key: str, default: int = 1) -> int:
            """Resolve a per-song stat override or fall back to shared caster stat."""
            v = song.get(key)
            return int(v) if v is not None else int(song.get(shared_key, default))

        # SC_WHISTLE: val2=FLEE bonus, val3=FLEE2 bonus (×10 scale in status.c)
        # skill.c:13245-13251; status.c:~4866 (flee), ~4952 (flee2)
        if song.get("SC_WHISTLE"):
            song_lv  = int(song["SC_WHISTLE"])
            mus_lv   = int(song.get("mus_lesson", 0))
            s_agi    = _sv("SC_WHISTLE_agi", "caster_agi")
            s_luk    = _sv("SC_WHISTLE_luk", "caster_luk")
            status.flee  += song_lv + s_agi // 10 + mus_lv
            status.flee2 += ((song_lv + 1) // 2 + s_luk // 10 + mus_lv) * 10

        # SC_APPLEIDUN: maxhp += maxhp * val2 / 100
        # skill.c:13283-13286; status.c:5766-5767
        if song.get("SC_APPLEIDUN"):
            song_lv  = int(song["SC_APPLEIDUN"])
            mus_lv   = int(song.get("mus_lesson", 0))
            s_vit    = _sv("SC_APPLEIDUN_vit", "caster_vit")
            val2 = 5 + 2 * song_lv + s_vit // 10 + mus_lv
            status.max_hp += status.max_hp * val2 // 100

        # SC_POEMBRAGI: cast time % + after-cast delay % (display-only)
        # skill.c:13261-13267; applied in cast time / ACD checks, not simulated here.
        if song.get("SC_POEMBRAGI"):
            song_lv  = int(song["SC_POEMBRAGI"])
            mus_lv   = int(song.get("mus_lesson", 0))
            s_dex    = _sv("SC_POEMBRAGI_dex", "caster_dex")
            s_int    = _sv("SC_POEMBRAGI_int", "caster_int")
            status.cast_time_reduction_pct       = 3 * song_lv + s_dex // 10 + 2 * mus_lv
            status.after_cast_delay_reduction_pct = (
                (3 * song_lv if song_lv < 10 else 50) + s_int // 5 + 2 * mus_lv
            )

        # === DANCER DANCES (song_state) ===

        # SC_HUMMING: hit += val2
        # skill.c:13253-13260; status.c:~4803-4804
        if song.get("SC_HUMMING"):
            song_lv   = int(song["SC_HUMMING"])
            dance_lv  = int(song.get("dance_lesson", 0))
            s_dex     = _sv("SC_HUMMING_dex", "dancer_dex")
            status.hit += 2 * song_lv + s_dex // 10 + dance_lv

        # SC_FORTUNE: critical += val2 (10× scale — same units as rest of cri)
        # skill.c:13309-13313; status.c:~4755-4756
        if song.get("SC_FORTUNE"):
            song_lv   = int(song["SC_FORTUNE"])
            dance_lv  = int(song.get("dance_lesson", 0))
            s_luk     = _sv("SC_FORTUNE_luk", "dancer_luk")
            status.cri += (10 + song_lv + s_luk // 10 + dance_lv) * 10

        # SC_SERVICEFORYU: maxsp % + sp_cost_reduction_pct (display-only)
        # skill.c:13288-13294; status.c:~5847-5848
        if song.get("SC_SERVICEFORYU"):
            song_lv   = int(song["SC_SERVICEFORYU"])
            dance_lv  = int(song.get("dance_lesson", 0))
            s_int     = _sv("SC_SERVICEFORYU_int", "dancer_int")
            val2 = 15 + song_lv + s_int // 10 + dance_lv // 2
            val3 = 20 + 3 * song_lv + s_int // 10 + dance_lv // 2
            status.max_sp            += status.max_sp * val2 // 100
            status.sp_cost_reduction_pct = val3

        # === ENSEMBLES (song_state) ===

        # SC_DRUMBATTLE DEF bonus: def += val3 = (skill_lv+1)*2
        # status.c:4999-5000 (hard DEF, same block as equipment DEF)
        drum_lv = int(song.get("SC_DRUMBATTLE", 0))
        if drum_lv:
            status.def_ += (drum_lv + 1) * 2

        # SC_NIBELUNGEN has no stat effect beyond WATK (handled in base_damage.py).
        # SC_SIEGFRIED elemental resistance affects incoming pipeline — Session R.

        return status