# PS_Calc — Consumables & Misc Section Design
_Design finalized 2026-03-14 (session S-5 planning). Not yet implemented._
_Load this doc at the start of implementation session. Do not re-research these decisions._

---

## Scope

Two new builder-panel sections:
- **`consumables_section.py`** — stat foods, ASPD potions, ATK/MATK items, combat stat items
- **`misc_section.py`** — auto-computed conditional item bonuses (framework; populate incrementally) and triggered item script effects.

These are standalone sections for pre-alpha. Post-alpha they'll be merged into Buffs as subsections.

---

## Architecture

### PlayerBuild — new fields

```python
consumable_buffs: Dict[str, object] = field(default_factory=dict)
# Keys defined in "Storage Keys" section below. Same typing pattern as support_buffs.

bonus_matk_flat: int = 0
# Flat MATK addend from SC_MATKFOOD/SC_PLUSMAGICPOWER consumables.
# Applied in StatusCalculator after rate scaling.
```

Do **not** add `consumable_item_ids` — the value-based dict design was chosen instead.

### build_applicator.py — new function

```python
def compute_consumable_bonuses(consumable_buffs: dict) -> dict[str, int | bool]:
    """Map consumable_buffs keys to stat deltas. Called inside apply_gear_bonuses()."""
```

Routing rules:
- **SC_FOOD_* conflict**: each SC slot takes the **max** of all sources (Hercules sc_start blocks lower val1, status.c:7362-7363). Per-stat food, all-stat food, and Grilled Corn all write to the same SC_FOOD_STR/AGI/etc. slots → `effective = max(food_X, food_all, grilled_corn_component)`.
- **SC_PLUSMAGICPOWER + SC_MATKFOOD**: separate SC slots, **stack** (both add to `bonus_matk_flat`).
- **ASPD potion**: maps to `bonus_aspd_percent` (aspd_rate -=100/150/200 out of 1000 → 10/15/20%).

`apply_gear_bonuses()` calls `compute_consumable_bonuses()` and folds results into the
`dataclasses.replace()` call alongside gear/SC/AI/MA bonuses.

### StatusCalculator — change

Add `effective_build.bonus_matk_flat` to MATK after rate scaling. Single insertion point.

### layout_config.json — new entries

Insert between `player_debuffs_section` (pos 7) and `active_items_section` (pos 8):

```json
{ "key": "consumables_section", "panel": "builder", "display_name": "Consumables",
  "compact_modes": ["header_summary"], "default_collapsed": true },
{ "key": "misc_section",         "panel": "builder", "display_name": "Active Effects",
  "compact_modes": ["header_summary"], "default_collapsed": true },
```

---

## Consumable Storage Keys & Routing

All keys live in `PlayerBuild.consumable_buffs`. The section emits a signal on any change;
MainWindow calls `apply_gear_bonuses()` which routes these into `bonus_*` fields.

### Group: Stat Foods (dropdowns)

| Key | Widget | Values | Maps to |
|---|---|---|---|
| `food_str` | NoWheelCombo | 0="STR", 1–10 | `bonus_str += max(food_str, food_all, grilled_corn_str)` |
| `food_agi` | NoWheelCombo | 0="AGI", 1–10 | `bonus_agi += max(food_agi, food_all, grilled_corn_agi)` |
| `food_vit` | NoWheelCombo | 0="VIT", 1–10 | `bonus_vit += max(food_vit, food_all)` |
| `food_int` | NoWheelCombo | 0="INT", 1–10 | `bonus_int += max(food_int, food_all, grilled_corn_int)` |
| `food_dex` | NoWheelCombo | 0="DEX", 1–10 | `bonus_dex += max(food_dex, food_all)` |
| `food_luk` | NoWheelCombo | 0="LUK", 1–10, 15, 20, 21 | `bonus_luk += max(food_luk, food_all)` |

Displayed as a compact "Stat Foods" sub-row: label + 6 small dropdowns inline.
Default first entry named after the stat (e.g. "STR") to serve as the None/zero option.
No tooltip on individual dropdowns needed — stat name is self-evident.

**LUK extra values:** 15 = Lucky Potion, 20 = Charm Of Luck, 21 = Lucky Rice Cake.

### Group: All-Stats Food (dropdown, mutually exclusive)

| Key | Widget | Values | Maps to |
|---|---|---|---|
| `food_all` | NoWheelCombo | 0="No All-Stats Food", 3, 6, 10 | `bonus_X += max(food_X, food_all)` for each of 6 stats |

Dropdown entries:
- "No All-Stats Food" (0)
- "Halo-Halo / Luxurious Western Food (+3 all)" (3)
- "Manchu-Han Imperial Feast (+6 all)" (6)
- "Charm Of Happiness (+10 all)" (10)

Conflict note: SC_FOOD_STR etc. are shared slots — max() routing handles overlap with per-stat dropdowns correctly.

### "Group": Grilled Corn (separate toggle, +2 STR/AGI/INT)

| Key | Widget | Maps to |
|---|---|---|
| `grilled_corn` | QCheckBox | bonus_str, bonus_agi, bonus_int each += 2 via max() |

Tooltip: "+2 STR, +2 AGI, +2 INT (SC_FOOD_*; conflicts with higher stat food)"

### Group: ASPD Potions (single dropdown, mutually exclusive)

| Key | Widget | Values | Maps to |
|---|---|---|---|
| `aspd_potion` | NoWheelCombo | 0–3 | `bonus_aspd_percent += [0, 10, 15, 20][v]` |

Dropdown entries:
- "No ASPD Potion" (0)
- "Concentration Potion (+10% ASPD)" (1) — SC_ATTHASTE_POTION1, aspd_rate−100
- "Awakening Potion (+15% ASPD)" (2) — SC_ATTHASTE_POTION2, aspd_rate−150
- "Berserk Potion (+20% ASPD)" (3) — SC_ATTHASTE_POTION3, aspd_rate−200 _(Berserk Potion Pitcher)_

Note on label: "Berserk Potion (+20% ASPD) — Berserk Potion Pitcher" in the combo text.
Available to all jobs (no job filter). Source: status.c:7851, 5661-5663.

### Group: HIT Foods (dropdown, same SC slot)

| Key | Widget | Values | Maps to |
|---|---|---|---|
| `hit_food` | NoWheelCombo | 0="HIT Food", 10, 20, 30, 33, 100 | `bonus_hit += v` |

Dropdown entries (item names in parens for tooltip):
- "HIT Food" (0)
- "+10 HIT" (Schwartzwald Pine Jubilee)
- "+20 HIT" (Schwartzwald Pine Jubilee tier 2)
- "+30 HIT" (Grilled Skewer / Sesame Pastry / Concentration Scroll)
- "+33 HIT" (Military Ration B)
- "+100 HIT" (Phreeoni Scroll)

### Group: FLEE Foods (dropdown, same SC slot)

| Key | Widget | Values | Maps to |
|---|---|---|---|
| `flee_food` | NoWheelCombo | 0="FLEE Food", 10, 20, 30, 33 | `bonus_flee += v` |

Dropdown entries:
- "FLEE Food" (0)
- "+10 FLEE" (Spray of Flowers)
- "+20 FLEE" (Schwartzwald Pine Jubilee)
- "+30 FLEE" (Citron / Honey Pastry / Evasion Scroll)
- "+33 FLEE" (Military Ration C)

### Group: CRI Food (single toggle)

| Key | Widget | Maps to |
|---|---|---|
| `cri_food` | QCheckBox | `bonus_cri += 7` |

Label: "Arunafeltz Desert Sandwich". Tooltip: "+7 CRI (SC_FOOD_CRITICALSUCCESSVALUE; status.c:4751)"

### Group: ATK Items (dropdown, SC_PLUSATTACKPOWER, same SC slot)

| Key | Widget | Values | Maps to |
|---|---|---|---|
| `atk_item` | NoWheelCombo | 0="ATK Food", 5, 10, 15, 20, 22, 24, 30 | `bonus_batk += v` |

Dropdown entries (show item name + value):
- "ATK Food" (0)
- "Rune Strawberry Cake (+5)"
- "Durian / Chewy Ricecake / Rainbow Cake (+10)"
- "Tasty Pink Ration (+15)"
- "Box of Resentment / Tyr's Blessing (+20)"
- "Distilled Fighting Spirit (+30)"

**Note**: SC_PLUSATTACKPOWER formula needs one grep at session start (verify `bonus_batk += val1` in status.c). Item 682 val1=30, 684 val1=10 etc. confirmed from item_db.

**Deferred (Payon Stories config session)**: Box of [...] items at values 22/24/32/40/52 — leave placeholder comment in dropdown definition.

### Group: MATK Items (dropdown, SC_PLUSMAGICPOWER)

| Key | Widget | Values | Maps to |
|---|---|---|---|
| `matk_item` | NoWheelCombo | 0="MATK Food", 5, 10, 15, 20, 30 | `bonus_matk_flat += v` |

Dropdown entries:
- "MATK Food" (0)
- "Rune Strawberry Cake (+5)"
- "Durian / Oriental Pastry / Rainbow Cake (+10)"
- "Tasty White Ration (+15)"
- "Box of Drowsiness / Tyr's Blessing (+20)"
- "Herb of Incantation (+30)"

Source: status.c:4635-4636 `matk += sc->data[SC_PLUSMAGICPOWER]->val1`.

### Group: MATK Food — Rainbow Cake (separate toggle, stacks with matk_item)

| Key | Widget | Maps to |
|---|---|---|
| `matk_food` | QCheckBox | `bonus_matk_flat += 10` |

Label: "Rainbow Cake (SC_MATKFOOD)". Tooltip: "+10 MATK flat, stacks with MATK Items above. Source: status.c:4637-4638"

This uses SC_MATKFOOD (item 12124), a **different SC** from SC_PLUSMAGICPOWER — they genuinely stack.

---

## Source Confirmations (all read 2026-03-14)

| SC | Formula | Source |
|---|---|---|
| SC_FOOD_STR | `str += val1` | status.c:3948-3949 |
| SC_FOOD_AGI | `agi += val1` | status.c:4013-4014 |
| SC_FOOD_VIT/INT/DEX/LUK | same pattern | status.c ~4076, ~4132, ~4201, ~4267 |
| SC_FOOD_BASICHIT | `hit += val1` | status.c:4799-4800 |
| SC_FOOD_BASICAVOIDANCE | `flee += val1` | status.c:4864-4865 |
| SC_FOOD_CRITICALSUCCESSVALUE | `critical += val1` (no 10× scale) | status.c:4751-4752 |
| SC_PLUSMAGICPOWER | `matk += val1` | status.c:4635-4636 |
| SC_MATKFOOD | `matk += val1` (stacks) | status.c:4637-4638 |
| SC_ATTHASTE_POTION1/2/3 | `aspd_rate -= 50*(2+type-POTION1)` → 100/150/200 | status.c:7851, 5661-5663 |
| SC_PLUSATTACKPOWER | **NOT YET CONFIRMED** — grep at session start | status.c (search `SC_PLUSATTACKPOWER`) |

---

## Misc Section (Active Effects) — Design

### Goal
Auto-compute conditional bonuses from equipped weapon scripts + current stats/skills.
No manual 5-slot picker needed — auto-trigger is more accurate and removes user error.

### Implementation (defer most to a future session)

At pipeline run time:
1. Identify equipped weapon item ID.
2. Look up its script from item_db.
3. Evaluate stat-threshold conditions against current `StatusData` / `PlayerBuild` stats.
4. Apply matching bonus effects to the pipeline (e.g. BATK, MATK%, ASPD%).

Tooltip (future): show which conditional bonus fired and why (e.g. "Doom Slayer: STR ≥ 95 → +340 BATK").

### Confirmed candidates (from item_db analysis, 2026-03-14)

These items have conditional effects that affect the damage pipeline:

| Item | Condition | Effect | Pipeline field |
|---|---|---|---|
| Doom Slayer (1370) | STR ≥ 95 | BATK+340 | bonus_batk |
| Krasnaya (1189) | STR ≥ 95 | BATK+20 | bonus_batk |
| Vecer Axe (1311) | LUK ≥ 90 | BATK+20 | bonus_batk |
| Vecer Axe (1311) | DEX ≥ 90 | CRI+5 | bonus_cri |
| Giant Axe (1387) | STR ≥ 95 | HIT+10, ASPD+5% | bonus_hit, bonus_aspd_percent |
| Sage's Diary (1560) | STR ≥ 50 | ASPD+5% | bonus_aspd_percent |
| Sage's Diary (1560) | INT ≥ 70 | MATK+15% | bonus_matk_rate |
| Veteran Sword (1188) | SM_BASH lv10 | Bash skill ATK +50% | skill_atk dict |
| Veteran Axe (1384) | BS_DAGGER/SWORD/etc lv3 | BATK+10 each | bonus_batk |

### Section framework (implement next session)

- `misc_section.py` as a `Section` subclass with `["header_summary"]` compact mode.
- No interactive widgets initially — just a display of auto-triggered effects.
- For now: can be a stub section (empty) until auto-compute logic is added.
- The auto-compute hook lives in `build_applicator.py`: `compute_misc_bonuses(equipped, status_data)` — returns dict of triggered bonuses + descriptions for tooltip.
- 178 total `if()` conditional scripts in item_db — the 9 candidates above are the most pipeline-relevant. Expand list in future sessions.

---

## UI Section Layout

```
consumables_section
├── [Stat Foods row]     STR▾ AGI▾ VIT▾ INT▾ DEX▾ LUK▾   (compact inline dropdowns)
├── [All-Stats Food]     No All-Stats Food▾
├── [Grilled Corn]       □ Grilled Corn
├── [ASPD Potion]        No ASPD Potion▾
├── [HIT Food]           HIT Food▾
├── [FLEE Food]          FLEE Food▾
├── [CRI Food]           □ Arunafeltz Desert Sandwich
├── [ATK Items]          ATK Food▾
├── [MATK Items]         MATK Food▾
└── [MATK Food]          □ Rainbow Cake (SC_MATKFOOD, stacks)

misc_section
└── [Active Effects]     (auto-computed; display only in first pass)
```

---

## Files to Create / Modify

| File | Change |
|---|---|
| `core/models/build.py` | Add `consumable_buffs`, `bonus_matk_flat` |
| `core/build_applicator.py` | Add `compute_consumable_bonuses()`; call in `apply_gear_bonuses()` |
| `core/calculators/status_calculator.py` | Add `bonus_matk_flat` to MATK output |
| `core/build_manager.py` | Save/load `consumable_buffs` |
| `gui/sections/consumables_section.py` | New file (see layout above) |
| `gui/sections/misc_section.py` | New stub file |
| `gui/layout_config.json` | Add two new section entries |
| `gui/main_window.py` | Wire `consumable_buffs` from section signal |

---

## Out of Scope (this session)

- Box of [...] item values (22/24/32/40/52) in ATK/MATK dropdowns → Payon Stories config session
- Actual auto-compute logic in misc_section → next session after consumables
- SC_FOOD_*_CASH variants (cash shop foods) — not in current item_db
- All-stat food conflict indicator in UI (visual warning) → post-alpha UX pass
