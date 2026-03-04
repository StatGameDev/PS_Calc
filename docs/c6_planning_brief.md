# C6 — Crit System Planning Brief
**PS_Calc / Pre-renewal Ragnarok Online damage calculator**
*Written for Claude Web planning session. All source citations are from Hercules emulator.*

---

## Project Context

PS_Calc is a Python 3.13 / CustomTkinter pre-renewal RO damage calculator. It faithfully ports
Hercules emulator formulas (no wikis). The damage pipeline is `BattlePipeline.calculate()` in
`core/calculators/battle_pipeline.py`.

**Hercules source of truth:** `Hercules/src/map/battle.c`, `status.c`, `skill.c`
**RENEWAL guards:** `#ifdef RENEWAL` = ignore. `#ifndef RENEWAL` = implement. No guard = both.

---

## Current Pipeline State

```
BattlePipeline.calculate(status, weapon, skill, target, build) → DamageResult
  BaseDamage.calculate(...)     # battle_calc_base_damage2
  SkillRatio.calculate(...)     # skill ratio multiplier
  DefenseFix.calculate(...)     # hard DEF % + soft VIT DEF subtract
  ActiveStatusBonus.calculate(...)
  MasteryFix.calculate(...)
  AttrFix.calculate(...)
  FinalRateBonus.calculate(...)
  → DamageResult (min/max/avg, steps list)
```

The pipeline currently produces a single normal damage result. **C6 must add a parallel crit
branch** so the caller gets both normal and crit outputs for any crittable attack.

---

## Key Models (current state)

### `DamageRange` (core/models/damage.py)
```python
@dataclass
class DamageRange:
    min: int
    max: int
    avg: int
    # methods: scale, add, add_range, subtract, floor_at
```

### `DamageStep` (core/models/damage.py)
```python
@dataclass
class DamageStep:
    name: str
    value: int          # avg
    min_value: int = 0
    max_value: int = 0
    multiplier: float = 1.0
    note: str = ""
    formula: str = ""
    hercules_ref: str = ""
```

### `DamageResult` (core/models/damage.py)
```python
@dataclass
class DamageResult:
    min_damage: int = 0
    max_damage: int = 0
    avg_damage: int = 0
    crit_chance: float = 0.0   # already present, not yet populated
    hit_chance: float = 0.0
    steps: List[DamageStep] = ...
```
`crit_chance` field exists but is never set. No `is_crit` flag exists yet.

### `StatusData` (core/models/status.py)
```python
@dataclass
class StatusData:
    str, agi, vit, int_, dex, luk: int
    batk: int       # base ATK
    cri: int        # in 0.1% units — 10 = 1.0% crit
    hit, flee, flee2, aspd, max_hp, max_sp: int
```

### `PlayerBuild` (core/models/build.py)
```python
@dataclass
class PlayerBuild:
    base_str/agi/vit/int/dex/luk: int
    bonus_str/agi/vit/int/dex/luk: int
    bonus_cri: int = 0      # flat crit bonus in 0.1% units
    active_status_levels: Dict[str, int]  # e.g. {"SC_CAMOUFLAGE": 1}
    # ...
```

### `BattleConfig` (core/config.py) — current fields
```python
@dataclass
class BattleConfig:
    weapon_damage_rate: int = 100
    short_attack_damage_rate: int = 100
    long_attack_damage_rate: int = 100
    critical_rate: int = 100    # already present
    enable_critical: bool = True
    max_aspd: int = 190
    enable_perfect_flee: bool = True
    vit_penalty_*: ...
```
`critical_rate` exists. `critical_min` (minimum crit floor) does **not** exist yet.

### `SkillInstance` (core/models/skill.py)
Carries `skill_id`, `level`, `ignore_size_fix`. Does not carry crit eligibility yet.

### `Weapon` (core/models/weapon.py)
```python
@dataclass
class Weapon:
    atk: int
    refine: int
    level: int          # weapon level 1-4
    element: int        # 0-9
    weapon_type: str    # "W_1HSWORD", "Katar", etc.
    hand: str
    aegis_name: str
    refineable: bool
```

---

## Bug to Fix: Katar Crit in StatusCalculator

**Current (wrong):**
```python
# core/calculators/status_calculator.py line 41-42
status.cri = 10 + (status.luk * 10 // 3) + (build.bonus_cri * 10)
if weapon.weapon_type == "Katar":
    status.cri *= 2     # BUG: belongs in battle crit roll, not here
```

**Why it's wrong:** Under the default Hercules config `show_katar_crit_bonus = 0`
(which is the pre-renewal default), katar doubling happens in `battle_calc_weapon_attack`
during the crit roll step, NOT in `status_calc_pc_`. The `StatusData.cri` value stored
should be the raw pre-katar value.

Source: `status.c lines ~3209-3210` — the katar `*=2` is inside a
`if (battle_config.show_katar_crit_bonus)` block, default 0.
The same doubling happens unconditionally in the crit roll at `battle.c:4954-4957`.

**Fix:** Remove the katar `*= 2` from `StatusCalculator`. Add it to `crit_chance.py` instead.

---

## Crit Eligibility — Skill Whitelist

Source: `battle.c lines 4926-4931` (pre-renewal, no RENEWAL guard on this block)

```c
// Only these skill IDs can trigger a crit roll:
case 0:                     // normal attack
case KN_AUTOCOUNTER:
case SN_SHARPSHOOTING:
case MA_SHARPSHOOTING:
case NJ_KIRIKAGE:
    // crit roll proceeds
    break;
default:
    // no crit possible
```

**Critical fact: `NK_CRITICAL` flag does NOT exist in Hercules.** There is no such flag.
Crit eligibility is this exact hardcoded whitelist. Nothing else.

**Implication for current scaffold:** SM_BASH (skill_id=5) is NOT in the whitelist —
it cannot crit. The current scaffold uses SM_BASH as the test skill, so `is_crit` will
always be false in scaffold runs.

---

## Crit Roll Formula

Source: `battle.c lines 4926-4986` (pre-renewal)

```
1. Start:        cri = sstatus->cri                     (from StatusCalculator, 0.1% units)
2. Race bonus:   cri += sd->critaddrace[tstatus->race]   (bCriticalAddRace)
                 if katar && !show_katar_crit_bonus: cri <<= 1   (doubling here)
3. Arrow:        cri += sd->bonus.arrow_cri              (bArrowCri, if flag.arrow set)
4. Camouflage:   if SC_CAMOUFLAGE: cri += 10*(10-val4)   (pre-renewal applicable)
5. vs Player:    cri -= tstatus->luk * 2                 (always 2 for PC attackers)
6. Sleep:        if SC_SLEEP: cri <<= 1
7. Autocounter:  if KN_AUTOCOUNTER: forced crit OR cri <<= 1 (per auto_counter_type config)
8. Def:          cri = cri * (100 - tstatus->critical_def) / 100  (bCriticalDef on target)
9. Roll:         rnd()%1000 < cri  →  flag.cri = 1
```

**Simplifications for calculator (no PvP targets):**
- Step 5 (vs player LUK penalty) only applies when target is a player — skip for mob targets
- Step 7 (KN_AUTOCOUNTER) only when skill_id == KN_AUTOCOUNTER
- `tstatus->critical_def` is 0 for all mobs (no mob has `bCriticalDef`) — skip for mobs
- `arrow_cri` is 0 unless the weapon is a bow/instrument/whip with an arrow equipped

**`cri_chance` = `cri / 10.0` percent** (0.1% units → percent)

---

## On Crit: What Changes

Source: `battle.c lines 4988-4993` (`#ifndef RENEWAL`)

```c
flag.idef = flag.idef2 = 1;   // both hard DEF and soft DEF are SKIPPED
flag.hit = 1;                  // guaranteed hit
```

**DEF bypass mechanism:** The values `def1` and `def2` are NOT zeroed. The flags
`flag.idef` and `flag.idef2` gate the reduction steps in `battle_calc_defense`.
When `idef=1`: `damage = damage * (100-def1) / 100` is skipped.
When `idef2=1`: `damage -= vit_def` is skipped.
Both subtraction steps execute zero effect. DEF values remain readable for any downstream
code that might check them (none in the current pipeline, but the model should remain correct).

**Weapon ATK variance on crit:**
Source: `battle.c calc_base_damage2 lines 648-651` — `flag&1` gates atkmin=atkmax:
```c
if (flag&1) damage = atkmax;   // crit: always max weapon roll
else        damage = (atkmax>atkmin ? rnd()%(atkmax-atkmin) : 0) + atkmin;
```
On crit: `DamageRange(atkmax, atkmax, atkmax)` — no variance.

**Overrefine on crit:** NOT forced to max. The overrefine roll
`rnd()%overrefine+1` has NO crit gate — it still randomizes on crit.
Source: the overrefine block in `calc_base_damage2` has no `flag&1` guard.

**Arrow ATK on crit:** Forced to full (no rnd). But we have no arrow ATK step
implemented yet — not relevant for current scope.

**Crit ATK rate bonus:**
Source: `battle.c lines 5333-5334`
```c
if (flag.cri)
    ATK_ADDRATE(wd.damage, sd->bonus.crit_atk_rate);
```
`crit_atk_rate` comes from `bCriticalDef` scripts (e.g., equipment/cards with
`bonus bCritAtkRate, N`). Currently 0 for all items in the DB (no card effects implemented).
This step still needs to be added as a modifier for correctness.

---

## `DamageResult` Model Change Required

The pipeline must return both normal and crit results. Two design options:

**Option A — Two separate `DamageResult` objects:**
```python
@dataclass
class BattleResult:
    normal: DamageResult
    crit: Optional[DamageResult]    # None if skill is not crit-eligible
    crit_chance: float              # 0.0 if not eligible
    can_crit: bool
```
Pipeline returns `BattleResult`. GUI shows both columns when `can_crit=True`.

**Option B — Dual values inside each `DamageStep`:**
```python
@dataclass
class DamageStep:
    name: str
    value: int          # normal avg
    crit_value: Optional[int] = None   # crit avg, None = same as normal
    min_value: int = 0
    max_value: int = 0
    crit_min: Optional[int] = None
    crit_max: Optional[int] = None
    ...
```
Steps before crit decision point have `crit_value = None` (same as normal).
Steps from crit decision onward carry both values.

**Recommendation:** Option A is cleaner. The crit branch has a fundamentally different
`BaseDamage` (no variance, skip DEF), so sharing a step list is artificial. Two results
with their own step lists is easier to display and test.

---

## Files to Create/Modify

### New file: `core/calculators/modifiers/crit_chance.py`
```python
class CritChance:
    ELIGIBLE_SKILLS = {0, KN_AUTOCOUNTER_ID, SN_SHARPSHOOTING_ID, MA_SHARPSHOOTING_ID, NJ_KIRIKAGE_ID}

    @staticmethod
    def is_eligible(skill_id: int) -> bool: ...

    @staticmethod
    def calculate(skill_id, status, weapon, target, build, config) -> tuple[int, float]:
        # Returns (cri_raw_01pct, cri_chance_pct)
        # Applies: katar doubling, race bonus, camouflage SC, sleep SC, critical_rate config
```

### New file: `core/calculators/modifiers/crit_atk_rate.py`
```python
class CritAtkRate:
    @staticmethod
    def calculate(crit_atk_rate: int, dmg: DamageRange, result: DamageResult) -> DamageRange:
        # ATK_ADDRATE(dmg, crit_atk_rate) — only called on crit branch
        # crit_atk_rate from build.bonus_crit_atk_rate (new field needed)
```

### Modify: `core/config.py`
Add: `critical_min: int = 10` — minimum crit floor (`calc_critical ~line 4743`)

### Modify: `core/calculators/status_calculator.py`
- Remove katar `*= 2` from cri calculation (move to `crit_chance.py`)
- Add `critical_rate` multiplier: `status.cri = status.cri * config.critical_rate // 100`
  Source: `status.c line 3919`

### Modify: `core/models/build.py`
Add: `bonus_crit_atk_rate: int = 0` — `sd->bonus.crit_atk_rate` (bCritAtkRate)
Add: `bonus_arrow_cri: int = 0` — `sd->bonus.arrow_cri` (bArrowCri), for future bow support
Add: `crit_add_race: Dict[str, int]` — `sd->critaddrace[]` (bCriticalAddRace), for future card support

### Modify: `core/calculators/battle_pipeline.py`
Structural change: `calculate()` returns `BattleResult` (or a named tuple) instead of
`DamageResult`. The crit branch runs only when `CritChance.is_eligible(skill.id)`.

### Modify: `core/calculators/modifiers/base_damage.py`
Add `is_crit: bool` parameter to `calculate()`. When `True`:
- Force `w_min = w_max = w_avg = atkmax` (no weapon ATK variance)
- Overrefine still randomizes (no change needed — already correct)

### Modify: `core/calculators/modifiers/defense_fix.py`
Add `is_crit: bool` parameter. When `True`: skip both hard DEF and soft DEF steps.
Log step as "Defense Fix (BYPASSED — critical hit)" with original DEF values as notes.

---

## Crit Branch Pipeline Order

The crit branch runs the same modifiers as normal, with two differences:
1. `BaseDamage.calculate(..., is_crit=True)` — forces atkmax
2. `DefenseFix.calculate(..., is_crit=True)` — skips both DEF layers
3. After `DefenseFix`: `CritAtkRate.calculate(...)` — `ATK_ADDRATE(crit_atk_rate)`
   (inserted between DefenseFix and ActiveStatusBonus — source line 5333 is post-defense)

All other steps (SkillRatio, MasteryFix, AttrFix, FinalRateBonus, ActiveStatusBonus) run
identically on both branches.

---

## Skill IDs (Hercules constants)
```
SM_BASH          = 5    (cannot crit — NOT in whitelist)
KN_AUTOCOUNTER   = 76
SN_SHARPSHOOTING = 312
MA_SHARPSHOOTING = 326  (Merchant Academy version — same mechanic)
NJ_KIRIKAGE      = 494
```

---

## Open Questions for Planning

1. **`BattleResult` vs dual `DamageStep`**: Which design to use? See Option A/B above.

2. **Skill ID constants**: Should they live in a `core/constants.py` file or be defined
   inline in `crit_chance.py`?

3. **`bonus_crit_atk_rate`**: Should this go on `PlayerBuild` directly, or inside a
   nested `BonusData` struct for future expansion?

4. **Testing**: The current scaffold uses SM_BASH which cannot crit.
   Need a second scaffold (or override) with a normal attack (skill_id=0) to test the
   crit branch.

5. **`critical_min`**: Source `battle.c calc_critical ~4743` sets a floor on crit.
   Exact formula TBD — investigate before implementing.
