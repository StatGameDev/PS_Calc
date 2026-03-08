# PS_Calc — Stat Food & Consumable Buffs

_Sources: Hercules/src/map/status.c (stat calculation functions)_
_Confidence: [explore] = Explore agent finding with line ref; [stub] = not yet researched_

> **Stub notice**: SC keys and approximate line references are from the Explore agent pass.
> Verify exact formulas before implementing. This document will be expanded once
> the full consumable list is provided.

---

## Overview

Stat foods and consumables apply flat bonuses to base stats or derived combat stats
via SC_ status conditions. Unlike skill buffs, these typically have no level scaling —
they apply a fixed value from `val1` directly to the stat.

**Current home**: flat stat bonuses from consumables are already handled by the
`active_items_bonuses` dict (G46 Active Items section) as per-stat spinboxes.
Whether foods get their own dedicated section or stay in G46 is an open question
(see README.md design notes).

---

## Base Stat Foods

All apply `stat += val1` where `val1` is fixed per-item. No level formula.

| SC key | Stat | Explore ref | Notes |
|--------|------|-------------|-------|
| SC_FOOD_STR | STR | status.c ~3900 | flat +val1 |
| SC_INCSTR | STR | status.c ~3900 | same stat, different source (skill-like) |
| SC_FOOD_AGI | AGI | status.c ~4013–4014 | flat +val1 |
| SC_INCAGI | AGI | status.c ~4011–4012 | skill-like source |
| SC_FOOD_VIT | VIT | status.c ~4076–4077 | flat +val1 |
| SC_INCVIT | VIT | status.c ~4074–4075 | skill-like source |
| SC_FOOD_INT | INT | status.c ~4132–4133 | flat +val1 |
| SC_INCINT | INT | status.c ~4130–4131 | skill-like source |
| SC_FOOD_DEX | DEX | status.c ~4201–4202 | flat +val1 |
| SC_INCDEX | DEX | status.c ~4199–4200 | skill-like source |
| SC_FOOD_LUK | LUK | status.c ~4267–4268 | flat +val1 |
| SC_INCLUK | LUK | status.c ~4265–4266 | skill-like source |
| SC_INCALLSTATUS | All 6 | status.c ~4072–4264 | +val1 to every base stat |

**Stacking**: SC_FOOD_* and SC_INC* apply to the same stat but are separate SC slots.
Whether they stack or which takes priority: [stub] — verify from Hercules.

---

## Derived Combat Stat Foods

| SC key | Stat | Explore ref | Notes |
|--------|------|-------------|-------|
| SC_FOOD_BASICHIT | HIT | status.c ~4799–4800 | flat +val1 |
| SC_FOOD_BASICAVOIDANCE | FLEE | status.c ~4864–4865 | flat +val1 |
| SC_FOOD_CRITICALSUCCESSVALUE | CRI | status.c ~4751–4752 | flat +val1 (10× scale?) |

---

## MATK Foods (pre-renewal, #ifndef RENEWAL)

| SC key | Explore ref | Formula |
|--------|-------------|---------|
| SC_MATKFOOD | status.c ~4681–4682 | `matk += val1` |
| SC_PLUSMAGICPOWER | status.c ~4679–4680 | `matk += val1` |

---

## Known consumable items — stubs

Specific item IDs and their SC assignments: [stub] — awaiting item list.
Examples expected: various stat-food items, Berserk Potion (ASPD), etc.

---

## Implementation status

All entries: formula not directly verified, calculator not started, GUI not started.
Currently covered via G46 Active Items spinboxes (per-stat flat bonus — covers
SC_FOOD_* and SC_INC* transparently without tracking the SC key).
