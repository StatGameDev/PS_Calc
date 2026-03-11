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
Tab infrastructure on combat panel. Stat budget, projections, what-if mode.

**Phase 6 — Comparison Tab**
Side-by-side build comparison. Diff highlighting and delta column.

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

#### Sub-group: Player Debuffs
`default_collapsed: true`

Framing: "debuffs the enemy has applied to you."
Widget pattern: QCheckBox + optional QSpinBox, 2-column grid.
Tooltip per row: stat modified + how.

Initial debuffs (Session R):
```
SC_ETERNALCHAOS  "Eternal Chaos"   no lv    → zeroes player's soft DEF (def2=0) in incoming calc
SC_CURSE         "Curse"           no lv    → Various effects
SC_BLIND         "Blind"           no lv    → DEX/HIT reduced
SC_DECREASEAGI   "Decrease AGI"    lv 1–10  → AGI reduced → FLEE reduced
```

Data model:
```python
PlayerBuild.player_active_scs = {
    "SC_ETERNALCHAOS": False,    # → player.def2 = 0 in incoming pipeline when True
    # Session R additions
}
```

SC_ETERNALCHAOS appears separately in `target_state_section` Applied Debuffs (as a debuff
on the enemy, owned by `support_buffs`) — two separate fields, two separate effects.

---

### target_state_section

File: `gui/sections/target_state_section.py`
Panel: combat (below summary_section, above step_breakdown)
compact_mode: `none` (ignores panel focus; stays in last user state)
default_collapsed: true

**Scope**: Debuffs and state overrides that affect the target. Primary location for all
outgoing debuffs (what the player's team has applied to the enemy).

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

Debuffs applied by the player's party to the enemy target before the pipeline runs.
Framing: "what your team has set up on this target."
Widget pattern: QCheckBox + optional QSpinBox, 2-column grid.
Tooltip per row: stat modified + how.

Data flows via `support_buffs` on `PlayerBuild`, collected/loaded through the normal
build round-trip (not via `Target` — the pipeline reads `support_buffs` to modify the
target's effective stats).

Initial debuffs (Session R):
```
SC_ETERNALCHAOS  "Eternal Chaos"   no lv    Sage → zeroes target soft DEF (def2=0)
SC_PROVOKE       "Provoke"         lv 1–10  → raises target ATK but lowers DEF
SC_DECREASEAGI   "Decrease AGI"    lv 1–10  → lowers target AGI → lower FLEE
PR_LEXAETERNA    "Lex Aeterna"     no lv    → doubles next magic hit on target
```
"Blessing vs Undead/Demon": Blessing on undead target → reduces INT/DEX/LUK.

Data model (in `PlayerBuild.support_buffs`):
```python
"SC_ETERNALCHAOS": False,    # → target.def2 = 0 in pipeline when True
# Session R additions
```

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
| SC_SIEGFRIED player-side elemental resist | Affects incoming pipeline; deferred to Session R. |
| SC_DRUMBATTLE / SC_NIBELUNGEN WATK timing | Needs Hercules grep for pipeline position. |
| SC_WHISTLE / SC_HUMMING formulas | Needs targeted Hercules grep before Session M2 implementation. |
| SC_CURSE / SC_BLIND player debuff formulas | Stat reductions; needs Hercules grep before Session R. |
| Guild GD_BLOODLUST | HP drain on hit — post-hit modelling required. |
| SC_DEVOTION (Crusader) | Damage redirect; requires attacker/defender pairing. |
| Target Strip/Divest | Deferred to Session R. |
| Target Stone Skin / Anti-Magic | Deferred to Session R. |
| Status ailments | Phase 5+ (requires turn-sequence model). |
