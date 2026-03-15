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

---

## Session Arch — 2026-03-13 — Debuff Routing Fix (G78)

**Problem**: `pvp_status = StatusCalculator(pvp_eff)` was computed before
`apply_to_target(target)` ran, so stat-cascade debuffs (DECREASEAGI → AGI →
FLEE/ASPD) were not reflected in `pvp_status`. Incoming pipeline used unbuffed
pvp stats.

**`core/calculators/target_utils.py`** (new file):
- `apply_mob_scs(target)`: reads `target.target_active_scs` and applies stat
  mutations for mob targets. Currently: SC_DECREASEAGI → `agi -= 2+lv`
  (status.c:7633, 4025-4026). Mob targets are not run through StatusCalculator
  so mutations are applied here directly. Session SC1 extends this.

**`gui/sections/target_state_section.py`**:
- Updated class docstring to describe the now-three-method API.
- Added `collect_target_player_scs() → dict[str, int]`: returns stat-cascade SCs
  for player targets (currently SC_DECREASEAGI). These must be merged into
  `pvp_eff.player_active_scs` before StatusCalculator runs.
- `apply_to_target()`: removed the `target.agi -= (2+lv)` direct mutation.
  Stat mutations now belong in `apply_mob_scs()` (mob path) or StatusCalculator
  (player path). `apply_to_target()` is now purely for pipeline-level flags
  (target_active_scs, element override, DEF strip).

**`gui/main_window.py`**:
- Import `target_utils` from `core.calculators`.
- Mob path: after `apply_to_target(target)`, call `target_utils.apply_mob_scs(target)`.
- PvP path: before `StatusCalculator.calculate(pvp_eff, pvp_weapon)`, call
  `collect_target_player_scs()` and merge into `pvp_eff.player_active_scs` via
  `dataclasses.replace()` (immutable — does not mutate the loaded build object).

**Gaps closed**: G78.

---

## Session SC1-research — 2026-03-13 — Source Read Pass for SC1

**No code changes.** Source verification session for Session SC1 target debuffs.

**Confirmed formulas** (all status.c unless noted):
- SC_BLIND: `hit -= hit*25/100` (4817-4818), `flee -= flee*25/100` (4902-4903)
- SC_CURSE: `luk = 0` via hard `return 0` (4261-4262)
- SC_POISON: `def_percent -= 25` no guard (4431-4432)
- SC_MINDBREAKER: `val2=20*lv` (`matk_percent += val2`, 4376-4377); `val3=12*lv` (`mdef_percent -= val3`, 4453-4454); val assignments at 8379-8382
- SC_CRUCIS (correct name — not SC_SIGNUCRUCIS): `def -= def*val2/100` (5022-5023); mob-only — BL_PC hard-blocked at 7205-7207
- SC_BLESSING debuff: `str >>= 1`, `dex >>= 1` when val2=0 (3964-3968, 4213-4218); mob-only — BL_PC always gets buff path (8271-8275)
- SC_QUAGMIRE: `agi -= val2`, `dex -= val2` (4027-4028, 4211-4212); `val2=10*lv` for mobs (8343-8344)
- SC_DONTFORGETME: `aspd_rate += 10*val2` (5666-5667); no FLEE effect found in flee function; val2 assignment not yet found
- SC_SLEEP: `cri <<= 1` (battle.c:4959); force-hit via opt1 not yet confirmed

**Scope corrections discovered**:
- SC_CRUCIS (not SC_SIGNUCRUCIS) is mob-only — remove from SC2 player debuff list
- SC_BLESSING debuff is mob-only — remove from SC2 player debuff list
- SC_DONTFORGETME has no FLEE effect — ASPD + movement speed only

**Remaining for SC1 session start** (2 greps only):
1. SC_SLEEP force-hit: check opt1 path in battle.c hit calculation
2. SC_DONTFORGETME val2: find `case DC_DONTFORGETME:` in skill.c ~line 13270

---

## Session SC1 — 2026-03-14 — Target Debuffs (G79, G81)

**`core/calculators/target_utils.py`**:
- Extended `apply_mob_scs(target)` with all remaining mob-path debuffs:
  SC_BLIND (`hit/flee ×75%`, status.c:4817/4902), SC_CURSE (`luk=0`, status.c:4261),
  SC_POISON (`def_percent−=25`, status.c:4431), SC_QUAGMIRE (`agi−=val2, dex−=val2`,
  status.c:4027/4211), SC_BLESSING debuff (`str>>=1, dex>>=1`, Undead/Demon only,
  status.c:3964/4213), SC_CRUCIS (`def−=def×val2/100`, Undead/Demon only, status.c:5022),
  SC_MINDBREAKER (`matk_percent+=20×lv`, `mdef_percent−=12×lv`, status.c:4376/4453),
  SC_DONTFORGETME (`aspd_rate+=10×val2`; val2=dancer_agi/10+3×lv+5, skill.c:13270,
  status.c:5667; dancer AGI stored as `SC_DONTFORGETME_agi` in target_active_scs).
- Boss immunities: each SC guarded by `_blocked()` against `_BOSS_IMMUNE_SCS` +
  `_BOSS_IMMUNE_NOBOSS` frozensets.
- Removed `status: StatusData` parameter — dancer AGI now passed via scs dict.

**`core/calculators/status_calculator.py`** (player attacker path):
- Added SC_BLIND (`hit×75%, flee×75%`) and SC_CURSE (`luk=0`) handling in player_scs block.
- Added SC_QUAGMIRE (`agi−=10×lv`, `dex−=10×lv`) in player_scs block.
- Added SC_MINDBREAKER (`mdef×(100−12×lv)//100`) in player_scs block.
- Removed wrong SC_DONTFORGETME block (was approximating dancer AGI from player ASPD path).

**`core/calculators/modifiers/defense_fix.py`**:
- Mob path: `target.def_percent` applied to vit_def min/max/avg after Provoke block.
- Magic path: `target.mdef_percent` applied before SC_STONE/FREEZE MDEF boost.

**`core/calculators/modifiers/crit_chance.py`**:
- SC_SLEEP: `cri <<= 1` when target has SC_SLEEP (battle.c:4959).

**`core/calculators/modifiers/hit_chance.py`**:
- SC_SLEEP added to force-hit set (opt1 OPT1_SLEEP path, battle.c:5014-5015).

**`gui/sections/target_state_section.py`**:
- Applied Debuffs: Quagmire LevelWidget(5), Don't Forget Me LevelWidget(10) + dancer AGI
  QSpinBox (`_sb_dfm_agi`, range 0–999), Mind Breaker LevelWidget(5).
- Status Ailments: Blind, Cursed, Asleep checkboxes (session-only).
- Monster State: Signum Crucis LevelWidget(10), Blessing Debuff checkbox.
- `set_is_boss(is_boss)`: disables/clears boss-immune SC widgets when target.is_boss=True.
- `apply_to_target()`: SC_DONTFORGETME stores both `lv` and `SC_DONTFORGETME_agi` in scs dict.
- `collect_into()`: SC_DONTFORGETME removed (session-only target debuff, not a player buff).
- `collect_target_player_scs()`: SC_DONTFORGETME removed (mob-path only).
- `load_build()`: DFM level + AGI spinbox reset on load (session-only).

**`gui/main_window.py`**:
- `apply_mob_scs(target)` call drops `status` arg (no longer needed).
- `set_is_boss(target.is_boss)` called in pipeline run.

**New Target fields** (`core/models/target.py`):
  `str`, `dex`, `hit` (SC_BLESSING/QUAGMIRE/BLIND propagation);
  `def_percent`, `mdef_percent`, `matk_percent`, `aspd_rate` (SC_POISON/MINDBREAKER/DONTFORGETME).

**Gaps closed**: G79 (target debuffs), G81 (boss protocol).

---

## Session SC2 — 2026-03-14 — Player Debuffs + G77 Lex Aeterna

**Gaps closed**: G77 (Lex Aeterna for BF_WEAPON), G80 (player-side debuffs).

**`core/calculators/battle_pipeline.py`** (_run_branch):
- Added PR_LEXAETERNA ×2 step after FinalRateBonus (G77).
- Reads `build.support_buffs.get("PR_LEXAETERNA")` — same key as magic_pipeline.py.
- Now applies to all BF_WEAPON hits (normal, crit, katar, dual-wield, proc branches).

**`core/calculators/status_calculator.py`** (player_active_scs path):
- SC_POISON: `def_percent -= 25` (status.c:4431-4432)
- SC_PROVOKE: `def_percent -= 5+5*lv` (status.c:4401-4402)
- def2 display scaling now triggers on `def_percent != 100` (was `if angelus_lv`)
- SC_ETERNALCHAOS: `def2 = 0` after def_percent scaling (status.c:5090)
- SC_DONTFORGETME: `aspd_rate += 10*val2` in ASPD slowdown section; val2=agi//10+3lv+5; `SC_DONTFORGETME_agi` aux key mirrors mob path (status.c:5667, skill.c:13270)
- SC_MINDBREAKER matk boost: `matk_min/max *= (100+20*lv)//100` after MATK computed (status.c:4376-4377)

**`gui/sections/player_debuffs_section.py`** (full rewrite):
- 14 debuff widgets: Curse, Blind, Decrease AGI, Quagmire, Mind Breaker, Poison, Provoke,
  Eternal Chaos, Don't Forget Me (LevelWidget + AGI spinbox), Stunned, Frozen, Petrified, Asleep.
- Freeze/Stone mutex (same as target_state_section).
- All debuffs persisted in `build.player_active_scs`.
- load_build() / collect_into() fully symmetrical.

**`core/build_manager.py`** (player_build_to_target):
- Propagates SC_STUN/FREEZE/STONE/SLEEP from `build.player_active_scs` to `target_active_scs`
  so incoming hit_chance.py sees force-hit flags (mirrors apply_to_target() on target side).
- FREEZE → element=1 (Water), STONE → element=2 (Earth) override on player Target.

**Architecture note**: See `docs/debuff_architecture.md` for full routing map of both target-side
and player-side debuffs, including known inconsistencies with routing through support_buffs
vs target_active_scs for some target-side SCs (PROVOKE, ETERNALCHAOS, LEX).

---

## Session SC2-Arch — 2026-03-14 — Debuff Routing Refactor

Resolved all three ⚠️ routing inconsistencies identified in `docs/debuff_architecture.md`.
SC_ETERNALCHAOS, SC_PROVOKE, and PR_LEXAETERNA were previously bypassing `target_active_scs`
and being read directly from `build.support_buffs` by pipeline modifier files.

**`core/models/build.py`**:
- Added `target_debuffs: Dict[str, object]` field — dedicated storage for persisted target
  debuffs (SC_ETERNALCHAOS, SC_PROVOKE, SC_DECREASEAGI, SC_QUAGMIRE, SC_MINDBREAKER,
  PR_LEXAETERNA). Pipeline never reads this dict; only used for save/load round-trip.

**`gui/sections/target_state_section.py`**:
- `collect_into()`: now writes to `build.target_debuffs` (was `build.support_buffs`);
  also clears the stale support_buffs keys from previous sessions.
- `apply_to_target()`: now writes SC_ETERNALCHAOS, SC_PROVOKE, and PR_LEXAETERNA into
  `target_active_scs` (previously absent — they went to support_buffs only).
- `collect_target_player_scs()`: added SC_ETERNALCHAOS and SC_PROVOKE so the PvP path
  feeds these through StatusCalculator correctly.
- `load_build()`: reads from `build.target_debuffs` (was `build.support_buffs`).
- Docstring updated to reflect two-method pipeline API.

**`core/calculators/target_utils.py`**:
- Added SC_PROVOKE to `apply_mob_scs()`: `target.def_percent -= (5 + 5*lv)`.
  NoBoss guard via existing `_BOSS_IMMUNE_NOBOSS`. Source: status.c:4401-4402.

**`core/calculators/modifiers/defense_fix.py`**:
- SC_ETERNALCHAOS: now reads from `target_scs` (target.target_active_scs) instead of
  `build.support_buffs`. Works for mob, PvP, and incoming player paths.
- SC_PROVOKE: removed all `prov_lv` logic. Effect is now pre-applied in `target.def_percent`
  by `apply_mob_scs` (mob) or `StatusCalculator` (player), so defense_fix.py reads it
  uniformly via `target.def_percent` / `dp`.

**`core/calculators/battle_pipeline.py`** and **`core/calculators/magic_pipeline.py`**:
- PR_LEXAETERNA check: changed from `build.support_buffs.get(...)` to
  `target.target_active_scs.get("PR_LEXAETERNA")`.

**`core/build_manager.py`**:
- `player_build_to_target()`: propagates SC_ETERNALCHAOS from `player_active_scs` to
  `target_scs` so the incoming pipeline's defense_fix.py sees the flag.

**`docs/debuff_architecture.md`**: fully updated to reflect resolved routing; ⚠️ markers removed.

---

## Session S-2 — 2026-03-14 — Missing Fields + Dead Field Wiring

**Bugs fixed**: `bMatkRate` (131 items) and `bMaxHPrate` (45 items) were parsed by `item_script_parser.py`
but their effect was silently dropped — `bonus_definitions.py` had `field=None` for both, and no
corresponding fields existed in `GearBonuses` or `PlayerBuild`. MATK/MaxHP from gear were therefore
always incorrect for items with these bonuses.

**New fields:**
- `GearBonuses` (`core/models/gear_bonuses.py`): `matk_rate: int`, `maxhp_rate: int`,
  `script_atk_ele: int | None`, `script_def_ele: int | None` (last two are S-3 stubs).
- `PlayerBuild` (`core/models/build.py`): `bonus_crit_atk_rate: int`, `bonus_matk_rate: int`,
  `bonus_maxhp_rate: int`.

**`core/bonus_definitions.py`**:
- `bMatkRate`: `field="matk_rate"` (was `None`). Source: status.c:1995-1997 — `matk *= matk_rate/100`; starts at 100, gear adds delta.
- `bMaxHPrate`: `field="maxhp_rate"` (was `None`). Source: status.c:1937 — `max_hp = APPLY_RATE(max_hp, hprate)`; starts at 100, gear adds delta.

**`core/calculators/status_calculator.py`**:
- MATK section: applies `build.bonus_matk_rate` as `matk *= (100+rate)//100` after base INT formula, before SC_MINDBREAKER. (status.c:1995-1997)
- MaxHP section: applies `build.bonus_maxhp_rate` as `max_hp *= (100+rate)//100` after CR_TRUST addend, before SC_APPLEIDUN/SC_DELUGE songs. (status.c:1937)

**New `core/build_applicator.py`** (extracted from MainWindow):
- `apply_gear_bonuses(build, gear_bonuses) -> PlayerBuild`: injects GearBonuses + Active Items + Manual Adj + SC stat bonuses into PlayerBuild overlay. Now also wires `bonus_crit_atk_rate`, `bonus_matk_rate`, `bonus_maxhp_rate`.
- `compute_sc_stat_bonuses(support_buffs) -> dict[str, int]`: SC_BLESSING/INC_AGI/GLORIA → stat deltas.

**`gui/main_window.py`**:
- Removed `_apply_gear_bonuses()` and `_sc_stat_bonuses()` private methods.
- All call sites replaced with `build_applicator.apply_gear_bonuses(build, gb)` and `build_applicator.compute_sc_stat_bonuses(...)`.
- `GearBonusAggregator.compute()` now called once per pipeline run (was called twice redundantly).
- `GearBonuses` import removed (no longer directly referenced).

**`core/calculators/modifiers/crit_atk_rate.py`**: `getattr(build, "bonus_crit_atk_rate", 0)` → `build.bonus_crit_atk_rate` (field now explicit).

**Note**: `near_atk_def_rate`/`long_atk_def_rate`/`magic_def_rate` were already wired into incoming pipelines via `player_build_to_target()` — roadmap item 5 was a no-op.

---

## Session S-1 — 2026-03-14 — Item Script Architecture Refactor (bonus_definitions.py)

**Pure refactor. No behavior change. No gaps closed.**

**New `core/bonus_definitions.py`**:
- `BonusDef` dataclass: `description: Callable`, `field: str | None`, `mode: str`, `fields: list[str] | None`.
- `BONUS1` (38 entries), `BONUS2` (20 entries), `BONUS3` (9 entries) — one entry per known bonus type.
- Name maps (`RACE_NAMES`, `ELEMENT_NAMES`, `SIZE_NAMES`, `STATUS_NAMES`, `CLASS_NAMES`) moved here from parser.
- Bug fix: `bAgiVit` (`mode="multi"`, fields=["agi","vit"]) and `bAgiDexStr` (`mode="multi"`, fields=["agi","dex","str_"]) added — previously silently dropped.
- `bMatkRate` and `bMaxHPrate` declared with `field=None` and comments marking them for S-2.
- `bAtkEle` and `bDefEle` declared with `field=None` and comments marking them for S-3.

**`core/item_script_parser.py`**:
- Removed `_BONUS1_TEMPLATES`, `_BONUS2_TEMPLATES`, `_BONUS3_TEMPLATES` (~120 lines).
- Removed `_RACE_NAMES`, `_ELEMENT_NAMES`, `_SIZE_NAMES`, `_STATUS_NAMES`, `_CLASS_NAMES` and shorthand helpers.
- `_make_description()` collapsed to 5 lines: dict lookup into `{1:BONUS1, 2:BONUS2, 3:BONUS3}`, try/except call.

**`core/gear_bonus_aggregator.py`**:
- Removed `_BONUS1_ROUTES` dict (27 entries), `_noop`, `_apply_all_stats` (~45 lines).
- Removed arity-2 if/elif chain (9 branches).
- `_apply()` rewritten as ~15 lines of table-driven logic: BONUS1 lookup for arity-1 (handles scalar/multi), BONUS2 lookup for arity-2 (handles dict/add modes).


---

## Session S-3 — 2026-03-14 — Element Precedence + DerivedSection Display

**No gaps closed. Correctness fix: bAtkEle/bDefEle scripts now wire into the pipeline.**

**`core/bonus_definitions.py`**:
- Added `_ELE_STR_TO_INT: dict[str, int]` — maps `"Ele_Fire"` etc. to int 0–9 (matches `data_loader.get_element_name`).
- Added `transform: Callable | None = None` field to `BonusDef` — used by mode="assign" to convert raw params before assignment.
- Added `mode="assign"` to BonusDef docstring.
- `bAtkEle`: changed from `field=None` (display-only) → `field="script_atk_ele"`, `mode="assign"`, `transform=_ELE_STR_TO_INT.get`.
- `bDefEle`: same, `field="script_def_ele"`.

**`core/gear_bonus_aggregator.py`** (`_apply()`):
- Added `mode=="assign"` branch for arity-1: calls `defn.transform(raw)` if transform present, then `setattr(bonuses, field, v)` when result is not None. Last-wins semantics.

**`core/build_manager.py`** (`resolve_weapon()`):
- Added `script_atk_ele: Optional[int] = None` parameter.
- Element precedence updated: `element_override → script_atk_ele → forge_element (if forged) → item_db`.

**`core/build_applicator.py`**:
- New `resolve_armor_element(armor_element_override: int, gear_bonuses: GearBonuses) -> int`.
- Precedence: non-zero override → `gear_bonuses.script_def_ele` → 0 (Neutral).

**`core/build_manager.py`** (`player_build_to_target()`):
- Imports `resolve_armor_element` from `build_applicator`.
- Now calls `resolve_armor_element(build.armor_element, gear_bonuses)` for `base_armor_ele`; uses it for both `element` (before SC override) and `armor_element` in the returned Target.

**`gui/sections/derived_section.py`**:
- Added two rows: `"ATK Ele"` and `"DEF Ele"` after ASPD, before HP.
- `refresh()` signature: added `atk_ele: int | None = None, def_ele: int | None = None`.
- Element rows display `loader.get_element_name(ele)` when value provided, else `"—"`.

**`gui/main_window.py`**:
- All 3 `resolve_weapon()` call sites (RH in `_run_status_calc`, RH in `_run_battle_pipeline`, PvP RH) now pass `script_atk_ele=gb.script_atk_ele`.
- `_run_status_calc`: computes `resolved_armor_ele = build_applicator.resolve_armor_element(eff_build.armor_element, gb)`, passes `atk_ele=weapon.element, def_ele=resolved_armor_ele` to `_derived_section.refresh()`.

---

## Session S-4 — 2026-03-14 — Scraper Expansion + sc_start Parsing

**No gaps closed. Infrastructure-only. Prerequisite for S-5 (consumable UI + routing).**

**`tools/import_item_db.py`**:
- Added `CONSUMABLE_TYPES = {"IT_USABLE", "IT_HEALING"}` alongside `EQUIP_TYPES`.
- Removed IT_USABLE and IT_HEALING from `SKIP_TYPES`.
- New `parse_consumable(entry, item_id, item_type)` → minimal schema: id, aegis_name, name, type, buy, sell, weight, script. No equip fields (no loc/upper/job/gender/slots).
- Dispatcher updated to route CONSUMABLE_TYPES to `parse_consumable()`.
- `EXPECTED_COUNTS` updated: IT_USABLE=785, IT_HEALING=292.
- item_db now has 3837 items (was 2760). All expected counts match.

**`core/models/sc_effect.py`** (new file):
- `SCEffect(sc_name, duration_ms, val1=0, val2=0, val3=0, val4=0)` — frozen dataclass.
- Represents one parsed `sc_start`/`sc_start2`/`sc_start4` call.

**`core/item_script_parser.py`**:
- New `parse_sc_start(script: str) -> list[SCEffect]`.
- Handles both space-form (`sc_start SC_NAME, dur, v1;`) and parenthesis-form (`sc_start4(SC_NAME, dur, v1, v2, v3, v4);`).
- All three variants (`sc_start`, `sc_start2`, `sc_start4`) handled uniformly.
- Non-numeric tokens (SCFLAG_NONE, Ele_Neutral, etc.) silently skipped during val collection.
- Duration=-1 stores as-is (permanent/OnEquip).

**`core/models/gear_bonuses.py`**:
- Added `sc_effects: List[SCEffect] = field(default_factory=list)`.

**`core/gear_bonus_aggregator.py`**:
- `compute()`: after `parse_script()`, also calls `parse_sc_start(script)` and extends `bonuses.sc_effects`.
- Applies to all item types (equippable gear, cards, ammo, and future consumables).

**`docs/lookup/item_ref.tsv`**:
- Regenerated from updated item_db.json — 3837 rows (was 2760).

---

## Session S-5 — 2026-03-14 — SC Effects Routing + Consumable UI

**No gaps closed. Infrastructure + UI for consumable buffs.**

SC_PLUSATTACKPOWER confirmed: `batk += val1` (status.c:4476, `#ifndef RENEWAL`).

**`core/models/build.py`**:
- Added `consumable_buffs: Dict[str, object]` — stores all consumable selections (value-based, same pattern as support_buffs). Keys defined in docs/consumables_design.md.
- Added `bonus_matk_flat: int = 0` — flat MATK addend from SC_MATKFOOD/SC_PLUSMAGICPOWER consumables; computed by apply_gear_bonuses(), applied in StatusCalculator after rate scaling.

**`core/build_applicator.py`**:
- New `compute_consumable_bonuses(consumable_buffs: dict) -> dict[str, int]`.
  SC conflict routing: max() per SC slot (Hercules blocks lower val1, status.c:7362-7363).
  food_str/agi/int compete with food_all and grilled_corn (gc=2); food_vit/dex/luk compete with food_all only.
  ASPD potions: _ASPD_VALS=(0,10,15,20) for indices 0-3. HIT/FLEE/CRI/ATK/MATK routed directly.
  SC_PLUSMAGICPOWER (matk_item) + SC_MATKFOOD (matk_food) are separate SC slots — stack into matk_flat.
- `apply_gear_bonuses()`: now calls compute_consumable_bonuses() and folds all consumable stats into dataclasses.replace(), including bonus_matk_flat.

**`core/calculators/status_calculator.py`**:
- After bMatkRate scaling and SC_MINDBREAKER: `matk_min/max += build.bonus_matk_flat` (status.c:4635-4638).

**`core/build_manager.py`**:
- save_build(): serialises `consumable_buffs`.
- load_build(): restores `consumable_buffs` from `data.get("consumable_buffs", {})`.

**`gui/sections/consumables_section.py`** (new file):
- 10-row QGridLayout with all consumable widgets.
- Stat Foods: 6 inline NoWheelCombo (STR/AGI/VIT/INT/DEX/LUK), 52px each; LUK has extra values +15/+20/+21.
- All-Stats Food: NoWheelCombo (0/+3/+6/+10 all).
- Grilled Corn: QCheckBox (+2 STR/AGI/INT tooltip).
- ASPD Potion: NoWheelCombo (None/Concentration/Awakening/Berserk).
- HIT Food: NoWheelCombo (0/+10/+20/+30/+33/+100).
- FLEE Food: NoWheelCombo (0/+10/+20/+30/+33).
- CRI Food: QCheckBox "Arunafeltz Desert Sandwich" (+7 CRI tooltip).
- ATK Item: NoWheelCombo (SC_PLUSATTACKPOWER; 0/+5/+10/+15/+20/+30); Payon Stories values deferred.
- MATK Item: NoWheelCombo (SC_PLUSMAGICPOWER; 0/+5/+10/+15/+20/+30); Payon Stories values deferred.
- MATK Food: QCheckBox "Rainbow Cake (SC_MATKFOOD, stacks)" (+10 flat, stacks with MATK Item).
- Header summary: auto-computed text of all active consumable effects.
- load_build() / collect_into() fully symmetrical via findData/currentData.

**`gui/sections/misc_section.py`** (new stub file):
- Section subclass with placeholder label. Auto-compute logic deferred to a future session.
- load_build() / collect_into() are no-ops.

**`gui/layout_config.json`**:
- Added `consumables_section` (header_summary, collapsed, builder panel) and `misc_section` (header_summary, collapsed, builder panel) between player_debuffs_section and active_items_section.

**`gui/main_window.py`**:
- Imports ConsumablesSection and MiscSection.
- Typed refs `_consumables` and `_misc_section`.
- `_consumables.changed` wired to `_on_build_changed`.
- load_build / collect_into calls added for both sections.
- `bonus_matk_flat = 0` added to the bonus-zeroing block in `_collect_build()`.

---

## Session S-6 — 2026-03-14 — Dual-Wield LH Element + Skill Element Fix

### S-6: Dual-wield LH element correctness

**Source confirmed (read 2026-03-14):**
- `pc.c:2588-2609`: `SP_ATKELE` uses `lr_flag` — `lr_flag==1` (LH slot) → `bst->lhw.ele = val`; `lr_flag==0` (RH slot) → `bst->rhw.ele = val`.
- `battle.c:4810-4811`: `s_ele = sstatus->rhw.ele; s_ele_ = sstatus->lhw.ele;`
- `battle.c:4856-4862`: skills always use only RH (`flag.lh` set only when `!skill_id`).

**`core/models/gear_bonuses.py`**:
- Renamed `script_atk_ele` → `script_atk_ele_rh`; added `script_atk_ele_lh: int | None = None`.

**`core/bonus_definitions.py`**:
- `bAtkEle` field updated: `"script_atk_ele"` → `"script_atk_ele_rh"` (default path for all non-LH slots).

**`core/gear_bonus_aggregator.py`**:
- Imported `_ELE_STR_TO_INT` from bonus_definitions.
- Inner loop: `bAtkEle` on `slot == "left_hand"` bypasses `_apply()` and writes directly to `bonuses.script_atk_ele_lh`. All other slots use the `_apply()` path → `script_atk_ele_rh`.

**`core/build_manager.py`**:
- `resolve_weapon()` param renamed `script_atk_ele` → `script_atk_ele_rh`. Docstring updated with slot-specific usage note.

**`core/calculators/battle_pipeline.py`**:
- Dual-wield section: computes `_dw_gb = GearBonusAggregator.compute(...)` to access LH element.
- LH `resolve_weapon()` call now passes `script_atk_ele_rh=_dw_gb.script_atk_ele_lh`.

**`gui/main_window.py`**:
- 3 `resolve_weapon()` call sites updated: `script_atk_ele=gb.script_atk_ele` → `script_atk_ele_rh=gb.script_atk_ele_rh` (×2 RH, ×1 PvP RH).

### Skill element in AttrFix (G82)

**Source:** `battle.c:4807`: `s_ele = skill_id ? skill->get_ele(skill_id, skill_lv) : -1`. Skills with a fixed element (e.g. `TF_POISON` = `Ele_Poison`) use that element; skills with `Ele_Weapon` / `Ele_Endowed` / `Ele_Random` use the fallback weapon path.

**`core/calculators/modifiers/attr_fix.py`**:
- `calculate()` gains optional `atk_element: int | None = None` parameter.
- `eff_ele = atk_element if atk_element is not None else weapon.element` used for both the table lookup and the ground-effect element check.

**`core/calculators/battle_pipeline.py`**:
- Imported `_ELE_STR_TO_INT` from `bonus_definitions`.
- `_run_branch()`: `skill_data` load moved up from ForgeBonus section.
- Before AttrFix: resolves `eff_atk_ele` from `skill_data["element"][lv_idx]` via `_ELE_STR_TO_INT`. `Ele_Weapon`/`Ele_Endowed`/`Ele_Random` not in dict → `None` → falls back to `weapon.element`.
- Passes `atk_element=eff_atk_ele` to `AttrFix.calculate()`.

---

## Session T — 2026-03-14 — Job Stat Bonuses + Stat Points Display

### G64 — Job Stat Bonuses

**Source:** `Hercules/db/job_db2.txt` — format: `JobID,stat_code_lv1,...`; codes 1=STR 2=AGI 3=VIT 4=INT 5=DEX 6=LUK. Applied via `param_bonus[type-SP_STR] += val` in `pc.c:2489`.

**`core/data_loader.py`**:
- `_parse_job_bonus_table()` — lru_cached parser for `Hercules/db/job_db2.txt`.
- `get_job_bonus_stats(job_id, job_level)` — returns cumulative `{str_, agi, vit, int_, dex, luk: int}` up to job_level.
- `_JOBL_UPPER_JOBS` class var — frozenset(range(4001, 4023)) for trans/high jobs.
- `_parse_statpoint_table()` — lru_cached parser for `Hercules/db/pre-re/statpoint.txt` (255 entries).
- `get_stat_points_at_level(base_level, job_id)` — cumulative stat points; +52 for JOBL_UPPER jobs (`pc.c:7522`).

**`core/calculators/status_calculator.py`**:
- `calculate()`: calls `loader.get_job_bonus_stats(build.job_id, build.job_level)` and adds `jb["str_"]` etc. to each stat before all further derivation.

### G65 — Stat Bonus Display + Stat Points Remaining

**Source:** `pc.c:7191 #else RENEWAL`: pre-renewal stat cost = `1 + (current_value + 9) // 10`.

**`gui/sections/stats_section.py`**:
- `_stat_cost(v)` and `_spent_points(base)` module-level helpers.
- `_make_tooltip()` gains `jb: int = 0` param; "Job Bonus" shows between Gear and Buffs.
- Stats grid gains "Next+" column (col 6) — `_next_labels` dict showing cost-of-next-point per stat.
- `StatsSection.__init__`: adds `_next_labels`, `_base_level=1`, `_job_id=0` instance vars; `_points_label` text changed from "Base Stat Total" to "Stat Points — Spent: N / Total  |  Left: N".
- `_update_totals()`: computes spent/available/remaining + fills `_next_labels`.
- `update_from_bonuses()`: gains `jb`, `base_level`, `job_id` params; stores level/job for planner; applies `jb.get(gb_attr, 0)` per stat row.

**`gui/main_window.py`**:
- `_run_status_calc()`: computes `jb_bonuses = loader.get_job_bonus_stats(build.job_id, build.job_level)` and passes `jb=jb_bonuses, base_level=build.base_level, job_id=build.job_id` to `update_from_bonuses()`.

---

## Session Pre-Alpha-1 — 2026-03-14 — Bonus Stats Display Fix

### Bonus column now reflects all stat sources

**Problem:** The "Bonus" column in Base Stats and the Flat Bonuses sub-section only showed gear + active items + manual adjustments. All SC stat changes (party buffs, self buffs, passives, consumable foods, player debuffs) were invisible; totals did not match the actual StatusCalculator output.

**Fix — `gui/sections/stats_section.py`:**
- `update_from_bonuses()` gains `sc_flat: dict[str, int] | None = None` parameter.
- Flat bonuses loop now adds `sc_flat.get(key_s, 0)` to total and shows "Buffs: X" in tooltip.

**Fix — `gui/main_window.py` (`_run_status_calc`):**
- Moved `update_from_bonuses()` call to **after** `StatusCalculator.calculate()` (it was previously called before, so SC/passive/debuff effects on stats were always zero).
- `sc_display[stat]` computed as `status.stat − base − gear − jb − ai − manual` — difference method ensures the displayed total always matches StatusCalculator regardless of what internal SC/passive/debuff effects are active.
- `sc_flat` dict computed for flat bonus rows:
  - BATK: SC_GS_MADNESSCANCEL (+100), SC_GS_GATLINGFEVER (+20+10lv), BS_HILTBINDING (+4), consumable atk_item
  - HIT: SC_GS_ACCURACY (+20), SC_GS_ADJUSTMENT (−30), SC_HUMMING, BS_WEAPONRESEARCH, AC_VULTURE, GS_SINGLEACTION/SNAKEEYE (gun), consumable hit_food
  - FLEE: SC_GS_ADJUSTMENT (+30), SC_RG_CCONFINE_M (+10), SC_GS_GATLINGFEVER (−5lv), SC_VIOLENTGALE, SC_WHISTLE, TF_MISS, MO_DODGE, consumable flee_food
  - CRI: SC_EXPLOSIONSPIRITS ((75+25lv)//10), SC_FORTUNE, consumable cri_food
  - DEF: SC_DRUMBATTLE (+( drum_lv+1)×2)
  - MDEF: SC_ENDURE (+lv)
  - ASPD%: consumable aspd_potion

### Consumables format-change bug — investigation in progress

**Symptom:** Expanding the Consumables section causes the Base Stats section to change visual format.
**Files read:** `consumables_section.py` (clean), `panel_container.py`, `panel.py`.
**Findings:**
- ConsumablesSection emits no cross-section signals; `expand_requested` is never fired by it.
- `set_slim_mode` (which triggers the compact widget) is only called from `PanelContainer.set_focus_state()` — no path from consumables open to slim mode via that route.
- Builder panel uses `QScrollArea(setWidgetResizable=True, ScrollBarAsNeeded vertical)`. When consumables expands and the content overflows panel height, the vertical scrollbar appears, reducing viewport width by ~15px.
- Root cause not confirmed. Next step: confirm whether the compact widget is being triggered or if it's a grid reflow. Add debug print to `StatsSection._enter_slim()` or observe directly.

---

## Session Scale — 2026-03-15 — UI Scaling + Packaging Prep

**Scope**: Font scaling via DPI auto-detect and Ctrl+/- manual override. Tier 1 (fonts only) chosen for pre-alpha; full layout scaling deferred to UX pass. G83 opened for post-alpha drag-to-reorder layout customisation.

**`gui/app_config.py`** — extended:
- `load_qss()`: reads `dark.qss` into `_raw_qss` module-level cache (called once from `main.py`)
- `get_scaled_qss()` / `apply_qss_scale(raw, scale)`: regex-replaces all `font-size: Npx` values by `effective_scale()` factor. Leaves borders, padding, heights untouched (Tier 1).
- `effective_scale()`: `UI_SCALE × _ui_scale_override`
- `scale_override()` / `set_scale_override(value)`: clamp to `[0.7, 1.5]`, persist to `settings.json` (merged into any existing keys)
- `_SETTINGS_PATH = "settings.json"`, `_SCALE_MIN/MAX/STEP` constants

**`main.py`** — two changes:
- Frozen CWD fix: `if getattr(sys, "frozen", False): os.chdir(os.path.dirname(sys.executable))` — ensures all relative paths (saves/, gui/themes/, core/data/) resolve correctly in a PyInstaller bundle.
- Uses `app_config.load_qss()` + `app_config.get_scaled_qss()` instead of raw stylesheet load; persisted override applied automatically on startup.

**`gui/main_window.py`** — scale controls:
- Toast: `QLabel#scale_toast` parented to central widget; `_show_scale_toast()` displays "Scale: N%" for 2 s via `QTimer.singleShot`; `_reposition_toast()` places it 12px from bottom-left; `resizeEvent()` keeps it positioned while visible.
- `_adjust_scale(delta)`: calls `set_scale_override`, re-applies QSS via `QApplication.instance().setStyleSheet()`, shows toast.
- Three `QShortcut`s: `Ctrl++`, `Ctrl+=` (covers keyboard layout variants), `Ctrl+-`.

**`gui/themes/dark.qss`** — added `QLabel#scale_toast` rule (blue border, blue text, rounded).

**`docs/gaps.md`** — G83 opened: user-configurable section layout (drag handles, cross-panel transfer, position_range constraints, settings.json persistence). UX-pass target.

---

## Session Pre-Alpha-2 — 2026-03-14 — Layout Overflow Fix

**Root cause:** `dark.qss` had `min-width: 180px` on the global `QComboBox` rule. When a
collapsed section containing combos (Consumables, Buffs) was expanded, those combos became
visible and reported a 180px minimum width to Qt's layout system. `setWidgetResizable(True)`
on the panel's QScrollArea sizes the inner widget to `max(viewport_width, widget_minimum_width)`.
When the combo minimum pushed the inner widget wider than the viewport, all sections overflowed
the panel's right edge (clipped, since horizontal scrollbar is disabled).
Affected any narrow window size or any section with combos.

**Fix — two files:**
- `gui/themes/dark.qss`: removed `min-width: 180px` from global `QComboBox {}` rule.
- `gui/widgets/level_widget.py`: added `minimumSizeHint()` override to `NoWheelCombo` returning
  `QSize(0, height)` — combos never report a minimum width to the layout system regardless of
  item text length or CSS. Permanent fix for all combo instances app-wide.

**Also updated:** `CLAUDE.md` Bug Investigation Protocol — added separate layout/visual bug
protocol directing Claude to read `dark.qss` and `panel_container.py` first, before any
section-level code or debug prints.

---

## Session Scale2 — 2026-03-15 — QFont Refactor + Ctrl+Scroll

### Problem
The Scale session used `setStyleSheet()` at runtime to re-apply font sizes on scale change.
Qt's CSS engine re-polishes the entire widget tree synchronously on each call — O(n_widgets × n_rules)
— causing 350–500ms freezes regardless of hardware. The debounce timer masked the stacking
problem but could not reduce the per-call cost.

### Solution (G84 closed)

**`gui/themes/dark.qss`** — removed all 43 `font-size: Npx` declarations. QSS now owns only
colors, borders, padding, and font-family. Font sizes are entirely programmatic.

**`gui/app_config.py`** — replaced `apply_qss_scale()` / `get_scaled_qss()` / `_raw_qss` with:
- `make_font(base_px) -> QFont`: returns a `QFont` with `setPixelSize(max(8, round(base_px * effective_scale())))`. No family set — QSS `font-family` rule merges in via Qt's partial font spec system.
- `app_font() -> QFont`: `make_font(13)` — the application base font.
- `_SIZE_MAP: dict[str, int]`: 36 objectName → base-px entries covering every named widget that previously had a non-13px QSS rule. 13px widgets omitted (inherit from application font).
- `rescale_all_fonts(root)`: iterates `root.findChildren(QWidget)`, applies `make_font(_SIZE_MAP[name])` per objectName. Also dispatches by class for `QTableWidget` (12px), `QListWidget` (12px), `QHeaderView` (11px). O(n) font-metric updates with async repaints — no CSS re-polish.
- `raw_qss()`: replaces `get_scaled_qss()` in startup path.

**`main.py`** — startup now applies the static QSS once (`app.setStyleSheet(raw_qss())`) then
sets the base font (`app.setFont(app_config.app_font())`). QSS is never re-applied at runtime.

**`gui/main_window.py`** — `_apply_scaled_qss()` replaced by `_apply_scaled_fonts()`:
calls `QApplication.setFont(app_config.app_font())` then `app_config.rescale_all_fonts(self)`.
Debounce interval reduced from 120ms to 50ms (operation is now fast enough to warrant it).

**`gui/panel.py`** — `StepsBar.paintEvent`: replaced `QFont(); font.setPointSize(9)` with
`app_config.make_font(12)` so the vertical text label scales with the rest of the UI.

### Ctrl+Scroll (added same session)
`MainWindow.eventFilter()` installed on `QApplication.instance()`. Intercepts `QEvent.Type.Wheel`
when `ControlModifier` is held. Accumulates `angleDelta().y()` in `_wheel_accum`; fires one
`_adjust_scale` step per 120-unit notch so smooth-scroll devices don't jump scale wildly.
Event consumed (`return True`) so the underlying widget does not also scroll.

---

## GUI-Pass — 2026-03-15

**Files changed**: `gui/section.py`, `gui/sections/equipment_section.py`, `gui/sections/stats_section.py`, `gui/layout_config.json`, `gui/panel_container.py`, `gui/main_window.py`

### Stats + Derived merge
- `StatsSection` (`stats_section.py`) rewritten: left/right `QHBoxLayout` split inside a single `add_content_widget()`. Left = existing base stats + flat bonuses; right = derived stats grid (all 17 rows from former `DerivedSection`).
- Added `refresh(status, atk_ele, def_ele)` and `_set_optional()` to `StatsSection`; mirrors former `DerivedSection.refresh()`.
- `_build_compact_widget()` extended with a derived mini-row (BATK / DEF / FLEE / HIT / CRI) below the 2×3 stats grid. `_enter_slim()` syncs derived compact labels.
- `layout_config.json`: removed `derived_section` block; `stats_section` display_name → "Stats".
- `panel_container.py`: removed `DerivedSection` import and factory entry.
- `main_window.py`: removed `_derived_section` reference; `_run_status_calc()` now calls `self._stats_section.refresh(...)`.

### Equipment section fixes
- `grid.setColumnStretch(1, 1)` added to equipment slot grid — name/card column now fills all remaining horizontal space.
- `_resolve_card_label()`: removed `[:10]` hard truncation; now returns full name (with " Card" suffix stripped).

### Section header fix
- `section.py`: `h_layout.addStretch()` is now only added when `_has_header_summary` is False. Previously the stretch competed with the Expanding summary label, causing premature word-wrap.

---

## Session SkillParam-Refactor — 2026-03-15 — Skill Param Architecture Refactor

Pure refactor — no new features, no gaps closed. Eliminates the 6-touch-point pattern
for adding skill runtime params (5 GUI + 1 core if/elif). Adding a new skill with params
now requires exactly 2 touches: one descriptor entry + one calculation function.

### New file: `gui/skill_param_defs.py`

- `SkillParamSpec` dataclass: `key`, `label`, `widget` ("combo"/"spin"/"check"),
  `default`, `options`, `mirrors_sc_key` (optional SC key for live sync),
  `default_from_build` (optional callable for build-aware initialisation).
- `SKILL_PARAM_REGISTRY: dict[str, list[SkillParamSpec]]` — all 5 current param skills:
  MO_FINGEROFFENSIVE, KN_CHARGEATK, MC_CARTREVOLUTION, MO_EXTREMITYFIST, TK_JUMPKICK.

### `gui/sections/combat_controls.py` — registry-driven rewrite

- New `_ParamWidget(QWidget)` class: uniform `value()` / `set_value()` API over
  combo/spin/check; single `changed = Signal()`.
- `__init__` Row 1: 5 bespoke widget blocks (80+ lines) → registry loop (12 lines).
  Builds `_skill_param_containers: dict[str, QWidget]` and `_param_rows: dict[str, _ParamWidget]`.
- `_update_skill_params_ui()`: `sub_map` dict → 3-line container loop.
- `collect_into()`: 7 hardcoded `skill_params` keys → 3-line dict comprehension over registry.
- `load_build()`: 6 manual widget-reset lines → registry loop using `default_from_build`
  (falling back to `build.skill_params.get(key, spec.default)`).
- Removed: `spirit_spheres_changed` signal, `_on_spheres_changed()`, `set_spirit_spheres()`.
- Added: `set_param_value(key, value)` — generic setter used for cross-section sync.

### `gui/sections/buffs_section.py` — sync signal generalised

- Removed bespoke `spirit_spheres_changed = Signal(int)` and `set_spirit_spheres()`.
- Added generic `sc_level_changed = Signal(str, int)` emitted from any SC combo that
  has a mirrored combat param (currently only MO_SPIRITBALL).
- `if sc_key == "MO_SPIRITBALL"` guard retained for label text ("0" instead of "Off");
  signal emit added inside the same guard.

### `gui/main_window.py` — wiring simplified

- Removed both old `spirit_spheres_changed` wires (both directions).
- `buffs_section.sc_level_changed` → new `_on_sc_level_changed(sc_key, value)`.
- `_on_sc_level_changed` iterates `SKILL_PARAM_REGISTRY` to find specs with matching
  `mirrors_sc_key` and calls `set_param_value` — fully generic for future mirrored params.

### `core/calculators/modifiers/skill_ratio.py` — if/elif → dict

- 5 module-level functions: `_ratio_chargeatk`, `_ratio_cartrev`, `_ratio_extremityfist`,
  `_ratio_jumpkick`, `_ratio_nj_syuriken`. Each returns `(ratio, ratio_src, flat_add)`.
- `_PARAM_SKILL_RATIO_FNS: dict` replaces `_BF_WEAPON_PARAM_SKILLS` frozenset.
- if/elif chain (35 lines) → `if fn := _PARAM_SKILL_RATIO_FNS.get(skill_name): ratio, ratio_src, flat_add = fn(...)` (1 line).
- `IMPLEMENTED_BF_WEAPON_SKILLS` updated: `| _BF_WEAPON_PARAM_SKILLS` → `| frozenset(_PARAM_SKILL_RATIO_FNS.keys())`.
- NJ_SYURIKEN removed from `_BF_WEAPON_RATIOS` (dead code; now fully handled in `_PARAM_SKILL_RATIO_FNS`).
- MO_FINGEROFFENSIVE hit-count fallback simplified: 8-line chain → 1 line
  (`params.get("MO_FINGEROFFENSIVE_spheres", 1)`), valid since `collect_into` always populates the key.
