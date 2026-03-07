# PS_Calc — Current State
# Updated by Claude on "handoff" request.
# Any Claude instance (Code or web) taking over after handoff should read this before starting work.
# Web Claude: also paste relevant sections of CLAUDE.md (rules, file structure, pipeline order).

---

## Last Completed Session
**Post-Session E — Documentation pass (no code changes).**

Files changed:
- `docs/aspd.md` — all unknowns from "What to Verify Next" resolved (see below)
- `docs/BARD_DANCER_SONGS.md` — new file; full Bard/Dancer song reference
- `CLAUDE.md` — BARD_DANCER_SONGS.md added to docs listing
- `memory/MEMORY.md` — BARD_DANCER_SONGS.md added to reference docs

### aspd.md — Resolved Unknowns

1. **`status_calc_aspd` guard confirmed**: entire function body is `#ifdef RENEWAL_ASPD`.
   Pre-renewal always returns 0. The `bonus = 7` for quicken SCs is Renewal ASPD only.
   The doc had the wrong function name ("status_base_amotion_pc") — corrected to `status_calc_aspd`.

2. **Pre-renewal PC ASPD call chain confirmed** (status_calc_sc_ ~line 3335):
   - `base_amotion_pc` → raw amotion from aspd_base table minus stat reduction plus aspd_add
   - `calc_aspd_rate(bl, sc, bst->aspd_rate)` called `#ifndef RENEWAL_ASPD`
   - `amotion = amotion * aspd_rate / 1000`
   - `status_calc_aspd` (bonus=7 function) is NOT called in this path. Current implementation is correct.

3. **SC_ASSNCROS val2 formula confirmed** (skill.c:13296 + 14277):
   `val2 = (BA_MUSICALLESSON_lv/2 + 10 + song_lv + bard_agi/10) * 10`
   Not applied to bow/revolver/rifle/gatling/shotgun/grenade.

### BARD_DANCER_SONGS.md — Contents

- Three skill categories: Solo Songs (BA_*, UF_SONG), Solo Dances (DC_*, UF_DANCE), Ensembles (BD_*, UF_ENSEMBLE)
- Note: skills.json uses `skill_info: "Song"` for both Bard songs AND Dancer dances; UF_SONG vs UF_DANCE only at unit level
- UF_DUALMODE, UF_NOMOB meanings documented
- Soul Link: no calculation modelling needed; document as GUI note only
- Ensemble scope: all BD_* in scope, deeper research deferred until party buffs implemented
- Party buff scope table: all solo song IDs with caster stat(s) and passive level used (user to append more IDs)
- Confirmed formulas: SC_ASSNCROS, SC_POEMBRAGI, SC_APPLEIDUN, SC_DONTFORGETME, SC_FORTUNE, SC_SERVICEFORYU
- Still unconfirmed (needs grep): BA_WHISTLE, DC_HUMMING exact formulas

## Key Architecture Notes (for next instance)

**player_build_to_target()**
- `BuildManager.player_build_to_target(build, status, gear_bonuses) -> Target`
- Sets is_pc=True, size=Medium, race=DemiHuman, element_level=1
- sub_size={} — GearBonuses has add_size (offensive) not sub_size (defensive); defer until cards adding size resistance are implemented
- Activates G7: PC VIT DEF formula in DefenseFix now live for all incoming physical hits

**IncomingPhysicalPipeline**
- Signature: `calculate(mob_id, player_target, gear_bonuses, build, is_ranged=False, mob_atk_bonus_rate=0)`
- Mob ATK computed internally from mob_db. `mob_atk_bonus_rate` is the buff/debuff hook (mirrors Hercules SC modifying rhw.atk/atk2).
- DefenseFix called with build=None, GearBonuses() — mob has no ignore_def cards
- CardFix.calculate_incoming_physical keys player sub_ele/sub_race/sub_size against mob's actual race/element/size

**IncomingMagicPipeline**
- Signature: `calculate(mob_id, player_target, gear_bonuses, build, skill=None, mob_matk_bonus_rate=0)`
- Optional skill parameter: applies SkillRatio + skill element from skills.json; falls back to mob natural element
- CardFix.calculate_incoming_magic uses mob's actual race (not hardcoded RC_DemiHuman like the outgoing calculate_magic)
- DefenseFix.calculate_magic called with empty GearBonuses — mob has no ignore_mdef cards

**IncomingDamageSection public API**
- `refresh(physical: Optional[DamageResult], magic: Optional[DamageResult])`

## Open Gaps Remaining (after Session E)

- **G43 [ ]**: Incoming attack type not skill-driven. Physical always assumes auto-attack; magic defaults to mob natural element. No mob skill picker in GUI. Design UI surface before implementing.
- **G30 [ ]**: PvP incoming physical absent. Architecturally: run full BF_WEAPON outgoing pipeline with second PlayerBuild as attacker, player_build_to_target() result as defender.
- **G12 [ ]**: F3 — Armor refine DEF. Needs import_refine_db.py scraper + pipeline step.
- **G13 [ ]**: F1 — Card slot UI absent.
- **G9 [~]**: SC_ASSNCROS ASPD buff deferred (needs party buff AGI input). Formula confirmed in aspd.md + BARD_DANCER_SONGS.md.
- **G41 [ ]**: LOW PRIORITY — PC VIT DEF formula discrepancy (Hercules comment vs C code).

## Known Issues
- `sub_size={}` in player_build_to_target — no defensive size resist from player cards. Wire when sub_size added to GearBonuses.
- G43: Physical/Magic toggle in IncomingDamageSection is manual — should follow mob attack type.

## Next Session Work Items (Session F)

1. **G43 design + implementation** — Decide UI for mob skill/attack-type picker. Options: (a) extend combat_controls with Incoming sub-section; (b) separate incoming_controls section; (c) Physical/Magic radio with optional skill combo. Implement chosen design.
2. **G30 — PvP incoming** — No new pipeline needed; wire existing BattlePipeline with a second PlayerBuild as attacker.
3. **G12 — Armor refine DEF** — write import_refine_db.py scraper, add DEF reduction step in IncomingPhysicalPipeline.

## Docs Updated This Session
- `docs/aspd.md` — all unknowns resolved, function name corrected, pre-renewal flow confirmed
- `docs/BARD_DANCER_SONGS.md` — new; full song reference with confirmed formulas
- `CLAUDE.md` — BARD_DANCER_SONGS.md added to docs listing
- `memory/MEMORY.md` — BARD_DANCER_SONGS.md added to reference docs
