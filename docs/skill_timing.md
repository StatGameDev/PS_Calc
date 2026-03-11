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

After the DEX and gear steps, `skill_castfix_sc` (skill.c:17227) applies SC-based modifiers
on top. See the **SC-Based Cast Time Modifiers** section below.

The gear `sd->castrate` step: if `!(castnodex & 4)` and `sd->castrate != 100`:
```c
time = time * sd->castrate / 100;   // skill_castfix ~line 17197
```
`sd->castrate` starts at 100; item scripts accumulate via `bonus bCastrate, val` (negative = faster).
In pre-renewal `SP_VARCASTRATE` also maps to `sd->castrate` (pc.c:2639, `#ifndef RENEWAL_CAST`).

---

---

## SC-Based Cast Time Modifiers — skill_castfix_sc (skill.c:17227)

Applied after DEX reduction and gear `sd->castrate`, before the cast timer is set.
All SCs below are pre-renewal unless noted.

| SC | val formula | Effect in skill_castfix_sc | Notes |
|---|---|---|---|
| SC_SLOWCAST | val2 = 20×lv (status.c:8458) | `time += time * val2 / 100` | Increases cast time |
| SC_NEEDLE_OF_PARALYZE | val3 = flat ms | `time += val3` | Flat ms increase |
| SC_SUFFRAGIUM | val2 = 15×lv (status.c:8485) | `time -= time * val2 / 100` | % reduction; **consumed on cast** (status_change_end called) |
| SC_MEMORIZE | val2 = 5 (charges, status.c:8149) | `time >>= 1` (halves) | Decrements val2; ends when val2 = 0 |
| SC_POEMBRAGI | val2 = 3×lv + bard_dex/10 (songs_dances.md) | `time -= time * val2 / 100` | % reduction; val2 = cast reduction |
| SC_SKF_CAST | val1 = % | `time -= time * val1 / 100` | Special SC — appears renewal-adjacent; skip |
| SC_IZAYOI | — | `time -= time * 50 / 100` | Kagerou/Oboro — **not pre-renewal**; skip |

Application order (multiplied sequentially, not summed): DEX → gear castrate → SC_SLOWCAST →
SC_NEEDLE_OF_PARALYZE → SC_SUFFRAGIUM → SC_MEMORIZE → SC_POEMBRAGI → SC_SKF_CAST.

Result floored at 0 (`max(time, 0)` at end of skill_castfix_sc).

### SD->castrate — Gear/Item Cast Rate Bonus

`sd->castrate` accumulates from item script bonuses (pc.c:2639). In pre-renewal,
both `bonus bCastrate, val` and `bonus bVariableCastrate, val` write to this field:

```c
// pc.c:2639 (#ifndef RENEWAL_CAST case SP_VARCASTRATE falls through to SP_CASTRATE)
sd->castrate += val;
```

Starting value: 100. Examples from pre-renewal item DB:
- `bonus bCastrate,-20` → castrate = 80 → cast time × 80/100 = −20% cast
- `bonus bCastrate,-3` → −3% (common on many staffs/accessories)

**Per-skill castrate** — `bonus2 bCastrate, skill_id, val` (pc.c:3607):
- Stored in `sd->skillfixcastrate[]` array, separate from `sd->castrate`
- Reduces cast time for that skill only (e.g. Holy Staff: AL_HOLYLIGHT −25%)
- Applied in skill_castfix alongside `sd->castrate` step (same guarded block)
- Not yet parsed by item_script_parser.py; stub at 0 for now

### SD->delayrate — Gear/Item After-Cast Delay Rate Bonus

`sd->delayrate` accumulates from item scripts via `bonus bDelayrate, val` (pc.c:3020).
Applied in `skill_delay_fix` when `!(delaynodex & 4)`:

```c
time = time * sd->delayrate / 100;   // skill_delay_fix ~line 17506
```

Starting value: 100. Examples from pre-renewal item DB:
- `bonus bDelayrate,-15` → delayrate = 85 → delay × 85/100 = −15%
- `bonus bDelayrate,-(getrefine()*3/2)` → refine-dependent reduction

Not yet in GearBonuses; stub at 100 for now.

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

    # gear sd->castrate (pc.c:2639; skill.c ~17197) — global % reduction
    castrate = 100 + gear_bonuses.castrate  # gear_bonuses.castrate is sum of bCastrate vals
    if castrate != 100:
        effective_cast = effective_cast * castrate // 100
    # per-skill castrate (bonus2 bCastrate, skill_id) — not yet in GearBonuses; stub

    # SC_POEMBRAGI val2 cast reduction (skill.c:17252)
    poem_lv = support_buffs.get("SC_POEMBRAGI", 0)
    if poem_lv and effective_cast > 0:
        val2 = 3 * bard_lv + bard_dex // 10  # see songs_dances.md; +2×MusicalLesson if applicable
        effective_cast -= effective_cast * val2 // 100

    # SC_SUFFRAGIUM val2 cast reduction (status.c:8485; skill.c:17244) — consumed on cast
    suf_lv = support_buffs.get("SC_SUFFRAGIUM", 0)
    if suf_lv and effective_cast > 0:
        val2 = 15 * suf_lv
        effective_cast -= effective_cast * val2 // 100
    # SC_MEMORIZE: halves cast time, 5 charges — rare, omit for now

    effective_cast = max(effective_cast, 0)

    # --- After-cast delay (skill_delay_fix, skill.c:17414) ---
    base_delay = (skill_entry["after_cast_act_delay"] or [0])[lv_idx]
    _MONK_COMBO_SKILLS = {
        "MO_TRIPLEATTACK", "MO_CHAINCOMBO", "MO_COMBOFINISH",
        "CH_TIGERFIST", "CH_CHAINCRUSH",
    }
    if skill_name in _MONK_COMBO_SKILLS:
        base_delay -= (4 * status.agi + 2 * status.dex)

    # SC_POEMBRAGI val3 delay reduction (skill.c:17486)
    if poem_lv and base_delay > 0:
        val3 = (3 * bard_lv if bard_lv < 10 else 50) + bard_int // 5  # +2×MusicalLesson if applicable
        base_delay -= base_delay * val3 // 100

    # gear sd->delayrate (pc.c:3020; skill.c ~17506)
    delayrate = 100 + gear_bonuses.delayrate  # gear_bonuses.delayrate is sum of bDelayrate vals
    if delayrate != 100:
        base_delay = base_delay * delayrate // 100

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

All SC formulas and gear modifier mechanics are **confirmed from source** (see above).
What is missing is the wiring into GearBonuses / calculate_skill_timing():

| Item | Source | Status | Notes |
|---|---|---|---|
| `sd->castrate` global gear bonus | pc.c:2639; skill.c ~17197 | Confirmed formula; not in GearBonuses/parser | `bonus bCastrate,val`; pre-renewal `bVarCastrate` identical |
| `sd->castrate` per-skill (bonus2) | pc.c:3607–3620 | Confirmed; not parsed | `bonus2 bCastrate,skill_id,val`; stored in `skillfixcastrate[]` |
| `sd->delayrate` gear bonus | pc.c:3020; skill.c ~17506 | Confirmed formula; not in GearBonuses/parser | `bonus bDelayrate,val` |
| SC_SUFFRAGIUM cast reduction | status.c:8485; skill.c:17244 | Confirmed (val2=15×lv, consumed on cast) | Not in support_buffs yet; Session Q0 |
| SC_MEMORIZE cast halving | status.c:8149; skill.c:17247 | Confirmed (5 charges, halves) | Not in support_buffs yet; rare |
| SC_SLOWCAST cast increase | status.c:8458; skill.c:17237 | Confirmed (val2=20×lv) | Debuff — not a player buff; display-only note |
| SC_POEMBRAGI val2 (cast) wiring | songs_dances.md; skill.c:17252 | Confirmed formula; not wired into timing calc yet | Wire in Q0 |
| SC_POEMBRAGI val3 (delay) wiring | songs_dances.md; skill.c:17486 | Confirmed formula; not wired into timing calc yet | Wire in Q0 |
| Soul Linker CR_SHIELDBOOMERANG / AS_SONICBLOW delay halving | skill.c:17480 | Confirmed; Spirit buffs not implemented | Deferred |
| `cool_down` field | skill_db.conf | Data in skills.json; not used in DPS | Affects next-use time independently of ACD |
