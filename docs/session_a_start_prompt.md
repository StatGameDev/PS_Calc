Start Session A. Read docs/current_state.md, then implement all 8 work items in order.
Pre-read all 9 files listed below before making any edits.

Files to read first (in parallel if possible):
- core/models/target.py
- core/models/gear_bonuses.py
- core/gear_bonus_aggregator.py
- core/item_script_parser.py
- core/data_loader.py
- core/calculators/modifiers/base_damage.py
- core/calculators/modifiers/defense_fix.py
- core/calculators/battle_pipeline.py
- core/data/pre-re/tables/active_status_bonus.json

Known facts to apply immediately (no re-investigation needed):
- active_status_levels uses string keys: "SC_IMPOSITIO", "SC_MAXIMIZEPOWER" etc.
- G1 SC_IMPOSITIO: inline check in BaseDamage like SC_MAXIMIZEPOWER — NO JSON change.
  lv = build.active_status_levels.get("SC_IMPOSITIO", 0); if lv: atkmax += lv * 5
  Add before the atkmin calculation. Add a result.add_step for it.
- G3 Arrow ATK: weapon.weapon_type == "Bow" is the bow check (RANGED_WEAPON_TYPES in weapon.py,
  but Bow is the relevant type for ammo). Fetch loader.get_item(build.equipped.get("ammo"))["atk"].
- CardFix boss/nonboss key strings: confirm from GearBonuses.add_race dict while reading gear_bonuses.py.

Commit at end with message: "Session A: CardFix + Arrow ATK + SC_IMPOSITIO + ignore_def + VIT DEF PC"
Update docs/context_log.md with files touched and line counts after committing.
