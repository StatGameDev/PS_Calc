# PS_Calc — Session Roadmap
_Each session is a coherent unit of work completable in one sitting._
_Gap IDs reference docs/gaps.md. Pipeline specs in docs/pipeline_specs.md._

---

## Session A — Model Foundation + Physical Pipeline Corrections

**Goal**: Extend all data models to their final shape. Fix the most impactful BF_WEAPON gaps.
**Gap IDs**: G1, G2, G3, G5, G6, G7, G8, G10 (partial), G11 (as part of G2), G28

### Work items (in order):

1. **Extend Target model** — add all new fields with zero defaults (see data_models.md).
   No existing code breaks. Mob path stays zero. is_pc=True gates the new branches.

2. **Extend GearBonuses** — add `near_atk_def_rate`, `long_atk_def_rate`, `magic_def_rate`, `atk_rate`.
   Add to `_BONUS1_ROUTES` in gear_bonus_aggregator.py.
   Add to item_script_parser.py template table: `bNearAtkDef`, `bLongAtkDef`, `bMagicDefRate`, `bAtkRate`.

3. **Update loader.get_monster()** — populate `target.mdef_` from `mob_data["mdef"]`,
   `target.int_` from `mob_data["stats"]["int"]`.

4. **Fix G1 SC_IMPOSITIO** — add type `"flat_watk"` entry to active_status_bonus.json.
   In BaseDamage, before the ATK range roll, add `val2 = level * 5` flat to weapon ATK.
   Source: status.c #ifndef RENEWAL ~line 4562.

5. **Fix G3 Arrow ATK** — in BaseDamage, if weapon is bow-type and ammo is equipped,
   fetch `loader.get_item(ammo_id)["atk"]` and add to weapon ATK before the range roll.
   Add a "Arrow ATK" info step.

6. **Implement CardFix modifier** — new `core/calculators/modifiers/card_fix.py`.
   - Recomputes `GearBonuses` from `build.equipped` (or receives it as parameter).
   - Attacker side: add_race, add_ele, add_size, boss/nonboss, long_atk_rate (if BF_LONG).
   - Target side (only if target.is_pc): sub_ele, sub_size, sub_race, near/long_def_rate.
   - Insert after AttrFix, before FinalRateBonus in battle_pipeline.py.
   - G11 (bLongAtkRate) is resolved as part of attacker CardFix.

7. **Fix G7 VIT DEF PC branch** — in defense_fix.py, branch on target.is_pc.
   PC branch: `vit_def += i * int(3 + (target.level + 1) * 0.04)`
   Mob branch: `vit_def += i * 5` (current behaviour, unchanged)

8. **Fix G5 ignore_def** — in defense_fix.py, before applying def1:
   `ignore_pct = gear_bonuses.ignore_def_rate.get(target.race, 0) + gear_bonuses.ignore_def_rate.get(boss_key, 0)`
   `def1 = def1 * (100 - ignore_pct) // 100`
   Note: also check ignore_def_ele if that field is implemented.

### Tests:

**G1 (SC_IMPOSITIO)**
- Auto: BaseDamage with SC_IMPOSITIO Lv5 → weapon ATK step +25.
- User: Load knight_bash.json. Enable SC_IMPOSITIO Lv5. Verify weapon ATK step +25. Disable → returns.

**G3 (Arrow ATK)**
- Auto: BaseDamage with bow + ammo (atk=25) → weapon ATK includes +25 vs no ammo.
- User: Load ak77_hunter.json. Note weapon ATK step. Unequip ammo → drops by arrow ATK.

**G2 + G11 (CardFix attacker side)**
- Auto: CardFix with add_race={"RC_Brute":20}, target.race="Brute" → ×1.20.
       With long_atk_rate=10, is_ranged=True → additional ×1.10.
- User: Equip Orc Card (bAddRace,RC_Brute,15) on weapon. Target Wolf (Brute).
  Verify "Card Fix" step ×1.15. Switch to non-Brute target → ×1.00.

**G8 (CardFix target side)**
- Auto: CardFix with target.is_pc=True, target.sub_race={"RC_DemiHuman":30},
  attacker race=DemiHuman → ×0.70.
- User: Manually set player Target with Thara Frog card sub_race RC_DemiHuman 30%.
  Damage 30% lower vs no card. is_pc=False (mob target) → card has no effect.

**G7 (VIT DEF PC branch)**
- Auto: DefenseFix is_pc=False vs is_pc=True, same vit=80, level=99 → different soft DEF ranges.
- User: Target Lv99 PC VIT 80 vs mob VIT 80. DefenseFix step VIT DEF ranges must differ.

**G5 (ignore_def)**
- Auto: DefenseFix ignore_def_rate={"RC_Boss":100}, boss mob DEF 50 → def1=0.
- User: Equip Thanatos Card vs boss mob. Hard DEF in step = 0. Remove → normal.

---

## Session B — MATK + BF_MAGIC Outgoing Pipeline

**Goal**: Implement the full magic damage pipeline for player attacking any target.
**Gap IDs**: G18, G19, G20, G21, G22, G23, G24, G25

### Work items:

1. **StatusCalculator: MATK** — add matk_min, matk_max to StatusData.
   `matk_min = int_ + (int_//7)**2`, `matk_max = int_**2 + (int_//5)**2`
   Source: status.c:3783-3792 #ifndef RENEWAL.

2. **StatusCalculator: MDEF** — investigate mdef2 formula in status.c (one grep needed).
   Add mdef, mdef2 to StatusData. Populate from equip (for mdef) and INT (for mdef2).

3. **derived_section.py** — add MATK row (show min–max range), MDEF row.

4. **skill_ratio.py: BF_MAGIC path** — add magic skill ratios.
   Grep `calc_skillratio` BF_MAGIC section before implementing. Key skills listed in pipeline_specs.md.

5. **MagicPipeline class** — new `core/calculators/magic_pipeline.py`.
   Steps: MATK roll → SkillRatio(BF_MAGIC) → matk_percent → ignore_mdef → DefenseFix(BF_MAGIC) → CardFix(target side only if is_pc).

6. **DefenseFix: BF_MAGIC branch** — `damage = damage*(100-mdef)//100 - mdef2`
   Source: battle.c:1581 #ifndef RENEWAL (magic_defense_type=0).

7. **GearBonuses: ignore_mdef_rate** — add field, add to aggregator, wire into magic DefenseFix.

8. **Wire MagicPipeline into BattlePipeline** — call when skill is BF_MAGIC type.
   Determine BF type from skills.json skill data.

### Tests:

**G18 (MATK)**
- Auto: StatusCalculator int_=99 → matk_min=99+14*14=295, matk_max=99+19*19=460.
- User: Set INT=99. MATK row in derived section shows 295–460.

**G19 + G22 (Magic pipeline)**
- Auto: Fire Bolt Lv5 (5 hits × 100%) on Neutral mob, matk_avg=370 → 5×370 after defense.
- User: Load Mage build. Fire Bolt Lv5 on Poring. Step breakdown shows MATK, SkillRatio (500%), MDEF reduction.

**G20 (MDEF defense)**
- Auto: DefenseFix BF_MAGIC, mdef=50, mdef2=10, damage=100 → 100*(100-50)/100-10 = 40.
- User: Target mob with known MDEF (e.g. check mob_db). Magic damage step shows correct MDEF reduction.

**G23 (Magic CardFix target side)**
- Auto: CardFix BF_MAGIC, target.is_pc=True, target.magic_def_rate=30 → ×0.70.
- User: Player target with Khalitzburg Card (bMagicDefRate,30) → magic damage drops 30%.

---

## Session C — Mastery Completion + ASPD Buffs + bAtkRate

**Goal**: Complete mastery system, fix ASPD buff display, route remaining small gaps.
**Gap IDs**: G4, G9, G10

### Work items:

1. **G4 ASC_KATAR** — in mastery_fix.py, after flat AS_KATAR:
   `if mastery_levels.get("ASC_KATAR", 0) > 0: dmg += dmg * (10 + 2*lv) / 100`
   Source: battle.c masteryfix #else (pre-re).
   Add ASC_KATAR to passive_section.py mastery list, visible only for job_id 24 (Assassin Cross).

2. **G9 ASPD buffs** — in status_calculator.py, after base amotion calculation:
   Check active_status_levels for ASPD SCs. Add a small inline lookup table with amotion reductions.
   SCs to handle: SC_TWOHANDQUICKEN, SC_ADRENALINE, SC_SPEARQUICKEN, SC_ONEHAND, SC_ASSASINEDGE.
   Grep status.c for each SC to get exact amotion reduction values before implementing.

3. **G10 bAtkRate** — add to item_script_parser, GearBonuses.atk_rate.
   Apply in BaseDamage or early pipeline step: `dmg = dmg.scale(100 + atk_rate, 100)`.
   Source: battle.c:5330 #ifndef RENEWAL (before SkillRatio in the code path).

### Tests:

**G4 (ASC_KATAR)**
- Auto: MasteryFix with katar, AS_KATAR=5, ASC_KATAR=5 → flat +15 then ×1.20 in step.
- User: Load nat_crit_sin.json. Set ASC_KATAR=5. MasteryFix step shows +20% of pre-mastery value.

**G9 (ASPD buffs)**
- User: Load knight_bash.json (2H sword). Enable SC_TWOHANDQUICKEN Lv10. ASPD in derived section
  increases by expected amount (cross-check vs irowiki ASPD table). Disable → base ASPD returns.

---

## Session D — Incoming Pipelines

**Goal**: Implement physical and magic incoming damage from both mobs and players.
**Gap IDs**: G16, G17, G26, G27, G28, G29, G30, G31, G32, G33

### Work items:

1. **PlayerBuild.armor_element** — add field to PlayerBuild. Add armor element selector to equipment_section.py (similar to weapon_element combo).

2. **`player_build_to_target()` helper** — in build_manager.py or a new converter module.
   See data_models.md for full field mapping.

3. **IncomingPhysicalPipeline** — new class.
   Steps: mob ATK roll → AttrFix(mob.element vs player.armor_element) → DefenseFix(BF_WEAPON, is_pc=True) → CardFix(target side, player.sub_race/ele/size etc.)
   Note: for Player→Player incoming, just run existing BattlePipeline with attacker=second build, target=player_build_to_target(defender_build).

4. **IncomingMagicPipeline** — new class.
   Steps: mob MATK roll → SkillRatio (if skill) → AttrFix → DefenseFix(BF_MAGIC) → CardFix(target side).

5. **incoming_damage.py expansion** — replace display stub with real step breakdown.
   Show both incoming physical and incoming magic (or toggle between them).

### Tests:

**Incoming physical (mob)**
- User: Select Orc Warrior (known ATK range). Note incoming range. Equip Raydric Card (sub_ele Neutral 20).
  Since Orc Warrior is Neutral element: incoming drops 20%. Remove card → returns.

**Incoming physical (PvP)**
- User: Configure two builds. Build A attacks Build B. Verify B's Thara Frog Card (sub_race DemiHuman 30)
  reduces A's outgoing physical by 30%. B's Raydric Card (sub_ele Neutral 20) with Neutral weapon reduces further.

**Incoming magic (mob)**
- User: Select magic-casting mob. Equip Pasana Card (armor Fire element) vs Fire-element magic → 0 damage.
  Equip Khalitzburg Card (magic_def_rate 30) → further 30% reduction on neutral magic.

---

## Session E — Card Slots UI + Filters + F3

**Goal**: Card sub-slots in equipment UI, filter UIs across the app, armor refine DEF.
**Gap IDs**: G12, G13, G34, G35, G36, G37, G38

### Work items:

1. **G13 F1 Card slots** — in equipment_section.py, after each item row, add 0-N card buttons
   based on `loader.get_item(item_id)["slots"]`. Key scheme: `{slot}_card_{n}` (e.g. `right_hand_card_0`).
   Card browser: EquipmentBrowserDialog filtered to IT_CARD only.
   Save schema: card keys go into build.equipped dict (no structural change needed).

2. **G38 F3 Armor refine DEF** — write tools/import_refine_db.py scraping refine_db.conf.
   Output: core/data/pre-re/tables/refine_armor.json.
   Add lookup in GearBonusAggregator using build.refine_levels[slot] for armor slots.

3. **G34 4.4 Skill job filter** — in combat_controls.py, filter skill combo to current job_id.

4. **G35 4.5 Equipment Browser job filter** — add job filter to EquipmentBrowserDialog.

5. **G36 4.6 Monster Browser filters** — race / element / size QComboBox in MonsterBrowserDialog.

6. **G37 4.7 Passives job filter** — hide/disable irrelevant mastery/flag entries by job.

### Tests:

**G13 (Card slots)**
- User: Equip 4-slot Composite Bow. Verify 4 card sub-slot buttons appear.
  Equip Hydra Card (slot 0). CardFix step shows ×1.20 vs DemiHuman. Save → reload → cards persist.
  Equip 0-slot item → no card buttons.

**G38 (Armor refine DEF)**
- User: Equip Full Plate (+0). Note hard DEF. Set refine to +10. DEF increases by correct amount
  per refine_armor table. Cross-check vs irowiki Refine article.

---

## Session F — Polish + E-Series

**Goal**: Remaining low-impact pipeline gaps, UI polish.
**Gap IDs**: G15, G16 (E4), G17 (E6), G39, G40

### Work items:

1. **G16 E4 Katar second hit** — grep battle.c for Katar dual-hit fraction. Implement as second
   branch result in pipeline (similar to crit branch).

2. **G17 E6 Forged weapon Verys** — after AttrFix, check weapon for "Very" gemstones. Add +5 ATK each.

3. **G15 F4 Gear bonus visibility** — read-only "from gear" indicators or tooltip next to bonus
   fields in stats_section.py. Show gear_bonuses total contribution per stat.

4. **G39 F7 Inline equipment dropdown** — consider for low-priority implementation.

5. **G40 P1 StepsBar state persistence** — restore expanded state after focus change.

---

## Deferred (Needs Design Session)

- **C1 Full variance distribution** — Monte Carlo / Irwin-Hall / exact convolution.
  Do NOT touch DamageRange until design is settled. See GUI_PLAN.md Session 2 handover.
- **E2 routing completion** — sub_ele/sub_race/add_ele etc. from GearBonuses are now wired into
  CardFix (Session A). Remaining: verify bSkillAtk, bIgnoreDefRate pipeline routing.
- **Phases 5-8** — Stat Planner Tab, Comparison Tab, Phase 7 histogram, Config/Scale.
