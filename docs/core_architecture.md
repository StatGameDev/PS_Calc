# PS_Calc — Core Architecture
_Technical reference for the core calculation system._
_For GUI layout and widget specs, see `docs/gui_plan.md`._
_For pipeline step formulas, see `docs/pipeline_specs.md`._

---

## Module Map

### Core models (`core/models/`)

| File | Owns |
|------|------|
| `build.py` | `PlayerBuild` dataclass — all player inputs: stats, gear, skill, buff state |
| `weapon.py` | `Weapon` dataclass, `RANGED_WEAPON_TYPES` |
| `target.py` | `Target` dataclass — mob or player-as-defender |
| `status.py` | `StatusData` dataclass — computed derived stats (output of StatusCalculator) |
| `damage.py` | `DamageStep`, `DamageResult`, `BattleResult`; PMF result storage |
| `skill.py` | `SkillInstance` |
| `gear_bonuses.py` | `GearBonuses` dataclass — aggregated item/card script bonuses |
| `item_effect.py` | `ItemEffect` — one parsed script bonus (bonus_type, arity, params, description) |

### Core calculators (`core/calculators/`)

| File | Owns |
|------|------|
| `status_calculator.py` | `StatusCalculator`: `PlayerBuild → StatusData` (HIT, FLEE, BATK, CRI, DEF, MATK, MDEF, ASPD, MaxHP, MaxSP) |
| `battle_pipeline.py` | `BattlePipeline`: routes to BF_WEAPON path or `MagicPipeline`; computes `crit_chance` + `hit_chance` |
| `magic_pipeline.py` | `MagicPipeline`: BF_MAGIC outgoing |
| `incoming_physical_pipeline.py` | mob→player or player→player physical incoming |
| `incoming_magic_pipeline.py` | mob→player magic incoming |
| `modifiers/` | One file per pipeline step — see Pipeline Step Order in `CLAUDE.md` |

### Core support

| File | Owns |
|------|------|
| `data_loader.py` | `DataLoader` singleton — all DB access (items, mobs, skills, jobs) |
| `bonus_definitions.py` | `BonusDef` + `BONUS1/2/3` tables — single source of truth for item script bonus types (S-1) |
| `item_script_parser.py` | `parse_script(script) → list[ItemEffect]`; `_make_description()` delegates to `bonus_definitions` |
| `gear_bonus_aggregator.py` | `GearBonusAggregator.compute(equipped) → GearBonuses`; table-driven `_apply()` |
| `build_applicator.py` | `apply_gear_bonuses(build, gb) → PlayerBuild`; `compute_sc_stat_bonuses(support_buffs) → dict` (S-2) |
| `build_manager.py` | Save/load builds; `player_build_to_target()` |
| `pmf/` | PMF probability operations (`operations.py`, `stats.py`) |

---

## Data Flow

```
User edits widget
  → Section emits change signal
    → MainWindow._on_build_changed()
      → _collect_build()                          → PlayerBuild (manual values)
        → build_applicator.apply_gear_bonuses(build, gb)  → PlayerBuild (+ gear overlay)
          │  gb = GearBonusAggregator.compute(build.equipped) → GearBonuses
          │  GearBonusAggregator.apply_passive_bonuses(gb, ...)
          │  dataclasses.replace(build, ...) injects bonuses as clean overlay
          │  Original manual values preserved — gear bonuses never written to disk
          │
          ├─ StatusCalculator.calculate(build)    → StatusData
          │   reads: build.support_buffs (priest/ground buffs)
          │   reads: build.song_state (Bard/Dancer songs)
          │
          ├─ TargetStatusCalculator.apply_debuffs(target)  → Target (effective)
          │   reads: target.target_active_scs
          │   returns new Target via dataclasses.replace
          │
          └─ BattlePipeline.calculate(
               build, status, effective_target,
               gear_bonuses, skill
             )                                    → BattleResult
               → MainWindow emits result_updated(BattleResult)
                 → combat sections render
```

### Pipeline context
Each modifier receives the full calculation context:
```python
@staticmethod
def calculate(pmf, build, status, target, gear_bonuses, skill, result): ...
```
Modifiers never hold state. All data flows in via parameters.

### PMF result storage
Each modifier operates on `pmf: dict[int, float]` and returns a new dict.
`result.add_step(...)` is called for every calculation — no silent mutations.
Final `result.pmf` is set at the end of each pipeline branch; `result.min/max/avg_damage`
are derived from it via `pmf_stats`.

---

## Buff Integration Design

⚠️ **OPEN — resolve in "Design Session — Buff Architecture" (pre-Session M)**

The following architecture questions must be answered before implementing Sessions M or M2.
Output of the design session: fill in the "Decisions" sub-section below; no code.

### Planned data model additions (GUI design decided — see `docs/gui_plan.md`)

```python
# PlayerBuild new fields (Sessions M–N prereq)
song_state: dict          # Bard/Dancer caster stats + per-song levels + per-stat overrides
support_buffs: dict       # External buffs received (Priest, Sage, ground, guild, applied debuffs)
misc_buff_bonuses: dict   # Catch-all temporary effects (item procs, pet buffs, etc.)

# Target new fields (Session R prereq)
target_active_scs: dict[str, int]   # SC key → level; absent = inactive
element_override: Optional[int]     # None = natural element; int = override
```

### Open questions

**Q1 — StatusCalculator extension strategy**
Where in the pipeline does each `support_buffs` SC modify stats?

- Option A: Extend `StatusCalculator` to read `build.support_buffs` and compute adjusted
  stats before returning `StatusData` (flat addition to existing stat fields).
- Option B: New pre-pipeline pass (e.g. `SupportBuffCalculator`) that post-processes
  `StatusData` before it reaches the pipeline.
- Option C: Inline in individual modifiers (e.g. `DefenseFix` reads `SC_ANGELUS` directly).

**Q2 — Song state reach**
How does `song_state` reach `StatusCalculator`?

- Option A: Via `PlayerBuild` directly — `StatusCalculator` reads `build.song_state`
  and computes val1/val2 inline for each active song.
- Option B: New `SongCalculator` that pre-computes val1/val2 → injects as flat bonuses
  into `StatusData` (or a parallel dict) before `BattlePipeline` runs.

**Q3 — misc_buff_bonuses aggregation**
Same aggregation path as `active_items_bonuses` in `_apply_gear_bonuses`?
Or separate pass closer to the pipeline?

**Q4 — target_active_scs reach**
How does `target_active_scs` reach the pipeline?

- Option A: Via `Target` fields directly — modifiers read `target.target_active_scs` inline.
- Option B: New `TargetStatusCalculator` that computes effective target stats before
  each pipeline run, injecting results back into `Target` or a new `TargetStatusData`.

**Q5 — SC_ETERNALCHAOS shared source** ✅ Resolved
Two separate fields, two separate effects, no shared source:
- `support_buffs["SC_ETERNALCHAOS"]` — in `target_state_section` Applied Debuffs —
  player's team casts it on the enemy → target.def2=0 in outgoing pipeline.
- `player_active_scs["SC_ETERNALCHAOS"]` — in `player_debuffs_section` —
  enemy casts it on the player → player.def2=0 in incoming pipeline.

### Decisions
_Resolved: Design Session — Buff Architecture (2026-03-09)_

**Q1 — StatusCalculator extension strategy: Option A**

Extend `StatusCalculator.calculate()` to read `build.support_buffs`.
- SC effects that modify base stats (STR/INT/DEX/AGI/LUK) are applied before downstream derived
  stat computation (BATK, HIT, FLEE, CRI, etc.) — same slot as `build.bonus_*` additions.
- SC effects that modify derived stats directly (DEF%, MaxHP, MaxSP, FLEE, HIT, CRI, ASPD)
  are applied at the relevant block within StatusCalculator.
- **Exception**: WATK-type buffs (SC_DRUMBATTLE, SC_NIBELUNGEN, SC_VOLCANO) are pre-SkillRatio
  flat ATK bonuses — they belong in `BaseDamage` (same position as ForgeBonus), not StatusCalculator.

Rationale: StatusCalculator already accepts buff inputs via `build.bonus_*` and
`build.active_status_levels`. Adding `build.support_buffs` follows the same pattern.
A separate SupportBuffCalculator would repeat the same stat-computation logic in a new file
for no architectural gain.

**Q2 — Song state reach: Option A**

`StatusCalculator.calculate()` reads `build.song_state` directly and computes val1/val2
inline for each active song (level > 0). No separate SongCalculator class.
- Songs target FLEE, FLEE2, HIT, CRI, MaxHP, MaxSP, ASPD — all already computed there.
- val1/val2 formulas are ~5 lines per song (function of caster_* stats + song level).
- **Exception**: SC_DRUMBATTLE WATK bonus → BaseDamage (same as Q1 exception).

**Q3 — misc_buff_bonuses: Deferred**

Do not add `misc_buff_bonuses` to `PlayerBuild` yet. No concrete use case for M or M2.
When needed, follow the `_apply_gear_bonuses` pattern: inject flat bonuses into `build.bonus_*`
fields via `dataclasses.replace` before StatusCalculator runs. StatusCalculator never sees the source.

**Q4 — target_active_scs reach: Option B**

New `core/calculators/target_status_calculator.py`:
```python
class TargetStatusCalculator:
    @staticmethod
    def apply_debuffs(target: Target) -> Target:
        """Apply target_active_scs debuffs; return effective Target via dataclasses.replace."""
        ...
```
Called in `MainWindow._on_build_changed()` before pipeline runs, alongside the existing
StatusCalculator call. Modifiers receive the effective Target and remain ignorant of debuff state.
Effects: SC_ETERNALCHAOS → def2=0, SC_CURSE → luk=0, SC_DECREASEAGI → agi reduction,
element debuffs → element_override, etc.

Rationale: If modifiers read `target.target_active_scs` directly, every modifier touching
def/luk/flee must check the debuff dict — couples pipeline to debuff system.
`TargetStatusCalculator` is a thin pre-pass (~20 lines), symmetric with `_apply_gear_bonuses`.

**Q5 — SC_ETERNALCHAOS: Already resolved** (two fields, two effects, no shared source)
- `support_buffs["SC_ETERNALCHAOS"]` → applied to enemy target → outgoing pipeline
- `player_active_scs["SC_ETERNALCHAOS"]` → applied to player → incoming pipeline

---

## Item Script Architecture (Session S)

_Decided: planning session 2026-03-14. Implemented in Session S (5 parts)._

### Design intent

The item script system must be fully data-driven: adding a new bonus type or a new item to
the database requires zero changes to parsing or routing logic. The GUI must own no business
logic — all script parsing, aggregation, and application live in core.

---

### bonus_definitions.py — single source of truth

**Problem solved:** Before S-1, adding a new `bonus bFoo` required edits in three files:
`item_script_parser.py` (description), `gear_bonuses.py` (field), `gear_bonus_aggregator.py`
(routing). Nothing enforced sync — several bonus types had descriptions but no routing and were
silently dropped.

**Solution:** `core/bonus_definitions.py` declares a table of `BonusDef` entries, one per
known `bonus_type`. Each entry carries:
- `field: str | None` — the `GearBonuses` attribute to accumulate into (`None` = display-only).
- `description: Callable` — lambda producing the human-readable effect string.
- `mode: Literal["add", "dict"]` — whether to add to a scalar or accumulate into a keyed dict.

`item_script_parser.py` and `gear_bonus_aggregator.py` both import from this table.
Adding a new bonus type = one entry in `bonus_definitions.py`, nothing else.

Multi-field bonuses (`bAllStats`, `bAgiVit`, `bAgiDexStr`) are declared with a `fields: list[str]`
instead of a single `field` and handled by a shared multi-field applier.

---

### build_applicator.py — core owns all business logic

**Problem solved:** `MainWindow._apply_gear_bonuses()` and `MainWindow._sc_stat_bonuses()` were
pure data transformations living in the GUI layer. The pipeline could not be exercised in tests
without instantiating a window.

**Solution:** New `core/build_applicator.py` owns two functions:
- `apply_gear_bonuses(build, gear_bonuses) -> PlayerBuild` — injects aggregated gear/card/consumable
  script bonuses into `PlayerBuild.bonus_*` fields via `dataclasses.replace`. Original manual values
  are preserved; gear values are a transient overlay, never written to disk.
- `compute_sc_stat_bonuses(support_buffs) -> dict[str, int]` — converts active SCs to flat stat deltas.

`MainWindow` calls both and passes results into the pipeline. It holds no computation itself.

---

### Element precedence

Weapon and armor effective elements follow a three-tier precedence chain, resolved at calc time:

```
explicit_element_override (user-set, stored on PlayerBuild)
  → script_atk_ele / script_def_ele (from GearBonuses, populated by bAtkEle/bDefEle script bonuses)
    → item_db_element (from item_db.json)
```

`BuildManager.resolve_weapon()` implements this for weapons.
`build_applicator.resolve_armor_element()` implements this for armor.

Resolved elements are displayed as read-only labels in `DerivedSection` (ATK Element, DEF Element).
They are not editable there — the override point is the equipment section.

---

### Consumable items — SCEffect model and routing

**Problem solved:** Before S-4/S-5, consumable items (stat foods, potions) had no data-driven
path. Effects had to be entered manually via G46 Active Items spinboxes — a hardcoded hack that
required a new spinbox per new consumable type.

**Solution:** Full data-driven pipeline:

1. **Scraper** (S-4) — `import_item_db.py` expanded to include IT_USABLE and IT_HEALING types.
2. **`SCEffect` model** (S-4) — `core/models/sc_effect.py`: `SCEffect(sc_name, duration_ms, val1..4)`.
3. **`parse_sc_start()`** (S-4) — added to `item_script_parser.py`; handles `sc_start`, `sc_start2`,
   `sc_start4` commands. Returns `list[SCEffect]` alongside the existing `list[ItemEffect]`.
4. **`GearBonuses.sc_effects`** (S-4) — aggregator collects all `SCEffect` from all equipped items.
5. **`build_applicator.apply_gear_bonuses()`** (S-5) — extracts SC_FOOD_* and other stat SCs from
   `GearBonuses.sc_effects`; merges into a transient `consumable_scs: dict[str, int]` on the
   effective build (not persisted).
6. **`StatusCalculator`** (S-5) — reads `consumable_scs` alongside `support_buffs`. Mapping from
   SC name to stat is in `docs/buffs/stat_foods.md` (already confirmed).

**Persistence:** `PlayerBuild.consumable_item_ids: list[int]` stores which consumable items the
player has active. The SCEffects themselves are recomputed from item_db on each calc run —
no stale state.

**Manual fallback:** G46 Active Items spinboxes remain as a "Manual Override" path for items not
in item_db or effects not yet parsed. They are not removed.

---

### What deliberately stays out of scope

- Weapon card proc scripts (`callfunc`, `monster`, `heal`, `percentheal`) — event-driven effects
  that don't fit a stat-overlay model. Display as-parsed description text only.
- `getitem`, `delitem`, `transform` — similarly event-driven. Description-only.
- Non-IT_USABLE/IT_HEALING sc_start items (e.g. throwable ammo) — handled by existing gear path;
  their SCEffects land in `GearBonuses.sc_effects` and are routed like any other.
