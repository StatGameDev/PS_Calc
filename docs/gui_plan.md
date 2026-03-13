# PS_Calc — GUI Plan
_Widget specs, section layout, and UI design for current and planned GUI work._
_For core system architecture and data flow, see `docs/core_architecture.md`._
_For pipeline step formulas, see `docs/pipeline_specs.md`._
_Phase 0–4 implementation history: `docs/phases_done.md`._

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

### compact_modes values (layout_config.json)
`compact_modes` is a `list[str]` — flags are independent and combinable.

| Flag | Behavior |
|---|---|
| `[]` | No change when panel is slim |
| `["hidden"]` | Section hidden entirely when slim |
| `["slim_content"]` | Compact widget shown in slim mode; toggle between collapsed and compact (full content never shown while slim). Subclass overrides `_enter_slim()` / `_exit_slim()`. |
| `["header_summary"]` | Always-visible summary label in header. Section auto-collapses when slim. Subclass calls `set_header_summary(text)` on any data change. |
| `["slim_content", "header_summary"]` | Both: compact widget + always-visible header text. |

See `docs/compact_modes.md` for implementation guide.

---

## Current Section Layout

**Builder panel** (`layout_config.json` — as implemented):

| # | Key | Display Name | compact_modes | default_collapsed |
|---|-----|-------------|--------------|------------------|
| 1 | `build_header` | Build | `[]` | false |
| 2 | `stats_section` | Base Stats | `["slim_content"]` | false |
| 3 | `derived_section` | Derived Stats | `["slim_content"]` | false |
| 4 | `equipment_section` | Equipment | `["slim_content"]` | false |
| 5 | `passive_section` | Passives | `["header_summary"]` | false |
| 6 | `buffs_section` | Buffs | `["header_summary"]` | true |
| 7 | `player_debuffs_section` | Player Debuffs | `["slim_content"]` | true |
| 8 | `active_items_section` | Active Items | `["hidden"]` | true |

**Combat panel** (`layout_config.json` — as implemented):

| # | Key | Display Name | compact_modes | default_collapsed |
|---|-----|-------------|--------------|------------------|
| 1 | `combat_controls` | Combat Controls | `[]` | false |
| 2 | `target_section` | Target Info | `["slim_content"]` | false |
| 3 | `summary_section` | Summary | `[]` | false |
| 4 | `step_breakdown` | Step Breakdown | `["hidden"]` | false |
| 5 | `incoming_damage` | Incoming Damage | `["hidden"]` | true |

---

## Planned Layout Changes (Session R+)

**Combat panel** — after Session R:

| # | Key | Display Name | compact_modes | default_collapsed |
|---|-----|-------------|--------------|------------------|
| 1 | `combat_controls` | Combat Controls | `[]` | false |
| 2 | `target_section` | Target Info | `["slim_content"]` | false |
| 3 | `summary_section` | Summary | `[]` | false |
| 4 | `target_state_section` | Target State | `[]` | true |
| 5 | `step_breakdown` | Step Breakdown | `["hidden"]` | false |
| 6 | `incoming_damage` | Incoming Damage | `["hidden"]` | true |

Changes vs current:
- New `target_state_section` added at position 4, below Summary — **target debuffs + monster state**

---

## LevelWidget Refactor (Session GUI-Rework)

_Planned after Session R. Pure GUI, no calculator changes. ~20–25k tokens._

### Problem

After the GUI-Adj session, every file that needs a level dropdown has its own local
`_NoWheelCombo` class definition (9 copies) and calls `_make_level_combo()` directly.
All load/collect call sites use `combo.currentData()` / `combo.findData()` instead of
the QSpinBox-compatible `value()` / `setValue()` API. A future widget-type swap requires
touching every call site again.

### Solution — `LevelWidget`

```python
# gui/widgets/level_widget.py
class LevelWidget(QComboBox):
    valueChanged = Signal(int)   # same name as QSpinBox

    def __init__(self, max_lv: int, include_off: bool = True):
        super().__init__()
        if include_off:
            self.addItem("Off", 0)
        for lv in range(1, max_lv + 1):
            self.addItem(str(lv), lv)
        self.currentIndexChanged.connect(
            lambda _: self.valueChanged.emit(self.value())
        )

    def value(self) -> int:
        return self.currentData() or 0

    def setValue(self, v: int) -> None:
        idx = self.findData(v)
        self.setCurrentIndex(idx if idx >= 0 else 0)

    def wheelEvent(self, event) -> None:
        event.ignore()
```

`setValue` / `value` / `valueChanged` match the QSpinBox API exactly — future widget
type changes require editing only this class.

### Work items

1. **`gui/widgets/level_widget.py`** — `LevelWidget` class as above.
2. **`gui/widgets/__init__.py`** — export `LevelWidget`, `NoWheelCombo`, `NoWheelSpin`;
   remove the 9 duplicate local class definitions across section and dialog files.
3. **`passive_section.py`** — `_mastery_combos: dict[str, LevelWidget]`; replace
   `_make_level_combo()` calls with `LevelWidget(max_lv, include_off=True)`.
4. **`buffs_section.py`** — all `_sc_combos`, `_party_level_combos`, `_song_level_combos`,
   `_dance_level_combos`, `_ensemble_combos`, `_ground_lv_combo` → `LevelWidget`.
   Remove `_make_level_combo()` and `_set_combo_value()` helpers (replaced by `setValue`).
5. **Lesson combo fix** — move `mus_lesson` / `dance_lesson` out of `_bard_caster_spins` /
   `_dancer_caster_spins` into dedicated `_bard_lesson: LevelWidget` /
   `_dancer_lesson: LevelWidget` attributes. This eliminates the `isinstance` guard
   in `_load_song_group` / `_collect_song_group`.

---

## Phases 5–8

**Phase 5 — Stat Planner Tab**
Tab infrastructure on combat panel. Stat budget and per-stat point cost display.

**Phase 6 — Comparison Tab**
Side-by-side build comparison using multiple variants stored within a single save file.
Toggle between saved variants via buttons; diff highlighting and delta column show
differences between the active variant and a selected reference variant.

**Phase 7 — Advanced Tab & Graphs**
Full step breakdown always-visible. pyqtgraph TTK distribution histogram
(median, 10th/90th percentile, normal vs crit overlay).
Requires C1 variance tuple structure to be correct.

**Phase 8 — Polish & Config**
Layout presets. Resolution scaling verification (1280×720 – 1920×1080).
`ui_scale_override` in settings JSON. compact_view rework.

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
- Remove `SC_ADRENALINE` and `SC_ASSNCROS` from `_SELF_BUFFS` (migrate to `buffs_section`).
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

**Scope**: Player buffs only — Self Buffs, party buffs received, songs/dances, ground effects,
guild buffs, miscellaneous item effects. No debuffs of any kind.
For debuffs applied ON the player → `player_debuffs_section` (builder panel, position 7).
For debuffs applied ON the target → `target_state_section` (combat panel).

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
SC_CARTBOOST, Spirit Spheres 0–5 (Monk/Champion), and others from buff_skills.md.

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
    # extended by Ground Effects, Applied Debuffs, and Guild sub-groups below
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
`default_collapsed: true`

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
`default_collapsed: true`

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
`default_collapsed: true`

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

#### Sub-group 7: Guild Buffs
`default_collapsed: true`

```
GD_BATTLEORDER  "Battle Orders"   lv 1–5   +level to STR, INT, DEX (guild members)
```
Data model (added to `support_buffs`):
```python
"GD_BATTLEORDER": 0,    # 0 = off; 1–5 = level
```

---

#### Sub-group 8: Miscellaneous Effects
`default_collapsed: true`

Catch-all for temporary effects triggered by equipped items and card scripts (proc effects,
conditional bonuses, pet buffs) that are not represented by any dedicated sub-group.

Widget pattern: named effect toggles — NOT per-stat spinboxes.
Each entry is a specific named effect with a QCheckBox (and optional QSpinBox for effects
that have a magnitude). Effects catalogued in advance from item_db.json scripts and other
sources; unrecognised effects do not appear.

Two display modes depending on how many known effects are catalogued:
- **Short list** (≤ ~8 effects): all shown as QCheckBox rows directly in the sub-group.
- **Long list**: QComboBox "Add effect..." picker above the list; selected effects appear
  as removable rows below (similar to how card browser adds cards to slots).

Distinct from:
- `active_items_section`: consumable item effects (potions, foods).
- `manual_adj_section` (now in build_header): permanent numeric overrides for unimplemented passives.

**Section boundary**: Miscellaneous Effects = equipped gear / card script procs and pet buffs.
Active Items = consumables and potions (items you actively use, not part of equipment loadout).

**Active Items implementation note**: G46 `active_items_section` currently uses temporary
per-stat spinboxes as a placeholder. Its proper implementation uses the same named-effect
toggle pattern as Miscellaneous Effects — both should be built together in the same session.

Data model: `PlayerBuild.misc_buff_bonuses: dict[str, int | bool]` (new field).
Keys = named effect identifiers; values = level or bool. Accumulated in `_apply_gear_bonuses`.

---

### player_debuffs_section

File: `gui/sections/player_debuffs_section.py`
Panel: builder (position 7)
compact_mode: `compact_view` → one-line summary of active debuff names
default_collapsed: true

**Scope**: Debuffs applied to the player by enemies — affects the player's own stats
in various ways. Symmetric to `target_state_section` Applied Debuffs,
but for the opposite role.

Public API:
- `collect_into(build: PlayerBuild)` — write active SCs to `build.player_active_scs`
- `load_build(build: PlayerBuild)` — restore from `build.player_active_scs`
- Signal: `changed = Signal()` → triggers pipeline re-run

Data model: `PlayerBuild.player_active_scs: dict[str, int]` (new field, Session R prereq).

#### Player Debuffs rows (flat, no sub-group header)

Framing: "debuffs the enemy has applied to you."
Widget pattern: one widget per row — `QCheckBox` for boolean, `LevelWidget` for leveled. No both.
2-column QGridLayout. Tooltip per row: stat modified + Hercules ref.

```
SC_ETERNALCHAOS  "Eternal Chaos"   QCheckBox        → player def2=0 in incoming (status.c:5090)
SC_CURSE         "Curse"           QCheckBox        → player LUK=0, ATK%−25 (status.c:4261, 4345)
SC_BLIND         "Blind"           QCheckBox        → player HIT×0.75, FLEE×0.75 (status.c:4817, 4902)
SC_DECREASEAGI   "Decrease AGI"    LevelWidget 1–10 → player AGI−(2+lv) → lower FLEE (status.c:7633)
```

Data model:
```python
PlayerBuild.player_active_scs = {
    "SC_ETERNALCHAOS": False,   # bool
    "SC_CURSE":        False,   # bool
    "SC_BLIND":        False,   # bool
    "SC_DECREASEAGI":  0,       # int 0=off, 1-10=level
}
```

SC_ETERNALCHAOS appears separately in `target_state_section` Applied Debuffs (as a debuff
on the enemy, owned by `support_buffs`) — two separate fields, two separate effects.

---

### target_state_section — IMPLEMENTED (Session R)

File: `gui/sections/target_state_section.py`
Panel: combat (below summary_section, above step_breakdown)
compact_mode: `["slim_content"]`
default_collapsed: true

**Scope**: Debuffs and state overrides that affect the target. Primary location for all
outgoing debuffs (what the player's team has applied to the enemy).

Public API:
- `update_target_type(is_monster: bool)` — show/hide monster-only rows
- `collect_into(build: PlayerBuild, target: Target)` — write debuffs to support_buffs, ailments to target
- `load_state(build: PlayerBuild, target: Target)` — restore from both
- Signal: `state_changed = Signal()` → triggers pipeline re-run

Data model:
- Applied Debuffs → `PlayerBuild.support_buffs` (build round-trip)
- Status Ailments → `Target.target_active_scs: dict[str, bool]` (new field)
- Element override → `Target.element_override: Optional[int]` (new field)

---

#### Widget pattern — one widget per row, no exceptions

**Boolean effect** → `QCheckBox("Name")` only. No spinbox alongside it.

**Leveled effect** → `LevelWidget(max_lv, include_off=True)` only. No separate checkbox.
Off = inactive; selecting a level activates it. Same pattern as has_lv=True self buffs.

---

#### Layout: flat rows with a horizontal line separator

No CollapsibleSubGroups inside this section. Content is a single QVBoxLayout with:
1. Applied Debuffs rows (flat)
2. `QFrame(shape=HLine)` — visual separator, no label
3. Status Ailments rows (flat)
4. Monster State rows (flat, shown/hidden via `update_target_type`)

2-column QGridLayout for rows above and below the separator separately.
Tooltip per row: effect summary + Hercules ref.

---

#### Applied Debuffs (rows above separator)

Data via `PlayerBuild.support_buffs`. All target types.

```
SC_ETERNALCHAOS  "Eternal Chaos"   QCheckBox        → target def2 = 0 (status.c:5090)
SC_PROVOKE       "Provoke"         LevelWidget 1–10 → target DEF%−(5+5×lv), ATK%+(2+3×lv) (status.c:8361-8362)
SC_DECREASEAGI   "Decrease AGI"    LevelWidget 1–10 → target AGI−(2+lv) → lower FLEE (status.c:7633)
PR_LEXAETERNA    "Lex Aeterna"     QCheckBox        → next magic hit ×2
```

Data model keys in `support_buffs`:
```python
"SC_ETERNALCHAOS": False       # bool
"SC_PROVOKE":      0           # int 0=off, 1-10=level
"SC_DECREASEAGI":  0           # int 0=off, 1-10=level
"PR_LEXAETERNA":   False       # bool
```

---

#### Status Ailments (rows below separator)

Data via `Target.target_active_scs`. All target types (though ailments are more common on monsters).
All boolean — `QCheckBox` only.

```
SC_STUN    "Stun"    QCheckBox  → hit_chance = 100% (battle.c:5014; OPT1_STUN)
SC_FREEZE  "Freeze"  QCheckBox  → hit_chance = 100%, element→Water Lv1, hard DEF÷2, MDEF+25% (status.c:5015,5155,5880)
SC_STONE   "Stone"   QCheckBox  → hit_chance = 100%, element→Earth Lv1, hard DEF÷2, MDEF+25% (status.c:5013,5153,5882)
SC_POISON  "Poison"  QCheckBox  → UI display only; no pipeline effect in pre-renewal damage
```

Data model keys in `target_active_scs`:
```python
"SC_STUN":   False
"SC_FREEZE": False
"SC_STONE":  False
"SC_POISON": False   # stored but has no pipeline effect
```

Note: Freeze and Stone are mutually exclusive (applying one should clear the other in the UI).

---

#### Monster State (rows shown only when is_monster=True)

Displayed below the Status Ailments rows. Hidden (not disabled) when target is a player.

**Element override** — one QComboBox, no other widget:
```
Element: [— natural | Neutral | Fire | Water | Wind | Earth | Poison | Holy | Dark | Ghost | Undead]
```
Overrides `target.element` for the pipeline run. Does not change `element_level` (stays at mob's natural level).
Maps to `Target.element_override: Optional[int]`. `—` = None = use natural element.

**Strip / Divest** — four QCheckBoxes on one row:
```
Stripped: □ Weapon  □ Armor  □ Shield  □ Helm
```
Each sets the corresponding defense component to 0 in the pipeline.
Stored as `Target.stripped: set[str]` (or four bool fields). DEF zeroing:
- Armor stripped → `target.equip_def = 0` in DefenseFix
- Shield/Helm: approximation — each reduces hard DEF by 25% of the equip_def value
- Weapon stripped → `target.atk_min = target.atk_max = 0` (affects incoming physical only)

---

### Data model additions summary

**`PlayerBuild`** new fields:
```python
song_state: dict              # Bard/Dancer caster stats + per-song levels + per-stat overrides
support_buffs: dict           # Buffs received from party + debuffs player's team applies to enemy
misc_buff_bonuses: dict       # Catch-all temporary buff effects (item procs, pet buffs)
player_active_scs: dict       # Debuffs the enemy has applied to the player (incoming damage)
```
All default to all-zero/None; backward-compatible with existing saves.

**`Target`** new fields:
```python
target_active_scs: dict[str, int]   # SC key → level; absent = inactive (Session R)
element_override: Optional[int]     # None = natural element; int = override (Session R)
```

**SC_ETERNALCHAOS is two separate fields with separate effects:**
- `support_buffs["SC_ETERNALCHAOS"]` — player casts it on enemy → target.def2=0 in outgoing
- `player_active_scs["SC_ETERNALCHAOS"]` — enemy casts it on player → player.def2=0 in incoming

**Build save migration** (one-time in BuildManager.load_build):
- `"SC_ADRENALINE"` in `active_status_levels` → move to `support_buffs["SC_ADRENALINE"]`.
- `"SC_ASSNCROS"` in `active_status_levels` → move level to `song_state["SC_ASSNCROS"]`.

---

### Deferred items

| Item | Reason |
|------|--------|
| Guild GD_BLOODLUST | HP drain on hit — post-hit modelling required. |
| SC_DEVOTION (Crusader) | Damage redirect; requires attacker/defender pairing. |
| Status ailments (advanced) | Simple toggle effects done in Session R. Turn-sequence / proc mechanics deferred to Session Adv-2. |
| Target Stone Skin / Anti-Magic | No Hercules source read yet. Deferred post-Session R. |
