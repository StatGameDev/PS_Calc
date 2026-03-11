"""
Skill timing calculator: effective cast time + after-cast delay for a single skill use.

Sources (all pre-renewal, #ifndef RENEWAL_CAST guards respected):
  Cast time:  skill_castfix      (skill.c:17176)
  ACD:        skill_delay_fix    (skill.c:17414)
  Period floor: unit_skilluse_id2 (unit.c:1846)
    canact_tick = tick + max(casttime, max(amotion, min_skill_delay_limit=100))
  then at cast-end:
    canact_tick = max(tick + delay_fix(), ud->canact_tick)
  Combined: period = max(cast + delay, amotion)   (amotion >= 100 always)
"""
from __future__ import annotations

from core.models.status import StatusData
from core.models.gear_bonuses import GearBonuses

# Monk combo skills receive an AGI/DEX-based ACD reduction.
# Source: skill_delay_fix (skill.c:17437)
#   time -= (4 * status_get_agi(bl) + 2 * status_get_dex(bl))
_MONK_COMBO_SKILLS: frozenset[str] = frozenset({
    "MO_TRIPLEATTACK",
    "MO_CHAINCOMBO",
    "MO_COMBOFINISH",
    "CH_TIGERFIST",
    "CH_CHAINCRUSH",
})

# DEX scale used by skill_castfix for the pre-renewal DEX reduction step.
# Default value from conf/map/battle/skill.conf:64 (castrate_dex_scale = 150).
_CASTRATE_DEX_SCALE: int = 150

# Minimum after-cast delay enforced by Hercules regardless of reductions.
# conf/map/battle/skill.conf:48 (min_skill_delay_limit = 100 ms).
_MIN_SKILL_DELAY_MS: int = 100


def calculate_skill_timing(
    skill_name: str,
    skill_lv: int,
    skill_data: dict,
    status: StatusData,
    gear_bonuses: GearBonuses,
    support_buffs: dict,
) -> tuple[int, int]:
    """Return (effective_cast_ms, effective_delay_ms) for one use of skill at skill_lv.

    The caller applies the amotion floor:
        period = max(effective_cast + effective_delay, amotion)

    effective_delay is always >= _MIN_SKILL_DELAY_MS (100 ms).
    effective_cast  is always >= 0.
    """
    lv_idx = skill_lv - 1

    # ── Cast time ─────────────────────────────────────────────────────────────
    # skill_castfix (skill.c:17176, #ifndef RENEWAL_CAST)
    cast_times = skill_data.get("cast_time") or []
    base_cast: int = cast_times[lv_idx] if lv_idx < len(cast_times) else 0

    cast_time_options: list = skill_data.get("cast_time_options") or []
    ignore_dex: bool = "IgnoreDex" in cast_time_options

    if base_cast == 0:
        effective_cast = 0
    elif ignore_dex:
        # CastTimeOptions.IgnoreDex: true → skip DEX reduction entirely (skill.c:17180)
        effective_cast = base_cast
    else:
        # DEX reduction (skill.c:17181):
        #   scale = castrate_dex_scale - dex
        #   if scale > 0: time = time * scale / castrate_dex_scale
        #   else: return 0  (instant cast when dex >= scale)
        scale = _CASTRATE_DEX_SCALE - status.dex
        effective_cast = base_cast * max(0, scale) // _CASTRATE_DEX_SCALE

    # Global gear castrate — sd->castrate = 100 + gear_bonuses.castrate
    # Applied when !(castnodex & 4) (default for most skills). (skill.c:~17197; pc.c:2639)
    if gear_bonuses.castrate != 0:
        effective_cast = effective_cast * (100 + gear_bonuses.castrate) // 100

    # Per-skill castrate — bonus2 bCastrate,skill_name,val (pc.c:3607)
    per_skill_cr = gear_bonuses.skill_castrate.get(skill_name, 0)
    if per_skill_cr != 0:
        effective_cast = effective_cast * (100 + per_skill_cr) // 100

    # SC_POEMBRAGI val2: cast time reduction % (skill.c:17252)
    # StatusCalculator already computes this as status.cast_time_reduction_pct.
    if status.cast_time_reduction_pct and effective_cast > 0:
        effective_cast -= effective_cast * status.cast_time_reduction_pct // 100

    # SC_SUFFRAGIUM val2: 15×lv % reduction (status.c:8485; skill.c:17244)
    # Consumed on cast — treated as always active for the cast being evaluated.
    suf_lv = int(support_buffs.get("SC_SUFFRAGIUM", 0))
    if suf_lv > 0 and effective_cast > 0:
        effective_cast -= effective_cast * (15 * suf_lv) // 100

    effective_cast = max(effective_cast, 0)

    # ── After-cast delay ──────────────────────────────────────────────────────
    # skill_delay_fix (skill.c:17414)
    delays = skill_data.get("after_cast_act_delay") or []
    base_delay: int = delays[lv_idx] if lv_idx < len(delays) else 0

    # Monk combo AGI/DEX reduction (skill.c:17437):
    #   time -= (4 * agi + 2 * dex)
    if skill_name in _MONK_COMBO_SKILLS:
        base_delay -= 4 * status.agi + 2 * status.dex

    # SC_POEMBRAGI val3: ACD reduction % (skill.c:17486)
    # StatusCalculator already computes this as status.after_cast_delay_reduction_pct.
    if status.after_cast_delay_reduction_pct and base_delay > 0:
        base_delay -= base_delay * status.after_cast_delay_reduction_pct // 100

    # Global gear delayrate — sd->delayrate = 100 + gear_bonuses.delayrate (skill.c:~17506; pc.c:3020)
    if gear_bonuses.delayrate != 0:
        base_delay = base_delay * (100 + gear_bonuses.delayrate) // 100

    # min_skill_delay_limit = 100 ms (skill.conf:48)
    effective_delay = max(base_delay, _MIN_SKILL_DELAY_MS)

    return effective_cast, effective_delay
