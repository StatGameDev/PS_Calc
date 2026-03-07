# PS_Calc — Current State
# Updated end of Session F (partial — target selector redesign deferred to Session F1).
# Any Claude instance taking over should read this before starting work.

---

## Last Completed Session
**Session F — Incoming damage controls (partial).**

### Code changes this session:

1. `core/calculators/incoming_magic_pipeline.py`
   - `ele_override: Optional[int] = None` — use instead of skill/mob natural element when set
   - `ratio_override: Optional[int] = None` — substitute as skill ratio when set (bypasses skill lookup)

2. `gui/sections/incoming_damage.py`
   - Added `config_changed = Signal()`
   - Added config row: Ranged checkbox + magic element QComboBox (Mob natural + 10 elements by ID) + Ratio QSpinBox 0–1000%
   - `get_incoming_config() -> tuple[bool, Optional[int], Optional[int]]` — (is_ranged, ele_override, ratio_override)
   - PvP row removed (was added then removed after design revision — see below)

3. `gui/main_window.py`
   - `config_changed` wired to `_run_battle_pipeline`
   - `is_ranged` passed to IncomingPhysicalPipeline
   - `ele_override` / `ratio_override` passed to IncomingMagicPipeline
   - `# TODO(Session F1)` stubs left for pvp_stem wiring (combat_controls not yet restructured)

4. `gui/themes/dark.qss`
   - `QLabel#combat_target_display` — prominent style (background, 13px bold) replacing old `combat_mob_selected`
   - `QPushButton#target_mode_btn:checked` — red (#e05555) for Player mode

### What changed mid-session (design revision):
F2 (G30) was initially implemented with a PvP combo in IncomingDamageSection.
After user feedback: PvP target selection belongs in CombatControls as the **unified target**
(one target per panel drives both outgoing and incoming). The PvP combo was backed out.
The full target selector redesign is Session F1's primary task.

---

## Architecture Notes (for next instance)

**IncomingDamageSection.get_incoming_config()** — 3-tuple: `(is_ranged, ele_override, ratio_override)`
- `ele_override`: None = mob natural; int 0-9 = element ID override for incoming magic
- `ratio_override`: None = skill ratio; int > 0 = manual % override

**IncomingMagicPipeline.calculate()** — new optional params at end of signature:
- `ele_override: Optional[int] = None`
- `ratio_override: Optional[int] = None`
Both default to None = original behavior preserved.

**dark.qss target label** — objectName `"combat_target_display"` (not `"combat_mob_selected"`).
`combat_controls.py` still uses `"combat_mob_selected"` — must be renamed to `"combat_target_display"` in Session F1 when the section is restructured.

---

## Session F1 — Unified Target Selector

**Primary task: Restructure CombatControlsSection target area.**
No Hercules greps needed. Pure GUI + wiring + one new dialog + save format extension.

### G0 — Extend save format with cached_display

Add to `BuildManager.save_build()` output:
```json
"cached_display": {
    "job_name": "...",
    "hp": 1234,
    "def_": 45,
    "mdef": 12
}
```
- `job_name`: `loader.get_job_entry(build.job_id)["name"]` (or stem if None)
- `hp`: `loader.get_hp_at_level(build.job_id, build.base_level - 1) * (100 + base_vit) // 100 + build.bonus_maxhp`
- `def_`: `build.equip_def`
- `mdef`: `build.equip_mdef`

Load path: `load_build` passes `cached_display` through as a raw dict on the PlayerBuild (or just reads it from JSON in the browser). No PlayerBuild field change needed — the browser reads it directly from JSON.

### G1 — MonsterBrowserDialog: add MDef column

File: `gui/dialogs/monster_browser.py`
- `_COLUMNS`: insert `"MDef"` after `"DEF"` (currently index 4) → MDef at index 5, shift Element/Race/Size/Boss to 5→9
- `_NUMERIC_COLS`: add 5 (MDef)
- `_populate`: add `self._make_item(str(m.get("mdef", "")), numeric=True)` at col 5; shift others +1
- mob_db field: `mdef` (top-level, confirmed in mob_db.json schema)

### G2 — PlayerTargetBrowserDialog (new file)

File: `gui/dialogs/player_target_browser.py`

Same QDialog structure as MonsterBrowserDialog.
Columns: `["Name", "Job", "Lv", "HP", "DEF", "MDEF"]`
All numeric except Name and Job.

Population:
```python
for stem in stems:
    path = os.path.join(saves_dir, f"{stem}.json")
    data = json.load(open(path))
    cd = data.get("cached_display", {})
    name = data.get("name", stem)
    job_name = cd.get("job_name", "?")
    level = data.get("base_level", "?")
    hp = cd.get("hp", "?")
    def_ = cd.get("def_", "?")
    mdef = cd.get("mdef", "?")
    # store stem as UserRole on name item
```

Public API: `selected_build_stem() -> Optional[str]`

### G3 — Restructure CombatControlsSection

File: `gui/sections/combat_controls.py`

**State to add:**
- `_target_type: str = "mob"` (default)
- `_target_pvp_stem: Optional[str] = None`
- `_player_build_pairs: list[tuple[str, str]] = []` — (stem, display_name)

**Layout change (target area only):**
```
[Mob]  toggle btn (objectName="target_mode_btn")

[search field…          ] [Browse…]
[results list — hidden until search/selection]

► Poring  [Lv 1]          ← QLabel objectName="combat_target_display"
  or "Player: Natural Crit Sin"
```

- Toggle btn: single QPushButton, checkable, text="Mob" when unchecked / "Player" when checked
- Search field: filters mobs (mob mode) or player build display names (player mode) — same widget, same ≥2-char threshold
- Browse btn: opens MonsterBrowserDialog (mob mode) or PlayerTargetBrowserDialog (player mode)
- Results list: same QListWidget, populated with mob names or build display names
- `_mob_selected_lbl` → rename/replace with `_target_display` (objectName="combat_target_display")

**New/changed methods:**
- `_on_mode_toggled(checked)`: update `_target_type`, update btn text, clear search/list, update display
- `_on_search_changed(text)`: mob mode = existing behavior; player mode = filter `_player_build_pairs`
- `_on_target_selected(item)`: mob mode = store mob_id; player mode = store pvp_stem
- `_open_browse()`: dispatch to correct dialog by mode
- `_update_target_display()`: format label based on mode + current selection
- `get_target_pvp_stem() -> Optional[str]`: returns `_target_pvp_stem` if player mode, else None
- `refresh_target_builds(pairs: list[tuple[str, str]])`: repopulate `_player_build_pairs`; if current pvp_stem still in list: keep; else: clear `_target_pvp_stem` + update display

**load_build change:** always reset to mob mode (pvp target is session-only, not saved).

**collect_into change:** `build.target_mob_id = self._selected_mob_id if self._target_type == "mob" else None`

### G4 — main_window.py wiring

Replace `# TODO(Session F1)` stubs:

In `_refresh_builds`:
```python
pairs = [(stem, display) for stem, display in zip(stems, displays)]
self._combat_controls.refresh_target_builds(pairs)
```

In `_run_battle_pipeline`:
```python
pvp_stem = self._combat_controls.get_target_pvp_stem()
mob_id = None if pvp_stem else (
    self._combat_controls.get_target_mob_id() or eff_build.target_mob_id
)

# PvP target setup (reused for both outgoing target and incoming)
pvp_eff = pvp_weapon = pvp_status = pvp_gear_bonuses = None
if pvp_stem:
    pvp_path = os.path.join(app_config.SAVES_DIR, f"{pvp_stem}.json")
    pvp_build = BuildManager.load_build(pvp_path)
    pvp_eff = self._apply_gear_bonuses(pvp_build)
    pvp_weapon = BuildManager.resolve_weapon(...)
    pvp_status = StatusCalculator(self._config).calculate(pvp_eff, pvp_weapon)
    pvp_gear_bonuses = GearBonusAggregator.compute(pvp_eff.equipped)
    target = BuildManager.player_build_to_target(pvp_eff, pvp_status, pvp_gear_bonuses)
else:
    target = loader.get_monster(mob_id) if mob_id is not None else Target()

# Incoming
if pvp_stem and pvp_eff:
    pvp_battle = self._pipeline.calculate(
        pvp_status, pvp_weapon, SkillInstance(), player_target, pvp_eff
    )
    phys_result = pvp_battle.normal
    magic_result = None
elif mob_id is not None:
    # existing mob physical + magic pipelines
    ...
```

Add `from core.models.skill import SkillInstance` import.

---

## Open Gaps (updated)

| Gap | Status | Session | Description |
|---|---|---|---|
| G43 | [x] | F | Ranged checkbox + magic ele/ratio override — DONE |
| G30 | [~] | G | PvP target — pipeline code ready; UI redesign deferred to Session F1 |
| G12 | [ ] | G | Armor refine DEF |
| G13 | [ ] | G | Card slot UI |
| G34–G37 | [ ] | H | Job/race/element filters |
| G15–G17, G39–G40 | [ ] | I | Stats visibility, katar 2nd hit, etc. |
| G9 + Party buffs | [~]/[ ] | J | ASPD + Bard/Dancer songs |
| G41, C1 | [ ] | Deferred | PC VIT DEF, variance distribution |

---

## Known Issues
- `sub_size={}` in player_build_to_target — no defensive size resist from player cards.
- `combat_controls.py` still uses objectName `"combat_mob_selected"` — rename to `"combat_target_display"` in G3.
- G43: Physical/Magic toggle in IncomingDamageSection is manual — follows mob attack type only in Phase 8+.
