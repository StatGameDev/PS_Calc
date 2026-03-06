# PS_Calc — Gap Tracker
_Last updated: Session A planning. All gaps confirmed from Hercules source unless marked (wiki) or (inferred)._
_Status: [ ] open, [x] done, [~] partial_

---

## BF_WEAPON Outgoing (Player → Any Target)

| ID | Status | Description | Hercules ref | Notes |
|---|---|---|---|---|
| G1 | [ ] | SC_IMPOSITIO misclassified as Renewal-only. Adds `val2` (level×5) flat to weapon ATK. | status.c #ifndef RENEWAL line ~4562 | active_status_bonus.py comment is wrong; add to BaseDamage as flat watk |
| G2 | [ ] | Attacker-side CardFix entirely absent. Chains: `addrace[target.race]`, `addele[target.def_ele]`, `addsize[target.size]`, boss/nonboss, `long_attack_atk_rate` (BF_LONG, #ifndef RENEWAL). | battle.c:5872 attacker side; cardfix fn ~1060 | GearBonuses stubs populated; nothing reads them. New `card_fix.py` after AttrFix, before FinalRateBonus |
| G3 | [ ] | Arrow ATK not added for bow builds. `sd->arrow_atk` contributes to weapon ATK for arrow attacks. Ammo `atk` field never fetched. | battle.c arrow_atk path | Fetch `loader.get_item(build.equipped["ammo"])["atk"]` in BaseDamage |
| G4 | [ ] | ASC_KATAR percentage mastery missing. Pre-renewal masteryfix: `damage += damage * (10 + 2*skill_lv) / 100` for W_KATAR. | battle.c masteryfix #else block (pre-re) | AS_KATAR flat exists; ASC_KATAR % branch and passive_section entry both absent |
| G5 | [ ] | ignore_def not wired into DefenseFix. `ignore_def_race[target.race] + ignore_def_race[boss_key]` reduces def1 %. Also `ignore_def_ele`. | battle.c ~5703-5712 | GearBonuses.ignore_def_rate populated; DefenseFix doesn't read it |
| G6 | [ ] | Target model cannot represent a player defender. `is_pc` field exists but unused. Fields needed: sub_race, sub_ele, sub_size, near/long_attack_def_rate, magic_def_rate, mdef_, int_, armor_element, flee. | battle.c battle_calc_cardfix target side | All default to 0 for mob targets — zero behaviour change until PvP used |
| G7 | [ ] | VIT DEF PC branch dead code — `target.is_pc` never True. Formula in defense_fix.py IS correct per C source (battle.c:1487-1488). Branch becomes live in Session D when player_build_to_target() is implemented. | battle.c:1487-1488 #ifndef RENEWAL | No formula change needed. Lines 1495/1498 are AL_DP (Angelus) and RA_RANGERMAIN skill bonuses on top — not the base formula (roadmap misread) |
| G41 | [ ] | [LOW PRIORITY] PC VIT DEF: Hercules comment (line 1486) disagrees with C implementation. Comment: `[VIT*0.5]+rnd([VIT*0.3],max([VIT*0.3],[VIT^2/150]-1))` → [64,81] for VIT=80. Code: `def2/2+rnd()%(def2*(def2-15)/150)` → [40,73] for VIT=80. Player testing matches comment, not code. | battle.c:1486-1488 | Do NOT change code based on comment. Investigate against official server data before any fix. Currently follow C implementation. |
| G8 | [ ] | Target-side CardFix not implemented. Multiplies: sub_ele, sub_size, sub_race, boss, near/long_def_rate. Only fires when target.is_pc. | battle.c battle_calc_cardfix cflag=0 BF_WEAPON | Goes in card_fix.py alongside attacker side |
| G9 | [ ] | ASPD skill buffs not in StatusCalculator. SC_TWOHANDQUICKEN, SC_ADRENALINE, SC_SPEARQUICKEN, SC_ONEHAND modify amotion in status.c. | status.c SC_TWOHANDQUICKEN etc. | active_status_levels read for damage SCs but not ASPD |
| G10 | [ ] | bAtkRate bonus not in system. `sd->bonus.atk_rate` applied before SkillRatio (#ifndef RENEWAL line 5330). | battle.c:5330 | Not in item parser, GearBonuses, or pipeline anywhere |
| G11 | [ ] | bLongAtkRate (GearBonuses.long_atk_rate) accumulated but never applied. Belongs inside CardFix for BF_LONG. | battle.c cardfix #ifndef RENEWAL line ~1262 | Fix as part of G2 CardFix implementation |
| G12 | [ ] | F3 — Armor refine DEF not calculated. No scraper, no table, no pipeline step. | Hercules refine_db.conf | Refine slider exists in GUI; value goes nowhere |
| G13 | [ ] | F1 — Card slot UI absent. No sub-slot buttons per item. | — | GearBonusAggregator handles any key in build.equipped — data side is ready |
| G14 | [ ] | bWeaponAtk (weapon-type ATK%) not in system. `sd->weapon_atk_rate[weapontype]` applied in base damage. | battle.c:679-685 | Rare in pre-re DB; low priority |
| G15 | [ ] | F4 — Gear bonuses invisible in Stats section. No "from gear" indicator. | — | UX only |
| G16 | [ ] | E4 — Katar second hit fraction unverified. | battle.c katar dual-hit section | Grep before implementing |
| G17 | [ ] | E6 — Forged weapon Verys: flat +5 ATK per Very gemstone after AttrFix. | battle.c forged weapon section | Low priority |

---

## BF_MAGIC Outgoing (Player → Any Target) — ENTIRELY ABSENT

| ID | Status | Description | Hercules ref | Notes |
|---|---|---|---|---|
| G18 | [ ] | No MATK in StatusCalculator. Pre-re: matk_min = INT+(INT/7)^2, matk_max = INT+(INT/5)^2. | status.c:3783,3792 #ifndef RENEWAL | StatusData missing matk_min, matk_max |
| G19 | [ ] | No BF_MAGIC pipeline. No MagicPipeline class. | battle.c:3828 battle_calc_magic_attack | All magic skills unsupported |
| G20 | [ ] | No MDEF defense step. Pre-re formula: `damage * (100-mdef)/100 - mdef2` (magic_defense_type=0 default). | battle.c:1581-1584 #ifndef RENEWAL | StatusData missing mdef, mdef2 fields |
| G21 | [ ] | MATK display absent from derived_section. | — | GUI gap |
| G22 | [ ] | No magic skill ratio support in skill_ratio.py. | battle.c calc_skillratio BF_MAGIC path | Common magic skills: Fire/Ice/Lighting Bolt, Jupitel, Lord of Vermillion, etc. |
| G23 | [ ] | Magic target-side CardFix unimplemented. sub_ele, sub_size, sub_race, near/long_def_rate, magic_def_rate. Only fires when target.is_pc. | battle.c:4134 cflag=0 BF_MAGIC | IMPORTANT: attacker-side magic cardfix (magic_addrace etc.) is #ifdef RENEWAL — does NOT apply pre-re |
| G24 | [ ] | ignore_mdef not in GearBonuses or pipeline. `sd->ignore_mdef[race] + [boss]` applied before magic defense. | battle.c:1564-1569 | Same pattern as G5 (ignore_def) |
| G25 | [ ] | Player MDEF not in StatusData. Hard MDEF from equip+cards; soft MDEF from INT. | status.c mdef2 formula | Needed for incoming magic too |

---

## Incoming Physical (Mob → Player) — DISPLAY STUB ONLY

| ID | Status | Description | Hercules ref | Notes |
|---|---|---|---|---|
| G26 | [ ] | No incoming physical pipeline. IncomingDamageSection shows mob ATK range as display text only. | — | Need IncomingPhysicalPipeline class |
| G27 | [ ] | Player armor element not tracked. Determines how player defends against elemental attacks. | attr_fix table | PlayerBuild has no armor element field; needed to look up attr_fix for incoming |
| G28 | [ ] | mob_db int_, str, dex not loaded into Target. Mob MATK derived from int_. | mob_db stats.int | loader.get_monster() doesn't populate these |
| G29 | [ ] | Target-side player cards not modelled for incoming. sub_race[mob.race], sub_ele[mob.element], near/long_def_rate from player cards. | battle.c cardfix target side | Same G6/G8 infrastructure; these fields just need populating from player gear |

---

## Incoming Physical (Player → Player) — ENTIRELY ABSENT

| ID | Status | Description | Notes |
|---|---|---|---|
| G30 | [ ] | PvP incoming physical pipeline absent. | Architecturally: run full BF_WEAPON outgoing pipeline with second PlayerBuild as attacker, first player's Target (is_pc=True) as defender. Attacker-side CardFix is active (they have gear). Defender-side CardFix is active (they have gear). Reuses entire existing pipeline — no new steps. |

---

## Incoming Magic (Mob or Player → Player) — ENTIRELY ABSENT

| ID | Status | Description | Hercules ref | Notes |
|---|---|---|---|---|
| G31 | [ ] | No mob MATK derivation. Mob MATK = mob.int_ + (int_/7)^2 to int_ + (int_/5)^2. | status.c same formula | mob_db has stats.int, not currently loaded |
| G32 | [ ] | No incoming magic pipeline. Player as target of magic. | — | Needs MagicPipeline run with mob/player as src, player Target (is_pc=True) as target |
| G33 | [ ] | Player MDEF not calculated. Hard MDEF from equip, soft MDEF from INT. | status.c calc_mdef | Needs StatusCalculator extension and StatusData fields |

---

## UI / Data Infrastructure

| ID | Status | Description |
|---|---|---|
| G34 | [ ] | 4.4 — Skill combo job filter |
| G35 | [ ] | 4.5 — Equipment Browser job filter |
| G36 | [ ] | 4.6 — Monster Browser race/element/size dropdowns |
| G37 | [ ] | 4.7 — Passives/Masteries job filter |
| G38 | [ ] | F3 — Armor refine DEF (needs import_refine_db.py scraper) |
| G39 | [ ] | F7 — Inline equipment dropdown (low priority) |
| G40 | [ ] | P1 — StepsBar expanded state persists across focus changes |

---

## Completed Gaps (reference)

| ID | Description | Session |
|---|---|---|
| — | B3/B4/B5 splitter/target bugs | 1 |
| — | B6 Normal Attack absent from skill combo | 1 |
| — | C1a VIT DEF avg off-by-0.5 | 2 |
| — | E1 Hit/Miss (hitrate, perfect_dodge) | 3 |
| — | C3 ASPD/HP/SP in StatusCalculator | 3 |
| — | B8/B9 Save button | 4 |
| — | D5/D4 Script parsing + GearBonusAggregator | 4 |
| — | F2 Armor base DEF from item_db | 5 |
| — | F5 2H weapon locks left hand | 5 |
| — | F6 Assassin dual-wield restriction | 5 |
| — | derived_section live ASPD/HP/SP labels | 5 |
