from __future__ import annotations

from typing import TYPE_CHECKING

from core.models.target import Target

if TYPE_CHECKING:
    from core.models.status import StatusData

# SC_COMMON (status.h:99-114): bosses are immune to all of these.
# Source: status.c:7472 (is_boss_resist_sc), status.c:10687 (is_boss_resist_sc fn)
_BOSS_IMMUNE_SCS = frozenset({
    "SC_STONE", "SC_FREEZE", "SC_STUN", "SC_SLEEP",
    "SC_POISON", "SC_CURSE", "SC_SILENCE", "SC_CONFUSION", "SC_BLIND",
})
# SCs with NoBoss flag — confirmed immune for bosses
# Source: db/pre-re/sc_config.conf, status.c:7472
_BOSS_IMMUNE_NOBOSS = frozenset({
    "SC_PROVOKE", "SC_DECREASEAGI",
})
_ALL_BOSS_IMMUNE = _BOSS_IMMUNE_SCS | _BOSS_IMMUNE_NOBOSS


def apply_mob_scs(target: Target) -> None:
    """Apply stat modifications from target_active_scs to a mob Target.

    Called in _run_battle_pipeline() immediately after apply_to_target() has
    populated target.target_active_scs.  Mob targets are not run through
    StatusCalculator, so stat-cascade effects must be applied here via direct
    field mutation.  Player targets receive the same effects through
    StatusCalculator (fed via collect_target_player_scs() in TargetStateSection).

    G81 — Boss Protocol: boss mobs are immune to SC_COMMON ailments and any SC
    with NoBoss flag.  Guarded per-SC below.
    Source: status.c:7472, status.h:99-114, db/pre-re/sc_config.conf.
    """
    scs = target.target_active_scs

    def _blocked(sc_key: str) -> bool:
        return target.is_boss and sc_key in _ALL_BOSS_IMMUNE

    # ── SC_DECREASEAGI: agi -= 2+lv  (status.c:7633, 4025-4026) ─────────────
    if "SC_DECREASEAGI" in scs and not _blocked("SC_DECREASEAGI"):
        lv = int(scs["SC_DECREASEAGI"])
        delta = 2 + lv
        target.agi  = max(0, target.agi  - delta)
        target.flee = max(0, target.flee - delta)  # flee = level+agi; propagate

    # ── SC_BLIND ─────────────────────────────────────────────────────────────
    # hit  -= hit  * 25 / 100  (status.c:4817)
    # flee -= flee * 25 / 100  (status.c:4903)
    if "SC_BLIND" in scs and not _blocked("SC_BLIND"):
        target.hit  = target.hit  - target.hit  * 25 // 100
        target.flee = target.flee - target.flee * 25 // 100

    # ── SC_CURSE: luk = 0  (status.c:4261-4262) ──────────────────────────────
    if "SC_CURSE" in scs and not _blocked("SC_CURSE"):
        target.luk = 0

    # ── SC_POISON: def_percent -= 25  (status.c:4431-4432, no guard) ─────────
    if "SC_POISON" in scs and not _blocked("SC_POISON"):
        target.def_percent = max(0, target.def_percent - 25)

    # ── SC_SLEEP: force-hit via opt1 (battle.c:5014); crit×2 (battle.c:4959)
    # No stat mutation here — handled in hit_chance.py and crit_chance.py via
    # target_active_scs flag.  Boss immune (SC_COMMON).

    # ── SC_QUAGMIRE ───────────────────────────────────────────────────────────
    # agi -= val2, dex -= val2; val2 = 10×lv for mobs (status.c:4027-4028, 4211-4212, 8343-8344)
    if "SC_QUAGMIRE" in scs:
        lv   = int(scs["SC_QUAGMIRE"])
        val2 = 10 * lv
        target.agi  = max(0, target.agi  - val2)
        target.dex  = max(0, target.dex  - val2)
        target.flee = max(0, target.flee - val2)  # propagate agi change
        target.hit  = max(0, target.hit  - val2)  # propagate dex change

    # ── SC_BLESSING debuff ───────────────────────────────────────────────────
    # str >>= 1, dex >>= 1; mob-only; only Undead element (9) or Demon race.
    # BL_PC is hard-blocked in Hercules (status.c:8271-8275).
    # Source: status.c:3964-3968 (str), 4213-4218 (dex), 8271-8275 (PC guard)
    if "SC_BLESSING" in scs:
        if target.element == 9 or target.race == "Demon":
            old_dex    = target.dex
            target.str = target.str >> 1
            target.dex = target.dex >> 1
            dex_delta  = old_dex - target.dex
            target.hit = max(0, target.hit - dex_delta)  # hit = level+dex; propagate

    # ── SC_CRUCIS ────────────────────────────────────────────────────────────
    # def -= def * val2 / 100; val2 = 10+4*lv  (status.c:7662-7664, 5022-5023)
    # Mob-only: Undead element (9) or Demon race; BL_PC hard-blocked (status.c:7205-7207)
    if "SC_CRUCIS" in scs:
        if target.element == 9 or target.race == "Demon":
            lv   = int(scs["SC_CRUCIS"])
            val2 = 10 + 4 * lv
            target.def_ = max(0, target.def_ - target.def_ * val2 // 100)

    # ── SC_PROVOKE ────────────────────────────────────────────────────────────
    # def_percent -= 5+5×lv  (status.c:4401-4402)
    # NoBoss flag — already in _BOSS_IMMUNE_NOBOSS (status.c:7472, sc_config.conf)
    if "SC_PROVOKE" in scs and not _blocked("SC_PROVOKE"):
        lv = int(scs["SC_PROVOKE"])
        target.def_percent = max(0, target.def_percent - (5 + 5 * lv))

    # ── SC_MINDBREAKER ───────────────────────────────────────────────────────
    # matk_percent += 20×lv  (status.c:4376-4377, 8379-8382)
    # mdef_percent -= 12×lv  (status.c:4453-4454, 8379-8382)
    if "SC_MINDBREAKER" in scs:
        lv = int(scs["SC_MINDBREAKER"])
        target.matk_percent = 100 + 20 * lv
        target.mdef_percent = max(0, 100 - 12 * lv)

    # ── SC_DONTFORGETME ──────────────────────────────────────────────────────
    # aspd_rate += 10 * val2  (status.c:5667)
    # val2 = caster_agi/10 + 3*lv + 5  (skill.c:13270 #else pre-renewal)
    # caster_agi stored alongside level in target_active_scs as "SC_DONTFORGETME_agi".
    if "SC_DONTFORGETME" in scs:
        lv         = int(scs["SC_DONTFORGETME"])
        caster_agi = int(scs.get("SC_DONTFORGETME_agi", 0))
        val2       = caster_agi // 10 + 3 * lv + 5
        target.aspd_rate += 10 * val2
        # NOTE: mob aspd_rate not consumed by any current pipeline calculation.
        # Stored for future incoming DPS modelling.
