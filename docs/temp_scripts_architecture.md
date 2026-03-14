# Item Script Architecture (Session S)

_Decided: planning session 2026-03-14. Implemented in Session S (5 parts)._
_Duplicate of the Session S section in `docs/core_architecture.md` — for low-token reference._
_S-1 done 2026-03-14. S-2 done 2026-03-14. Next: S-3._

---

## Design intent

The item script system must be fully data-driven: adding a new bonus type or a new item to
the database requires zero changes to parsing or routing logic. The GUI must own no business
logic — all script parsing, aggregation, and application live in core.

---

## bonus_definitions.py — single source of truth

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

**S-3 note — `mode="assign"` needed for element overrides:**
`bAtkEle`/`bDefEle` must _assign_ (last-wins) rather than accumulate into `script_atk_ele`/`script_def_ele`.
The aggregator's `_apply()` currently handles only "add"/"multi"/"dict". S-3 adds `mode="assign"`:
`setattr(bonuses, field, v)` (not `+= v`). BonusDef entries for `bAtkEle`/`bDefEle` change from
`field=None` to `field="script_atk_ele"` / `field="script_def_ele"`, `mode="assign"`.

---

## build_applicator.py — core owns all business logic

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

## Element precedence

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

## Consumable items — SCEffect model and routing

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

## What deliberately stays out of scope

- Weapon card proc scripts (`callfunc`, `monster`, `heal`, `percentheal`) — event-driven effects
  that don't fit a stat-overlay model. Display as-parsed description text only.
- `getitem`, `delitem`, `transform` — similarly event-driven. Description-only.
- Non-IT_USABLE/IT_HEALING sc_start items (e.g. throwable ammo) — handled by existing gear path;
  their SCEffects land in `GearBonuses.sc_effects` and are routed like any other.
