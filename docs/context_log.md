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

## Session A  2026-xx-xx  claude-sonnet-4-6
ctx_used: ___%   (fill in after session)

Work items planned (session_roadmap.md):
1. Extend Target model — new fields with zero defaults
2. Extend GearBonuses — near/long_atk_def_rate, magic_def_rate, atk_rate + aggregator/parser routes
3. Update loader.get_monster() — mdef_, int_ population
4. Fix G1 SC_IMPOSITIO — active_status_bonus.json + BaseDamage flat watk
5. Fix G3 Arrow ATK — BaseDamage bow path + ammo atk fetch
6. Implement CardFix — new card_fix.py (attacker + target sides), insert into pipeline
7. Fix G7 VIT DEF PC branch — defense_fix.py branch on is_pc
8. Fix G5 ignore_def — defense_fix.py reads GearBonuses.ignore_def_rate

Files to read (planned):
| file | lines | est_tok |
|---|---|---|
| core/models/target.py | 16 | 112 |
| core/models/gear_bonuses.py | 56 | 392 |
| core/gear_bonus_aggregator.py | 117 | 819 |
| core/item_script_parser.py | 232 | 1,624 |
| core/data_loader.py | 277 | 1,939 |
| core/calculators/modifiers/base_damage.py | 177 | 1,239 |
| core/calculators/modifiers/defense_fix.py | 114 | 798 |
| core/calculators/battle_pipeline.py | 151 | 1,057 |
| core/data/pre-re/tables/active_status_bonus.json | 12 | 60 |
| **subtotal reads** | **1,152** | **~8,040** |

Files to edit: same files (×1.5 of read cost) → ~12,060
Files to create: core/calculators/modifiers/card_fix.py (~120 lines est) → ~840

Total est_tokens: 8,040 reads + 12,060 edits + 840 create + 6,000 fixed + 8,000 conv ≈ 35,000 (~17% of 200k)
Notes: fill in ctx_used at session end. Extra reads row for any unplanned debug reads.

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
