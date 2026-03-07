# PS_Calc — Current State
# Updated by Claude on "handoff" request.
# Any Claude instance (Code or web) taking over after handoff should read this before starting work.
# Web Claude: also paste relevant sections of CLAUDE.md (rules, file structure, pipeline order).

---

## Last Completed Session
**Session D (partial)** — Hercules investigation + armor_element stub. Most implementation deferred.

Files changed:
- `core/models/build.py` — `armor_element: int = 0` field added (G27)
- `core/build_manager.py` — armor_element saved under `flags.armor_element`; loaded with default 0

saves/ — scaffold builds (knight_bash, spear_peco, agi_bs) deleted. Do not recreate.

## Key Architectural Decision (from Session D investigation)

**Mob ATK is two-part:**

Part 1 — **Baseline calculation** (what Hercules computes at db load, `mob.c:4937`):
- Weapon range: `rhw.atk = Attack[0]`, `rhw.atk2 = Attack[1]` from mob_db.conf → stored as `atk_min`/`atk_max` in mob_db.json
- BATK: `status_calc_misc` computes `batk = str + (str//10)^2` (pre-renewal BL_MOB path — NO dex or luk terms; those are PC-only).
- MATK: `matk_min = int_ + (int_//7)^2`, `matk_max = int_ + (int_//5)^2` — computed from stats.int, no separate mob_db field.
- On mob spawn: normal mobs copy `db->status` → `status`. This is the **default/unmodified state**.

Part 2 — **Pipeline implementation** (what players see in encounters):
- Read `atk_min`/`atk_max` from `loader.get_monster_data(mob_id)` — weapon component baseline.
- Compute `batk = str + (str//10)^2` from `mob_db.json stats.str`.
- Effective mob base ATK range = `[atk_min + batk, atk_max - 1 + batk]` (rnd()%(atk2-atk1)+atk1 rolls [atk_min, atk_max-1]).
- **IMPORTANT**: Some buffs/debuffs (e.g. Provoke, certain SC effects) modify mob ATK post-spawn by directly changing `rhw.atk`/`rhw.atk2`. The pipeline must NOT hard-exclude this. Design: provide user-adjustable mob ATK override fields (or a %-modifier) on the incoming pipeline so users can model buffed/debuffed mob states. mob_db values are the default baseline only.
- Important: many pre-renewal mobs have str=0 (batk=0) or str=1 (batk=1); batk is only significant for high-str MVPs (Boitata: batk=336 = 21% of avg ATK).

Source refs: `battle_calc_base_damage2` (battle.c, #else RENEWAL); `status_base_atk` (status.c:3749–3774); `mob_read_db_sub` (mob.c:4937).

## Next Session Work Items (Session E)

All from original Session D plan, not yet implemented:

1. **`player_build_to_target(build, status, gear_bonuses) → Target`** — add to `core/build_manager.py`.
   Map: `def_=status.def_`, `vit=status.vit`, `level=build.base_level`, `is_pc=True`,
   `size="Medium"`, `race="DemiHuman"`, `element=build.armor_element`,
   `armor_element=build.armor_element`, `element_level=1`, `luk=status.luk`,
   `agi=status.agi`, `flee=status.flee`, `mdef_=status.mdef`, `int_=status.int_`,
   `sub_race=gear_bonuses.sub_race`, `sub_ele=gear_bonuses.sub_ele`,
   `sub_size=gear_bonuses.sub_size`, `near_attack_def_rate=gear_bonuses.near_atk_def_rate`,
   `long_attack_def_rate=gear_bonuses.long_atk_def_rate`, `magic_def_rate=gear_bonuses.magic_def_rate`.

2. **`IncomingPhysicalPipeline`** — new `core/calculators/incoming_physical_pipeline.py`.
   Steps: MobBaseDamage → AttrFix(mob.element vs player.armor_element)
          → DefenseFix(BF_WEAPON, target.is_pc=True) → CardFix(target-side only).
   Mob base damage (two parts as above): weapon_roll [atk_min, atk_max-1] + batk.
   Get mob data via `loader.get_monster_data(mob_id)` for atk_min/atk_max/stats.
   The pipeline label should clearly say these values are "fixed at spawn time."

3. **`IncomingMagicPipeline`** — new `core/calculators/incoming_magic_pipeline.py`.
   Steps: MobMATKRoll [matk_min, matk_max] → SkillRatio(BF_MAGIC, if skill)
          → AttrFix(skill.element vs player.armor_element)
          → DefenseFix.calculate_magic(player.mdef_, player.int_)
          → CardFix.calculate_magic(target-side: player.magic_def_rate, sub_ele, sub_race).

4. **Replace `gui/sections/incoming_damage.py`** with a proper step breakdown panel
   (similar to the outgoing combat panel). Wire to `main_window.py`.

5. **Armor element selector** — add to `gui/sections/equipment_section.py`
   (same pattern as weapon_element combo). Triggers recalc on change.

6. **Wire incoming pipelines** in `gui/main_window.py` — trigger on build/mob changes.

## Gaps Resolved by Session D (partial)
- G27 [x]: armor_element field added to PlayerBuild + save/load.
- G28 [~]: mob str needed for batk in IncomingPhysicalPipeline — available via `loader.get_monster_data(mob_id)['stats']['str']`; no DataLoader change needed, read directly in pipeline.
- G33 [x]: ALREADY DONE in Session B (MDEF in StatusData + StatusCalculator). Mark done in gaps.md.

## Active Known Bugs (produce wrong output)
- G7: VIT DEF PC branch — activates automatically once player_build_to_target() is implemented.
- Incoming pipelines entirely absent (G26, G32) — no incoming damage calculation exists.
