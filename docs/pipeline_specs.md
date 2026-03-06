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
[CardFix]       battle_calc_cardfix        — NOT YET IMPLEMENTED (G2, G8)
FinalRateBonus  battle_config rates        — short/long/weapon_damage_rate
```

### Missing steps to add:

**CardFix** — insert after AttrFix, before FinalRateBonus.
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

### Other missing pieces in BF_WEAPON:

**SC_IMPOSITIO (G1)** — Pre-renewal, adds `val2 = level * 5` flat to weapon ATK.
Source: `status.c #ifndef RENEWAL ~line 4562`: `watk += sc->data[SC_IMPOSITIO]->val2`
Apply: in BaseDamage before the ATK range roll, as a flat addition to weapon ATK value.

**Arrow ATK (G3)** — For bow/ranged weapons, add equipped ammo ATK.
Apply: in BaseDamage, if `weapon.weapon_type` is ranged and `build.equipped.get("ammo")` is set:
```python
ammo = loader.get_item(build.equipped["ammo"])
arrow_atk = ammo.get("atk", 0) if ammo else 0
```
Add `arrow_atk` to the weapon ATK value used in the range roll.

**ASC_KATAR (G4)** — Advanced Katar Research, Assassin Cross skill, percentage mastery.
Source: `battle.c masteryfix #else (pre-re)`:
```c
if (sd->weapontype == W_KATAR && (skill2_lv=pc->checkskill(sd,ASC_KATAR)) > 0)
    damage += damage * (10 + 2 * skill2_lv) / 100;
```
Apply: in MasteryFix after flat AS_KATAR mastery, as a % branch.
GUI: add ASC_KATAR (lv 1-5) to passive_section.py mastery list; only show for Assassin Cross (job_id 24).

**ignore_def (G5)** — Percentage of hard DEF bypassed before defense formula.
Source: `battle.c:5703-5712`: `ignore_def_race[target.race] + ignore_def_race[boss_key]`.
Also `ignore_def_ele[target.def_ele]` (separate field).
Apply: in DefenseFix, reduce `def1` by combined ignore %, then apply normal formula.
Data: `GearBonuses.ignore_def_rate` dict already populated by aggregator. Also need `ignore_def_ele` dict.

**VIT DEF PC branch (G7)** — Different multiplier in soft DEF variance formula.
Source: `battle.c:1495` (tsd): `vit_def += i * (int)(3 + (tsd->status.base_level+1) * 0.04)`
vs `battle.c:1498` (else): `vit_def += i * 5`
Apply: in DefenseFix, branch on `target.is_pc`.

**bAtkRate (G10)** — Generic ATK% bonus before SkillRatio.
Source: `battle.c:5330 #ifndef RENEWAL`: `ATK_ADDRATE(sd->bonus.atk_rate)`
Apply: in BaseDamage or as a new step, `dmg = dmg.scale(100 + gear_bonuses.atk_rate, 100)`.

---

## BF_MAGIC Outgoing — Full Spec (Not Yet Implemented)

Source: `battle.c:3828 battle_calc_magic_attack`.

### Pre-renewal MATK formulas (status.c #ifndef RENEWAL):
```
matk_min = INT + (INT / 7) * (INT / 7)    # status.c:3783
matk_max = INT + (INT / 5) * (INT / 5)    # status.c:3792
```
Both capped by `battle_config.matk_min` and `battle_config.matk_max`.

### Pipeline step order:
```
MATK base       random roll in [matk_min, matk_max]
                On SC_MAXIMIZEPOWER: use matk_max (no roll)
SkillRatio      MATK_RATE(calc_skillratio BF_MAGIC)    — same fn, BF_MAGIC path
matk_percent    MATK_RATE(sstatus->matk_percent)       — gear/buff % modifier
skillatk_bonus  MATK_ADD(pc->skillatk_bonus * %)       — skill-specific % from gear
[sub_skillatk]  MATK_ADD(-pc->sub_skillatk_bonus * %)  — target skill-specific reduction (PC target only)
ignore_mdef     reduce mdef by %                        — sd->ignore_mdef[race+boss]
calc_defense    BF_MAGIC:
                  pre-re (magic_defense_type=0):  damage = damage*(100-mdef)/100 - mdef2
                  pre-re (magic_defense_type=1+): damage -= mdef*magic_defense_type + mdef2
[CardFix]       target-side only (cflag=0), only if target.is_pc:
                  sub_ele, sub_size, sub_race, near/long_attack_def_rate, magic_def_rate
                NOTE: attacker-side magic cardfix (magic_addrace etc.) is #ifdef RENEWAL — skip
FinalRateBonus  same as BF_WEAPON (weapon_damage_rate? or separate magic rate)
```

### MDEF values:
- `mdef` (hard MDEF): from equip for PC, from mob_db `mdef` for mobs. Percentage-style formula.
- `mdef2` (soft MDEF): from INT. Exact formula needs one more status.c grep — likely `INT/2` or similar.
- `ignore_mdef`: `GearBonuses` field needed. Same pattern as `ignore_def`.

### Magic skill ratios (common pre-renewal spells):
All MATK_RATE calls in calc_skillratio BF_MAGIC path. Key skills to implement:
- Bolt spells (Fire/Ice/Lightning Bolt Lv1-10): 100% * skill_lv per hit
- Jupitel Thunder: 100+20*skill_lv%
- Lord of Vermillion: 100+20*skill_lv%
- Thunderstorm: 80+20*skill_lv%
- Fire Pillar: 100% + MATK_ADD(100+50*lv) special case
- Storm Gust: 100+40*skill_lv%
- Heavens Drive/Earth Spike: 100+25*skill_lv%
Grep `calc_skillratio` BF_MAGIC section before implementing.

---

## Incoming Physical — Mob to Player (Not Yet Implemented)

This is the reverse BF_WEAPON pipeline with the player as target.

### Architecture:
Create `IncomingPhysicalPipeline`. Inputs:
- `mob_data: dict` — raw mob_db entry (atk_min, atk_max, element, element_level, race, size)
- `player_target: Target` — player as target (is_pc=True, def_, vit, element=armor_element, sub_race/ele/size from gear)
- `config: BattleConfig`

### Steps:
```
Mob ATK         random in [mob.atk_min, mob.atk_max]
                No SizeFix for mob attacks (mobs have no weapon_type in same sense)
AttrFix         mob.element vs player.armor_element — same attr_fix table, swapped roles
DefenseFix      player hard DEF (def1, flat subtraction for PC) + VIT soft DEF (PC branch)
CardFix         target-side only: player.sub_ele[mob.element], sub_race[mob.race],
                  sub_size[mob.size], near/long_attack_def_rate
```

### Player armor element:
Must be tracked as `Target.armor_element` (or `PlayerBuild.armor_element`).
Sources: equipped armor's element card (Pasana Card = Fire, etc.) or endow status effect.
In pre-renewal: most players are Neutral element unless endowed or wearing elemental armor.

---

## Incoming Physical — Player to Player (Not Yet Implemented)

### Architecture:
This is the FULL BF_WEAPON outgoing pipeline with:
- Attacker: second PlayerBuild (their weapon, skills, cards)
- Target: first player as `Target` (is_pc=True, with all defensive gear fields)

No new pipeline code needed — the existing `BattlePipeline.calculate()` already accepts any `Target`.
The only requirement is that `Target` fields be fully populated for the defending player.

To build a player Target from a PlayerBuild:
```python
def player_build_to_target(build: PlayerBuild, status: StatusData) -> Target:
    gear = GearBonusAggregator.compute(build.equipped)
    return Target(
        def_    = status.def_,      # hard DEF
        vit     = status.vit,       # for VIT DEF variance
        level   = build.base_level,
        is_pc   = True,
        size    = "Medium",         # all pre-re PCs are Medium
        race    = "DemiHuman",      # all pre-re PCs are DemiHuman
        element = build.armor_element,  # derived from equipped armor
        element_level = 1,
        luk     = status.luk,
        agi     = status.agi,
        flee    = status.flee,
        sub_race = gear.sub_race,
        sub_ele  = gear.sub_ele,
        sub_size = gear.sub_size,
        near_attack_def_rate = gear.near_atk_def_rate,
        long_attack_def_rate = gear.long_atk_def_rate,
        magic_def_rate       = gear.magic_def_rate,
        mdef_   = status.mdef,
        int_    = status.int_,      # for soft MDEF
    )
```

---

## Incoming Magic — Mob to Player (Not Yet Implemented)

### Architecture:
Create `IncomingMagicPipeline`. Inputs:
- `mob_data: dict` — raw mob_db entry (int_ from stats, element, element_level, race)
- `player_target: Target` — player as target (is_pc=True, mdef_, int_ for soft MDEF, armor_element)
- `skill: SkillInstance` (if mob is using a specific skill; else use generic magic attack)
- `config: BattleConfig`

### Mob MATK:
```
mob_matk_min = mob.int_ + (mob.int_ / 7) * (mob.int_ / 7)
mob_matk_max = mob.int_ + (mob.int_ / 5) * (mob.int_ / 5)
```
Same formula as player MATK.

### Steps:
```
Mob MATK        random in [mob_matk_min, mob_matk_max]
SkillRatio      if mob uses specific skill (else 100%)
AttrFix         mob.element vs player.armor_element
DefenseFix(M)   player MDEF: damage = damage*(100-mdef)/100 - mdef2
CardFix         target-side only: player.sub_ele[mob.element], magic_def_rate
```

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
- `mdef2` is soft MDEF (INT-based flat subtraction — exact formula needs verification)
- `ignore_mdef[race + boss]` applied before this: `mdef -= mdef * i / 100`
