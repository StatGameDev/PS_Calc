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
