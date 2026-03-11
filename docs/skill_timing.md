# PS_Calc — Skill Timing Investigation Notes
_Researched 2026-03-11. Source: Hercules/src/map/skill.c, unit.c, status.c, conf/map/battle/skill.conf._

---

## Overview

Three quantities control how quickly a player can repeat a skill or auto-attack:

| Quantity | Meaning | Set by |
|---|---|---|
| `amotion` | Animation motion — time until damage is applied after swing/cast | status_calc_pc_ |
| `adelay` | Attack delay — minimum time between consecutive auto-attacks | status_calc_pc_ |
| `canact_tick` | Earliest tick at which the next **skill** can be cast | unit_skilluse_id2 + skill_castend_id |

For players: **`adelay = 2 × amotion`** (status.c:2134).
This is the "half ASPD" effect: skills always have a shorter minimum reuse time than auto-attacks.

---

## amotion vs adelay

```c
// status.c:2112
bstatus->amotion = cap_value(i, pc_max_aspd(sd), 2000);
// status.c:2134
bstatus->adelay = 2 * bstatus->amotion;
```

`amotion` is what ASPD buffs/passives actually modify (via `aspd_rate` 1000-scale).
`adelay` is derived from it, always 2× for PCs (mobs differ).

In the current implementation `StatusData.aspd` stores the display value `(2000 - amotion) / 10`.
To recover `amotion` in ms: `amotion = int(2000 - status.aspd * 10)`.

---

## Cast Time — skill_castfix (skill.c:17176, `#ifndef RENEWAL_CAST`)

```c
static int skill_castfix(struct block_list *bl, uint16 skill_id, uint16 skill_lv)
{
    int time = skill->get_cast(skill_id, skill_lv);  // from skill_db.conf CastTime[lv]

#ifndef RENEWAL_CAST
    // Step 1: DEX reduction (unless CastTimeOptions.IgnoreDex: true)
    if (!(skill->get_castnodex(skill_id, skill_lv) & 1)) {
        int scale = battle_config.castrate_dex_scale - status_get_dex(bl);
        if (scale > 0)
            time = time * scale / battle_config.castrate_dex_scale;
        else
            return 0;  // instant cast when dex >= castrate_dex_scale
    }

    // Step 2: gear/card castrate bonus (sd->castrate, %)
    if (!(skill->get_castnodex(skill_id, skill_lv) & 4) && sd) {
        if (sd->castrate != 100)
            time = time * sd->castrate / 100;
        // plus per-skill bCastrate bonuses
    }
#endif

    // Step 3: server config multiplier (default cast_rate = 100, no effect)
    if (battle_config.cast_rate != 100)
        time = time * battle_config.cast_rate / 100;

    return max(time, 0);
}
```

Key default (skill.conf:64): **`castrate_dex_scale = 150`**

**Pre-renewal cast time formula:**
```
effective_cast = cast_time[lv] × max(0, 150 - dex) / 150
```
- `dex ≥ 150` → instant cast (0 ms)
- `CastTimeOptions.IgnoreDex: true` in skill_db → skip DEX reduction entirely
- `sd->castrate` (not yet tracked in GearBonuses) — stub at 100 for now

SC-based cast reductions (`skill_castfix_sc`, skill.c:17227) also apply on top, including
SC_POEMBRAGI and item/food bonuses tracked under `sd->bonus.varcastrate`. These are applied
after `skill_castfix` returns, before the timer is set.

---

## After-Cast Action Delay — skill_delay_fix (skill.c:17414)

```c
static int skill_delay_fix(struct block_list *bl, uint16 skill_id, uint16 skill_lv)
{
    int time = skill->get_delay(skill_id, skill_lv);  // from skill_db.conf AfterCastActDelay[lv]

    if (time < 0)
        time = -time + status_get_amotion(bl);  // negative delay: add to amotion (rare)

    // Special reductions: Monk combo skills
    switch (skill_id) {
        case MO_TRIPLEATTACK:
        case MO_CHAINCOMBO:
        case MO_COMBOFINISH:
        case CH_TIGERFIST:
        case CH_CHAINCRUSH:
            time -= (4 * status_get_agi(bl) + 2 * status_get_dex(bl));
            break;
        // HP_BASILICA: 0 delay on creation only
        default:
            // delay_dependon_dex / delay_dependon_agi: both false by default (skill.conf:43-44)
            // So generic skills are NOT reduced by DEX/AGI
    }

    // SC_POEMBRAGI (if !(delaynodex & 2)):
    if (sc->data[SC_POEMBRAGI])
        time -= time * sc->data[SC_POEMBRAGI]->val3 / 100;

    // sd->delayrate (gear, not yet in GearBonuses):
    if (!(delaynodex & 4) && sd && sd->delayrate != 100)
        time = time * sd->delayrate / 100;

    // server config (default delay_rate = 100, no effect)
    if (battle_config.delay_rate != 100)
        time = time * battle_config.delay_rate / 100;

    return max(time, 0);  // min_skill_delay_limit = 100ms (skill.conf:48)
}
```

Key defaults:
- `delay_dependon_dex: false` (skill.conf:43) — delay NOT reduced by DEX generically
- `delay_dependon_agi: false` (skill.conf:44) — delay NOT reduced by AGI generically
- `min_skill_delay_limit: 100` ms (skill.conf:48)

**SC_POEMBRAGI** reduces `after_cast_act_delay` by `val3 %`. The val3 formula is confirmed
in docs/buffs/songs_dances.md. This is already implemented in the buff system.

---

## Minimum canact_tick — The "Half-ASPD" Floor

This is the critical mechanic: **both** target and ground-skill paths enforce a minimum
`canact_tick` of `amotion` at cast START (before the cast timer even fires).

```c
// unit.c:1846 (unit_skilluse_id2, target skills)
// unit.c:1986 (unit_skilluse_pos2, ground skills)
ud->canact_tick = tick + max(casttime, max(status_get_amotion(src), battle_config.min_skill_delay_limit));
```

Then at cast END, `canact_tick` can only move further out (skill.c:6527):
```c
ud->canact_tick = max(tick + skill->delay_fix(src, ud->skill_id, ud->skill_lv), ud->canact_tick);
```

Combining both updates, the total `canact_tick` offset from cast-start is:
```
canact_tick_offset = max(casttime + delay_fix(), max(amotion, 100))
```

---

## DPS Period Formula (combined result)

For skills, the period between consecutive uses (minimum time before next skill):

```
period = max(effective_cast + effective_delay, amotion)
```

where:
- `effective_cast` = `cast_time[lv] × max(0, 150 - dex) / 150`
- `effective_delay` = `after_cast_act_delay[lv]` after SC_POEMBRAGI / Monk combo reduction
- `amotion` = `int(2000 - status.aspd × 10)` ms
- `min_skill_delay_limit = 100` ms (irrelevant in practice since amotion > 100 for any real character)

Concrete examples (using skills.json data):

| Skill | cast_time[lv] | after_cast_act_delay[lv] | Example period (amotion=500ms) |
|---|---|---|---|
| SM_BASH lv1 | 0 | 0 | **500ms** (= amotion) |
| SM_MAGNUM any lv | 0 | 2000 | **2000ms** |
| KN_BRANDISHSPEAR lv1 | 700 (DEX-reduced) | 0 | **max(700×(150-dex)/150, 500)** |
| MO_EXTREMITYFIST lv1 | 4000 (DEX-reduced) | 3000 | **max(7000×..., 500)** |
| CR_SHIELDBOOMERANG any lv | 0 | 700 | **max(700, 500) = 700ms** |
| MO_FINGEROFFENSIVE lv1 | 1000 (DEX-reduced) | 500 | **max(1500×..., 500)** |

**For auto-attack (`skill_id == 0`):** period = `adelay = 2 × amotion`. Do NOT use amotion.

---

## Monk Combo Delay Reduction

MO_TRIPLEATTACK, MO_CHAINCOMBO, MO_COMBOFINISH, CH_TIGERFIST, CH_CHAINCRUSH:
```
effective_delay = max(after_cast_act_delay[lv] - (4×agi + 2×dex), 100)
```
(Confirmed skill.c:17437. The floor of 100ms from `min_skill_delay_limit` applies.)

These skills also override `canact_tick` via a separate combo path (skill.c:3424):
```c
sd->ud.canact_tick = max(tick + skill->delay_fix(src, MO_TRIPLEATTACK, skill_lv), sd->ud.canact_tick);
```
The combo system is deferred (see Deferred section in session_roadmap.md).

---

## Soul Linker Delay Reductions

From `skill_delay_fix` (skill.c:17480–17490):
```c
if (sc->data[SC_SOULLINK]) {
    case CR_SHIELDBOOMERANG:
        if (sc->data[SC_SOULLINK]->val2 == SL_CRUSADER) time /= 2;
    case AS_SONICBLOW:
        if (!gvg_or_bg && val2 == SL_ASSASIN)           time /= 2;
}
```
These halve the after-cast delay for those specific skills when the appropriate Spirit is active.
Not implemented yet — note for Session Q1.

---

## Data Available in skills.json

All timing fields are already scraped by `tools/import_skill_db.py` and present in
`core/data/pre-re/db/skills.json` (keyed by numeric string ID, name in `"name"` field):

| Field | Source in skill_db.conf | Stored as |
|---|---|---|
| `cast_time` | `CastTime` | `list[int]` per level, ms |
| `after_cast_act_delay` | `AfterCastActDelay` | `list[int]` per level, ms |
| `after_cast_walk_delay` | `AfterCastWalkDelay` | `list[int]` per level, ms |
| `cool_down` | `CoolDown` | `list[int]` per level, ms |
| `interrupt_cast` | `InterruptCast` | `bool` |
| `cast_time_options` | `CastTimeOptions` block | `list[str]` of true keys (e.g. `["IgnoreDex"]`) |
| `skill_delay_options` | `SkillDelayOptions` block | `list[str]` of true keys |

Skills not present in skill_db.conf (e.g. passive skills) have all timing fields as `[0, 0, ...]`.

Lookup by name: build `{entry["name"]: entry for entry in skills.values()}` (skills keyed by numeric string).

---

## Implementation Plan (Session Q0 — G56)

File: `core/calculators/dps_calculator.py` (or new `core/calculators/skill_timing.py`).

```python
def calculate_skill_timing(
    skill_name: str,
    skill_lv: int,
    status: StatusData,
    support_buffs: dict,
) -> tuple[int, int]:
    """
    Returns (effective_cast_ms, effective_delay_ms) for the given skill at the given level.
    Both values have the amotion floor applied externally in calculate_dps().
    Source: skill_castfix (skill.c:17176) + skill_delay_fix (skill.c:17414).
    """
    skill_entry = _get_skill_by_name(skill_name)  # lookup from skills.json
    lv_idx = skill_lv - 1

    # --- Cast time (skill_castfix, #ifndef RENEWAL_CAST, skill.c:17176) ---
    base_cast = (skill_entry["cast_time"] or [0])[lv_idx]
    ignore_dex = "IgnoreDex" in (skill_entry.get("cast_time_options") or [])
    if ignore_dex or base_cast == 0:
        effective_cast = base_cast
    else:
        dex = status.dex
        effective_cast = base_cast * max(0, 150 - dex) // 150
    # sd->castrate (gear) not yet tracked — stub at 100

    # --- After-cast delay (skill_delay_fix, skill.c:17414) ---
    base_delay = (skill_entry["after_cast_act_delay"] or [0])[lv_idx]
    _MONK_COMBO_SKILLS = {
        "MO_TRIPLEATTACK", "MO_CHAINCOMBO", "MO_COMBOFINISH",
        "CH_TIGERFIST", "CH_CHAINCRUSH",
    }
    if skill_name in _MONK_COMBO_SKILLS:
        base_delay -= (4 * status.agi + 2 * status.dex)
    # SC_POEMBRAGI reduction
    poem_lv = support_buffs.get("SC_POEMBRAGI", 0)
    if poem_lv and base_delay > 0:
        val3 = ...  # computed from Bard stats + poem level per songs_dances.md
        base_delay -= base_delay * val3 // 100
    effective_delay = max(base_delay, 100)  # min_skill_delay_limit

    return effective_cast, effective_delay
```

In `calculate_dps()`, replace the period for skills:
```python
amotion = int(2000 - status.aspd * 10)
if skill_id == 0:
    period = int(status.aspd_adelay)  # = 2 * amotion, auto-attack
else:
    cast_ms, delay_ms = calculate_skill_timing(skill_name, skill_lv, status, support_buffs)
    period = max(cast_ms + delay_ms, amotion)
```

---

## Known Gaps / Not Yet Implemented

| Item | Source | Notes |
|---|---|---|
| `sd->castrate` gear bonus | gear/card scripts | Not in GearBonuses yet; stub at 100 |
| `sd->delayrate` gear bonus | gear/card scripts | Not in GearBonuses yet; stub at 100 |
| Soul Linker CR_SHIELDBOOMERANG / AS_SONICBLOW halved delay | skill.c:17480 | Not tracked; Spirit buffs not implemented |
| SC_POEMBRAGI val3 derivation | songs_dances.md | val3 formula confirmed there; needs wiring |
| `cool_down` field (separate from `after_cast_act_delay`) | skill_db.conf | Not used in DPS yet; affects next-use time independently |
| Cast time SC reductions beyond POEMBRAGI (`skill_castfix_sc`) | skill.c:17227 | SC_WIND_INSIGNIA (renewal-adjacent), item bonuses — low priority |
