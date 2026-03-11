# PS_Calc — ASPD Investigation Notes
_Session C + verification pass. Source: Hercules/src/map/status.c, skill.c._

---

## The Three ASPD Functions — What They Do

### status_base_amotion_pc (line 3662)

Computes the raw base amotion (delay) before SC modifiers.

```c
#ifdef RENEWAL_ASPD
    // ... complex renewal formula using floats ...
#else
    // PRE-RENEWAL PATH (status.c:3699-3701):
    // Single weapon:
    amotion = aspd_base[job][weapontype];
    // Dual-wield (sd->weapontype > MAX_SINGLE_WEAPON_TYPE):
    amotion = (aspd_base[job][weapontype1] + aspd_base[job][weapontype2]) * 7 / 10;

    amotion -= amotion * (4*agi + dex) / 1000;  // stat reduction
    amotion += sd->bonus.aspd_add;  // flat bAspd bonus
    // Angra Manyu: return 0
#endif
return amotion;
```

#### Dual-Wield ASPD (G52-cont — implemented)

For Assassin / Assassin Cross (`_DUAL_WIELD_JOBS = {12, 4013}`) with a LH weapon equipped,
the base amotion is **(aspd_base[RH_type] + aspd_base[LH_type]) × 7 / 10** — NOT just aspd_base[RH].

Source: `status.c:3699-3701` (`#else`, not `RENEWAL_ASPD`):
```c
amotion = (sd->weapontype < MAX_SINGLE_WEAPON_TYPE)
    ? aspd_base[class][weapontype]                                       // single weapon
    : (aspd_base[class][weapontype1] + aspd_base[class][weapontype2]) * 7 / 10;  // dual-wield
```

The ×7/10 factor is the inherent ASPD penalty for swinging two weapons simultaneously.
SC_ASSNCROS, AS_RIGHT/AS_LEFT, and stat reductions apply on top of this base.
Implemented in `status_calculator.py` ASPD block (detects dual-wield from `job_id` + LH item).

### status_calc_aspd (line 5431) — RENEWAL_ASPD ONLY, returns 0 pre-renewal

**CONFIRMED**: Entire body is inside `#ifdef RENEWAL_ASPD`. The `#else` branch is `return 0`.

```c
static short status_calc_aspd(struct block_list *bl, struct status_change *sc, short flag)
{
#ifdef RENEWAL_ASPD
    // flag&1: fixed values — bonus = 7 for TWOHANDQUICKEN/ONEHANDQUICKEN/ADRENALINE/SPEARQUICKEN
    // flag&2: percentage values
    return (bonus + pots);
#else
    return 0;  // <-- PRE-RENEWAL ALWAYS RETURNS THIS
#endif
}
```

The `bonus = 7` for quicken SCs is **Renewal ASPD only**. It has no effect pre-renewal.

### status_calc_aspd_rate (line 5587) — NO RENEWAL GUARD, runs pre-renewal

```c
/// Note that the scale of aspd_rate is 1000 = 100%.
static short status_calc_aspd_rate(..., int aspd_rate)
```

Takes `max` of active SC val2/val3 values, subtracts from `aspd_rate`.
Result is applied as: `amotion = amotion * aspd_rate / 1000`.

This is the correct pre-renewal SC-ASPD function.

---

## Pre-Renewal PC ASPD Flow (confirmed from status_calc_sc_, ~line 3335)

```c
// status.c ~line 3335
amotion = status->base_amotion_pc(sd, st);          // raw amotion from stats+table

#ifndef RENEWAL_ASPD
st->aspd_rate = status->calc_aspd_rate(bl, sc, bst->aspd_rate);  // apply SC reductions
#endif

if (st->aspd_rate != 1000)
    amotion = amotion * st->aspd_rate / 1000;        // scale amotion by rate
```

`bst->aspd_rate` starts at 1000 (set in status_calc_pc_) and is already reduced by
passive skills (`#ifndef RENEWAL_ASPD` block at ~line 2115):
- SA_ADVANCEDBOOK (Book): `-5 * skill_lv`
- SG_DEVIL (Star Gladiator, maxed): `-30 * skill_lv`
- GS_SINGLEACTION (Gunslinger): `-((skill_lv+1)/2) * 10`
- Riding Peco: `+500 - 100 * KN_CAVALIERMASTERY`

`status_calc_aspd` (the `bonus=7` function) is **not called** in the pre-renewal PC path.
It only appears inside `#ifdef RENEWAL_ASPD` at line 3353.

---

## SC Values for status_calc_aspd_rate (1000-scale)

Confirmed from status_change_start (~line 7811-7823):
- `SC_ONEHANDQUICKEN`: val2 = 300
- `SC_TWOHANDQUICKEN`: val2 = 300
- `SC_SPEARQUICKEN`: val2 = 200 + 10 × val1 (level-dependent, `#ifndef RENEWAL_ASPD`)
- `SC_ADRENALINE`: val3 = (val2) ? 300 : 200 — val2=1 = self/Blacksmith (300), val2=0 = party (200)
- `SC_ASSNCROS`: val2 = see formula below

### SC_ASSNCROS val2 formula (confirmed from skill.c lines 13296-13307 + 14277)

`skill_unitsetting` (skill.c line 13072) computes for BA_ASSASSINCROSS:

```c
// #else (pre-renewal):
val1 = pc->checkskill(sd, BA_MUSICALLESSON) / 2;
val1 += 10 + skill_lv + (bard_st->agi / 10);  // ASPD increase
val1 *= 10;  // scale to 1000 = 100%
```

This `val1` becomes the skill group's `sg->val1`. When the SC is applied to a target
stepping into the song area (`skill_unit_onplace_timer`, line 14277):

```c
tsc->data[SC_ASSNCROS]->val2 = sg->val1;
```

So: **`SC_ASSNCROS val2 = (MusicalLesson_lv/2 + 10 + song_lv + bard_agi/10) * 10`**
(1000-scale; e.g. Bard AGI=99, song lv=10, MusLesson=10 → (5+10+10+9)*10 = 340)

Weapon restriction (same in both ASPD functions, status.c lines 5638-5645):
NOT applied to W_BOW / W_REVOLVER / W_RIFLE / W_GATLING / W_SHOTGUN / W_GRENADE.

---

## Current Implementation (Sessions C, N, G52-cont)

File: `core/calculators/status_calculator.py` ASPD block.

```python
# Uses status_calc_aspd_rate approach (1000-scale):
sc_aspd_reduction = max(active SCs' reduction values)
amotion = amotion * (1000 - sc_aspd_reduction) // 1000
```

Values used:
- SC_TWOHANDQUICKEN: 300  (confirmed correct by user testing)
- SC_ONEHANDQUICKEN: 300
- SC_ADRENALINE:     300  (self-cast assumed; party = 200 — not distinguished)
- SC_SPEARQUICKEN:   200 + 10 × level  (level from active_status_levels)
- SC_ASSNCROS:       NOT IMPLEMENTED (deferred — needs party buff UI)

---

## Known Inaccuracies / Deferred Items

### SC_ADRENALINE — weapon restriction not enforced
Hercules checks `pc_check_weapontype(sd, skill->get_weapontype(BS_ADRENALINE))` at line
7227. Only axe and mace weapon types receive the ASPD bonus. The current implementation
applies the bonus regardless of weapon type. The user must select Adrenaline Rush
responsibly until this is enforced.

### SC_ADRENALINE — self vs party amount
`val3 = (val2) ? 300 : 200`. Party members receive a smaller bonus (200 vs 300).
Current implementation always uses 300. A separate "party Adrenaline" toggle would be
needed to support this properly.

### SC_ASSNCROS — requires party buff UI
Formula is now confirmed (see above). Requires a separate user input for Bard's AGI
and song level, which fits the Party Buffs section, not Self Buffs. Deferred until
party buff input is designed.
The SC_ASSNCROS checkbox in passive_section.py currently does nothing in the calculation.

---

## GUI Display — ASPD Should Show Decimals

Currently `status.aspd = (2000 - amotion) // 10` (integer division) — discards the
fractional part, so e.g. amotion=147 shows as `185` instead of `185.3`.

Fix requires two changes:
1. `status_calculator.py`: store `status.aspd = (2000 - amotion) / 10` (float, not `//`)
   and change `StatusData.aspd` field type from `int` to `float`.
2. `gui/sections/derived_section.py`: format as `f"{status.aspd:.1f}"` instead of `str(int(...))`.

Tracked as G42 in gaps.md.

---

## DPS Formula (confirmed 2026-03-11)

`status.aspd` stores the display value: `(2000 - amotion) / 10` (float, e.g. 185.3).

```python
amotion          = 2000 - status.aspd * 10          # ms unit used internally
attacks_per_sec  = 500.0 / amotion                  # = 1000 / (amotion * 2)
```

**Derivation:** The actual attack interval is `adelay = amotion * 2`. User-confirmed:
190 ASPD → amotion = 100 → adelay = 200ms → 5 hits/s. ✓

**Correct DPS formula** — ratio of expected damage to expected time per attack cycle:

```
dps = Σ(chance_i × avg_damage_i) / Σ(chance_i × (pre_delay_i + post_delay_i))
```

Do NOT use `Σ(chance_i × dps_i)` — mathematically incorrect when delays differ
between attack types (e.g. a normal auto-attack vs a skill with a cast time).

For a plain auto-attack: `pre_delay = 0`, `post_delay = adelay = amotion * 2`.

TF_DOUBLE and GS_CHAINACTION set `wd.type = BDT_MULTIHIT` and stay within the same
attack action — their `post_delay` is the same auto-attack `adelay`. The formula
therefore reduces to `Σ(chance_i × damage_i) / adelay * 1000` for these specific procs.

Not all auto-attack procs share the same delay. MO_TRIPLEATTACK (Monk) fires as a
skill with its own action delay, not the base auto-attack adelay — it requires a
separate `AttackDefinition` with its own `post_delay` value. Never assume equal delays
across proc types; always use the delay that applies to each specific attack action.

Crit and proc are mutually exclusive — confirmed from battle.c:4926:
`wd.type != BDT_MULTIHIT` gates the crit check. When a double-hit proc fires
(sets BDT_MULTIHIT), the crit check is skipped entirely.

**Architecture** — implemented in Session G54 via `AttackDefinition` +
`SelectionStrategy` abstraction (see `core/models/attack_definition.py`,
`core/calculators/dps_calculator.py`). The strategy pattern is the seam
for a future Markov Chain model: `FormulaSelectionStrategy` (stateless,
chance values treated as steady-state weights) will be replaced by
`MarkovSelectionStrategy` (eigenvector solution over state graph) without
changing the DPS calculator or any call sites.

---

## Remaining Open Items

1. Consider making SC_ADRENALINE weapon-type-aware (restrict to axe/mace) when the
   calculator gains weapon-type-aware buff display in a future session.

2. SC_ASSNCROS implementation deferred until Party Buffs UI is designed.
   Formula confirmed — no further Hercules research needed.
