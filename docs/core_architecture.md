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
| `item_script_parser.py` | `parse_script(script) → list[ItemEffect]` |
| `gear_bonus_aggregator.py` | `GearBonusAggregator.compute(equipped) → GearBonuses` |
| `build_manager.py` | Save/load builds; `player_build_to_target()` |
| `pmf/` | PMF probability operations (`operations.py`, `stats.py`) |

---

## Data Flow

```
User edits widget
  → Section emits change signal
    → MainWindow._on_build_changed()
      → _collect_build()                          → PlayerBuild (manual values)
        → _apply_gear_bonuses(build)              → PlayerBuild (+ gear overlay)
          │  GearBonusAggregator.compute(build.equipped) → GearBonuses
          │  dataclasses.replace(build, ...) injects bonuses as clean overlay
          │  Original manual values preserved — gear bonuses never written to disk
          │
          ├─ StatusCalculator.calculate(build)    → StatusData
          │
          └─ BattlePipeline.calculate(
               build, status, target,
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
_(fill in after design session)_
