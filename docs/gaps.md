# PS_Calc — Gap Tracker
_Last updated: Post-Session G. All gaps confirmed from Hercules source unless marked (wiki) or (inferred)._
_Status: [ ] open, [x] done, [~] partial_

---

## BF_WEAPON Outgoing (Player → Any Target)

| ID | Status | Description | Hercules ref | Notes |
|---|---|---|---|---|
| G1 | [x] | SC_IMPOSITIO misclassified as Renewal-only. Adds `val2` (level×5) flat to weapon ATK. | status.c #ifndef RENEWAL line ~4562 | Fixed in Session A: base_damage.py after atkmax, before atkmin |
| G2 | [x] | Attacker-side CardFix entirely absent. Chains: `addrace[target.race]`, `addele[target.def_ele]`, `addsize[target.size]`, boss/nonboss, `long_attack_atk_rate` (BF_LONG, #ifndef RENEWAL). | battle.c:5872 attacker side; cardfix fn ~1060 | Fixed in Session A: new card_fix.py after AttrFix, before FinalRateBonus |
| G3 | [x] | Arrow ATK not added for bow builds. `sd->arrow_atk` contributes to weapon ATK for arrow attacks. Ammo `atk` field never fetched. | battle.c arrow_atk path | Fixed in Session A: base_damage.py fetches ammo ATK for Bow weapon type |
| G4 | [x] | ASC_KATAR percentage mastery missing. Pre-renewal masteryfix: `damage += damage * (10 + 2*skill_lv) / 100` for W_KATAR. | battle.c masteryfix #else block (pre-re) | Fixed Session C: mastery_fix.py + passive_section ASC_KATAR row (job-filtered to Assassin Cross) |
| G5 | [x] | ignore_def not wired into DefenseFix. `ignore_def_race[target.race] + ignore_def_race[boss_key]` reduces def1 %. Also `ignore_def_ele`. | battle.c ~5703-5712 | Fixed in Session A: defense_fix.py reads ignore_def_rate by race_rc + boss_rc |
| G6 | [x] | Target model cannot represent a player defender. `is_pc` field exists but unused. Fields needed: sub_race, sub_ele, sub_size, near/long_attack_def_rate, magic_def_rate, mdef_, int_, armor_element, flee. | battle.c battle_calc_cardfix target side | Fixed in Session A: all 9 fields added to target.py with zero defaults |
| G7 | [x] | VIT DEF PC branch dead code — `target.is_pc` never True. Formula in defense_fix.py IS correct per C source (battle.c:1487-1488). Branch becomes live in Session D when player_build_to_target() is implemented. | battle.c:1487-1488 #ifndef RENEWAL | Fixed Session E: player_build_to_target() sets is_pc=True; PC VIT DEF formula now active for all incoming physical hits. |
| G41 | [ ] | [LOW PRIORITY] PC VIT DEF: Hercules comment (line 1486) disagrees with C implementation. Comment: `[VIT*0.5]+rnd([VIT*0.3],max([VIT*0.3],[VIT^2/150]-1))` → [64,81] for VIT=80. Code: `def2/2+rnd()%(def2*(def2-15)/150)` → [40,73] for VIT=80. Player testing matches comment, not code. | battle.c:1486-1488 | Do NOT change code based on comment. Investigate against official server data before any fix. Currently follow C implementation. |
| G8 | [x] | Target-side CardFix not implemented. Multiplies: sub_ele, sub_size, sub_race, boss, near/long_def_rate. Only fires when target.is_pc. | battle.c battle_calc_cardfix cflag=0 BF_WEAPON | Fixed in Session A: card_fix.py fires target side when is_pc=True (activates in Session D) |
| G9 | [x] | ASPD skill buffs not in StatusCalculator. SC_TWOHANDQUICKEN, SC_ADRENALINE, SC_SPEARQUICKEN, SC_ONEHAND modify amotion in status.c. | status.c SC_TWOHANDQUICKEN etc. | Fixed Session C: status_calc_aspd_rate 1000-scale approach. SC_ASSNCROS completed Session M2 (formula: (MusLesson_lv/2+10+song_lv+caster_agi/10)*10 → amotion reduction). |
| G10 | [x] | bAtkRate bonus not in system. `sd->bonus.atk_rate` applied before SkillRatio (#ifndef RENEWAL line 5330). | battle.c:5330 | Fixed Session C: bAtkRate step added in battle_pipeline.py between BaseDamage and SkillRatio; removed from CardFix where it was incorrectly placed. |
| G11 | [x] | bLongAtkRate (GearBonuses.long_atk_rate) accumulated but never applied. Belongs inside CardFix for BF_LONG. | battle.c cardfix #ifndef RENEWAL line ~1262 | Fixed in Session A: CardFix applies long_atk_rate when is_ranged=True |
| G12 | [x] | F3 — Armor refine DEF not calculated. No scraper, no table, no pipeline step. | Hercules/db/pre-re/refine_db.conf | Fixed Session G: import_refine_db.py + refine_armor.json (stats_per_level=66). GearBonusAggregator.compute() accumulates raw units per IT_ARMOR slot, applies (total+50)//100 once. 5 call sites updated. |
| G13 | [x] | F1 — Card slot UI absent. No sub-slot buttons per item. | — | Fixed Session G: equipment_section.py card sub-slot buttons per item (dynamic count from item.slots). EquipmentBrowserDialog item_type_override="IT_CARD" + EQP_ACC bug fix. collect_into/load_build round-trip via {slot}_card_{n} keys in build.equipped. |
| G14 | [ ] | bWeaponAtk (weapon-type ATK%) not in system. `sd->weapon_atk_rate[weapontype]` applied in base damage. | battle.c:679-685 | Rare in pre-re DB; low priority |
| G15 | [x] | F4 — Bonus stat column redesign. StatsSection bonus spinboxes become read-only auto-computed labels. Value = GearBonuses + Active Items (G46) + Manual Adjustments (G47). Tooltip per stat shows per-source breakdown. Flat bonus row (BATK/HIT/FLEE/CRI/DEF/MDEF/ASPD%) same treatment. | Done Session K: stat_bonus_auto QLabel with tooltip; update_from_bonuses() in StatsSection wired from _run_status_calc via separate GearBonusAggregator.compute call; legacy bonus_* zeroed on load+collect. SC stat effects deferred (not yet in StatusCalculator). |
| G16 | [x] | E4 — Katar second hit. Normal attacks only. Formula: `damage2 = max(1, damage * (1 + TF_DOUBLE*2) // 100)`. CardFix does NOT apply to damage2 (flag.lh set after CardFix block). | battle.c:5941-5952 #ifndef RENEWAL | Done Session K: ForgeBonus + BattleResult.katar_second/_crit; summary "X + Y" display; TF_DOUBLE in passives. |
| G17 | [x] | E6 — Forged weapon Verys: flat star ATK per hit after AttrFix before CardFix. star: sc_count×5, ≥15→40, +10 if ranked. Element from forge elemental stone. | status.c:1634-1643; battle.c:5864 #ifndef RENEWAL | Done Session K: ForgeBonus modifier; forge toggle in equipment_section (replaces card row); is_forged/forge_sc_count/forge_ranked/forge_element on PlayerBuild+Weapon. |
| G44 | [ ] | P2 — Forge toggle exposed on all right_hand weapons. Should only appear on forgeable weapon types. Requires item_db weapon consolidation (duplicate IDs with different slot counts) before allowed-types list can be defined. | — | Prerequisite: DB consolidation discussion. |

---

## BF_MAGIC Outgoing (Player → Any Target)

| ID | Status | Description | Hercules ref | Notes |
|---|---|---|---|---|
| G18 | [x] | No MATK in StatusCalculator. Pre-re: matk_min = INT+(INT/7)^2, matk_max = INT+(INT/5)^2. | status.c:3783,3792 #ifndef RENEWAL | Fixed Session B: StatusData+StatusCalculator, derived_section MATK row |
| G19 | [x] | No BF_MAGIC pipeline. No MagicPipeline class. | battle.c:3828 battle_calc_magic_attack | Fixed Session B: magic_pipeline.py; routed from BattlePipeline on attack_type=="Magic" |
| G20 | [x] | No MDEF defense step. Pre-re formula: `damage * (100-mdef)/100 - mdef2` (magic_defense_type=0 default). | battle.c:1581-1584 #ifndef RENEWAL | Fixed Session B: DefenseFix.calculate_magic(); mdef2=int_+vit//2 computed inline |
| G21 | [x] | MATK display absent from derived_section. | — | Fixed Session B: MATK row (min–max) + MDEF row (hard+soft) added |
| G22 | [x] | No magic skill ratio support in skill_ratio.py. | battle.c calc_skillratio BF_MAGIC path | Fixed Session B: _BF_MAGIC_RATIOS dict (15 spells) + calculate_magic(); cosmetic vs actual hits per damage_div_fix |
| G23 | [x] | Magic target-side CardFix unimplemented. sub_ele, sub_size, sub_race, near/long_def_rate, magic_def_rate. Only fires when target.is_pc. | battle.c:4134 cflag=0 BF_MAGIC | Fixed Session B: CardFix.calculate_magic(); attacker-side magic bonuses correctly skipped (#ifdef RENEWAL) |
| G24 | [x] | ignore_mdef not in GearBonuses or pipeline. `sd->ignore_mdef[race] + [boss]` applied before magic defense. | battle.c:1564-1569 | Fixed Session B: ignore_mdef_rate in GearBonuses+aggregator; wired in DefenseFix.calculate_magic() |
| G25 | [x] | Player MDEF not in StatusData. Hard MDEF from equip+cards; soft MDEF from INT. | status.c mdef2 formula | Fixed Session B: mdef+mdef2 in StatusData; equip_mdef in PlayerBuild; bMdef route in aggregator |

---

## Incoming Physical (Mob → Player)

| ID | Status | Description | Hercules ref | Notes |
|---|---|---|---|---|
| G26 | [x] | No incoming physical pipeline. IncomingDamageSection shows mob ATK range as display text only. | — | Fixed Session E: IncomingPhysicalPipeline; step breakdown panel; wired in main_window. |
| G27 | [x] | Player armor element not tracked. Determines how player defends against elemental attacks. | attr_fix table | Session D: armor_element: int = 0 added to PlayerBuild; saved/loaded under flags.armor_element |
| G28 | [x] | mob_db int_, str, dex not loaded into Target. Mob MATK derived from int_. | mob_db stats.int | Fixed Session E: pipelines read stats.str/stats.int directly from get_monster_data(); no Target changes needed. |
| G29 | [x] | Target-side player cards not modelled for incoming. sub_race[mob.race], sub_ele[mob.element], near/long_def_rate from player cards. | battle.c cardfix target side | Fixed Session E: CardFix.calculate_incoming_physical() keys sub_ele/sub_race/sub_size against mob's actual element/race/size. |

---

## Incoming Physical (Player → Player)

| ID | Status | Description | Notes |
|---|---|---|---|
| G30 | [x] | PvP incoming physical pipeline absent. | Fixed Session F: CombatControlsSection Mob↔Player toggle; PlayerTargetBrowserDialog; _run_battle_pipeline wires pvp_stem to outgoing target and incoming result. |

---

## Incoming Magic (Mob or Player → Player)

| ID | Status | Description | Hercules ref | Notes |
|---|---|---|---|---|
| G31 | [x] | No mob MATK derivation. Mob MATK = mob.int_ + (int_/7)^2 to int_ + (int_/5)^2. | status.c same formula | Fixed Session E: IncomingMagicPipeline computes from mob_data stats.int directly. |
| G32 | [x] | No incoming magic pipeline. Player as target of magic. | — | Fixed Session E: IncomingMagicPipeline; optional skill parameter for mob skill ratios; wired in main_window. |
| G33 | [x] | Player MDEF not calculated. Hard MDEF from equip, soft MDEF from INT. | status.c calc_mdef | Done in Session B: StatusData.mdef + mdef2; StatusCalculator computes both |

---

## UI / Data Infrastructure

| ID | Status | Description |
|---|---|---|
| G34 | [x] | 4.4 — Skill combo job filter. skill_tree.json scraper + DataLoader.get_skills_for_job + CombatControlsSection.update_job + "All" toggle. Rogue/Stalker include AllowPlagiarism skills. |
| G35 | [x] | 4.5 — Equipment Browser job filter. item_db.job now list[int] IDs; filter = job_id in item["job"]. "All Jobs" checkbox. |
| G36 | [x] | 4.6 — Monster Browser Race/Element/Size QComboBox dropdowns; AND filter with name search. |
| G37 | [x] | 4.7 — Passives job filter. Data-driven via get_skills_for_job + source_skill field. buff_type: self/passive/party. BS_HILTBINDING added. "Show All" checkbox. |
| G39 | [x] | F7 — Inline equipment dropdown. _NoWheelCombo subclass; job-filtered repopulate; dual-wield left hand; browser sync. Done Session L. |
| G40 | [x] | P1 — StepsBar expanded state persists across focus changes. set_expanded_state() + QTimer. Done Session L. |
| G45 | [x] | P3 — StepsBar step tooltip (name, formula, output range, hercules_ref). Done Session L. |
| G46 | [x] | F8 — "Active Items" section (temporary catch-all). New collapsible section for consumable item effects (foods, triggered item script bonuses, potions) not tracked by gear parsing or skill/buff sections. Documented as a temporary catch-all: effects will be migrated to proper dedicated sections as they are implemented. Provides per-stat bonus spinboxes with an optional source/note label. Feeds into G15 auto-computed bonus column. | Done Session K: active_items_section.py; active_items_bonuses dict on PlayerBuild; stacked in _apply_gear_bonuses. |
| G47 | [x] | F9 — "Manual Stat Adjustments" section. New collapsible section for explicit numeric bonus entry on any base or derived stat. Pure escape hatch — no source attribution required. Intended for edge cases not covered by any tracked section, not for known script bonuses (those belong in gear/buff/G46). Feeds into G15 auto-computed bonus column alongside gear, SC, and G46 values. | Done Session K: manual_adj_section.py; manual_adj_bonuses dict on PlayerBuild; stacked in _apply_gear_bonuses. |
| G42 | [x] | ASPD display shows integer (e.g. 185) — should show one decimal place (e.g. 185.3). | Fixed Session C: StatusData.aspd→float; /10 not //10; derived_section {:.1f} |
| G43 | [x] | Incoming pipeline attack type not skill-driven. Physical always assumes auto-attack; magic defaults to mob natural element, no ratio. Add Ranged checkbox to physical row; add element override + ratio spinbox to magic row in IncomingDamageSection. | Fixed Session F: Ranged checkbox, magic element combo, ratio spinbox added to IncomingDamageSection; IncomingMagicPipeline accepts ele_override/ratio_override; all wired in main_window. |
| G51 | [ ] | SC_NIBELUNGEN DEF bypass: in-game tests on a stock pre-renewal Hercules server confirm the buff completely bypasses DEF, while SC_DRUMBATTLE (same `status_calc_watk` code path) does not. All Hercules pre-renewal source code paths for both SCs appear identical after exhaustive static analysis. Hypothesis: the `wlv==4` check in `status_calc_watk` may be failing at runtime (adds 0), with the actual bonus applied via an unlocated secondary path. Hercules devs contacted for clarification. Current `base_damage.py` implementation follows the Hercules pre-renewal code (pre-defense). If confirmed as post-defense, move to `mastery_fix.py`. | status.c:4589 #ifndef RENEWAL; battle.c:879 #ifdef RENEWAL | Awaiting Hercules dev response. Do not move to mastery_fix.py until source-confirmed. |

---

## Planned (Post-Session J)

| ID | Status | Description | Session |
|---|---|---|---|
| G48 | [ ] | Target debuff system: `target_active_scs: dict[str,int]` on Target; new target-side status calculator; "Target State" UI section with debuff toggles + level spinboxes. | R |
| G49 | [~] | Buffs section UI: role-grouped collapsible panel. M0: skeleton + Self Buffs wired. M: Party Buffs sub-group wired. M2: Bard Songs + Dancer Dances + Ensembles sub-groups wired. N: 22 new Self Buff rows (all Session N SCs + stubs + sphere/coin spinners). O: Ground Effects sub-group wired (SC_VOLCANO/DELUGE/VIOLENTGALE). Remaining: Guild Buffs, Misc (future sessions). | M–future |
| G50 | [~] | Passive skills completion: stat/HIT/FLEE/ASPD/regen passives wired (Session P). Deferred: GS_CHAINACTION→G54 (done), AS_RIGHT/AS_LEFT→G52 (done), HT_STEELCROW→G53, AC_VULTURE/GS_SNAKEEYE range increase (range not tracked in StatusData). | P |
| G52 | [x] | Dual-wield pipeline: AS_RIGHT/AS_LEFT passives, LH forge fields+widgets, lh_normal/lh_crit on BattleResult, dual-wield branch in BattlePipeline (ATK_RATER/ATK_RATEL, battle.c:5923-5938), LH card browser EQP fix, monster perfect_dodge=0. Proc interaction: damage_div_fix doubles RH only (battle.c:5567); ATK_RATER applied to double_hit branches; double_avg includes lh_normal. ASPD dual-wield formula: (aspd_base[RH]+aspd_base[LH])*7/10 (status.c:3699-3701). | G52, G52-cont |
| G53 | [ ] | Falcon/Blitz Beat system: HT_STEELCROW affects Blitz Beat ATK formula (battle.c:4242). Requires modelling the falcon auto-attack proc probability and its own damage branch. Deferred from Session P. | future |
| G54 | [x] | Double-hit proc branches: TF_DOUBLE (Knife, 5×lv% chance) and GS_CHAINACTION (Revolver, 5×lv% chance). Both run full pipeline with proc_hit_count=2 (×2 at SkillRatio position, battle.c:5567). Crit×proc mutex enforced (eff_crit scaled by 1−p). DPS stat via AttackDefinition list on BattleResult + calculate_dps(); correct probability tree (crits auto-hit, proc-miss accounted for, katar combined). | G54 |
| G55 | [ ] | NJ_TOBIDOUGU weapon_type string "Shuriken" unverified against item_db. mastery_fix.py uses "Shuriken" (assumed from naming convention). Verify before Session Q Ninja skills — if wrong, the bonus silently never applies. | P |
| G56 | [x] | DPS: skill timing calculator. `calculate_skill_timing()` in `core/calculators/skill_timing.py`; wired into BattlePipeline. Period = max(cast+delay, amotion) for skills; adelay for auto. BF_MAGIC DPS computed. Speed (actions/s) shown in SummarySection. dps_valid gates DPS display. | Q0 |
| G59 | [x] | Cast/delay gear bonuses: `castrate`/`delayrate`/`skill_castrate` in GearBonuses; `bCastrate`/`bVarCastrate`/`bDelayrate` routed in aggregator; per-skill `bonus2 bCastrate` stored in `skill_castrate` dict. Applied in `calculate_skill_timing()`. | Q0 |
| G60 | [x] | SC_SUFFRAGIUM: val2 = 15×lv % cast reduction (status.c:8485; skill.c:17244). Party Buffs UI row (spin, lv 1–3). Wired into `calculate_skill_timing()` via `support_buffs["SC_SUFFRAGIUM"]`. | Q0 |

| G57 | [ ] | DPS: Markov chain steady-state for turn-sequence modelling. AttackDefinition has state_requirement/next_state seam; BattleResult.attacks carries the full distribution. Replace FormulaSelectionStrategy with MarkovSelectionStrategy (eigenvector of transition matrix) when combo/status-ailment turn-sequence systems are implemented. Prerequisite: G56 + combo/status session. | future |
| G58 | [ ] | Card GUI rework: current card slot UI (G13) is a minimal inline-button approach. Needs a proper rework — per-slot card detail, correct card browser filtering for all edge cases (LH weapon vs shield fixed in G52; other slot types may have similar issues). Low priority until core pipeline work is complete. | future |

| G61 | [x] | BF_WEAPON skill ratios Q1: 31 ratios in `_BF_WEAPON_RATIOS` + `_BF_WEAPON_HIT_COUNT_FN`. SM/KN/CR/MC/TF/AS/RG/AC/HT/MO/BA/DC/TK level-linear lambdas. KN_PIERCE uses hit_count override (tgt.size+1, battle.c:4719-4722); no-target fallback=3. `IMPLEMENTED_BF_WEAPON_SKILLS`=31. Deferred to Q3: AS_SPLASHER (+mastery), RG_BACKSTAP (bow split), BA_DISSONANCE/TF_THROWSTONE/HT_LANDMINE/BLASTMINE/CLAYMORETRAP (BF_MISC). | Q1 |
| G62 | [~] | BF_WEAPON skill ratios Q2: MO_FINGEROFFENSIVE (ratio+hit_count), MO_INVESTIGATE (ratio+pdef=2 DefenseFix), AM_ACIDTERROR (ratio+def1=0 DefenseFix) done. DefenseFix now handles NK_IGNORE_DEF separately from crit. Remaining: KN_CHARGEATK, MC_CARTREVOLUTION, MO_EXTREMITYFIST, TK_JUMPKICK (all need skill_params+UI). Deferred: CR_GRANDCROSS, AL_HEAL, PR_TURNUNDEAD. BF_MAGIC: all entries already done in prior sessions. | Q2/Q2-cont |
| G68 | [ ] | pdef=1 from def_ratio_atk_ele/race card bonuses (battle.c:5686/5694): sets `flag.pdef=1` via SD bonus; formula `damage*1*(def1+vit_def)/100`. Needs new `gear_bonuses.def_ratio_atk_ele/race` fields + item_script_parser support. Currently not parsed — any such card silently ignores this effect. | Q3+ |
| G63 | [ ] | BF_WEAPON/BF_MAGIC skill ratios Q3: Ninja hybrid (NJ_* BF_WEAPON + BF_MAGIC) and Gunslinger (all GS_* BF_WEAPON + GS_MAGICALBULLET BF_MAGIC). | Q3 |
| G64 | [ ] | Job Stat Bonuses: Every Job gains bonus stats depending on Job Level, requires Job Bonus table. |
| G65 | [ ] | Stat Bonuses etc. missing from Base Stats section's Bonus Stat display |
| G66 | [ ] | Blacksmith Weaponry Mastery missing ATK Bonus; Overthrust goes to 10 instead of 5, should be party buff; Adrenaline Rush update: self->Self Buffs, party->Party Buffs; Skin Tempering does nothing right now, add Def increas, implement resistance. Cart Revolution is missing from Skill List, Mammonite does nothing; Loud->Loud Exclamation.|
| G67 | [ ] | Equipment section: Widen card fields, rework card selection in general->Make List useful, allow editing multiple through List dialogue? |

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
| G1 | SC_IMPOSITIO flat weapon ATK (base_damage.py) | A |
| G2 | Attacker-side CardFix (card_fix.py) | A |
| G3 | Arrow ATK for bow builds (base_damage.py) | A |
| G5 | ignore_def wired into DefenseFix | A |
| G6 | Target model fields for PvP (target.py) | A |
| G8 | Target-side CardFix in card_fix.py (activates Session D) | A |
| G11 | bLongAtkRate applied in CardFix for ranged | A |
| G18 | MATK in StatusCalculator + StatusData + derived_section | B |
| G19 | MagicPipeline class (full BF_MAGIC outgoing) | B |
| G20 | DefenseFix.calculate_magic (mdef+mdef2, per-hit) | B |
| G21 | MATK+MDEF rows in derived_section | B |
| G22 | Magic skill ratios (_BF_MAGIC_RATIOS, cosmetic vs actual hits) | B |
| G23 | CardFix.calculate_magic (target-side only) | B |
| G24 | ignore_mdef_rate in GearBonuses + aggregator + DefenseFix | B |
| G25 | mdef/mdef2 in StatusData; equip_mdef in PlayerBuild; bMdef bIgnoreMdefRate routes | B |
| G4 | ASC_KATAR mastery % (mastery_fix.py) | C |
| G10 | bAtkRate moved to pre-SkillRatio position | C |
| G42 | ASPD decimal display | C |
| G27 | armor_element field in PlayerBuild | D |
| G7 | VIT DEF PC branch activated via player_build_to_target() | E |
| G26 | IncomingPhysicalPipeline | E |
| G28 | Mob stats.str/int read in incoming pipelines | E |
| G29 | CardFix.calculate_incoming_physical | E |
| G31 | Mob MATK derivation in IncomingMagicPipeline | E |
| G32 | IncomingMagicPipeline | E |
| G33 | Player MDEF in StatusData (done Session B) | B |
| G43 | Ranged checkbox + magic element override + ratio spinbox in IncomingDamageSection | F |
| G30 | PvP target selector: Mob↔Player toggle in CombatControls; PlayerTargetBrowserDialog; main_window pvp wiring | F |
| G12 | Armor refine DEF: import_refine_db.py scraper + refine_armor.json + GearBonusAggregator aggregate rounding | G |
| G13 | Card slot UI: dynamic sub-slot buttons in equipment_section, IT_CARD browser filter, EQP_ACC fix | G |
| G34 | Skill combo job filter: skill_tree.json scraper, DataLoader.get_skills_for_job, CombatControlsSection.update_job | J1 |
| G35 | Equipment Browser job filter: item_db.job list[int] IDs, job_id filter, "All Jobs" checkbox | J2 |
| G36 | Monster Browser Race/Element/Size filter dropdowns with AND logic | J2 |
| G37 | Passives job filter: data-driven via get_skills_for_job + source_skill, buff_type, BS_HILTBINDING, "Show All" checkbox | J2 |