# PS_Calc — Current State
# Updated by Claude at session end or on "handoff" request.
# Any Claude instance (Code or web) should read this before starting work.
# Web Claude: also paste relevant sections of CLAUDE.md (rules, file structure, pipeline order).

---

## Last Completed Session
**Session A planning** — no implementation committed. Previous implementation: Session 5 (commit e2e22bd).

Key discoveries from planning session:
- G7 was based on a misread of battle.c. Lines 1495/1498 are AL_DP (Angelus) and RA_RANGERMAIN
  skill bonuses, NOT the base PC VIT DEF formula.
- PC VIT DEF formula in defense_fix.py is already correct per C source (battle.c:1487-1488).
  No formula change needed. Branch is dead code only because target.is_pc is never True yet.
- Hercules comment on line 1486 disagrees with the implementation. Track as G41 (low priority).
  Follow C code, not the comment.
- GearBonuses boss/nonboss keys confirmed: "RC_Boss", "RC_NonBoss" (raw RC_ format).
- CardFix will compute GearBonuses internally from build.equipped (cached, O(1)).

## Next Session
**Session A implementation** — Model Foundation + Physical Pipeline Corrections
Gap IDs: G1, G2, G3, G5, G6 (model only), G7 (dead-code only, no formula change), G8, G11, G28

Work items in order (plan file: C:\Users\Felix\.claude\plans\abundant-leaping-umbrella.md):

1. Extend Target model — add sub_race, sub_ele, sub_size (Dict[str,int] fields), plus
   near/long_attack_def_rate, magic_def_rate, mdef_, int_, armor_element, flee (int, all 0).
   Need to import field + Dict. No behaviour change — all zero for mob targets.

2. Extend GearBonuses — add near_atk_def_rate, long_atk_def_rate, magic_def_rate, atk_rate.
   Add routes in gear_bonus_aggregator.py + templates in item_script_parser.py:
   bNearAtkDef, bLongAtkDef, bMagicDefRate, bAtkRate.

3. Update loader.get_monster() — add mdef_=entry.get("mdef",0) and int_=stats.get("int",0).

4. Fix G1 SC_IMPOSITIO — in base_damage.py after atkmax=weapon.atk, before atkmin calc:
   lv = build.active_status_levels.get("SC_IMPOSITIO", 0); if lv: atkmax += lv * 5
   Add result.add_step. Source: status.c #ifndef RENEWAL ~4562.

5. Fix G3 Arrow ATK — in base_damage.py after SC_IMPOSITIO, before atkmin:
   if weapon.weapon_type == "Bow" and build.equipped.get("ammo"):
       ammo = loader.get_item(ammo_id); atkmax += ammo["atk"]; add_step.

6. Implement CardFix — new core/calculators/modifiers/card_fix.py.
   Attacker side: add_race[race_rc]+add_race[boss_rc]+add_ele+add_size+long_atk_rate(if ranged).
   Target side (is_pc only): sub_ele[weapon_ele]+sub_size[Size_Medium]+sub_race[RC_DemiHuman]
     + near/long_attack_def_rate.
   Key: RC_ format keys everywhere. Compute gear_bonuses=GearBonusAggregator.compute(build.equipped)
   once at top of _run_branch() in battle_pipeline.py. Also compute is_ranged early (reuse for both
   CardFix and FinalRateBonus). Resolves G2 + G8 + G11.

7. G7 VIT DEF PC branch — NO FORMULA CHANGE. Formula in defense_fix.py is already correct:
   def2*(def2-15)//150; def2//2 + rnd()%vit_def. Branch dead until Session D wires is_pc=True.
   Only confirm correct via read — do not edit defense_fix.py for G7.

8. Fix G5 ignore_def — add gear_bonuses param to DefenseFix.calculate(). Before def1 % reduction:
   race_rc = _RACE_TO_RC.get(target.race,""); boss_rc = "RC_Boss" if target.is_boss else "RC_NonBoss"
   ignore_pct = ignore_def_rate.get(race_rc,0) + ignore_def_rate.get(boss_rc,0)
   if ignore_pct>=100 or build.ignore_hard_def: def1=0  elif >0: def1=def1*(100-ignore_pct)//100

## In-Progress Work
None. Session A implementation not yet started.

## Active Code Errors (produce wrong output right now)
- **SC_IMPOSITIO missing**: adds level×5 flat to weapon ATK but not implemented. (Fix: G1)
- **CardFix entirely absent**: race/ele/size offensive cards have zero pipeline effect. (Fix: G2)
- **Arrow ATK missing**: bow builds undercount by full arrow ATK value. (Fix: G3)
- **ASC_KATAR absent**: Assassin Cross katar builds missing up to +20% damage. (Fix: G4, Session C)
- **ignore_def not wired**: DEF-bypassing cards (e.g. Thanatos) have no effect. (Fix: G5)
- **VIT DEF PC branch dead**: target.is_pc=True is never set (no PvP yet). Formula is correct. (G7)

## Key Architectural Reminders
- Pipeline order: BaseDamage → SkillRatio → CritAtkRate(crit) → DefenseFix(skip crit) →
  ActiveStatusBonus → RefineFix → MasteryFix → AttrFix → [CardFix — G2] → FinalRateBonus
- CardFix position: after AttrFix, before FinalRateBonus
- GearBonuses dict keys (add_race, ignore_def_rate etc.) use RC_/Size_/Ele_* raw script format
- GearBonuses computed inside _run_branch() from build.equipped — not threaded from main_window
- DataLoader singleton: `from core.data_loader import loader`

## Scaffold Builds Available
- saves/knight_bash.json — Flamberge +7 fire, vs Porcellio (Brute, for CardFix testing)
- saves/spear_peco.json — Lance +7 fire, vs Sandman
- saves/agi_bs.json — non-refineable 2H axe (needs item ID fix before use)
