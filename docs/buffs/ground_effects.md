# PS_Calc — Ground / Zone AoE Buff Effects

_Sources: Hercules/src/map/skill.c (skill_unitsetting), status.c_
_Confidence: [confirmed] = directly read; [explore] = Explore agent finding; [stub] = not researched_

> **Stub notice**: Most entries here need direct Hercules grep before implementing.
> This document will be expanded once the full skill list is provided.

---

## Overview

Ground effects are AoE skills that create a persistent field on the ground. Units
standing in the field receive the buff (or debuff). Unlike songs, these have no
caster-stat formulas — the effect is determined solely by skill level.

For the calculator, these are modelled as toggles (bool) since the player either
stands in the field or does not.

---

## Sage / Scholar Ground Elements — SA_*

### SA_VOLCANO → SC_VOLCANO [confirmed]

**Effect**: flat WATK bonus while standing on Fire-element ground
**Formula**: `val2 = skill_lv * 10; watk += val2`
**Hercules ref**: status.c:7780 (init: `val2 = val1*10`); status.c:4569-4570 (apply: `watk += sc->data[SC_VOLCANO]->val2`)
**Pre-renewal guard**: `#ifndef RENEWAL` — if player armor element ≠ Fire, val2 = 0 (status.c:7781-7783)
**Calculator**: user's responsibility to apply only with matching armor element
**Inputs**: QComboBox (Volcano selected) + level QSpinBox 1–5

---

### SA_DELUGE → SC_DELUGE [confirmed]

**Effect**: MaxHP% bonus while standing on Water-element ground
**Formula**: `val2 = deluge_eff[skill_lv-1]` = {5, 9, 12, 14, 15}%; `maxhp += maxhp * val2 / 100`
**Hercules ref**: status.c:7793-7799 (init); status.c:5768-5769 (apply); skill.c:25192 (deluge_eff table)
**Pre-renewal guard**: `#ifndef RENEWAL` — if player armor element ≠ Water, val2 = 0 (status.c:7795-7797)
**Calculator**: MaxHP is a build stat — implemented in status_calculator.py (Session O fix)
**Inputs**: QComboBox (Deluge selected) + level QSpinBox 1–5

---

### SA_VIOLENTGALE → SC_VIOLENTGALE [confirmed]

**Effect**: flat FLEE bonus while standing on Wind-element ground
**Formula**: `val2 = skill_lv * 3; flee += val2`
**Hercules ref**: status.c:7786-7790 (init: `val2 = val1*3`); status.c:4870-4871 (apply: `flee += sc->data[SC_VIOLENTGALE]->val2`)
**Pre-renewal guard**: `#ifndef RENEWAL` — if player armor element ≠ Wind, val2 = 0 (status.c:7788-7790)
**Calculator**: user's responsibility to apply only with matching armor element
**Inputs**: QComboBox (Violent Gale selected) + level QSpinBox 1–5

---

## Ensemble Ground Effects

Ensemble songs already documented in [songs_dances.md](songs_dances.md):
- BD_DRUMBATTLEFIELD → SC_DRUMBATTLE (WATK + DEF)
- BD_RINGNIBELUNGEN → SC_NIBELUNGEN (WATK)
- BD_SIEGFRIED → SC_SIEGFRIED (all elemental resistance)

---

## Ninja Ground Effects

### NJ_KAENSIN → fire AoE ground [explore]

Hostile AoE — deals fire damage to enemies stepping in. Not a player buff.
Not relevant to this calculator.

### NJ_SUITON → water AoE ground [explore]

Hostile AoE — slows movement of enemies. Not a player buff.
Not relevant to this calculator.

---

## Priest Ground Effects

### PR_SANCTUARY [stub]

HP regen on ground. Not a combat stat modifier.
Not relevant to damage calc. Out of scope.

### PR_MAGNUS [stub]

Deals Holy damage to undead on ground. Hostile skill, not a buff. Out of scope.

---

## Ground Element Attack Amplification [confirmed]

All three SCs also amplify attacks whose element matches the ground element.
This is applied in `battle_attr_fix` by adding to the elemental `ratio` before
the damage multiplier is applied.

**Formula**: `ratio += enchant_eff[skill_lv - 1]`
**Table** (`enchant_eff`, skill.c:25191): {10, 14, 17, 19, 20} percentage points
**Condition**: `atk_elem == ELE_FIRE` (Volcano) / `ELE_WATER` (Deluge) / `ELE_WIND` (ViolentGale)
**Hercules ref**: battle.c:395-400 (inside `battle_attr_fix`); skill.c:25191

**No armor element check** on the amplification — only the weapon/skill attack element matters.
The armor element check (val2=0 if armor ≠ ground element) applies only to the stat bonuses
(WATK/FLEE/MaxHP), NOT to the ratio amplification.

**Calculator**: implemented in `attr_fix.py` — `build` passed in from `battle_pipeline.py`.
Produces a separate DamageStep before the Attr Fix step.

---

## Implementation status

| SC | Formula | Calculator | GUI |
|----|---------|-----------|-----|
| SC_VOLCANO | confirmed (status.c:7780, 4570; battle.c:395; skill.c:25191) | base_damage.py (WATK) + attr_fix.py (ratio+enchant when atk=Fire) | Ground Effects combo |
| SC_DELUGE | confirmed (status.c:7793, 5768; skill.c:25192; battle.c:399) | status_calculator.py (MaxHP) + attr_fix.py (ratio+enchant when atk=Water) | Ground Effects combo |
| SC_VIOLENTGALE | confirmed (status.c:7786, 4871; battle.c:397; skill.c:25191) | status_calculator.py (FLEE) + attr_fix.py (ratio+enchant when atk=Wind) | Ground Effects combo |
