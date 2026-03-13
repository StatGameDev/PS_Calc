# PS_Calc — Completed Work Log
_Append new entries at the bottom. Sessions 1–Q1 archived in `docs/archive/completed_work_pre_gui_rework.md`._

---

## Session GUI-Rework — 2026-03-11 — Widget Architecture Cleanup

**Skill browser fixes** (`gui/dialogs/skill_browser.py`, `gui/sections/combat_controls.py`):
- Crash fix: element field was list, not str — `_fmt_type` now handles list input
- Columns restructured to ID | Name | Type | Description(—)
- Filter to `_IMPLEMENTED_SKILLS` only (BF_WEAPON ∪ BF_MAGIC)
- Skill combo shows `description` (in-game name) with `name` fallback
- "List" button fixed width 52px

**`gui/widgets/level_widget.py`** (new file):
- `NoWheelCombo(QComboBox)`: hover-delay 0.1s before scroll wheel accepted
- `NoWheelSpin(QSpinBox)`: same hover-delay pattern
- `LevelWidget(NoWheelCombo)`: `value()`/`setValue()`/`valueChanged` API; `item_prefix` param

**`gui/widgets/__init__.py`**: exports all three classes.

**9 files swept** — `_NoWheelCombo`/`_NoWheelSpin` local class definitions removed, `NoWheelCombo`/`NoWheelSpin` imported from `gui.widgets`:
- `gui/main_window.py`, `gui/dialogs/monster_browser.py`, `gui/dialogs/new_build_dialog.py`
- `gui/sections/build_header.py`, `gui/sections/equipment_section.py`, `gui/sections/incoming_damage.py`
- `gui/sections/active_items_section.py`, `gui/sections/manual_adj_section.py`, `gui/sections/stats_section.py`

**`gui/sections/combat_controls.py`**:
- `_level_spin` (QSpinBox) replaced with `_level_widget = LevelWidget(10, include_off=False, item_prefix="Lv ")`
- `_on_skill_changed()` + `_sync_level_widget()` added: repopulates level widget items 1..max_lv from skill data on skill change, clamping previous selection
- `_repopulate_skill_combo()` calls `_sync_level_widget()` after rebuilding combo
- `get_skill_instance()` updated to use `_level_widget.value()`
- `QSpinBox` and `QComboBox` removed from Qt imports

**`gui/sections/passive_section.py`**:
- `_NoWheelCombo` local class removed
- Mastery combos use `LevelWidget(max_lv, include_off=True)` with `valueChanged` signal
- `_get_mastery_value`: `currentData() or 0` → `combo.value()`
- `_set_mastery_value`: `findData`/`setCurrentIndex` → `combo.setValue(value)`
- Type annotation: `dict[str, QComboBox]` → `dict[str, LevelWidget]`

**`gui/sections/buffs_section.py`**:
- `_NoWheelCombo`, `_NoWheelSpin` local classes removed
- `_make_level_combo()` helper removed — all callers use `LevelWidget(...)`
- `_set_combo_value()` helper removed — callers use `.setValue()` / `.value()`
- All `currentIndexChanged` on level combos → `valueChanged`; `currentData()` → `.value()`
- `_make_caster_row()`: `lesson_key`/`lesson_label` params replaced with `lesson_widget: LevelWidget`; lesson no longer stored in `caster_store`
- `_bard_lesson` / `_dancer_lesson` (`LevelWidget`) created in `_build_bard_widget` / `_build_dancer_widget` and passed to `_make_caster_row`
- `_load_song_group` / `_collect_song_group`: `isinstance(QComboBox)` guard eliminated; all `caster_store` values are now `NoWheelSpin`
- `load_build` / `collect_into`: lesson load/collect via `_bard_lesson.setValue/value()` and `_dancer_lesson.setValue/value()`
- Type annotations updated throughout; `QComboBox`/`QSpinBox` removed from Qt imports

---

## GUI — Compact Mode Architecture Rework (GUI-CompactRework2)

Complete replacement of the single-string `compact_mode` system with two independent
boolean flags. No Hercules source reads. Pure architectural improvement.

**`gui/section.py`** — full rewrite of compact mode logic:
- Constructor param: `compact_mode: str` → `compact_modes: list[str]`
- Three boolean flags extracted: `_has_hidden`, `_has_header_summary`, `_has_slim_content`
- Optional `_header_summary_lbl: QLabel` added to header layout when `"header_summary"` present
- `_is_compact` → `_is_slim`; `set_compact_mode()` → `set_slim_mode()` with correct state machine:
  - `slim_content`: entering slim while expanded hides full content, calls `_enter_slim()`; exiting slim while expanded calls `_exit_slim()`, shows full content; toggle in slim cycles collapsed ↔ compact widget (never full content)
  - `header_summary`: auto-collapses on entering slim, restores on exit; header label always visible
- `_enter_compact_view` / `_exit_compact_view` → `_enter_slim` / `_exit_slim` (hooks)
- `_enter_slim` fallback: shows full content (graceful degradation for unimplemented stubs)
- `set_header_summary(text: str)` public API
- Old string values auto-convert in constructor for backward compat (`"compact_view"` → `["slim_content"]` etc.)
- New doc: `docs/compact_modes.md`

**`gui/layout_config.json`**:
- All `"compact_mode"` keys → `"compact_modes"` lists
- `compact_view` → `["slim_content"]` for stats, derived, equipment, player_debuffs, target
- `compact_view` → `["header_summary"]` for passive, buffs
- `hidden` → `["hidden"]`; `none` → `[]`

**`gui/panel_container.py`**:
- Reads `compact_modes` list from config; passes to section constructor as `compact_modes=`
- `sec.set_compact_mode(...)` → `sec.set_slim_mode(...)`

**All 14 section `__init__` signatures**: `compact_mode` param → `compact_modes`

**`slim_content` subclasses** (stats, derived, equipment, player_debuffs, target):
- `_enter_compact_view` → `_enter_slim`; `_exit_compact_view` → `_exit_slim`
- Removed from each: `self._pre_compact_collapsed = ...`, `self._content_frame.setVisible(False)`,
  `self._is_collapsed = False`, `self._arrow.setText("▼")` — base class now owns these

**`passive_section.py`** (→ `header_summary`):
- Removed: `_compact_widget`, `_compact_summary_lbl`, `_build_compact_widget()`, `_enter_slim()`, `_exit_slim()`
- All update sites (`_on_passives_changed`, `load_build`) → `set_header_summary(self._build_summary())`
- Initial call added at end of `__init__`

**`buffs_section.py`** (→ `header_summary`):
- Same pattern as passive_section; three update sites (`_on_changed`, `load_build`) + initial `__init__` call

---

## Session Q2 — BF_WEAPON Special Mechanics + DefenseFix Flags (partial G62)  2026-03-12

**Q2-1 — MO_FINGEROFFENSIVE ratio + hit count** (`core/calculators/modifiers/skill_ratio.py`)
- Ratio: `100 + 50*lv` (battle.c:2191-2192).
- Hit count: special-cased before `_BF_WEAPON_HIT_COUNT_FN` lookup — reads `build.mastery_levels.get("MO_CALLSPIRITS", 1)` as proxy for `sd->spiritball_old` (spheres held at cast, battle.c:4698-4704, `finger_offensive_type=0` default).
- Avoids the JSON `number_of_hits` fallback to ensure sphere count always governs (not the fixed max from skills.json).

**Q2-2 — MO_INVESTIGATE ratio** (`core/calculators/modifiers/skill_ratio.py`)
- Ratio: `100 + 75*lv` (battle.c:2194-2195).
- Note: `flag.pdef = flag.pdef2 = 2` set by Hercules at battle.c:4759; DEF reversal handled in DefenseFix (see Q2-4).

**Q2-3 — AM_ACIDTERROR ratio** (`core/calculators/modifiers/skill_ratio.py`)
- Ratio: `100 + 40*lv` (battle.c:2187-2189, `#else` pre-renewal block).
- Note: custom ATK+MATK block at battle.c:5424 is `#ifdef RENEWAL` only — pre-renewal uses standard pipeline.
- `def1=0` override handled in DefenseFix (see Q2-4).

**Q2-4 — DefenseFix flag handling** (`core/calculators/modifiers/defense_fix.py`, `core/calculators/battle_pipeline.py`)

Three new behaviours added to `DefenseFix.calculate()`:

*NK_IGNORE_DEF* (new `nk_flags: list` param):
- Source: battle.c:4673 — `flag.idef = flag.idef2 = (nk&NK_IGNORE_DEF) ? 1 : 0;`
- Same skip-everything outcome as crit but distinct display note.
- `battle_pipeline.py` now passes `skill_name` + `nk_flags` (from `loader.get_skill`) to `DefenseFix.calculate()`.

*AM_ACIDTERROR* (`def1 = 0`):
- Source: battle.c:1474 (`#ifndef RENEWAL`) — `if (skill_id == AM_ACIDTERROR) def1 = 0;`
- Applied after ignore_def_rate / VIT penalty adjustments and before the formula branch.
- Normal pre-renewal formula then runs; only vit_def (soft DEF) reduces damage.

*MO_INVESTIGATE* (pdef=2):
- Source: battle.c:4759 (`flag.pdef = flag.pdef2 = 2`); battle.c:1539 (`#else` pre-re): `damage = damage * pdef * (def1+vit_def) / 100` (pdef=2).
- DEF reversal: higher DEF → higher damage. vit_def NOT subtracted separately (battle.c:1542 `flag&2` blocks it).
- PMF uses average vit_def; step note shows multiplier range `[factor_lo/100×, factor_hi/100×]`.

*New gap G68*: `pdef=1` from `def_ratio_atk_ele/race` card bonuses (battle.c:5686/5694) not yet implemented — needs `gear_bonuses` field + parser.

**`IMPLEMENTED_BF_WEAPON_SKILLS`**: 31 → 34 (added MO_FINGEROFFENSIVE, MO_INVESTIGATE, AM_ACIDTERROR).

---

## Session Q2-cont — Runtime-Param Skill Ratios + skill_params UI  2026-03-12

**Q2-cont-1 — `skill_params` on PlayerBuild** (`core/models/build.py`)
- New field: `skill_params: Dict[str, Any] = field(default_factory=dict)`.
- Not saved to disk; populated from GUI at each pipeline run via `collect_into()`.
- Keys (all combat-context values): `KN_CHARGEATK_dist`, `MC_CARTREVOLUTION_pct`, `MO_EXTREMITYFIST_sp`, `TK_JUMPKICK_combo`, `TK_JUMPKICK_running`.

**Q2-cont-2 — 4 param-skill ratios** (`core/calculators/modifiers/skill_ratio.py`)
- Added `_BF_WEAPON_PARAM_SKILLS` frozenset (4 skills); `IMPLEMENTED_BF_WEAPON_SKILLS` now includes these.
- Special-case blocks at the top of `SkillRatio.calculate()` before the `_BF_WEAPON_RATIOS` dict lookup (param skills need `build`, can't be plain lambdas).

Formulas (all confirmed in session_roadmap.md Q2 — no re-read needed):
| Skill | Formula | Source |
|---|---|---|
| `KN_CHARGEATK` | `100 + 100*min((dist-1)//3, 2)` | battle.c:2350-2359 |
| `MC_CARTREVOLUTION` | `150 + cart_pct` (+50+100*w/wmax) | battle.c:2120-2127 |
| `MO_EXTREMITYFIST` | `min(100+100*(8+sp//10), 60000)` | battle.c:2197-2206 #ifndef RENEWAL |
| `TK_JUMPKICK` | `(30+10*lv [+10*lv//3 combo]) * (2 if running)` | battle.c:2290-2300 |

**Q2-cont-3 — Skill params UI** (`gui/sections/combat_controls.py`)
- New grid row 1 (params row): shown/hidden contextually when a param skill is selected.
- Sub-widgets (all hidden by default):
  - `KN_CHARGEATK`: `NoWheelCombo` with 3 distance tiers (1-3/4-6/7+), values 1/4/7.
  - `MC_CARTREVOLUTION`: `NoWheelSpin` 0–100 step 10 with "%" suffix.
  - `MO_EXTREMITYFIST`: `NoWheelSpin` 0–9999 for current SP.
  - `TK_JUMPKICK`: Two `QCheckBox`es ("Combo Attack", "Running (TK_RUN)").
- `_update_skill_params_ui()` called on every skill change.
- `collect_into()` writes all param values to `build.skill_params`.
- `load_build()` resets all params to defaults (not persisted).
- Target row shifted from grid row 1→2, Env from row 2→3.

**`IMPLEMENTED_BF_WEAPON_SKILLS`**: 34 → 38 (added 4 param skills).

**Q2-cont addendum — MO_FINGEROFFENSIVE sphere priority** (`core/calculators/modifiers/skill_ratio.py`)
Hit count lookup priority updated: `skill_params["MO_FINGEROFFENSIVE_spheres"]` → `active_status_levels["MO_SPIRITBALL"]` → `mastery_levels["MO_CALLSPIRITS"]` (mastery fallback kept for saves that never set the buff).

**Q2-cont addendum — MO_FINGEROFFENSIVE sphere dropdown** (`gui/sections/combat_controls.py`)
Sphere count `NoWheelCombo` (1–5) shown in params row when MO_FINGEROFFENSIVE selected.
`load_build`: pre-populates from `active_status_levels["MO_SPIRITBALL"]` (or mastery fallback) so it starts in sync with the buffs section.

---

## Session GUI-BuffLvl — Buff Level Widget Rework + Sphere Sync  2026-03-12

**GUI-BuffLvl-1 — Self buff level widgets** (`gui/sections/buffs_section.py`)
All `has_lv=True` self buffs now use combo-only layout (QLabel in col 0 + `LevelWidget(include_off=True)` in col 1), replacing the previous QCheckBox + disabled-LevelWidget pair. Value 0 = inactive; value > 0 = active at that level.
Special case: MO_SPIRITBALL relabels the off item from "Off" to "0" (sphere count reads naturally as a number).
Affected buffs (12):
SC_AURABLADE, SC_OVERTHRUST, SC_OVERTHRUSTMAX, SC_SPEARQUICKEN, SC_ENDURE, SC_DEFENDER,
MO_SPIRITBALL, SC_EXPLOSIONSPIRITS, SC_CONCENTRATION, GS_COINS, SC_GS_GATLINGFEVER, SC_NJ_NEN.
- `collect_into`: writes `active[sc_key] = val` if `val > 0`; no checkbox needed.
- `load_build`: `combo.setValue(active.get(sc_key, 0))`.
- `update_job`: on hide, resets combo to index 0 (no checkbox to uncheck).
- `_build_summary`: includes combo-only buffs when value > 0.

**GUI-BuffLvl-2 — Bidirectional spirit sphere sync** (`gui/sections/buffs_section.py`, `gui/sections/combat_controls.py`, `gui/main_window.py`)
MO_SPIRITBALL combo (buffs section) and the MO_FINGEROFFENSIVE sphere combo (combat params) are now kept in sync in both directions:
- `BuffsSection`: `spirit_spheres_changed = Signal(int)` emitted when MO_SPIRITBALL changes; `set_spirit_spheres(n)` setter uses blockSignals (no re-emit).
- `CombatControlsSection`: `spirit_spheres_changed = Signal(int)` emitted from new `_on_spheres_changed()`; `set_spirit_spheres(n)` setter uses blockSignals (no re-emit).
- `MainWindow._connect_builder_signals`: `buffs_section.spirit_spheres_changed → combat_controls.set_spirit_spheres`.
- `MainWindow._connect_combat_signals`: `combat_controls.spirit_spheres_changed → buffs_section.set_spirit_spheres`.
Circular loop avoided by design: setter methods never re-emit the signal.

**Known bug (G69) — MO_EXTREMITYFIST ratio**: Flagged for Q3 fix. Formula in `skill_ratio.py` is incorrect. Re-read battle.c:2197-2206 #ifndef RENEWAL before fixing.

---

## Session G69-Analysis (2026-03-13) — investigation only, no implementation

**G69 source investigation**: Read battle.c:2197-2206 #ifndef RENEWAL. Ratio formula
`min(100+100*(8+sp//10), 60000)` confirmed correct — the placeholder written in Q2 was right.
G69 description was wrong; the real bugs are architectural.

Three pipeline bugs confirmed:
1. `battle_pipeline.py:429` reads `"nk_flags"` but skills.json uses `"damage_type"` →
   `nk_ignore_def` never triggers for any skill (MO_EXTREMITYFIST has `IgnoreDefense` in
   `damage_type` per skill_db.conf, confirmed).
2. `SkillInstance.ignore_size_fix` never set for MO_EXTREMITYFIST → SizeFix applied
   incorrectly. Source: battle.c:5279 `#ifndef RENEWAL` passes `i=8` to `calc_base_damage2`,
   which skips SizeFix when `flag&8` (calc_base_damage2:668).
3. `mastery_fix.py` doesn't exclude MO_EXTREMITYFIST. Source: battle.c:838-842 returns
   early from `battle_calc_masteryfix` for MO_INVESTIGATE/EXTREMITYFIST/CR_GRANDCROSS/
   NJ_ISSEN/CR_ACIDDEMONSTRATION.

Architectural fix plan approved: hydrate `SkillInstance` fully before `_run_branch`; add
`name`/`nk_ignore_def`/`nk_ignore_flee` fields to SkillInstance; pass `skill` to
DefenseFix + MasteryFix. Full plan in session_roadmap.md Q3 Step 0. Four files: skill.py,
battle_pipeline.py, defense_fix.py, mastery_fix.py.

---

## Session Q3-partial (2026-03-13) — G69 fix + G55 fix + Q3 ratio source confirmation

**G69 — Architectural pipeline fix (4 files)**

`core/models/skill.py`: Added `name: str = ""`, `nk_ignore_def: bool = False`, `nk_ignore_flee: bool = False` fields to SkillInstance. (ignore_size_fix already existed.)

`core/calculators/battle_pipeline.py`: After resolving `skill_name` in `calculate()`, now hydrates `skill` before any `_run_branch` call:
- `skill.name = skill_name`
- `damage_type = skill_data.get("damage_type", [])` — corrects the old `"nk_flags"` bug
- `skill.nk_ignore_def = "IgnoreDefense" in damage_type`
- `skill.nk_ignore_flee = "IgnoreFlee" in damage_type`
- `_NO_SIZEFIX_SKILLS = frozenset({"MO_EXTREMITYFIST"})` → `skill.ignore_size_fix`
- MasteryFix call in `_run_branch` now passes `skill`
- DefenseFix call in `_run_branch` now passes `skill=skill` (removed `_sk_data`/`_sk_name`/`_nk_flags` re-load)

`core/calculators/modifiers/defense_fix.py`: Replaced `skill_name: str, nk_flags: list` params with `skill: SkillInstance = None`. Uses `skill.nk_ignore_def` for NK bypass, `skill.name` for AM_ACIDTERROR and MO_INVESTIGATE checks.

`core/calculators/modifiers/mastery_fix.py`: Added `skill: SkillInstance = None` param. Added `_MASTERY_EXEMPT_SKILLS = frozenset({"MO_INVESTIGATE", "MO_EXTREMITYFIST", "CR_GRANDCROSS", "NJ_ISSEN", "CR_ACIDDEMONSTRATION"})` (source: battle.c:838-842). Added early-return bypass step when `skill.name in _MASTERY_EXEMPT_SKILLS`.

**G55 — NJ_TOBIDOUGU mastery fix**

`mastery_fix.py`: The old `weapon.weapon_type == "Shuriken"` check silently never fired because "Shuriken" doesn't exist as a weapon_type in item_db. Fixed to `skill is not None and skill.name == "NJ_SYURIKEN"` (source: battle.c:843-850: `case NJ_SYURIKEN: if(NJ_TOBIDOUGU>0 && weapon) damage += 3*skill2_lv`).

Also added NJ_KUNAI mastery: `if skill.name == "NJ_KUNAI": damage += 60` (battle.c:852-855 `#ifndef RENEWAL`).

**Q3 ratio source confirmation (battle.c:2300-2352, 5172-5510) — NOT YET in skill_ratio.py**

All 14 BF_WEAPON GS/NJ ratios confirmed. See session_roadmap.md Q3 Step 1 for exact formulas.
NJ_SYURIKEN: ratio=100% + ATK_ADD(4*lv) flat (battle.c:5506 #ifndef RENEWAL).
Deferred: NJ_ISSEN (HP formula), NJ_ZENYNAGE/GS_FLING (BF_MISC), GS_MAGICALBULLET (needs StatusData).
NJ BF_MAGIC ratios: must re-read battle.c:1699-1757 at start of next session before implementing.

---

## Session Q3 — Ninja Hybrid + Gunslinger

**Step 1 — GS + NJ BF_WEAPON ratios (`skill_ratio.py`)**

9 Gunslinger skills added to `_BF_WEAPON_RATIOS`: GS_TRIPLEACTION/BULLSEYE/TRACKING/PIERCINGSHOT/RAPIDSHOWER/DESPERADO/DUST/FULLBUSTER/SPREADATTACK. Sources: battle.c:2300-2337 #ifndef RENEWAL.

5 Ninja BF_WEAPON skills added: NJ_HUUMA/KASUMIKIRI/KIRIKAGE/KUNAI/SYURIKEN. Sources: battle.c:2338-2348.

NJ_SYURIKEN special case: `flat_add = 4 * skill.level` applied via `_add_flat` after `_scale_floor(ratio)`, before hit multiply. Source: battle.c:5506 #ifndef RENEWAL `ATK_ADD(4*skill_lv)`. `_add_flat` import added.

BF_MISC infrastructure: `_BF_MISC_RATIOS: dict = {}` + `IMPLEMENTED_BF_MISC_SKILLS` frozenset. Wired into `combat_controls.py` and `skill_browser.py` `_IMPLEMENTED_SKILLS`.

KN_PIERCE crash fix: `tgt.size + 1` was broken (`size` is a string). Replaced with `_SIZE_TO_HITS = {"Small": 1, "Medium": 2, "Large": 3}` lookup.

IMPLEMENTED_BF_WEAPON_SKILLS: 31 (Q1) → 38 (Q2) → 55 (Q3, includes GS+NJ).

**Step 2 — NJ BF_MAGIC ratios (`skill_ratio.py`)**

Read battle.c:1699-1757 this session. The roadmap table (`100+100×lv` for all) was WRONG. Actual source:
- NJ_KOUENKA: 90 (skillratio -= 10; no lv modifier)
- NJ_KAENSIN: 50 (skillratio -= 50)
- NJ_BAKUENRYU: 50 + 50×lv (skillratio += 50*(lv-1))
- NJ_HYOUSENSOU: 100 (case is #ifdef RENEWAL only → pre-re default)
- NJ_HYOUSYOURAKU: 100 + 50×lv (skillratio += 50*lv)
- NJ_RAIGEKISAI: 160 + 40×lv (skillratio += 60+40*lv)
- NJ_KAMAITACHI: 100 + 100×lv (fall-through to NPC_ENERGYDRAIN: skillratio += 100*lv)

Charm bonuses (+20/10/15/25/15/10 per charm_count for fire/fire/fire/water/wind/wind) deferred: requires `sd->charm_type/charm_count` — new G71 gap.

IMPLEMENTED_BF_MAGIC_SKILLS: 23 (prior) → 30 (Q3, adds 7 NJ spells).

---

## Session Q3-fix — Hit Count Audit (2026-03-13)

Full audit of `number_of_hits` from skills.json against Hercules `skill_db.conf` for all 21
GS/NJ skills added in Q3. All values confirmed correct. No code changes required.

**Confirmed actual multi-hit (positive number_of_hits — PMF multiplied):**
- GS_TRIPLEACTION: 3 hits (skill_db.conf `NumberOfHits: 3`); ratio 150% × 3 = 450% total
- GS_RAPIDSHOWER: 5 hits constant (skill_db.conf `NumberOfHits: 5`); ratio (100+10×lv)% × 5
- NJ_KUNAI: 3 hits (skill_db.conf `NumberOfHits: 3`); ratio 100% × 3 + mastery +60
- NJ_KOUENKA (BF_MAGIC): lv hits (1 at lv1, 10 at lv10); ratio 90% per hit
- NJ_BAKUENRYU (BF_MAGIC): 3 hits (skill_db.conf `NumberOfHits: 3`); ratio (50+50×lv)% × 3
- NJ_HYOUSENSOU (BF_MAGIC): lv+2 hits (3 at lv1, 12 at lv10); ratio 100% per hit

**Confirmed cosmetic multi-hit (negative number_of_hits — PMF unchanged):**
- NJ_HUUMA: -3/-3/-4/-4/-5 (skill_db.conf negative per level); ratio 150+150×lv encodes total

**Confirmed single-hit (number_of_hits=1):**
- GS_BULLSEYE, GS_TRACKING, GS_PIERCINGSHOT, GS_DESPERADO, GS_DUST, GS_FULLBUSTER, GS_SPREADATTACK
- NJ_KASUMIKIRI, NJ_KIRIKAGE, NJ_SYURIKEN, NJ_KAENSIN, NJ_HYOUSYOURAKU, NJ_RAIGEKISAI, NJ_KAMAITACHI

**The `flag.tdef = 1` block for NJ_KUNAI/NJ_SYURIKEN (skill.c:4791) is `#ifdef RENEWAL` only —
no pre-renewal effect.**

**NJ_BAKUENRYU, NJ_HYOUSENSOU, NJ_HYOUSYOURAKU, NJ_RAIGEKISAI, NJ_KAMAITACHI all confirmed
`AttackType: "Magic"` in skill_db.conf → correctly in `_BF_MAGIC_RATIOS`.**

---

## Session R — Target Debuff System (2026-03-13)

**G48 — Target debuff system (full)**

New field `target_active_scs: Dict[str, int]` on `Target` (core/models/target.py).
New section `gui/sections/target_state_section.py`: SC_STONE/FREEZE/STUN toggles (mob-only);
SC_PROVOKE level 1–10 (mob-only); SC_ETERNALCHAOS toggle (both). Two-method API:
`collect_into(build)` → support_buffs; `apply_to_target(target)` → mutates Target fields directly.

**G70 — Skill combo empty on first load**

`combat_controls.py` load_build() now calls `_repopulate_skill_combo(build.job_id, preserve_selection=False)` at end, so skill list is populated with the correct job on build load, not just on job-change.

**defense_fix.py — SC_STONE/FREEZE/STUN/PROVOKE/EC**

- SC_STONE or SC_FREEZE active on target: `def1 >>= 1` (status.c:5013-5016 #ifndef RENEWAL)
- SC_ETERNALCHAOS active (build.support_buffs): `def2 = 0` (status.c:5090)
- SC_PROVOKE level: PC path reduces `dp` by `5+5×lv`; mob path scales vd_min/max/avg by `(100 - 5+5×lv) / 100` (status.c:4401-4402)
- calculate_magic(): SC_STONE or SC_FREEZE → `mdef = min(100, mdef + 25*mdef//100)` (status.c:5153-5156)

**hit_chance.py — Force-hit**

SC_STONE, SC_FREEZE, or SC_STUN on target → return (100.0, 0.0) immediately (battle.c:5014-5015).

**magic_pipeline.py — PR_LEXAETERNA**

After FinalRateBonus, if `build.support_buffs.get("PR_LEXAETERNA")`: `pmf × 2` with its own
pipeline step "Lex Aeterna". Source: status.c:8490.

**buffs_section.py — SC_SIEGFRIED storage moved**

SC_SIEGFRIED in ensemble loop now writes to `build.support_buffs` (not song_state) in both
`collect_into` and `load_build`. Architectural correction: SC_SIEGFRIED is a received party
ensemble buff with an incoming pipeline effect; same home as SC_BLESSING/SC_ADRENALINE.

**layout_config.json / panel_container.py / main_window.py — target_state_section wired**

- layout_config.json: `target_state_section` entry added before `step_breakdown` (combat panel, collapsed, slim_content)
- panel_container.py: import + factory entry
- main_window.py: import, typed ref `_target_state`, signal wiring, collect_into, load_build, set_target_type + apply_to_target after target resolved, SC_SIEGFRIED incoming resist (55+5×lv added to all non-Neutral sub_ele on player_target)

---

## Session Plan-SC — 2026-03-13 — Debuff Audit + Architecture Planning

**No code changes.** Planning and architecture session establishing the work queue for
Sessions Arch, SC1, and SC2.

**Debuff audit completed** (replaces investigation phase that was in Session SC stub):
- Full table of target-side and player-side SC status for all debuffs in scope.
- Confirmed implemented: target SC_STONE/FREEZE/STUN/EC/PROVOKE/DECREASEAGI; player SC_BLIND/CURSE/DECREASEAGI.
- Missing target-side (9 SCs): SC_BLIND, SC_CURSE, SC_SLEEP, SC_POISON, SC_DONTFORGETME, SC_MINDBREAKER, SC_SIGNUCRUCIS, SC_BLESSING-debuff, SC_QUAGMIRE.
- Missing player-side (12 SCs): SC_STUN/FREEZE/STONE/SLEEP/POISON/DONTFORGETME/EC/MINDBREAKER/PROVOKE/SIGNUCRUCIS/BLESSING-debuff/QUAGMIRE.

**Scope decisions made**:
- All debuffs that affect players apply to both build panel (player) and combat panel (target), except strip skills and elemental change.
- Players can have Undead attribute → SIGNUCRUCIS + BLESSING-debuff apply to player.
- SC_PROVOKE: debuff section on both panels; ATK buff deferred to self-buffs if other cast methods found.
- No short-circuit for immobilising SCs (Stun/Freeze/Stone/Sleep) on player — UX decision.
- Spider Web / Flying: out of scope for current calculator.

**Architecture decision**:
- Player target pipeline (pvp_build → StatusCalculator → player_build_to_target) was already correctly implemented (Session F/R).
- Gap found: debuffs from TargetStateSection run *after* pvp_status is computed; cascading stat effects not reflected in incoming pipeline.
- Fix: `collect_target_player_scs()` on TargetStateSection; route to `pvp_eff.player_active_scs` before StatusCalculator call.
- New `core/calculators/target_utils.py` with `apply_mob_scs()` centralises mob-target stat SC application.

**New gaps**: G78 (Arch routing fix), G79 (target debuffs SC1), G80 (player debuffs SC2).
**Session SC stub replaced** with finalised SC1 + SC2 entries in session_roadmap.md.
