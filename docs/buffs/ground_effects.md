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
**Calculator**: MaxHP does not affect damage output — UI toggle present, no pipeline step
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

## Known interactions — stubs

Ground elements (Volcano/Deluge/ViolentGale) also affect which element is "boosted"
by atk/matk attribute tables when the attacker or target stands in the field.
The exact interaction (field element vs. weapon element vs. skill element) needs
Hercules trace before implementing. Deferred.

---

## Implementation status

| SC | Formula | Calculator | GUI |
|----|---------|-----------|-----|
| SC_VOLCANO | confirmed (status.c:7780, 4570) | base_damage.py (Session O) | buffs_section Ground Effects combo |
| SC_DELUGE | confirmed (status.c:7793, 5768; skill.c:25192) | N/A — MaxHP only, no damage effect | buffs_section Ground Effects combo |
| SC_VIOLENTGALE | confirmed (status.c:7786, 4871) | status_calculator.py (Session O) | buffs_section Ground Effects combo |
