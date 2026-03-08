# PS_Calc — Weapon Element Endow Skills

_Sources: Hercules/src/map/skill.c, status.c_
_Confidence: [confirmed] = directly read; [explore] = Explore agent finding; [stub] = not researched_

---

## Overview

Endow skills assign an element to the player's right-hand weapon, overriding the
item's native element for the duration of the buff. In the calculator this maps to
`PlayerBuild.weapon_element` (field already exists, range 0–9).

All endow SCs are **mutually exclusive** — only one weapon element endow can be active
at a time (applying a new one cancels the previous).

**GUI**: single "Endow Element" dropdown, options: None + the 8 endow-able elements.

---

## Sage / Scholar Endow Skills — SA_*

These are the primary source of weapon endow in party play (Sage/Scholar casts on allies).

| Skill | SC key | Element assigned | Hercules ref |
|-------|--------|-----------------|--------------|
| SA_FLAMELAUNCHER | SC_PROPERTYFIRE | ELE_FIRE (4) | [explore] status.c:~5931, skill.c:~7240 |
| SA_FROSTWEAPON | SC_PROPERTYWATER | ELE_WATER (5) | [explore] status.c:~5925, skill.c:~7241 |
| SA_LIGHTNINGLOADER | SC_PROPERTYWIND | ELE_WIND (6) | [explore] status.c:~5934, skill.c:~7242 |
| SA_SEISMICWEAPON | SC_PROPERTYGROUND | ELE_EARTH (7) | [explore] status.c:~5928, skill.c:~7243 |

**Implementation**: set `weapon_element` to the appropriate ELE_* constant.
Duration / level scaling: [stub] — needs grep.

---

## Priest Endow — PR_ASPERSIO

| Skill | SC key | Element assigned | Hercules ref |
|-------|--------|-----------------|--------------|
| PR_ASPERSIO | SC_ASPERSIO | ELE_HOLY (3) | [explore] status.c:~5939, skill.c:~7271 |

**Note**: Aspersio also has a special interaction with Undead monsters. The weapon
hits them with Holy element which may interact differently with the attr_fix table.
No additional formula change needed — the element override handles it.

---

## Assassin Endow — AS_ENCHANTPOISON

| Skill | SC key | Element assigned | Hercules ref |
|-------|--------|-----------------|--------------|
| AS_ENCHANTPOISON | SC_ENCHANTPOISON | ELE_POISON (8) | [explore] status.c:~5937, skill.c:~7514 |

**Note**: also applies a Poison status proc on attack — not modelled in damage calc.

---

## Taekwon Kid — TK_SEVENWIND

Assigns one of several elements based on skill level or sub-variant.
Elements available: Fire, Water, Wind, Earth, Holy, Ghost, Dark.

| Level/variant | Element | SC key |
|--------------|---------|--------|
| 1 | [stub] | [stub] |
| ... | ... | ... |

Full level→element mapping: [stub] — awaiting skill list.

---

## Calculator interface

All endow SCs ultimately do the same thing for the calculator:
set `weapon_element = ELE_*` for the attack resolution.

The `PlayerBuild.weapon_element` field already exists (range 0–9, None = use item_db value).
The endow dropdown in the GUI writes to this field, using the same mechanism as the
existing weapon element override combo.

No new pipeline steps needed — `base_damage.py` already reads `weapon_element`.

---

## Implementation status

| SC | Formula | Calculator | GUI |
|----|---------|-----------|-----|
| SC_PROPERTYFIRE | explore | not started | — |
| SC_PROPERTYWATER | explore | not started | — |
| SC_PROPERTYWIND | explore | not started | — |
| SC_PROPERTYGROUND | explore | not started | — |
| SC_ASPERSIO | explore | not started | — |
| SC_ENCHANTPOISON | explore | not started | — |
| SC_PROPERTYDARK | explore | not started | — |
| SC_PROPERTYTELEKINESIS | explore | not started | — |
| TK_SEVENWIND full table | stub | not started | — |
