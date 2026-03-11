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
# Added Session A (G6):
sub_race: Dict[str, int] = field(default_factory=dict)  # RC_* keys — player race resistance
sub_ele:  Dict[str, int] = field(default_factory=dict)  # Ele_* keys — element resistance
sub_size: Dict[str, int] = field(default_factory=dict)  # Size_* keys — size resistance
near_attack_def_rate: int = 0   # bNearAtkDef — melee physical damage reduction %
long_attack_def_rate: int = 0   # bLongAtkDef — ranged physical damage reduction %
magic_def_rate: int = 0         # bMagicDefRate — magic damage reduction %
mdef_: int = 0          # hard MDEF — from mob_db "mdef" or player equip
int_: int = 0           # used to derive mdef2 (soft MDEF) from mob or player INT
armor_element: int = 0  # element the target defends as (from armor card/endow)
flee: int = 0           # full FLEE — used when is_pc=True
```

### Fields to add [NEW]:
_All previously listed [NEW] fields were added in Session A. No remaining Target fields to add._

### How mob_db populates Target (loader.get_monster):
**Currently populated**: def_, vit, luk, agi, size, race, element, element_level, is_boss, level, mdef_, int_
**Still missing**: armor_element (always = element for mobs — set when player_build_to_target() is implemented)
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
# Added Session B:
matk_min: int = 0   # INT + (INT/7)^2 — status.c:3783 #else not RENEWAL
matk_max: int = 0   # INT + (INT/5)^2 — status.c:3790 #else not RENEWAL
mdef: int = 0       # hard MDEF — from build.equip_mdef (bMdef scripts; IT_ARMOR has no mdef field)
mdef2: int = 0      # soft MDEF = int_ + vit//2 — status.c:3867 #else not RENEWAL
```

### Fields added in Session M [EXISTS]:
```python
def_percent: int = 100  # st->def_percent: vit_def multiplier for PC targets (SC_ANGELUS adds 5*lv); default 100
```

### Fields added in Session M2 [EXISTS]:
```python
cast_time_reduction_pct: int = 0       # SC_POEMBRAGI val1 — display-only; no action speed simulation
after_cast_delay_reduction_pct: int = 0 # SC_POEMBRAGI val2 — display-only
sp_cost_reduction_pct: int = 0         # SC_SERVICEFORYU val3 — display-only
```

### Fields to add [NEW]:
_No remaining StatusData fields to add._

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
# Added Session A:
near_atk_def_rate: int = 0  # bNearAtkDef — reduce incoming melee physical
long_atk_def_rate: int = 0  # bLongAtkDef — reduce incoming ranged physical
magic_def_rate: int = 0     # bMagicDefRate — reduce incoming magic
atk_rate: int = 0           # bAtkRate — generic ATK% (currently consumed in CardFix; should move before SkillRatio — G10)
```

### Fields to add [NEW]:
```python
ignore_def_ele: dict = {}   # bIgnoreDefEle — ignore DEF by element (G5 extension)
```

### item_script_parser additions needed:
```
"bIgnoreDefEle"   → GearBonuses.ignore_def_ele (arity=2)
```
_Added Session A: bNearAtkDef, bLongAtkDef, bMagicDefRate, bAtkRate — all wired._
_Added Session B: mdef_ (bMdef hard MDEF), ignore_mdef_rate (bIgnoreMdefRate by race/boss) — both wired._

---

## PlayerBuild (core/models/build.py)

### Current fields [EXISTS]:
_See `core/models/build.py` for full field list._

### Fields added in Session D [EXISTS]:
```python
armor_element: int = 0      # Element the player defends as for incoming damage.
                             # Manual override; future: derive from equipped armor element card.
```

### Fields added in Session K [EXISTS]:
```python
is_forged: bool = False       # Right-hand weapon is player-forged (hides card row, enables forge element)
forge_sc_count: int = 0       # Star crumb count 0–3
forge_ranked: bool = False    # Forger was ranked Blacksmith (+10 star bonus)
forge_element: int = 0        # Element from elemental stone (0=Neutral/none)
```

### Fields added in Session K2 [EXISTS]:
```python
active_items_bonuses: Dict[str, int] = {}   # G46: consumable/food bonuses (temporary catch-all)
manual_adj_bonuses:   Dict[str, int] = {}   # G47: raw numeric escape hatch, no source attribution
# Keys: "str","agi","vit","int","dex","luk","batk","hit","flee","cri","def","mdef","aspd_pct","maxhp","maxsp"
# Saved/loaded under "active_items" / "manual_adj" in build JSON.
# bonus_str–luk and flat bonus fields are now zeroed on load; all bonuses come from gear+G46+G47.
```

### Fields added in Session M0 [EXISTS]:
```python
support_buffs: Dict[str, object] = field(default_factory=dict)
    # Party/outgoing buffs and target-applied debuffs received by player's team.
    # Keys added per-session as sub-groups are implemented (M, M2, O, R).
    # e.g. {"SC_ADRENALINE": 0, "SC_BLESSING": 0, ...}
    # SC_ADRENALINE migrated here from active_status_levels (build save migration in BuildManager).
player_active_scs: Dict[str, object] = field(default_factory=dict)
    # Debuffs the enemy has applied TO the player (affects incoming damage calcs).
    # Keys added in Session R when player_debuffs_section gets actual toggles.
    # e.g. {"SC_ETERNALCHAOS": False, "SC_CURSE": False, ...}
```

### Fields added in Session M2 [EXISTS]:
```python
song_state: Dict[str, object] = field(default_factory=dict)
    # Bard/Dancer song caster stats + per-song levels + per-stat overrides.
    # Bard keys: "caster_agi/dex/vit/int/luk", "mus_lesson", "SC_ASSNCROS" (level), "SC_ASSNCROS_agi" (None=shared)
    # Dancer keys: "dancer_agi/dex/vit/int/luk", "dance_lesson", "SC_HUMMING" (level), etc.
    # Ensemble keys: "SC_DRUMBATTLE", "SC_NIBELUNGEN", "SC_SIEGFRIED" (level only).
    # Saved under "song_state" key in build JSON. Migration: SC_ASSNCROS moved from active_status_levels.
```

### Other [EXISTS] fields added in Session B:
```python
equip_mdef: int = 0     # Hard MDEF total from bMdef item scripts (PlayerBuild field;
                         # fed into StatusData.mdef via StatusCalculator + main_window)
```

---

## mob_db.json — Unused Fields (core/data/pre-re/db/)

All exist in JSON but `loader.get_monster()` doesn't populate them into Target:

| JSON field | Where needed | Status |
|---|---|---|
| `mdef` | `Target.mdef_` — mob hard MDEF for incoming magic | [x] Added Session A |
| `stats.int` | `Target.int_` — for mob MATK calc and mob soft MDEF (mdef2) | [x] Added Session A |
| `stats.str` | Mob physical ATK derivation (for custom mob ATK if needed) | [ ] not yet loaded |
| `stats.dex` | Mob HIT calculation | [ ] not yet loaded |
| `atk_min` | `IncomingPhysicalPipeline` — already shown in IncomingDamageSection display | [ ] pipeline not yet implemented |
| `atk_max` | Same | [ ] pipeline not yet implemented |

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
    # Added Session B:
    magic: Optional[DamageResult] = None       # BF_MAGIC outgoing (mirrored to .normal for GUI)
    # Added Session K:
    katar_second: Optional[DamageResult] = None
    katar_second_crit: Optional[DamageResult] = None
    # Added Session G54:
    proc_chance: float = 0.0                   # 0 = not eligible
    double_hit: Optional[DamageResult] = None  # TF_DOUBLE / GS_CHAINACTION proc branch
    double_hit_crit: Optional[DamageResult] = None
    dps: float = 0.0                           # Σ(chance×dmg)/Σ(chance×delay) × 1000
    attacks: List[AttackDefinition] = []       # full distribution; append to extend; Markov seam
```

### Fields to add for full product [NEW]:
```python
BattleResult:
    incoming_physical: Optional[DamageResult] = None
    incoming_magic: Optional[DamageResult] = None
    # OR: separate result objects from separate pipeline runs — TBD at design time
```

Architecture note: BattleResult is used for both physical and magic outgoing (magic routed
via MagicPipeline, stored in `.magic` and mirrored to `.normal` for GUI compatibility).
Incoming pipelines may follow the same pattern or use separate result types — decide at Session D.

---

## SkillInstance (core/models/skill.py)

No changes needed for current gaps. BF_MAGIC uses the same `SkillInstance` passed to
`calc_skillratio(BF_MAGIC, ...)`. The skill's `bf_type` (BF_WEAPON vs BF_MAGIC) is
determined by `skills.json` data and the skill ID.
