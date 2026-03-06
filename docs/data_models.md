# PS_Calc — Data Model Reference
_Current state vs target state for all core models._
_Fields marked [NEW] need to be added. Fields marked [EXISTS] are already present._

---

## Target (core/models/target.py)

The Target represents any entity being attacked. Currently modelled only for mob targets.
`is_pc = True` gates all PC-specific calculation branches.

### Current fields [EXISTS]:
```python
def_: int = 0           # hard DEF (mob_db def_, or player equip+stat DEF)
vit: int = 0            # for VIT DEF variance (mob vit, or player VIT stat)
size: str = "Medium"    # Small / Medium / Large
race: str = "Formless"  # RC_* string
element: int = 0        # element ID 0-9 (for outgoing: mob defending element)
element_level: int = 1  # 1-4
is_boss: bool = False
level: int = 1          # for VIT DEF PC formula: 3 + (level+1)*0.04 factor
luk: int = 0            # crit roll: cri -= luk*2 (battle.c:4957)
agi: int = 0            # mob FLEE = level + agi (for hit/miss)
is_pc: bool = False     # gates PC-specific branches (VIT DEF formula, target-side CardFix)
targeted_count: int = 1 # unit_counttargeted for VIT DEF penalty
```

### Fields to add [NEW]:
```python
# For player defenders (PvP / incoming damage)
sub_race: dict = field(default_factory=dict)  # {race_key: int%} — e.g. {"RC_DemiHuman": 30}
sub_ele: dict  = field(default_factory=dict)  # {ele_id_str: int%}
sub_size: dict = field(default_factory=dict)  # {size_key: int%}
near_attack_def_rate: int = 0   # bNearAtkDef — melee physical damage reduction %
long_attack_def_rate: int = 0   # bLongAtkDef — ranged physical damage reduction %
magic_def_rate: int = 0         # bMagicDefRate — magic damage reduction %

# For magic (both mob and player targets)
mdef_: int = 0          # hard MDEF — from mob_db "mdef" or player equip
int_: int = 0           # used to derive mdef2 (soft MDEF) from mob or player INT
armor_element: int = 0  # element the target defends as (from armor card/endow)
                        # For mobs: same as element. For players: from equipped armor.

# For hit/miss vs player defenders
flee: int = 0           # full FLEE (level + agi + gear bonuses) — used when is_pc=True
```

### How mob_db populates Target (loader.get_monster):
**Currently populated**: def_, vit, luk, agi, size, race, element, element_level, is_boss, level
**Missing — add to loader**: mdef_ (from mob_db "mdef"), int_ (from mob_db "stats.int")
Note: for mobs, `armor_element = element` (same defending element), `sub_race/ele/size = {}` (mobs have no cards)

### How a PlayerBuild populates a Target (player_build_to_target — to implement):
```
def_     ← StatusData.def_       (equip_def + VIT hard bonus)
vit      ← PlayerBuild.base_vit + bonus_vit (+ gear)
level    ← PlayerBuild.base_level
is_pc    ← True
size     ← "Medium"              (all pre-renewal PCs)
race     ← "DemiHuman"           (all pre-renewal PCs)
element  ← PlayerBuild.armor_element  (derived from equipped armor)
armor_element ← same
element_level ← 1
luk, agi ← from StatusData
flee     ← StatusData.flee
sub_race ← GearBonuses.sub_race
sub_ele  ← GearBonuses.sub_ele
sub_size ← GearBonuses.sub_size
near_attack_def_rate ← GearBonuses.near_atk_def_rate
long_attack_def_rate ← GearBonuses.long_atk_def_rate
magic_def_rate ← GearBonuses.magic_def_rate
mdef_    ← StatusData.mdef
int_     ← StatusData.int_
```

---

## StatusData (core/models/status.py)

### Current fields [EXISTS]:
```python
str, agi, vit, int_, dex, luk  # (int_ not int — keyword collision)
batk, hit, flee, flee2, cri
def_, def2     # hard and soft DEF
aspd, max_hp, max_sp
```

### Fields to add [NEW]:
```python
matk_min: int = 0   # INT + (INT/7)^2 — pre-re magic ATK minimum
matk_max: int = 0   # INT + (INT/5)^2 — pre-re magic ATK maximum
mdef: int = 0       # hard MDEF (from equip + stat contribution)
mdef2: int = 0      # soft MDEF (INT-based flat; exact formula needs status.c grep)
```

### StatusCalculator additions needed:
1. MATK: `matk_min = int_ + (int_//7)**2`, `matk_max = int_ + (int_//5)**2`
   Source: status.c:3783-3792 `#ifndef RENEWAL`
2. MDEF (hard): from equip_def equivalent (sum of equipped armor mdef values — item_db field needed?)
   Note: IT_ARMOR items in item_db do NOT appear to have a `mdef` field (only `def`). Needs investigation.
3. MDEF (soft, mdef2): INT-based formula — grep `status_base_matk` or `mdef2` in status.c

---

## GearBonuses (core/models/gear_bonuses.py)

### Current fields [EXISTS]:
```python
# Attacker flat bonuses
str_, agi, vit, int_, dex, luk, batk, hit, flee, flee2, cri
crit_atk_rate, long_atk_rate, def_, maxhp, maxsp, aspd_percent, aspd_add
all_effects: List[ItemEffect]
# Attacker E2 stubs (populated, not yet wired to pipeline)
add_race, sub_ele, sub_race, add_size, add_ele, ignore_def_rate, skill_atk
```

### Fields to add [NEW]:
```python
# Additional attacker fields
atk_rate: int = 0          # bAtkRate — generic ATK% before SkillRatio (G10)
ignore_def_ele: dict = {}  # bIgnoreDefEle — ignore DEF by element (G5 extension)
ignore_mdef_rate: dict = {} # bIgnoreMdefRate — ignore MDEF by race/boss (G24)

# Defender fields (player as target of incoming damage)
sub_race: dict = {}         # bSubRace — already in existing stubs but named same
                             # EXISTING sub_race is attacker "add vs race" — RENAME CONFLICT
                             # Need to clarify: bSubRace is DEFENSIVE (reduce incoming from race)
                             # bAddRace is OFFENSIVE (increase outgoing vs race)
                             # Current: sub_race = bSubRace (defensive) — naming is correct
near_atk_def_rate: int = 0  # bNearAtkDef — reduce incoming melee physical
long_atk_def_rate: int = 0  # bLongAtkDef — reduce incoming ranged physical
magic_def_rate: int = 0     # bMagicDefRate — reduce incoming magic
```

### item_script_parser additions needed:
```
"bNearAtkDef"   → GearBonuses.near_atk_def_rate
"bLongAtkDef"   → GearBonuses.long_atk_def_rate
"bMagicDefRate" → GearBonuses.magic_def_rate
"bAtkRate"      → GearBonuses.atk_rate
"bIgnoreDefEle" → GearBonuses.ignore_def_ele (arity=2)
"bIgnoreMdefRace" → GearBonuses.ignore_mdef_rate (arity=2)
```

---

## PlayerBuild (core/models/build.py)

### Current fields [EXISTS]: (see MODELS.md)

### Fields to add [NEW]:
```python
armor_element: int = 0      # Element the player defends as for incoming damage.
                             # 0 = Neutral (default for bare armor).
                             # Set by: armor card (Pasana=Fire), endow status effect, etc.
                             # This is separate from weapon_element.
```

Note: `armor_element` can be derived from equipped armor's element card in the future (via
`GearBonusAggregator` or a dedicated pass). For now, expose as a manual override similar
to `weapon_element`.

---

## mob_db.json — Unused Fields (core/data/pre-re/db/)

All exist in JSON but `loader.get_monster()` doesn't populate them into Target:

| JSON field | Where needed |
|---|---|
| `mdef` | `Target.mdef_` — mob hard MDEF for incoming magic |
| `stats.int` | `Target.int_` — for mob MATK calc and mob soft MDEF (mdef2) |
| `stats.str` | Mob physical ATK derivation (for custom mob ATK if needed) |
| `stats.dex` | Mob HIT calculation |
| `atk_min` | `IncomingPhysicalPipeline` — already shown in IncomingDamageSection display |
| `atk_max` | Same |

---

## build.py — Save Schema (build_manager.py)

Card slots will require save schema changes when F1 (G13) is implemented.
Planned key scheme: `right_hand_card_0`, `right_hand_card_1`, `right_hand_card_2`, `right_hand_card_3`
Same pattern for all refineable slots: `armor_card_0`, `garment_card_0`, etc.
These are just additional keys in `build.equipped` dict — no structural change needed.
`build.refine_levels` does not apply to card slots.

---

## DamageResult / BattleResult (core/models/damage.py)

### Current [EXISTS]:
```python
BattleResult:
    normal: DamageResult
    crit: Optional[DamageResult]
    crit_chance: float
    hit_chance: float
    perfect_dodge: float
```

### Fields to add for full product [NEW]:
```python
BattleResult:
    magic: Optional[DamageResult] = None   # BF_MAGIC outgoing result
    incoming_physical: Optional[DamageResult] = None
    incoming_magic: Optional[DamageResult] = None
    # OR: separate result objects from separate pipeline runs — TBD at design time
```

Architecture note: it may be cleaner to keep BattleResult as physical-only and have
`MagicResult`, `IncomingResult` as separate types returned from separate pipeline objects.
Decide during Session B/D implementation.

---

## SkillInstance (core/models/skill.py)

No changes needed for current gaps. BF_MAGIC uses the same `SkillInstance` passed to
`calc_skillratio(BF_MAGIC, ...)`. The skill's `bf_type` (BF_WEAPON vs BF_MAGIC) is
determined by `skills.json` data and the skill ID.
