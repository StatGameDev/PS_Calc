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

### SA_VOLCANO → SC_VOLCANO [explore]

**Effect**: flat WATK bonus while in the fire-element field
**Formula**: `watk += val2` — exact val2 formula [stub]
**Hercules ref**: status.c ~4569–4570
**Inputs needed**: checkbox

---

### SA_DELUGE → SC_DELUGE [explore]

**Effect**: MaxHP% bonus while in the water-element field
**Formula**: `maxhp += maxhp * val2 / 100` — exact val2 formula [stub]
**Hercules ref**: status.c ~4870–4871
**Inputs needed**: checkbox

---

### SA_VIOLENTGALE → SC_VIOLENTGALE [explore]

**Effect**: flat FLEE bonus while in the wind-element field
**Formula**: `flee += val2` — exact val2 formula [stub]
**Hercules ref**: status.c ~4870–4871, ~5667 (aspd penalty [explore] — verify)
**Inputs needed**: checkbox

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
| SC_VOLCANO | explore | not started | — |
| SC_DELUGE | explore | not started | — |
| SC_VIOLENTGALE | explore | not started | — |
