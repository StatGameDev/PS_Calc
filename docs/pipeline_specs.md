# PS_Calc — Pipeline Specifications
_All formulas confirmed from Hercules source unless marked (wiki) or (inferred)._
_Pre-renewal only. Ignore all #ifdef RENEWAL blocks._

---

## BF_WEAPON Outgoing — Current Step Order

Implemented in `core/calculators/battle_pipeline.py`.

```
BaseDamage      battle_calc_base_damage2   — weapon ATK range, SizeFix, overrefine
SkillRatio      battle_calc_skillratio     — skill % multiplier
[CritAtkRate]   crit branch only           — ATK_ADDRATE(crit_atk_rate) battle.c:5333
DefenseFix      battle_calc_defense        — hard DEF % + VIT DEF random range (skipped on crit)
ActiveStatusBonus  post-defense SC_*       — SC_AURABLADE etc. flat ATK_ADD
RefineFix       ATK_ADD2(sstatus->rhw.atk2)  — deterministic, both branches
MasteryFix      battle_calc_masteryfix     — flat + conditional mastery bonuses
AttrFix         calc_elefix                — elemental multiplier table
[CardFix]       battle_calc_cardfix        — attacker side always; target side if is_pc=True
FinalRateBonus  battle_config rates        — short/long/weapon_damage_rate
```

### CardFix (Implemented Session A)

Insert after AttrFix, before FinalRateBonus.
Source: `battle.c:5872` (attacker side), `battle.c:5885` (target side, only if `tsd != NULL`).

Attacker side (always runs):
```
cardfix = 1000
cardfix = cardfix * (100 + addrace[target.race]) / 100
cardfix = cardfix * (100 + addele[target.def_ele]) / 100
cardfix = cardfix * (100 + addsize[target.size]) / 100
cardfix = cardfix * (100 + addrace[RC_BOSS or RC_NONBOSS]) / 100
if BF_LONG:
    cardfix = cardfix * (100 + long_attack_atk_rate) / 100   # #ifndef RENEWAL, battle.c:~1262
damage = damage * cardfix / 1000
```

Target side (only if `target.is_pc == True`):
```
cardfix = 1000
cardfix = cardfix * (100 - sub_ele[weapon_element]) / 100
cardfix = cardfix * (100 - sub_size[attacker_size]) / 100
cardfix = cardfix * (100 - sub_race[attacker_race]) / 100
cardfix = cardfix * (100 - sub_race[RC_BOSS or RC_NONBOSS]) / 100
if BF_SHORT: cardfix = cardfix * (100 - near_attack_def_rate) / 100    # #ifndef RENEWAL
if BF_LONG:  cardfix = cardfix * (100 - long_attack_def_rate) / 100    # #ifndef RENEWAL
damage = damage * cardfix / 1000
```

Data source for attacker side: `GearBonuses` (recompute via `GearBonusAggregator.compute(build.equipped)`).
Data source for target side: `Target` fields (sub_race, sub_ele, etc.).

### Other completed BF_WEAPON items:

**SC_IMPOSITIO (G1)** — Fixed Session A. Pre-renewal, adds `val2 = level * 5` flat to weapon ATK.
Source: `status.c #ifndef RENEWAL ~line 4562`: `watk += sc->data[SC_IMPOSITIO]->val2`
Applied in BaseDamage before the ATK range roll.

**Arrow ATK (G3)** — Fixed Session A. For bow/ranged weapons, equipped ammo ATK added to weapon ATK in BaseDamage.

**ASC_KATAR (G4)** — Fixed Session C. After flat AS_KATAR mastery:
Source: `battle.c masteryfix #else (pre-re)`:
```c
if (sd->weapontype == W_KATAR && (skill2_lv=pc->checkskill(sd,ASC_KATAR)) > 0)
    damage += damage * (10 + 2 * skill2_lv) / 100;
```
GUI: ASC_KATAR row in passive_section.py, visible only for job_id 24 (Assassin Cross).

**ignore_def (G5)** — Fixed Session A. Percentage of hard DEF bypassed before defense formula.
Source: `battle.c:5703-5712`: `ignore_def_race[target.race] + ignore_def_race[boss_key]`.
Applied in DefenseFix, reducing `def1` by combined ignore % before applying normal formula.

**bAtkRate (G10)** — Fixed Session C. Generic ATK% bonus before SkillRatio.
Source: `battle.c:5330 #ifndef RENEWAL`: `ATK_ADDRATE(sd->bonus.atk_rate)`
Applied as a dedicated step between BaseDamage and SkillRatio in battle_pipeline.py.

---

## BF_MAGIC Outgoing — Implemented Session B

Source: `battle.c:3828 battle_calc_magic_attack`.

### Pre-renewal MATK formulas (status.c #ifndef RENEWAL):
```
matk_min = INT + (INT / 7) * (INT / 7)    # status.c:3783
matk_max = INT + (INT / 5) * (INT / 5)    # status.c:3792
```
Both capped by `battle_config.matk_min` and `battle_config.matk_max`.

### Pipeline step order (magic_pipeline.py):
```
MATK base       random roll in [matk_min, matk_max]
                On SC_MAXIMIZEPOWER: use matk_max (no roll)
SkillRatio      MATK_RATE(calc_skillratio BF_MAGIC) — per-hit
DefenseFix      BF_MAGIC per-hit:
                  pre-re (magic_defense_type=0):  damage = damage*(100-mdef)/100 - mdef2
                  mdef2 computed inline from target.int_ + (target.vit >> 1)
AttrFix         per-hit — magic element vs player armor_element
HitCount×N      positive hit_count = actual multiply; negative = cosmetic (damage_div_fix macro)
[CardFix]       target-side only (cflag=0), only if target.is_pc:
                  sub_ele, sub_race, magic_def_rate
                NOTE: attacker-side magic cardfix (magic_addrace etc.) is #ifdef RENEWAL — skip
FinalRateBonus  same as BF_WEAPON
```

### MDEF values:
- `mdef` (hard MDEF): from equip for PC (`bMdef` scripts via GearBonuses), from mob_db `mdef` for mobs.
- `mdef2` (soft MDEF): `int_ + vit//2` — status.c:3867 `#else not RENEWAL`.
- `ignore_mdef`: `GearBonuses.ignore_mdef_rate` dict, keyed by race_rc + boss_rc.
- IT_ARMOR items have no raw `mdef` field in item_db.json — equip MDEF comes from `bMdef` scripts only.

### Magic skill ratios:
`_BF_MAGIC_RATIOS` dict in `skill_ratio.py` — 15 pre-renewal spells from battle.c:1631-1785.
Positive hit_count → actual multi-hit (dmg × N). Negative → cosmetic only (damage_div_fix macro).
WZ_FIREPILLAR has negative number_of_hits → cosmetic, no multiplication.

### matk_percent and skillatk_bonus:
Both are stubs — no GearBonuses fields yet. Deferred until cards/gear using these are encountered.

---

## Incoming Physical — Mob to Player — Implemented Session E

Implemented in `core/calculators/incoming_physical_pipeline.py`.

### Architecture:
`calculate(mob_id, player_target, gear_bonuses, build, is_ranged=False, mob_atk_bonus_rate=0)`

- Mob ATK computed internally from mob_db (`atk_min/atk_max` + batk from `stats.str`).
  Two-part: weapon component `[atk_min, atk_max-1]` + `batk = str + (str//10)^2` (no dex/luk for mobs).
  Source: mob.c:4937, status.c:3749 `#else not RENEWAL`.
- `mob_atk_bonus_rate` is the buff/debuff hook for future SC effects (mirrors SC modifying rhw.atk/atk2).

### Steps:
```
MobBaseATK      atk_min/atk_max from mob_db + batk from stats.str
AttrFix         mob.element vs player.armor_element
DefenseFix      is_pc=True — flat def1 subtraction + PC VIT DEF formula
CardFix         calculate_incoming_physical() — keys player's sub_ele/sub_race/sub_size
                against mob's actual element/race/size (not hardcoded DemiHuman)
```

DefenseFix called with `build=None`, `GearBonuses()` — mob has no attacker-side ignore_def cards.

### Player armor element:
Tracked as `PlayerBuild.armor_element` (int 0–9, default 0 = Neutral).
Set by armor element selector in equipment_section.py (added Session E).
Saved/loaded under `flags.armor_element` in build_manager.py (Session D).

---

## Incoming Physical — Player to Player — Planned Session F (G30)

### Architecture:
No new pipeline code needed. The existing `BattlePipeline.calculate()` already accepts any `Target`.
Run with attacker=second PlayerBuild, target=`player_build_to_target(defender_build)`.

`player_build_to_target()` is already implemented in `build_manager.py` (Session E):
```python
BuildManager.player_build_to_target(build, status, gear_bonuses) -> Target
# Sets is_pc=True, size=Medium, race=DemiHuman, element_level=1
# sub_size={} — GearBonuses has add_size (offensive) not sub_size (defensive)
```

GUI plan: add "PvP Attacker" QComboBox to IncomingDamageSection, populated from
`BuildManager.list_builds()`. On selection change, run BattlePipeline with second build as attacker.

---

## Incoming Magic — Mob to Player — Implemented Session E

Implemented in `core/calculators/incoming_magic_pipeline.py`.

### Architecture:
`calculate(mob_id, player_target, gear_bonuses, build, skill=None, mob_matk_bonus_rate=0)`

- Optional `skill: SkillInstance` — when provided, applies skill ratio and resolves element
  from skills.json; falls back to mob natural element.
- `mob_matk_bonus_rate: int = 0` for future buff/debuff support.

### Mob MATK:
```
mob_matk_min = mob.int_ + (mob.int_ / 7) * (mob.int_ / 7)
mob_matk_max = mob.int_ + (mob.int_ / 5) * (mob.int_ / 5)
```
Same formula as player MATK. Read from `get_monster_data()["stats"]["int"]` directly.

### Steps:
```
MobMATKRoll     random in [mob_matk_min, mob_matk_max]
SkillRatio      if skill provided (else 100%)
AttrFix         mob.element vs player.armor_element
DefenseFix      calculate_magic() — per hit, MDEF%+mdef2
CardFix         calculate_incoming_magic() — mob's actual race for sub_race lookup
                (not hardcoded RC_DemiHuman like player-vs-player calculate_magic)
```

Empty `GearBonuses()` passed to DefenseFix — mob has no ignore_mdef cards.

### G43 — mob skill picker (Planned Session F):
Currently IncomingDamageSection provides no way to select a mob skill or override element.
Plan: Ranged checkbox (BF_LONG in CardFix) + magic element override combo + ratio spinbox.
See docs/session_roadmap.md Session F for full design.

---

## Attribute Fix Table

Same table used by all pipelines. Source: `core/data/pre-re/tables/attr_fix.json`.
Indexed by: attacking_element × defending_element × defending_level (1-4).
100 = neutral, >100 = vulnerability, <100 = resistance, 0 = immunity.

For incoming damage: `attacking = mob.element`, `defending = player.armor_element`.
For outgoing damage: `attacking = weapon.element`, `defending = target.element`.

---

## Pre-Renewal Defense Formulas (Quick Reference)

### Physical hard DEF:
- **Mob target**: `damage = damage * (100 - def1/(def1+400)*90) / 100`  (percentage curve)
- **PC target**: `damage -= def1`  (flat subtraction)
- Controlled by `weapon_defense_type` config and `tsd` check.

### Physical soft DEF (VIT DEF), randomized:
- `variance_max = def2 * (def2 - 15) / 150`  (or simpler for mob)
- **Mob target**: `vit_def = def2/2 + rnd() % variance_max` then `+= i * 5`
- **PC target**: same range formula, then `+= i * (3 + (level+1) * 0.04)`

### Magic defense (pre-renewal, magic_defense_type=0):
- `damage = damage * (100 - mdef) / 100 - mdef2`
- `mdef2 = int_ + vit//2`  (status.c:3867 `#else not RENEWAL`)
- `ignore_mdef[race + boss]` applied before this: `mdef -= mdef * i / 100`