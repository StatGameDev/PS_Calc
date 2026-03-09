# PS_Calc GUI Plan
_Load at the start of any GUI session. `docs/phases_done.md` contains full Phase 0–4 specs._

---

## Session Plan

| Session | Focus | Exit Criteria |
|---|---|---|
| **1** | Bugs B3+B4+B5 (splitter/target), verify B6+B7 | Layout stable, target refresh working, crit/overrefine verified |
| **2** | C1 Variance + E1 Hit/Miss | ⚠️ Partial — C1a avg fix done; E1 deferred; C1 distribution needs planning session |
| **3** | E1 Hit/Miss + C3 ASPD + HP + SP | Hit chance in summary card; derived stats correct for naked builds |
| **4** | D5/D4 Script parsing + gear/card effects + tooltips | ✅ Done — gear/card bonuses live; tooltip descriptions generated |
| **5** | Enhancements 4.4–4.7 (filter UIs) | All four filter UIs complete |
| **6** | E3 Bane skills + E4 Katar second hit + polish | Correct output for Hunter and Katar Sin builds |

**Pre-Session 4 gate:** grep item_db bonus-type distribution and decide
manual-vs-generated split before writing any parser code.

---

## Known Bugs

**B3 — StepsBar starts in wrong position** ✅ _Fixed Session 1_
Root cause: inner QSplitter not sized on first show (50/50 default).
Fix: `Panel.reset_steps_to_collapsed()` called via `QTimer.singleShot(0, ...)` from
`PanelContainer.set_focus_state` after `set_visible_bar(True)`.

**B4 — Combat panel doesn't expand when Steps expanded** ✅ _Fixed Session 1_
Root cause: StepsBar signals only wired to inner splitter; outer splitter nudge not triggered.
Fix: Added `steps_expand_requested`/`steps_collapse_requested` signals to Panel forwarding
from StepsBar. PanelContainer connects them to `_on_section_expand_requested`/`_on_section_collapse_requested`.

**B5 — Target sections not refreshing on selection** ✅ _Fixed Session 1_
Root cause: `except` block in `_run_battle_pipeline` called `refresh_mob(None)` / `refresh_status(None)`,
blanking the display on any pipeline error.
Fix: Target/incoming refresh moved before try block and removed from except. Pipeline result
becomes `None` on error; `result_updated` still emitted.

**B6 — Basic attack crit eligibility** ✅ _Fixed Session 1_
Root cause: skills.json has no id=0 entry; Normal Attack was absent from skill combo.
Fix: Prepend synthetic "Normal Attack (id=0)" as first combo item in CombatControlsSection.
Runtime: load knight_bash.json, select Normal Attack, verify crit branch in Summary.

**B7 — Overrefine shows as unrefinable** ✅ _Verified Session 1 (no code change)_
Static: Flamberge (1129) refineable=true in item_db.json. resolve_weapon reads it correctly.
get_overrefine(3, 7) = 16. Code path correct — no fix needed.

**B8 — No Save button in GUI** ✅ _Fixed Session 4_
"Save" QPushButton added to top bar. Disabled when no build loaded or build name is empty.
`_on_save_build()`: collects build from sections, then `BuildManager.save_build(build, path)`.
Overwrites without confirmation. No "Save As" (Phase 8 polish).

**B9 — Save had stale build.name before _collect_build()** ✅ _Fixed Session 4_
Root cause: `_on_save_build` referenced `build` (undefined local) and checked `build.name`
before `_collect_build()` was called, so the Name field value was not yet reflected.
Fix: call `_collect_build()` first, then use `build.name` (Name field) as the filename.
If the name changed (e.g. "agi_bs" → "Agi BS"), `_current_build_name` and the combo are
refreshed after save so they stay consistent.

---

## Equipment System Gaps _(Session 5)_

**F1 — No card slots in equipment UI**
The equipment section has one item per slot (weapon, armor, etc.) but no sub-slots for cards.
Pre-renewal allows up to 4 card slots per item (weapon_type-dependent).
Required:
- Each equipped item needs 0–4 card sub-slots based on item `slots` field from item_db.
- Card sub-slots should open the Equipment Browser filtered to IT_CARD only.
- Parsed card scripts feed into `GearBonusAggregator` (already handles any item in `equipped`).
- Depends on: the slot key scheme for cards (e.g. `"right_hand_card_0"` through `"_card_3"`).

**F2 — Armor base DEF not added from item_db**
IT_ARMOR items have a `def` field (hard DEF) that is currently ignored.
Only `bDef` script bonus is applied via `GearBonusAggregator`.
Required: in `_apply_gear_bonuses` (or a separate pass), sum `item["def"]` for all equipped
IT_ARMOR items and add to `equip_def`.
Note: weapon ATK is handled via `resolve_weapon` → Weapon.atk, so the pattern is different.

**F3 — Armor refine DEF not calculated**
Refining armor adds hard DEF per refine level (Hercules: `refine_db.conf` table for armor).
Currently no armor refine DEF is computed. `refine_fix.py` handles weapon ATK2 only.
Required: scrape refine_db.conf for armor DEF table (analogous to `import_item_db.py`),
add to `GearBonuses.def_` during aggregation using `build.refine_levels[slot]`.

**F4 — Gear bonuses invisible in Stats section**
The Stats section bonus fields show manually-entered values only. Gear bonuses (from `_apply_gear_bonuses`)
are silently applied to the pipeline but not surfaced anywhere in the UI.
Users cannot tell whether a card's bStr bonus is being applied.
Required: a read-only "from gear" indicator or tooltip next to each bonus field, or a
dedicated "Gear Bonuses" row in the Derived section. Decide display approach first.

**F5 — 2H weapon does not block Left Hand slot**
Equipping a 2H weapon (Spear, 2HAxe, 2HStaff, etc.) should disable and clear the Left Hand slot.
Currently both slots are independent and the UI allows logically invalid combinations.
Required:
- In `equipment_section.py`, detect `weapon.weapon_type in RANGED_WEAPON_TYPES` or weapon
  `loc` field containing both hands → disable L. Hand row, clear its item ID.
- Trigger: whenever right_hand item changes.
- Also: 2H weapon items are currently not filtered out from the Equipment Browser when
  opening the L. Hand slot — should show only shield/off-hand eligible items.

**F6 — Class-based dual-wield restriction not enforced**
In pre-renewal only Assassin (job_id 12) and Assassin Cross (job_id 24) can equip a
weapon in the Left Hand slot. All other jobs should have L. Hand disabled entirely
(unless holding a shield — which is a separate slot in the full system).
Currently L. Hand is unrestricted for all classes.
Required: check `build.job_id` when rendering the Left Hand row; disable if not Assassin/AssX.

**F7 — Equipment slots use Edit button only (no inline dropdown)**
Each slot has only an "Edit" button that opens the Equipment Browser dialog.
There is no inline combo/dropdown for quick re-selection without the full browser.
Low priority — the browser dialog is functional. Consider for Session 5 polish.

---

## Pending Enhancements _(Session 5)_

**4.4 — Skill list real names + job filter**
Filter skill combo to current build's job_id. Use skills.json job data; "Show All" toggle.
Special handling for Rogue and Stalker, they can copy some skills with Plagiarism.
The flag should be under "skill_info": ["AllowPlagiarism"] in data\pre-re\db\skills.json

**4.5 — Equipment Browser job filter**
Filter by `item["job"]` list. "All Jobs" toggle in dialog toolbar.

**4.6 — Monster Browser filter dropdowns**
Race / Element / Size QComboBox above table. AND logic with name search.

**4.7 — Passives and Masteries job filter**
Hide/disable entries irrelevant to loaded job. "Show All" override in section header.

**P1 — Persist StepsBar expanded/collapsed state across focus changes** _(Phase 8 prereq)_
Currently `set_focus_state("combat_focused")` hides the StepsBar entirely, and
`set_focus_state("builder_focused")` always calls `reset_steps_to_collapsed()` via
`QTimer.singleShot`. If the user expanded the step list and then toggled to combat focus
and back, the expanded state is lost.
Required when user-adjustable widget sizes are introduced (Phase 8):
- Add `_steps_expanded: bool` to `StepsBar` (already has `self._expanded`; just needs
  to survive hide/show).
- `Panel.set_visible_bar(True)` should restore the last expanded state rather than
  always resetting to collapsed. Call `_on_steps_expand` or `reset_steps_to_collapsed`
  based on the saved flag.

---

## Session 2 — C1 Variance + E1 Hit/Miss _(partial)_

### Done
- **C1a** — VIT DEF avg off-by-0.5 fixed in `defense_fix.py`: `variance_max//2`.
- **B7 debug** — runtime print added to `base_damage.py`; run app to see actual
  weapon.level/refine values and confirm root cause before removing.

### C1 Variance — Handover (needs web-Claude planning session)

`DamageRange(min, max, avg)` is insufficient for Phase 7 histogram.
The final damage distribution is a **convolution of three independent uniform
random variables** (weapon ATK range, overrefine roll, VIT DEF roll), each
subtracted or added at different pipeline stages. The min and max are propagated
correctly, but `avg` is an approximation only. To support a damage histogram:

- **Option A — Exact convolution**: keep variance sources as `(lo, hi, step)` tuples;
  convolve at each stage. O(n²) in the range size, feasible for small overrefine but
  not for high-ATK weapons.
- **Option B — Irwin-Hall approximation**: sum of n uniform → approximately normal
  for large n. Fast, but loses tail accuracy.
- **Option C — Monte Carlo**: simulate k=10k rolls. Simple, correct, fast enough.
- **Architectural constraint**: deterministic multipliers (SkillRatio, AttrFix, etc.)
  must be applied to the *entire distribution*, not just avg. They scale the range.

Defer to web-Claude planning session. Do NOT change `DamageRange` until design is
settled — the tuple structure is the right starting point.

### E1 Hit/Miss — Deferred to Session 3

Verified Hercules formulas:
- `hitrate = 80 + player_HIT − mob_FLEE`, clamped to `[min_hitrate, max_hitrate]`
  (defaults 5/100). `#ifndef RENEWAL`, battle.c:4469/5024.
- `mob_FLEE = mob.level + mob.agi` (standard status formula).
- `perfect_dodge_chance = (target.luk + 10) / 10 %` — `rnd()%1000 < flee2`
  where `flee2 = luk + 10`, battle.c:4799.
- hitrate has further modifiers not modelled: skill per-level bonuses, SC_FOGWALL
  (−50 for ranged normal), arrow_hit, agi_penalty_type. Add TODO when implementing.

Required changes for E1:
1. `core/models/target.py` — add `agi: int = 0`
2. `core/data_loader.py` — `get_monster()` populate `agi` from `stats.agi`
3. `core/config.py` — add `min_hitrate: int = 5`, `max_hitrate: int = 100`
4. `core/models/damage.py` — add `perfect_dodge: float = 0.0` to `BattleResult`
5. `core/calculators/modifiers/hit_chance.py` — new: `calculate_hit_chance(status, target, config)`
6. `core/calculators/battle_pipeline.py` — call calculate_hit_chance, set result fields
7. `gui/sections/summary_section.py` — show hit% + perfect dodge% in Hit row

---

## Session 3 — E1 Hit/Miss + C3 Derived Stats ✅ DONE

**E1** — implemented. See COMPLETED_WORK.md Session 3 for full detail.
Unmodelled hitrate modifiers (documented in hit_chance.py TODO):
- Skill per-level HIT bonuses
- SC_FOGWALL: −50 hitrate for ranged normal attacks
- arrow_hit: ammo HIT bonus
- agi_penalty_type: AoE hit penalty
These require script parsing (Session 4) or separate modifier handling.

**C3** — implemented. Real ASPD/HP/SP in StatusCalculator.
Bonus stubs defined (`bonus_aspd_add`, `bonus_maxhp`, `bonus_maxsp`) — populated Session 4.
`derived_section` still shows placeholder ASPD/HP/SP labels — update needed (Session 4 or 5).

---

## Session 4 — D5/D4 Script Parsing + Gear/Card Effects ✅ DONE

**Implemented:**
- `core/models/item_effect.py` — `ItemEffect(bonus_type, arity, params, description)`
- `core/item_script_parser.py` — `parse_script(script) -> list[ItemEffect]`
  - Regex parser for bonus/bonus2/bonus3. Template table: ~35/25/9 types.
- `core/models/gear_bonuses.py` — `GearBonuses` dataclass (flat fields + E2 stub dicts)
- `core/gear_bonus_aggregator.py` — `GearBonusAggregator.compute(equipped) -> GearBonuses`
- `gui/main_window.py` — `_apply_gear_bonuses()` applies parsed bonuses as a clean overlay;
  save_build always writes manual-only values.

**Verified:** Alice Card `bSubRace,RC_Boss,40` → "Reduces damage from Boss monsters by 40%."
Picky Card `bStr,1 + bBaseAtk,10` → str_=1, batk=10 correctly routed.

**Not implemented (future sessions):**
- Tooltips in Equipment Browser / Equip Section UI (Session 5)
- bonus2/bonus3 E2 routing (race/size/element mults → pipeline) — blocked on E2 design
- bSkillAtk, bIgnoreDefRate pipeline routing (Session 6)
- Manual override dict for exceptional items

---

## Phase 5 — Stat Planner Tab
Tab infrastructure on combat panel. Stat budget, projections, what-if mode.

## Phase 6 — Comparison Tab
Side-by-side build comparison. Diff highlighting and delta column.

## Phase 7 — Advanced Tab & Graphs
Full step breakdown always-visible. pyqtgraph TTK distribution histogram
(median, 10th/90th percentile, normal vs crit overlay).
Requires C1 variance tuple structure to be correct.

## Phase 8 — Polish & Config
Layout presets. Resolution scaling verification (1280×720 – 1920×1080).
`ui_scale_override` in settings JSON. Payon Stories BattleConfig fully wired.

---

## Architecture Reference

### Rules (non-negotiable)
- All styling via `dark.qss`. No inline style strings.
- No business logic in widget classes. Signals only.
- No cross-thread polling. Signals and slots only.

### Signal flow
```
User edits widget
  → section emits change signal
    → MainWindow._on_build_changed()
      → PlayerBuild → StatusCalculator + BattlePipeline → BattleResult
        → MainWindow emits result_updated(BattleResult)
          → combat sections render
```

### Focus states
- `builder_focused` (builder_fraction ≈ 0.62): builder expanded, combat compact.
- `combat_focused` (builder_fraction ≈ 0.22): combat expanded, builder compact.
- Free drag doesn't change compact state — only FOCUS buttons and snap do.
- Step breakdown expand nudge: +5% to combat panel width, not a named state.

### compact_mode values (layout_config.json)
| Value | Behavior |
|---|---|
| `"none"` | No change when panel is compact |
| `"hidden"` | Section hidden entirely |
| `"collapsed"` | Collapses to header; user can re-expand |
| `"compact_view"` | Subclass swaps content via `_enter_compact_view()` |

---

## Buffs & Target State — UI Design Spec
_Design session: 2026-03-09. Sessions M–R implementation target._

---

### New Widget Pattern: CollapsibleSubGroup

Sections containing multiple logical groups use internally collapsible sub-sections.
New class `CollapsibleSubGroup` (proposed: `gui/widgets/collapsible_sub_group.py`) —
NOT a `Section`; lives inside a Section's content frame.

```
[ ▶ Sub-group Name ]   ← clickable header row; arrow toggles
  content widget        ← QWidget hidden/shown on click
```

- Click header → toggle content visibility. No signal propagates to PanelContainer.
- Qt's VBoxLayout naturally shifts content below upward when a sub-group collapses.
- `default_collapsed: bool` is a per-instance argument, not in layout_config.json.
- Sub-groups do NOT participate in the Section compact_mode protocol.
- QSS object name: `"subgroup_header"` (visually distinct from Section headers).
- Tooltip on each individual buff/passive widget: effect description + Hercules ref line.

**Multi-column layout**: Sub-groups with many items use `QGridLayout` 2-column,
items placed top-to-bottom in the left column first then the right, balancing heights.

---

### Layout Changes

**Builder panel — revised section order:**

| # | Key | Display Name | compact_mode | default_collapsed |
|---|-----|-------------|-------------|------------------|
| 1 | `build_header` | Build | none | false |
| 2 | `stats_section` | Base Stats | compact_view | false |
| 3 | `derived_section` | Derived Stats | compact_view | false |
| 4 | `equipment_section` | Equipment | compact_view | false |
| 5 | `passive_section` | Passives | compact_view | false |
| 6 | `buffs_section` | Buffs | compact_view | true |
| 7 | `active_items_section` | Active Items | hidden | true |

Removed as standalone sections: `manual_adj_section` → becomes a CollapsibleSubGroup
inside `build_header`.

**Combat panel — revised section order:**

| # | Key | Display Name | compact_mode | default_collapsed |
|---|-----|-------------|-------------|------------------|
| 1 | `combat_controls` | Combat Controls | none | false |
| 2 | `target_section` | Target Info | compact_view | false |
| 3 | `summary_section` | Summary | none | false |
| 4 | `target_state_section` | Target State | none | true |
| 5 | `step_breakdown` | Step Breakdown | hidden | false |
| 6 | `incoming_damage` | Incoming Damage | hidden | true |

Note: `summary_section` will expand into a more comprehensive results display (future session).
`target_section` will become more compact in the same session. In combat focus, they are
planned to sit side-by-side. `target_state_section` sits below Summary so both are
simultaneously visible while toggling debuffs.

---

### build_header — Manual Adjustments Sub-group

Add one CollapsibleSubGroup at the bottom of `build_header`'s content:

```
[ ▶ Manual Adjustments ]   default_collapsed: true
  [same widget content as current manual_adj_section.py]
```

Framing: permanent build configuration for unimplemented passives or edge cases — NOT
per-scenario buffs. `collect_into()` / `load_build()` delegation unchanged.
Data model: `PlayerBuild.manual_adj_bonuses` — unchanged.

---

### passive_section — Changes

- Rename display: "Passives & Buffs" → "Passives"
- Remove `SC_ADRENALINE` and `SC_ASSNCROS` from `_SELF_BUFFS` (migrate to buffs_section).
- All `_PASSIVES` (masteries) and Flags sub-group remain.
- compact_mode: `compact_view` — unchanged.
- Self-buff rows (SC_AURABLADE etc.) migrate to `buffs_section` Self Buffs sub-group.

After migration, passive_section contains: masteries (2-column grid) + Flags only.

---

### buffs_section

File: `gui/sections/buffs_section.py`
Panel: builder (position 6)
compact_mode: `compact_view` → one-line summary of all active buff names
default_collapsed: true

Contains the following CollapsibleSubGroups in order:

---

#### Sub-group 1: Self Buffs
`default_collapsed: false`

Header row: "Show All" QCheckBox (right-aligned).
Content: QGridLayout 2-column. Each row: `QCheckBox(name)` + optional `QSpinBox(level)`.
Job-filtered via `update_job(job_id)` — rows hidden (not disabled) when filtered out.
Tooltip per QCheckBox: effect description + Hercules ref.

Initial SC list (migrated from passive_section._SELF_BUFFS, minus SC_ADRENALINE + SC_ASSNCROS):
```
SC_AURABLADE      "Aura Blade"          lv 1–5    LK_AURABLADE
SC_MAXIMIZEPOWER  "Maximize Power"      no lv     BS_MAXIMIZE
SC_OVERTHRUST     "Overthrust"          lv 1–10   BS_OVERTHRUST
SC_OVERTHRUSTMAX  "Max. Overthrust"     lv 1–5    WS_OVERTHRUSTMAX
SC_TWOHANDQUICKEN "Two-Hand Quicken"    no lv     KN_TWOHANDQUICKEN
SC_SPEARQUICKEN   "Spear Quicken"       lv 1–10   CR_SPEARQUICKEN
SC_ONEHANDQUICKEN "One-Hand Quicken*"   no lv     KN_ONEHAND
```
Session N additions: SC_TRUESIGHT, SC_CONCENTRATE, SC_DEFENDER, SC_AUTOGUARD,
SC_CARTBOOST, Spirit Spheres 0–15 (Monk/Champion), and others from buff_skills.md.

Data model: `PlayerBuild.active_status_levels` — unchanged key format.

---

#### Sub-group 2: Party Buffs
`default_collapsed: false`

Single QGridLayout 2-column distributing all provider roles together (Priest, Blacksmith, etc.)
ordered to balance column heights. No internal sub-headers — the sub-group header "Party Buffs"
is sufficient. Tooltip per row: effect + who casts it + Hercules ref.

Initial items (Session M scope):
```
SC_BLESSING        "Blessing"           lv 1–10   Priest → STR/INT/DEX per level
SC_INCREASEAGI     "Increase AGI"       lv 1–10   Priest → AGI per level
SC_GLORIA          "Gloria"             no lv     Priest → +30 LUK flat
SC_ANGELUS         "Angelus"            lv 1–10   Priest → VIT-based DEF%
SC_MAGNIFICAT      "Magnificat"         lv 1–10   Priest → SP regen rate
SC_IMPOSITIOMANUS  "Impositio Manus"    lv 1–5    Priest → flat WATK bonus
SC_ADRENALINE      "Adrenaline Rush"    no lv     Blacksmith → ASPD
```

Note: SC_IMPOSITIO currently hardcoded in `base_damage.py` — migrate to `support_buffs` dict
and wire via BaseDamage when this sub-group is implemented.

Data model: `PlayerBuild.support_buffs: dict` (new field, Session M prereq):
```python
{
    "SC_BLESSING": 0, "SC_INCREASEAGI": 0, "SC_GLORIA": False,
    "SC_ANGELUS": 0,  "SC_MAGNIFICAT": 0,  "SC_IMPOSITIOMANUS": 0,
    "SC_ADRENALINE": 0,
    # extended by Ground Effects and Guild sub-groups below
}
```

---

#### Sub-group 3: Ground Effects (Sage / Scholar)
`default_collapsed: false`

Ground effects are mutually exclusive — only one active tile at a time.
```
Ground:  [QComboBox: — (none) | Volcano | Deluge | Violent Gale]   Level: [QSpinBox 1–5]
```
SpinBox disabled when "none". Tooltip on QComboBox lists each option's effect summary.

Data model (added to `support_buffs`):
```python
"ground_effect": None,    # str: "SC_VOLCANO"|"SC_DELUGE"|"SC_VIOLENTGALE"|None
"ground_effect_lv": 1,    # int 1–5
```

Eternal Chaos (SA_ETERNALCHAOS): NOT a ground effect — appears in Applied Debuffs
sub-group (see below) because it modifies target DEF.

---

#### Sub-group 4: Bard Songs
`default_collapsed: false`

**Shared caster stat row** (compact, one line):
```
AGI [▲▼]  DEX [▲▼]  VIT [▲▼]  INT [▲▼]  LUK [▲▼]   Mus. Lesson [▲▼ 0–10]
```
Range: 1–200 (effective stat). Tooltip: "Bard caster's effective stats (base + equipment)."

**Per-song rows**: `QCheckBox(name)` + `QSpinBox(level 1–10)` + stat override widget.

Override pattern per song:
- Small `□ Override` QCheckBox enables inline `QSpinBox` for each stat the song uses.
- Disabled until `□ Override` is checked; uses shared caster value when unchecked.
- Tooltip on song name: full scaling formula with all stat contributions and level.

Songs using multiple stats show multiple override spinboxes on the same row.

Initial songs (formulas in docs/buffs/songs_dances.md):
```
SC_ASSNCROS    "Assassin Cross"   lv 1–10   override: AGI
SC_WHISTLE     "Whistle"          lv 1–10   override: AGI  (needs grep — formula TBD)
SC_POEMBRAGI   "Poem of Bragi"    lv 1–10   override: DEX, INT
SC_APPLEIDUN   "Apple of Idun"    lv 1–10   override: VIT
```

Data model: `PlayerBuild.song_state: dict` (new field):
```python
{
    "caster_agi": 1, "caster_dex": 1, "caster_vit": 1,
    "caster_int": 1, "caster_luk": 1, "mus_lesson": 0,
    "SC_ASSNCROS": 0,   "SC_ASSNCROS_agi": None,
    "SC_WHISTLE": 0,    "SC_WHISTLE_agi": None,
    "SC_POEMBRAGI": 0,  "SC_POEMBRAGI_dex": None, "SC_POEMBRAGI_int": None,
    "SC_APPLEIDUN": 0,  "SC_APPLEIDUN_vit": None,
    # override key = None → use shared; int → use this value
}
```

---

#### Sub-group 5: Dancer Dances
`default_collapsed: false`

Same structure as Bard Songs. Separate shared caster stat row:
```
AGI [▲▼]  DEX [▲▼]  VIT [▲▼]  INT [▲▼]  LUK [▲▼]   Dance Lesson [▲▼ 0–10]
```

Initial dances:
```
SC_HUMMING       "Humming"          lv 1–10   override: DEX  (needs grep — formula TBD)
SC_FORTUNE       "Fortune's Kiss"   lv 1–10   override: LUK
SC_SERVICEFORYU  "Service for You"  lv 1–10   override: INT
```

Data model (added to `song_state`):
```python
"dancer_agi": 1, "dancer_dex": 1, "dancer_vit": 1,
"dancer_int": 1, "dancer_luk": 1, "dance_lesson": 0,
"SC_HUMMING": 0,      "SC_HUMMING_dex": None,
"SC_FORTUNE": 0,      "SC_FORTUNE_luk": None,
"SC_SERVICEFORYU": 0, "SC_SERVICEFORYU_int": None,
```

---

#### Sub-group 6: Ensembles
`default_collapsed: false`

Requires both Bard + Dancer in party. No per-caster stat input — ensemble formulas TBD.
```
SC_DRUMBATTLE  "Battle Theme"         lv 1–5   WATK+, DEF+
SC_NIBELUNGEN  "Song of Nibelungen"   lv 1–5   WATK+
SC_SIEGFRIED   "Lullaby of Woe"       lv 1–5   all-element resist (incoming — deferred)
```
Data model (added to `song_state`):
```python
"SC_DRUMBATTLE": 0, "SC_NIBELUNGEN": 0, "SC_SIEGFRIED": 0,
```
Open question (buffs/README.md Q1): SC_DRUMBATTLE / SC_NIBELUNGEN timing in pipeline
(pre- or post-SkillRatio). Needs Hercules grep before implementing.

---

#### Sub-group 7: Applied Debuffs
`default_collapsed: false`

Debuffs applied by the player's party to the target before the pipeline runs.
Framing: "what your team has set up on this target."
Widget pattern: QCheckBox + optional QSpinBox, 2-column grid (same as Self Buffs).
Tooltip per row: stat modified + how.

Initial debuffs:
```
SC_ETERNALCHAOS  "Eternal Chaos"   no lv    Sage → zeroes target soft DEF (def2=0)
```
Session R additions: SC_PROVOKE (lv 1–10), SC_DECREASEAGI (lv 1–10),
PR_LEXAETERNA (doubles next magic hit on target),
"Blessing vs Undead/Demon" (Blessing on undead target → reduces INT/DEX/LUK).

Data model (added to `support_buffs`):
```python
"SC_ETERNALCHAOS": False,    # → target.def2 = 0 in pipeline when True
```

Note: SC_ETERNALCHAOS also appears as a toggle in `target_state_section` Applied Debuffs.
Both read/write the same field via the normal collect/load_build cycle to avoid divergence.

---

#### Sub-group 8: Guild Buffs
`default_collapsed: true`

```
GD_BATTLEORDER  "Battle Orders"   lv 1–5   +level to STR, INT, DEX (guild members)
```
Data model (added to `support_buffs`):
```python
"GD_BATTLEORDER": 0,    # 0 = off; 1–5 = level
```

---

#### Sub-group 9: Miscellaneous Effects
`default_collapsed: false`

Catch-all for temporary effects triggered by equipped items and card scripts (proc effects,
conditional bonuses, pet buffs) that are not represented by any dedicated sub-group.

Widget pattern: named effect toggles — NOT per-stat spinboxes.
Each entry is a specific named effect with a QCheckBox (and optional QSpinBox for effects
that have a magnitude). Effects to include here are catalogued in advance from item_db.json
scripts and other sources; unrecognised effects do not appear.

Two display modes depending on how many known effects are catalogued:
- **Short list** (≤ ~8 effects): all shown as QCheckBox rows directly in the sub-group.
- **Long list**: QComboBox "Add effect..." picker above the list; selected effects appear
  as removable rows below (similar to how card browser adds cards to slots).

Distinct from:
- `active_items_section`: consumable item effects (potions, foods — see note below).
- `manual_adj_section` (now in build_header): permanent numeric overrides for unimplemented passives.

Section boundary: **Miscellaneous Effects** = equipped gear / card script procs and pet buffs
(effects from items you are wearing that trigger under conditions). **Active Items** =
consumables and potions (items you actively use that are not part of your equipment loadout).

**Active Items implementation note**: G46 `active_items_section` currently uses temporary
per-stat spinboxes as a placeholder. Its proper implementation uses the same named-effect
toggle pattern as Miscellaneous Effects — both are unimplemented in final form and should
be built together in the same session.

Data model: `PlayerBuild.misc_buff_bonuses: dict[str, int | bool]` (new field).
Keys = named effect identifiers; values = level or bool. Accumulated in `_apply_gear_bonuses`.

---

### target_state_section

File: `gui/sections/target_state_section.py`
Panel: combat (below summary_section, above step_breakdown)
compact_mode: `none` (ignores panel focus; stays in last user state)
default_collapsed: true

Public API:
- `update_target_type(is_monster: bool)` — show/hide monster-only content
- `collect_into(target: Target)` — write active SCs + overrides to target
- `load_state(target: Target)` — restore from target
- Signal: `state_changed = Signal()` → triggers pipeline re-run

Data model: `Target.target_active_scs: dict[str, int]` + `Target.element_override: Optional[int]`
(both new fields, Session R prereq).

---

#### Sub-group: Applied Debuffs
`default_collapsed: false` — all target types

Mirror of buffs_section Applied Debuffs. Shows the same debuff toggles from the
target's perspective. Reads/writes same `support_buffs` fields as the player-side
sub-group; no separate data storage.

---

#### Sub-group: Monster State
`default_collapsed: false` — hidden entirely when `update_target_type(is_monster=False)`

**Elemental Override** (Sage elemental change):
```
Element:  [QComboBox: — (natural) | Fire | Water | Wind | Earth | Ghost | Dark | Holy | Undead | Poison | Neutral]
```
Overrides `target.element` for this pipeline run. Does not change `element_level`.
Maps to `Target.element_override: Optional[int]`.

**Strip / Divest** (placeholder — deferred to Session R):
```
Stripped:  □ Weapon   □ Armor   □ Shield   □ Helm
```
Sets corresponding target defense component to 0 in pipeline.

---

#### Sub-group: Status Ailments (deferred stub)
`default_collapsed: true`

Single QLabel content: "(Status ailments — Phase 5+)". Placeholder for Freeze, Stone,
Stun, Poison interactions with damage formulae.

---

### Data model additions summary

**`PlayerBuild`** new fields:
```python
song_state: dict          # Bard/Dancer caster stats + per-song levels + overrides
support_buffs: dict       # Received external buffs (Priest, ground, guild, applied debuffs)
misc_buff_bonuses: dict   # Catch-all temporary buff effects (item procs, pet buffs, etc.)
```
All default to all-zero/None; backward-compatible with existing saves.

**`Target`** new fields:
```python
target_active_scs: dict[str, int]   # SC key → level; absent = inactive
element_override: Optional[int]     # None = natural element; int = override
```

**Build save migration** (one-time in BuildManager.load_build):
- `"SC_ADRENALINE"` in `active_status_levels` → move to `support_buffs["SC_ADRENALINE"]`.
- `"SC_ASSNCROS"` in `active_status_levels` → move level to `song_state["SC_ASSNCROS"]`.

---

### Deferred items

| Item | Reason |
|------|--------|
| SC_SIEGFRIED player-side elemental resist | Affects incoming pipeline; deferred to Session R. |
| SC_DRUMBATTLE / SC_NIBELUNGEN WATK timing | Needs Hercules grep for pipeline position. |
| SC_WHISTLE / SC_HUMMING formulas | Needs targeted Hercules grep before Session J implementation. |
| Guild GD_BLOODLUST | HP drain on hit — post-hit modelling required. |
| SC_DEVOTION (Crusader) | Damage redirect; requires attacker/defender pairing. |
| Target Strip/Divest | Deferred to Session R. |
| Target Stone Skin / Anti-Magic | Deferred to Session R. |
| Status ailments | Phase 5+ (requires turn-sequence model). |