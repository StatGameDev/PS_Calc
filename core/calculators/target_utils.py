from __future__ import annotations

from core.models.target import Target


def apply_mob_scs(target: Target) -> None:
    """Apply stat modifications from target_active_scs to a mob Target.

    Called in _run_battle_pipeline() immediately after apply_to_target() has
    populated target.target_active_scs.  Mob targets are not run through
    StatusCalculator, so stat-cascade effects must be applied here via direct
    field mutation.  Player targets receive the same effects through
    StatusCalculator (fed via collect_target_player_scs() in TargetStateSection).

    Extend this function in Session SC1 with BLIND, CURSE, QUAGMIRE, etc.
    """
    scs = target.target_active_scs

    # SC_DECREASEAGI: agi -= 2+lv  (status.c:7633, 4025-4026)
    if "SC_DECREASEAGI" in scs:
        lv = int(scs["SC_DECREASEAGI"])
        target.agi = max(0, target.agi - (2 + lv))
