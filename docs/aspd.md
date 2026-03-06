# PS_Calc — ASPD Investigation Notes
_Session C. Source: Hercules/src/map/status.c. Revisit before claiming G9 complete._

---

## The Two ASPD Functions — What They Do

### status_base_amotion_pc (flag&1 branch, ~line 5440)

Returns `bonus + pots` — an integer representing SC/buff contributions to ASPD.
`bonus = 7` for SC_TWOHANDQUICKEN / SC_ONEHANDQUICKEN / SC_ADRENALINE / SC_SPEARQUICKEN
(these SCs all set `bonus = max(bonus, 7)` — only the highest applies, no stacking).
`return (bonus + pots)` at line 5559; `#else return 0; #endif` follows.

**Unknown**: The `#if/#else/#endif` guard around this function is unread. It may be
`#ifndef RENEWAL_ASPD` (pre-re returns bonus; renewal returns 0) or the reverse.
Without reading the guard, it is not known whether this function is the relevant
pre-renewal path or not.

**Unknown**: How the returned `bonus + pots` value is applied to `amotion` in
`status_calc_pc_`. Presumably: `amotion -= base_amotion * bonus / 100` (i.e. `bonus=7`
= 7% of base_amotion). But this is an inference, not confirmed from source.

### status_calc_aspd_rate (~line 5587)

Comment in source (line 5588): *"Note that the scale of aspd_rate is 1000 = 100%."*
Function: `static short status_calc_aspd_rate(struct block_list *bl, struct status_change *sc, int aspd_rate)`

Computes `max` of active SC val2/val3 values, then `aspd_rate -= max`.
Applied to amotion as: `amotion = amotion * aspd_rate / 1000`.

SC values confirmed from status_change_start (~line 7811-7823):
- `SC_ONEHANDQUICKEN`: val2 = 300
- `SC_TWOHANDQUICKEN`: val2 = 300
- `SC_SPEARQUICKEN`: val2 = 200 + 10 × val1 (level-dependent, `#ifndef RENEWAL_ASPD`)
- `SC_ADRENALINE`: val3 = (val2) ? 300 : 200  — val2=1 = self/Blacksmith (300), val2=0 = party (200)
- `SC_ASSNCROS`: val2 = f(Bard's AGI) — set by calling skill code, not status_change_start

---

## Current Implementation (Session C)

File: `core/calculators/status_calculator.py` lines 65-91.

```python
# Uses status_calc_aspd_rate approach (1000-scale):
sc_aspd_reduction = max(active SCs' reduction values)
amotion = amotion * (1000 - sc_aspd_reduction) // 1000
```

Values used:
- SC_TWOHANDQUICKEN: 300  ✓ (confirmed correct by user testing)
- SC_ONEHANDQUICKEN: 300
- SC_ADRENALINE:     300  (self-cast assumed; party = 200 — not distinguished)
- SC_SPEARQUICKEN:   200 + 10 × level  (level from active_status_levels)
- SC_ASSNCROS:       NOT IMPLEMENTED (deferred)

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

### SC_ASSNCROS — Bard's AGI dependency
Assassin's Cross of Sunset (BA_ASSASSINCROSS) is a Bard song. val2 is set by the
calling skill code in skill.c, not in status_change_start. Per user research:
> "Assassin cross song is a Buff Bard can generate, which has a value that depends on
> the Bard's Agi Stat. Most Bard Buffs depend on the Bard's stats and a Skill the Bard has."

This requires a separate user input (Bard's AGI and skill level) that fits the
Party Buffs section, not Self Buffs. Deferred until party buff input is designed.
The SC_ASSNCROS checkbox in passive_section.py currently does nothing in the calculation.

### flag&1 branch relationship to status_calc_aspd_rate
It is unresolved whether both functions apply for pre-renewal PCs (double-counting
the same SCs) or whether only one runs. If `status_base_amotion_pc` flag&1 branch
is renewal-only (returns 0 pre-re), then the current implementation using
`status_calc_aspd_rate` values is fully correct. If both run, the bonus from quicken
SCs is counted twice and must be reconciled.

Testing confirmed 30% reduction for SC_TWOHANDQUICKEN — consistent with
`status_calc_aspd_rate` val2=300, not with the flag&1 `bonus=7` (7%) approach.
This strongly suggests `status_calc_aspd_rate` is the correct pre-renewal function.

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

## What To Verify Next

1. Read `status_calc_pc_` in status.c to find:
   a. The `#if/#else` guard around `status_base_amotion_pc` return path
   b. Whether `status_calc_aspd_rate` is conditionally called for pre-renewal PCs
   c. How `(bonus + pots)` return value is applied to `amotion`

2. Read skill.c BA_ASSASSINCROSS to find SC_ASSNCROS val2 formula (Bard AGI input).
   Required before implementing Assassin's Cross song ASPD.

3. Consider making SC_ADRENALINE weapon-type-aware (restrict to axe/mace) if the
   calculator gains weapon-type-aware buff display in a future session.
