# PS_Calc — Current State
# Updated by Claude at session end or on "handoff" request.
# Any Claude instance (Code or web) should read this before starting work.
# Web Claude: also paste relevant sections of CLAUDE.md (rules, file structure, pipeline order).

---

## Last Completed Session
**Session A** — Model Foundation + Physical Pipeline Corrections. All work items complete, uncommitted.

Files changed:
- `core/models/target.py` — 9 new fields: sub_race/sub_ele/sub_size (Dict), near/long/magic_def_rate, mdef_, int_, armor_element, flee
- `core/models/gear_bonuses.py` — 4 new fields: near_atk_def_rate, long_atk_def_rate, magic_def_rate, atk_rate
- `core/gear_bonus_aggregator.py` — 4 new _BONUS1_ROUTES: bNearAtkDef, bLongAtkDef, bMagicDefRate, bAtkRate
- `core/item_script_parser.py` — 4 new _BONUS1_TEMPLATES for same keys
- `core/data_loader.py` — get_monster() now populates mdef_ and int_
- `core/calculators/modifiers/base_damage.py` — SC_IMPOSITIO (G1) + Arrow ATK (G3) inserted after atkmax, before atkmin
- `core/calculators/modifiers/card_fix.py` — NEW: CardFix (G2+G8+G11): race/ele/size/long_atk attacker bonuses + PvP target resist
- `core/calculators/modifiers/defense_fix.py` — G5 ignore_def wired; added gear_bonuses param + _RACE_TO_RC dict
- `core/calculators/battle_pipeline.py` — imports GearBonusAggregator + CardFix; gear_bonuses + is_ranged computed at top of _run_branch(); CardFix inserted after AttrFix; DefenseFix receives gear_bonuses

Suggested commit message: `Session A: CardFix + Arrow ATK + SC_IMPOSITIO + ignore_def + model fields`

## Next Session
**Session B** — see docs/session_roadmap.md for scope. Before starting, update docs/gaps.md:
- G1 SC_IMPOSITIO → [x] done
- G2 CardFix attacker side → [x] done
- G3 Arrow ATK → [x] done
- G5 ignore_def → [x] done
- G6 model fields → [x] partial (Target + GearBonuses extended; full G6 may have more)
- G8 CardFix target side → [x] done (wired, activates when is_pc=True in Session D)
- G11 bLongAtkRate → [x] done (CardFix applies it for ranged)

## In-Progress Work
None. Session A fully implemented. Ready to commit.

## Active Code Errors (produce wrong output right now)
- **ASC_KATAR absent**: Assassin Cross katar builds missing up to +20% damage. (Fix: G4, Session C)
- **VIT DEF PC branch dead**: target.is_pc=True is never set (no PvP yet). Formula is correct. (G7, Session D)

## Key Architectural Reminders
- Pipeline order: BaseDamage → SkillRatio → CritAtkRate(crit) → DefenseFix(skip crit) →
  ActiveStatusBonus → RefineFix → MasteryFix → AttrFix → CardFix → FinalRateBonus
- CardFix: after AttrFix, before FinalRateBonus — DONE
- GearBonuses computed once per branch at top of _run_branch() — O(1) cached
- DataLoader singleton: `from core.data_loader import loader`

## Scaffold Builds Available
- saves/knight_bash.json — Flamberge +7 fire, vs Porcellio (Brute, for CardFix testing)
- saves/spear_peco.json — Lance +7 fire, vs Sandman
- saves/agi_bs.json — non-refineable 2H axe (needs item ID fix before use)
