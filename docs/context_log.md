# PS_Calc — Context Usage Log
# How to use:
#   I fill in: session ID, date, model, work items, files (with line counts), estimated tokens.
#   You fill in: "ctx_used" (% shown in Claude Code UI at session end), and any notes.
#   After ~3 sessions the per-item costs become useful calibration data for future planning.
#
# Line count → token estimate: code ~7 tok/line, JSON/config ~5 tok/line, prose ~4 tok/line
# Fixed overhead per session (system prompt + CLAUDE.md + MEMORY.md): ~6k tokens (unverified)

---

## Session 5  2026-01-xx  claude-sonnet-4-6
ctx_used: ___%   (fill in after session)

Work items completed:
- F2 armor base DEF from item_db
- F5 2H weapon locks left hand
- F6 Assassin dual-wield restriction
- derived_section live ASPD/HP/SP labels

Files read:
| file | lines | est_tok |
|---|---|---|
| (not recorded) | — | — |

Files edited:
| file | lines | est_tok |
|---|---|---|
| (not recorded) | — | — |

Files created: none recorded

Total est_tokens: unknown (baseline entry — no data)
Notes: retroactive entry, no size data recorded. Use Session A onward for calibration.

---

## Session A  2026-03-06  claude-sonnet-4-6
ctx_used: 93% Session 1 (planning), 63% Session 2 (implementation)

Work items completed:
- W1: Extend Target model — 9 new fields (sub_race/ele/size, near/long/magic_def_rate, mdef_, int_, armor_element, flee)
- W2: Extend GearBonuses + aggregator + parser — near/long_atk_def_rate, magic_def_rate, atk_rate
- W3: loader.get_monster() — mdef_ and int_ populated
- W4: Fix G1 SC_IMPOSITIO — base_damage.py, after atkmax before atkmin
- W5: Fix G3 Arrow ATK — base_damage.py Bow path
- W6: Implement CardFix — new card_fix.py (attacker + target sides), wired after AttrFix
- W7: G7 VIT DEF PC — formula confirmed correct; no code change
- W8: Fix G5 ignore_def — defense_fix.py reads GearBonuses.ignore_def_rate
- W9: Wire GearBonuses + CardFix in battle_pipeline.py

Files read:
| file | lines | est_tok |
|---|---|---|
| core/models/target.py | 17 | 119 |
| core/models/gear_bonuses.py | 57 | 399 |
| core/gear_bonus_aggregator.py | 117 | 819 |
| core/item_script_parser.py | 232 | 1,624 |
| core/data_loader.py | 277 | 1,939 |
| core/calculators/modifiers/base_damage.py | 177 | 1,239 |
| core/calculators/modifiers/defense_fix.py | 114 | 798 |
| core/calculators/battle_pipeline.py | 152 | 1,064 |
| docs/current_state.md | 85 | 340 |
| plans/abundant-leaping-umbrella.md | 278 | 1,112 |
| **subtotal reads** | **1,506** | **~9,453** |

Files edited:
| file | lines_added | est_tok |
|---|---|---|
| core/models/target.py | +11 | ~77 |
| core/models/gear_bonuses.py | +6 | ~42 |
| core/gear_bonus_aggregator.py | +6 | ~42 |
| core/item_script_parser.py | +5 | ~35 |
| core/data_loader.py | +2 | ~14 |
| core/calculators/modifiers/base_damage.py | +33 | ~231 |
| core/calculators/modifiers/defense_fix.py | +24 | ~168 |
| core/calculators/battle_pipeline.py | +7 | ~49 |
| docs/gaps.md | +16 | ~64 |
| docs/current_state.md | rewrite | ~300 |
| docs/context_log.md | +32 | ~128 |

Files created:
| file | lines | est_tok |
|---|---|---|
| core/calculators/modifiers/card_fix.py | 101 | ~707 |

Total est_tokens: 9,453 reads + ~1,150 edits + 707 create + 6,000 fixed + ~12,000 conv ≈ 29,000 (~15% of 200k)
Notes: Split across two conversation segments (planning context + implementation). No unplanned debug reads. G10 (bAtkRate) partially resolved — field wired in CardFix but position should be before SkillRatio per Hercules; flagged for Session B.

---

## Session A (doc cleanup)  2026-03-06  claude-sonnet-4-6
ctx_used: 56% (post-compaction continuation; compaction occurred mid-session when previous
conversation hit context limit during data_models.md editing — the Target section had been
updated but GearBonuses/mob_db/PlayerBuild sections were still at their old state at handoff)

Work items completed:
- completed_work.md: fix stale pipeline order in header; append Session 5 and Session A sections
- data_models.md: GearBonuses [NEW]→[EXISTS] for 4 Session A fields; mob_db table updated with Status column; PlayerBuild MODELS.md ref removed
- gui_plan.md: F6 job IDs corrected (10/22 → 12/24); phases_done ref updated
- CLAUDE.md: handoff protocol clarified (current_state.md is cross-instance only; context_log made optional/user-triggered with post-push reminder; data_models.md item 4 made more specific)

Files read:
| file | lines | est_tok |
|---|---|---|
| docs/completed_work.md | 437 | ~3,059 |
| docs/current_state.md | 52 | ~364 |
| docs/session_roadmap.md | 265 | ~1,855 |
| docs/gui_plan.md (partial) | 50 | ~350 |
| CLAUDE.md (partial) | 35 | ~245 |
| **subtotal reads** | **839** | **~5,873** |

Files edited:
| file | lines_added | est_tok |
|---|---|---|
| docs/completed_work.md | +80 | ~560 |
| docs/data_models.md | +15 net | ~105 |
| docs/gui_plan.md | +2 | ~14 |
| CLAUDE.md | +20 net | ~140 |

Files created: none

Total est_tokens: ~5,873 reads + ~819 edits + ~6,000 fixed + ~8,000 conv ≈ 21,000 (~11% of 200k)
Notes: Pure doc cleanup session. No code changes. data_models.md was pre-loaded via system-reminder
(not counted as a read). All deferred Session A doc items resolved and committed in two commits
(c540e8d + 9b0d08f).

---

## Session B  2026-03-06  claude-sonnet-4-6
ctx_used: ~100% segment 1 (compacted mid doc-maintenance), ~30% segment 2 (doc finish + commit)

Work items completed:
- B1: StatusData MATK — matk_min/matk_max added to status.py + status_calculator.py
- B2: StatusData MDEF — mdef (hard, from equip_mdef) + mdef2 (soft = int_+vit//2)
- B3: GearBonuses mdef_ + ignore_mdef_rate; PlayerBuild equip_mdef; main_window wiring
- B4: derived_section — MATK (range) and MDEF (hard+soft) display rows
- B5: skill_ratio.py calculate_magic() — 15 pre-renewal spells, raw hit_count with sign encoding
- B6: defense_fix.py calculate_magic() — MDEF% + mdef2 per-hit (battle.c:1585)
- B7: card_fix.py calculate_magic() — target-side PvP magic resist only (attacker magic is #ifdef RENEWAL)
- B8: magic_pipeline.py — new MagicPipeline (battle_calc_magic_attack #else not RENEWAL)
      Correct per-hit order: SkillRatio → DefenseFix → AttrFix → HitCount×N
      Positive hit_count = actual multiply; negative = cosmetic step only (damage_div_fix macro)
- B9: battle_pipeline.py — route attack_type==Magic to MagicPipeline; BattleResult.magic field
- Doc maintenance: gaps.md G18-G25 done; completed_work.md Session B; data_models.md; CLAUDE.md

Files read (estimated — not recorded precisely):
| file | lines | est_tok |
|---|---|---|
| docs/session_roadmap.md (partial) | ~80 | ~560 |
| core/models/status.py | ~40 | ~280 |
| core/calculators/status_calculator.py | ~110 | ~770 |
| core/models/gear_bonuses.py | 65 | 455 |
| core/gear_bonus_aggregator.py | ~130 | ~910 |
| core/models/build.py | ~70 | ~490 |
| gui/main_window.py (partial) | ~40 | ~280 |
| gui/sections/derived_section.py | ~80 | ~560 |
| core/calculators/modifiers/skill_ratio.py | ~120 | ~840 |
| core/calculators/modifiers/defense_fix.py | 139 | ~973 |
| core/calculators/modifiers/card_fix.py | ~101 | ~707 |
| core/calculators/battle_pipeline.py | 152 | 1,064 |
| core/models/damage.py | ~60 | ~420 |
| core/models/target.py | 28 | 196 |
| docs/data_models.md | 207 | ~828 |
| docs/context_log.md | 156 | ~624 |
| Hercules greps (battle.c, status.c) | ~120 | ~840 |
| **subtotal reads** | **~1,698** | **~10,797** |

Files edited:
| file | lines_added | est_tok |
|---|---|---|
| core/models/status.py | +7 | ~49 |
| core/calculators/status_calculator.py | +11 | ~77 |
| core/models/gear_bonuses.py | +4 | ~28 |
| core/gear_bonus_aggregator.py | +3 | ~21 |
| core/models/build.py | +1 | ~7 |
| gui/main_window.py | +1 | ~7 |
| gui/sections/derived_section.py | +4 | ~28 |
| core/calculators/modifiers/skill_ratio.py | +72 | ~504 |
| core/calculators/modifiers/defense_fix.py | +45 | ~315 |
| core/calculators/modifiers/card_fix.py | +44 | ~308 |
| core/calculators/battle_pipeline.py | +23 | ~161 |
| core/models/damage.py | +1 | ~7 |
| docs/gaps.md | +26 | ~104 |
| docs/completed_work.md | +52 | ~208 |
| docs/data_models.md | +37 | ~148 |
| CLAUDE.md | +19 | ~133 |

Files created:
| file | lines | est_tok |
|---|---|---|
| core/calculators/magic_pipeline.py | 161 | 1,127 |

Total est_tokens: ~10,797 reads + ~2,105 edits + 1,127 create + 6,000 fixed + ~15,000 conv ≈ 35,000 (~18% of 200k per segment)
Notes: Two context segments. Compaction hit during doc maintenance of segment 1 — resumed cleanly.
Cosmetic vs actual hit count distinction required mid-session investigation + re-implementation of
skill_ratio.calculate_magic (initially used abs(), corrected to return raw signed hit_count).
Per-hit defense order also corrected mid-session (initially multiplied before defense, fixed to match
Hercules: ratio→defense→attr_fix per-hit, then hit_count×N after).

---

## Session C  2026-03-07  claude-sonnet-4-6
ctx_used: ~100% (hit limit during commit/push phase; docs/aspd.md created but gaps.md/completed_work.md update + commit deferred to next segment)

Work items completed:
- C1: G4 ASC_KATAR % mastery — mastery_fix.py + passive_section job-filtered row
- C2: G9 ASPD SC buffs — status_calc_aspd_rate 1000-scale; SC_ASSNCROS deferred (Bard AGI dependency)
- C3: G10 bAtkRate — moved to pre-SkillRatio position in battle_pipeline; removed from CardFix
- Doc maintenance: gaps.md G4/G9/G10; completed_work.md Session C; docs/aspd.md created; G42 added

Files read:
| file | lines | est_tok |
|---|---|---|
| docs/session_roadmap.md (Session C section) | ~35 | ~245 |
| core/calculators/modifiers/mastery_fix.py | ~30 | ~210 |
| gui/sections/passive_section.py | ~330 | ~2,310 |
| core/calculators/status_calculator.py | 131 | ~917 |
| gui/main_window.py (partial ~10 lines) | 10 | ~70 |
| core/calculators/battle_pipeline.py | ~165 | ~1,155 |
| core/calculators/modifiers/card_fix.py | ~145 | ~1,015 |
| core/calculators/modifiers/base_damage.py | 209 | ~1,463 |
| core/models/gear_bonuses.py | 65 | ~455 |
| docs/gaps.md | 120 | ~480 |
| docs/completed_work.md (tail ~30 lines) | 30 | ~120 |
| docs/context_log.md | 229 | ~916 |
| docs/aspd.md (created this session, re-read) | 108 | ~432 |
| Hercules greps (status.c ASPD, battle.c ASC_KATAR) | ~60 | ~420 |
| **subtotal reads** | **~1,667** | **~10,208** |

Files edited:
| file | lines_added | est_tok |
|---|---|---|
| core/calculators/modifiers/mastery_fix.py | +19 | ~133 |
| gui/sections/passive_section.py | +44 | ~308 |
| core/calculators/status_calculator.py | +29 | ~203 |
| gui/main_window.py | +1 | ~7 |
| core/calculators/battle_pipeline.py | +15 | ~105 |
| core/calculators/modifiers/card_fix.py | -2 | ~14 |
| docs/gaps.md | +7 net | ~28 |
| docs/completed_work.md | +31 | ~124 |
| docs/context_log.md | +this entry | ~200 |

Files created:
| file | lines | est_tok |
|---|---|---|
| docs/aspd.md | 120 | ~480 |

Total est_tokens: ~10,208 reads + ~1,122 edits + 480 create + 6,000 fixed + ~18,000 conv ≈ 36,000 (~18% of 200k)
Notes: Context hit ~100% before docs update + commit could complete. Resumed cleanly in next segment.
ASPD formula investigation required mid-session — initial 7% implementation was wrong; user testing
confirmed 30% (status_calc_aspd_rate val2=300). SC_SPEARQUICKEN changed to has_level=True after
discovering level-dependent val2. bAtkRate position fix was a clean correction with no investigation needed.

---

## Session D  2026-03-07  claude-sonnet-4-6
ctx_used: 73%

Work items completed:
- D0: armor_element: int = 0 added to PlayerBuild; saved/loaded under flags.armor_element in BuildManager (G27)
- D-inv: Extensive Hercules investigation of mob ATK/MATK lifecycle (battle.c, status.c, mob.c)
  Key findings: (1) mob batk = str+(str//10)^2 only — no dex/luk (PC-only); (2) all mob ATK values
  frozen at db load time via status_calc_misc; (3) most mobs str=0 or str=1 (batk negligible);
  (4) scaffold mob Porcellio has str=0 → batk=0 → explains "no stats connection" observation.
- D-clean: Scaffold build files deleted (knight_bash, spear_peco, agi_bs); MEMORY.md section removed.
- D-arch: Architectural decision — mob ATK is two-part (spawn-time frozen + per-attack roll);
  implementation reads atk_min/atk_max from mob_db.json and adds batk from stats.str separately.

Files read (investigation-heavy session):
| file | lines | est_tok |
|---|---|---|
| core/models/build.py | 72 | ~504 |
| core/models/target.py | 28 | ~196 |
| core/build_manager.py | 202 | ~1,414 |
| core/data_loader.py | 280 | ~1,960 |
| core/calculators/battle_pipeline.py | 194 | ~1,358 |
| core/calculators/magic_pipeline.py | 161 | ~1,127 |
| core/calculators/modifiers/defense_fix.py | 184 | ~1,288 |
| core/calculators/modifiers/card_fix.py | 155 | ~1,085 |
| gui/sections/incoming_damage.py | 65 | ~455 |
| tools/import_mob_db.py (partial) | ~80 | ~560 |
| Hercules/src/map/battle.c (greps + sed) | ~200 | ~1,400 |
| Hercules/src/map/status.c (greps + sed) | ~150 | ~1,050 |
| Hercules/src/map/mob.c (greps + sed) | ~180 | ~1,260 |
| Hercules/db/pre-re/mob_db.conf (Poring, Porcellio) | ~60 | ~420 |
| docs/context_log.md | 283 | ~1,132 |
| docs/current_state.md | 52 | ~208 |
| memory/MEMORY.md | 133 | ~532 |
| **subtotal reads** | **~2,479** | **~15,949** |

Files edited:
| file | lines_added | est_tok |
|---|---|---|
| core/models/build.py | +3 | ~21 |
| core/build_manager.py | +2 | ~14 |
| docs/current_state.md | rewrite | ~600 |
| docs/context_log.md | +this entry | ~300 |
| docs/gaps.md | +3 | ~12 |
| memory/MEMORY.md | -4 (section removed) | ~16 |

Files created: none

Total est_tokens: ~15,949 reads + ~963 edits + 6,000 fixed + ~22,000 conv ≈ 45,000 (~23% of 200k)
Notes: Investigation-heavy session. All context spent on Hercules source tracing for mob ATK/MATK.
Only G27 (armor_element) implemented; all pipeline work deferred to Session E.
Two-part mob ATK architecture decision is the primary deliverable beyond the armor_element field.

---

## Template for future sessions

## Session X  YYYY-MM-DD  claude-sonnet-4-6
ctx_used: ___%

Work items completed:
- ...

Files read:
| file | lines | est_tok |
|---|---|---|

Files edited:
| file | lines | est_tok |
|---|---|---|

Files created:
| file | lines | est_tok |
|---|---|---|

Extra reads (debug/investigation not in plan):
| file | lines | est_tok |
|---|---|---|

Total est_tokens: (sum) + ~6k fixed overhead
Notes:
