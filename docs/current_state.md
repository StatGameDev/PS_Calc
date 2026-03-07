# PS_Calc — Current State
# Updated by Claude on "handoff" request.
# Any Claude instance (Code or web) taking over after handoff should read this before starting work.
# Web Claude: also paste relevant sections of CLAUDE.md (rules, file structure, pipeline order).

---

## Last Completed Session
**Session E** — All six work items complete.

Files changed:
- `core/build_manager.py` — `player_build_to_target(build, status, gear_bonuses) -> Target` added
- `core/calculators/incoming_physical_pipeline.py` — new: MobBaseATK → AttrFix → DefenseFix → CardFix
- `core/calculators/incoming_magic_pipeline.py` — new: MobMATKRoll → SkillRatio(optional) → AttrFix → DefenseFix → CardFix
- `core/calculators/modifiers/card_fix.py` — two new static methods: `calculate_incoming_physical`, `calculate_incoming_magic`
- `gui/sections/incoming_damage.py` — complete rewrite: step breakdown panel with Physical/Magic toggle
- `gui/sections/equipment_section.py` — armor element combo added (loads/saves build.armor_element)
- `gui/main_window.py` — incoming pipelines wired; `refresh(phys, magic)` replaces old stubs

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

**IncomingDamageSection public API changed**
- Old: `refresh_mob(mob_id)` + `refresh_status(status)` — GONE
- New: `refresh(physical: Optional[DamageResult], magic: Optional[DamageResult])`

**CardFix new methods**
- `calculate_incoming_physical(mob_race, mob_element, mob_size, is_ranged, player_target, dmg, result)`
- `calculate_incoming_magic(mob_race, magic_ele_name, player_target, dmg, result)`
- Both fire only when player_target.is_pc=True

## Open Gaps Remaining (after Session E)

- **G43 [ ]**: Incoming attack type not skill-driven. Physical always assumes auto-attack; magic defaults to mob natural element. No mob skill picker in GUI. Design UI surface before implementing.
- **G30 [ ]**: PvP incoming physical absent. Architecturally: run full BF_WEAPON outgoing pipeline with second PlayerBuild as attacker, player_build_to_target() result as defender.
- **G12 [ ]**: F3 — Armor refine DEF. Needs import_refine_db.py scraper + pipeline step.
- **G13 [ ]**: F1 — Card slot UI absent.
- **G9 [~]**: SC_ASSNCROS ASPD buff deferred (needs party buff AGI input).
- **G41 [ ]**: LOW PRIORITY — PC VIT DEF formula discrepancy (Hercules comment vs C code).

## Known Issues
- `sub_size={}` in player_build_to_target — no defensive size resist from player cards. Wire when sub_size added to GearBonuses.
- G43: Physical/Magic toggle in IncomingDamageSection is manual — should follow mob attack type.

## Next Session Work Items (Session F)

1. **G43 design + implementation** — Decide UI for mob skill/attack-type picker. Options: (a) extend combat_controls with Incoming sub-section; (b) separate incoming_controls section; (c) Physical/Magic radio with optional skill combo. Implement chosen design.
2. **G30 — PvP incoming** — No new pipeline needed; wire existing BattlePipeline with a second PlayerBuild as attacker.
3. **G12 — Armor refine DEF** — write import_refine_db.py scraper, add DEF reduction step in IncomingPhysicalPipeline.

## Docs Updated This Session
- `docs/gaps.md` — G7, G26, G28, G29, G31, G32 marked [x]; G43 added
- `docs/completed_work.md` — Session D stub + Session E appended
- `docs/current_state.md` — this file
