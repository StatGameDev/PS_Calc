# Payon Stories — Consolidated Skill & Mechanic Changes
*Persistent changes vs vanilla Ragnarok Online.*
*Sources: Class Rebalance wiki page + patch notes Jan 2023 – Mar 2026*
*The simulator descriptions are source of truth for current numbers. This document captures behavioral changes, context, and changes not visible from descriptions alone.*

---

## General Mechanics

- **ASPD delay** is applied at cast start rather than cast end — noticeable speed improvement for most skills
- **Body Relocation / Snap** range: 18 cells (vanilla: 24)
- **Max walk range**: 17 cells (vanilla: 25)
- **Snap in WoE**: Traps will not stop Snap cast by same guild members
- **Snap**: Cannot be used to escape Ankle Snare traps (vanilla: could escape)
- **HP natural regen**: Ticks every 4 seconds standing, every 2 seconds sitting (server-wide standard)
- **SP natural regen**: Ticks every 6 seconds standing, every 3 seconds sitting

---

## Swordsman

### Increase HP Recovery
- Ticks every **5 seconds** (vanilla: 10 seconds)

### Bash
- SP Cost: **3 + 1 SP per level** (vanilla: 8 SP at lv 1–5, 15 SP at lv 6–10)

### Magnum Break
- SP Cost: **18 SP** (vanilla: 30)
- Range: **3 cells (7x7 area)** (vanilla: 2 cells / 5x5)
- Minimum aftercast delay of **0.4 seconds**

### Moving HP Recovery
- Job Level requirement to learn: **15** (vanilla: 35)
- Quest requirement: **50 Empty Bottles** (vanilla: 200)

---

## Knight

### Two-Hand Quicken
- Duration: **60 seconds per level** / 600 sec at max (vanilla: 30 sec/level)
- Also grants **+1 FLEE per level** and **+0.8% CRIT per level**

### Bowling Bash
- Hits **twice**, each hit doing **400% ATK** at max level (up to 800% total)
- Gutter line mechanic completely removed

### Spear Mastery
- **+5 ATK per level** / **+7 ATK mounted** (vanilla: +4 / +5)

### Brandish Spear
- No limit on how many mobs can be hit
- If a monster hits a wall during knockback, it takes **a second hit**
- Knockback is always toward the target
- Hits twice when affected targets would collide into an unmovable cell after moving at least 1 cell

---

## Crusader

### Holy Cross
- Damage: **(300 + 25×SkillLv)%** — 550% at max (vanilla: ~450%)
- SP Cost: **2 + 1 per level** — 12 SP at max (vanilla: 20)
- Range: **7 cells** (vanilla: 1 cell; was temporarily 9, reverted to 7)
- **+2% accuracy bonus per level** (+20% at max)

### Shield Boomerang
- Damage: **(40×SkillLv)%** — 200% at max (vanilla: ~250%; further buffed from earlier server value)
- SP Cost: **10** (vanilla: 12)
- **Can no longer miss**

### Shield Charge
- Damage: **(200 + 20×SkillLv)%** — 300% at max (vanilla: ~200%)
- **Can no longer miss**

### Spear Quicken
- 2H Spear ASPD: **20% + 1.5% per level** (35% at max; vanilla: ~30%)
- 1H Spear ASPD: **7.5% + 0.5% per level** (12.5% at max; vanilla: none)
- Also grants **+1 CRIT per level**
- Effect is removed when swapping between 1H and 2H spears

### Spear Mastery
- **+5 ATK per level / +7 ATK mounted** (same as Knight)

---

## Acolyte

### SP Recovery
- Ticks every **5 seconds** (vanilla: 10)
- Timer counts while standing but doesn't reset on movement

### Increase AGI
- Duration: **100 + 20×SkillLv** seconds / 300 sec at max (vanilla: ~240)
- SP Cost: **15 + 4×SkillLv** (vanilla: 15 + 3×SkillLv)

### Demon Bane
- Against Undead/Demon: **+5 ATK per level + 0.5×(1+BaseLevel)** (vanilla: +3 + 0.05×BaseLv)
- Now also increases ATK against **all other races**: **+4 per level** (+40 at max)

### Holy Light
- Job Level requirement: **15** (vanilla: 30)
- Damage: **(101 + BaseLevel)%** MATK — ~200% at max base level (vanilla: 125% flat)
- Cast Time: **1.5 seconds** (vanilla: 2)
- SP Cost: **12** (vanilla: 15)

---

## Priest

### Blessing
- Duration: **100 + 20×SkillLv** seconds / 300 sec at max (vanilla: ~240)
- SP Cost: **24 + 5×SkillLv** (vanilla: 24 + 4×SkillLv)

### Battle Mastery *(formerly Mace Mastery)*
- Increases ATK of **all weapons Priests can equip** by **+4 per level** (vanilla: +3 maces only)
- **Lv 10 bonus: Mace/Book ASPD +12%**
- **Now also increases Book weapon damage and ASPD**

### Turn Undead
- Damage on failure: **[Base Level + INT + Skill Level × 10] × 2.5** (vanilla: ×1)

### Gloria
- Duration: **10 + 10×SkillLv** seconds / 60 sec at max (vanilla: ~30 sec)

### Magnus Exorcismus
- Cast Time: **9 + (0.6×SkillLevel)** seconds (vanilla: 14s flat; now level-selectable)
- Duration: **14 seconds** at all levels (vanilla: 4+1s/level)
- Non-Undead/non-Demon enemies take **50% reduced damage** (vanilla: immune)

### Impositio Manus
- Duration: **120 seconds** (vanilla: 60)

### Slow Poison
- **Removed**. Replaced by Renew.

### Renew *(new skill)*
- Retains Slow Poison functionality (stops Poison HP drain without curing it)
- Heals **(25 + 1.5% of MaxHP) × SkillLv** every 3 seconds for 30 seconds (10 heals total)
- Max Level: 4, Instant cast, SP cost: 40 + 15×SkillLv
- Cannot be used on monsters (including undead)

### Holy Strike *(new platinum skill)*
- Passive: melee attacks sometimes proc a Holy damage attack
- Damage: **[100 + STR + (1 + BaseLevel)]%** ATK — ~299% at Lv99
- Activation rate: **20% + 1% per 10 LUK**
- Procs only on **Undead and Shadow element** monsters
- Can **crit**

---

## Monk

### Dodge
- FLEE: **+2 per level** / +20 at max (vanilla: +1.5 rounded down)

### Steel Body / Mental Strength
- DEF set to **[HardDEF × 2]** capped at 90 (vanilla: flat 90 regardless of gear)
- MDEF set to **[HardMDEF × 4]** capped at 90 (vanilla: flat 90)
- Does **not** disable natural SP recovery (vanilla: disabled)

### Iron Fists
- **+5 ATK per level** + **-1% weapon delay per level** (vanilla: +3 ATK, no ASPD)

### Chain Combo
- Damage: 240/320/400/480/560% (patched up from earlier values)
- SP Cost: **8 + SkillLv** (was higher)
- Proc chance of Triple Attack increased by **(ChainCombo SkillLv / 2)**%

### Combo Finish
- Damage: 340/425/510/595/680% (patched up from earlier values)
- SP Cost: **8 + SkillLv**
- Grants personal **+15% damage buff for 8 seconds** on cast
- Buff is refreshed even if already active
- Proc chance of Triple Attack increased by **(ComboFinish SkillLv × 2/3)**%

### Triple Attack
- Proc rate increased by **ChainCombo/2 + ComboFinish×2/3**%

### Raging Quadruple Blow
- Damage: 240/320/400/480/560% (was 200/250/300/350/400%)
- Proc chance of Triple Attack increases by **(SkillLv/2)**%

### Raging Thrust
- Damage: 340/425/510/595/680% (was 300/360/420/480/540%)
- Now also grants a **+15% attack buff for 8 seconds** on use
- Proc chance of Triple Attack increases by **(SkillLv×2/3)**%

### Asura Strike
- No longer ignores DEF
- No longer disables natural SP recovery after use
- Damage **reduced by 1% per point of target's HardDEF**

### Throw Spirit Sphere
- Damage normalized to **350% ATK** at all levels
- Aftercast ActDelay reduced to **400ms**; WalkDelay **100ms×SkillLevel**

### Spiritual Sphere Absorption
- Success chance: **40%** (vanilla: 20%)
- SP Gain: **1×MonsterLv** (vanilla: 2×MonsterLv)
- **Grants 1 Spirit Sphere on successful cast**

### Summon Spirit Sphere / Call Spirits
- Added **200ms aftercast delay**

### Spiritual Cadence
- Ticks every **5 seconds** (vanilla: 10), **10 seconds** if overweight (vanilla: 20)

### Snap
- Cannot escape Ankle Snare traps
- Range: **18 cells** (vanilla: 24)

### Investigate
- **Refunds 1 Spirit Sphere if the target is killed by Investigate**

---

## Archer

### Arrow Shower
- Now **targetable on enemies** (vanilla: ground-targeted)
- Pushback: **1 cell away from caster** (vanilla: random 2-cell)
- **Can no longer move or break traps** (vanilla: could)
- Can be modified by the quest skill **Scattering** (restores ground-targeting and trap interaction)

### Improve Concentration
- Duration: **100 + 20×SkillLv** seconds / 300 sec at max (vanilla: ~240)
- SP Cost: **20 + 6×SkillLv** (vanilla: 20 + 5×SkillLv)

### Arrow Crafting
- Job Level requirement: **15** (vanilla: 30)
- Quest requirement: **5 Trunks** (vanilla: 13)
- **Learnable by Rogues** via the same questline

---

## Hunter

### Blitz Beat
- Damage formula per hit: **([LUK] + [INT/2] + 6×Steel Crow + 20) × 2**
- Splash damage is **full to all targets** — no longer split
- Auto-blitz proc: **0.3% × LUK** (unchanged)

### Blast Mine
- New damage formula: **[SkillLv × (70+DEX) × (70+INT) / 65]**
- Does small **splash damage** to nearby targets

### Land Mine
- New damage formula: **[SkillLv × (80+DEX) × (100+INT) / 70]**
- No splash (high single-target damage)

### Freezing Trap
- New damage formula: **[(25+25×SkillLv)% ATK + 650]** (flat damage added)

### Claymore Trap
- New damage formula: **[SkillLv × (30+DEX) × (100+INT) / 100]**
- **Medium splash range** (was large)
- SP Cost: **15** (wiki had 25, simulator confirms 15)
- Reagent cost: **1 Trap** (was 2 Traps)

### Shockwave Trap / Flasher / Freezing Trap
- All now require only **1 Trap** (was 2 Traps)

### Phantasmic Arrow
- Quest requirement **removed** (vanilla: 5 Harpy Feathers)
- Affected by **Vulture's Eye** range increase

---

## Bard / Dancer

### Musical Lesson
- Damage: **+5 ATK per level** (+50 at max; vanilla: +3)
- Reduces instrument weapon delay by **1% per level** (+10% ASPD at max)

### Dancing Lesson
- Damage: **+5 ATK per level** (+50 at max; vanilla: +3)
- Increases **CRIT rate by 1% per level** (+10% at max)

### Musical Strike / Throw Arrow
- Damage: **[175 + 25×SkillLv]%** — 300% at max (vanilla: ~250%)
- Gains **+100% ATK bonus when used while performing** (400% total while performing)
- Fixed **0.3s cooldown**

### Frost Joker (Bard)
- Success chance: **[(25 + 9×SkillLv) - (DistanceInCells × 5)]%** (vanilla: 40% flat at max; distance-based reduction)

### Scream (Dancer)
- Success chance: **[(25 + 9×SkillLv) - (DistanceInCells × 5)]%** (vanilla: 50% flat at max; distance-based reduction)

### Mr. Kim A Rich Man (Ensemble)
- EXP bonus: **10 + 8×SkillLv%** — +50% at max (vanilla: ~80%; was +60%, then +50%)

---

## Mage

### SP Recovery
- Ticks every **5 seconds** (vanilla: 10)

### Energy Coat
- Job Level requirement: **15** (vanilla: 35)
- Quest requirement: **1 Glass Bead** (vanilla: 3)

### Soul Strike
- If **learned to level 10**: ignores **50% MDEF** at any cast level — works on MVPs and players

### Fire Ball
- Damage: **(40 + 30×SkillLv)%** MATK — **340%** at max (vanilla: 170%)

### Frost Diver
- With **Deluge buff (Empowered)**: +25% freeze chance; also applies **Chilled** status (−40% movement speed for 10 seconds) to non-boss targets at 100% chance

### Napalm Beat
- AoE range: **6×6** (vanilla: 3×3)

---

## Wizard

### Sense
- Passive bonus: **+2% resistance** to Fire, Water, Wind, and Earth elemental physical attacks

### Earth Spike
- Damage: **140% MATK per hit** (vanilla: 100%)

### Heaven's Drive
- Damage: **140% MATK per hit** (vanilla: 100%)

### Frost Nova
- Completely reworked: **5 skill levels** (vanilla: 10)
- Target-centered AoE (vanilla: caster-centered)
- Damage: **190–250% MATK** + **10% per level of Frost Diver learned** (up to 350% with max Frost Diver)
- Cast time: **2.3 − 0.3×SkillLevel** seconds
- Level 5 inflicts **Hypothermia** instead of Freeze (Hypothermia: −40% movement speed for 10 seconds, non-stackable with Chilled)

### Fire Pillar
- **5 skill levels** (vanilla: 10)
- Damage: **50% MATK + 2%×Fire Wall level per hit**
- Ignores **50% of MDEF** (vanilla: ignores all)
- **No gemstone cost**
- **5 second priming time** before activation
- **Can be placed under targets**
- Maximum **5 active pillars** at once

### Sightrasher
- **5 skill levels** (vanilla: 10)
- Damage: **100 + 75×SkillLv%** per fireball (vanilla: 100 + 20×SkillLv%; was 100+75 but reduced to 33+2, now 100+75 per simulator)

### Meteor Storm
- Meteors strike within a **5×5 grid** centered on target (vanilla: full 7×7 random)
- Cast time: **10 seconds** (vanilla: 15)
- Stun chance scales with skill level (5% per level, up to 50%)

### Lord of Vermilion
- Damage: **2000% MATK** at level 10 (vanilla: 1120%; confirmed by simulator)
- Each wave deals **increasing damage** (vanilla: equal waves)
- Each hit has a chance to inflict **Silence** (vanilla: Blind; Blind removed)
- Each wave applies a **1-second flinch** locking targets

### Storm Gust
- Fixed to correctly freeze after **3 hits** (was bugged)

### Gravitational Field *(High Wizard)*
- Reworked: **7×7 AoE** (was smaller)
- Movable after cast
- No gemstone cost
- Reduced aftercast delay

---

## Sage

### Sense
- Passive: **+2% resistance** to Fire, Water, Wind, and Earth elemental attacks

### Advanced Book
- **5 skill levels** (vanilla: 10)
- Damage: **10 + 10×SkillLv** ATK + **3 + 1×SkillLv%** ASPD while book equipped
- **All books have at least +15% MATK built in**

### Cast Cancel
- **Max level 1** (vanilla: 5)
- Level 1 returns **100% SP** with no aftercast delay

### Free Cast
- **Max level 5** (vanilla: 10)
- Level 5: **100% movement speed** (vanilla: 75%)
- Each level grants **+4 FLEE**

### Dispel
- Prerequisite reduced to **Spell Breaker Lv 1** (vanilla: Lv 3)
- **No longer consumes Yellow Gemstone**
- Success chance **not reduced on MVPs** (vanilla: reduced)

### Spell Breaker
- Level 5: **reduces target's HP by 20%** on successful spell break (non-boss only)

### Magic Rod
- Spamming the button is essentially a guaranteed absorb of any single-target magic cast on you

### Auto Spell / Hindsight
- **Cannot be dispelled**
- No cast time, no cooldown, no SP cost when activating
- No skill selection window — choose level directly on skill bar
- SP cost for autocasted spells remains 2/3 normal
- **Double Bolt**: reduced to half bolts when Hindsight is active
- Duration: **5 minutes** at all levels (fixed)

### Double Bolt
- **Max level 1** (was 5 for Scholar, now available to Sage)
- **100% cast chance** (vanilla: ~40–90%)
- Duration: **300 seconds**
- Also causes **Soul Strike** and **Earth Spike** to double cast
- **Cannot be dispelled**

### Abracadabra
- **Max level 5** (vanilla: 10; skills remapped to lower levels)
- **Disabled in all towns**

### Flame Launcher / Frost Weapon / Lightning Loader / Seismic Weapon
- All levels have **100% success rate** (vanilla: 70–100%, could fail and break weapon)
- **Level 1 requires no elemental stone** (duration: 120 seconds)
- **Level 1 also grants Impositio Manus Lv 5** to the target for 120 seconds
- Levels 2–5 require elemental stone, longer durations

### Elemental Change (Water/Fire/Earth/Wind)
- All 4 elements **auto-learned** for free after talking to NPC Yuna — no skill points needed
- **No cast delay** after casting
- **No reagent required**
- Element level stays the same; only element type changes
- **8 second cooldown**
- Effect cleared on Sage death

### Volcano / Deluge / Violent Gale
- All three: instant cast, 9-cell range, no gemstone cost, 300-second duration at all levels, 30 SP cost at all levels
- **Persistence buff**: after leaving the area, buff lasts 120 additional seconds (does not stack between land spells)
- Volcano prerequisite: Flame Launcher Lv 1
- Deluge prerequisite: Frost Weapon Lv 1; **Water Ball tiles no longer depleted**
- Violent Gale prerequisite: Lightning Loader Lv 1; also grants **+25% movement speed** to affected players
- Land spells only affect allies (not enemies)

### Dragonology
- No longer has a prerequisite skill
- Also increases EXP from dragons by up to **10%**

### Gemstone Extraction *(new platinum skill)*
- Chance to drop Red/Yellow/Blue Gemstones and elemental stones when killing non-boss monsters

### Berserk Potion
- Sages can now use Berserk Potions

### Spell Breaker (EXP)
- Spell Breaker now grants EXP (previously caused EXP loss on use)

---

## Thief

### Double Attack
- Chance: **7% per level** / 70% at max (vanilla: 5% / 50%)
- **Sword Mastery** gives rogues **+7% double attack chance with swords per level** via passive
- **Vulture's Eye** gives rogues **+7% double attack chance with bows per level** (both skills must be learned)

### Envenom
- Damage: **[100 + 15×SkillLv]%** — 250% at max (vanilla: flat +15×SkillLv bonus to normal ATK)
- SP Cost: **8** (vanilla: 12)
- Uses **weapon element** instead of Poison element

### Detoxify
- Also cures **Hallucination** status (vanilla: Poison only)

---

## Assassin

### Cloaking
- Can now be activated from **Hiding** state
- Level 3+: First auto-attack from cloak deals **double damage**
- Level 3+: Sonic Blow from cloak deals **+10% damage**
- **ASPD debuff removed** (previously had a debuff while cloaked)

### Katar Mastery
- **+4 ATK + 0.5% CRIT per level** with katars (+40 ATK, +5% CRIT at max; vanilla: +3 ATK)
- **+50% critical damage** with katars at max skill level
- Offhand damage: **+4% per level** up to 40% at max (stacks with Double Attack's 20%)

### Grimtooth
- Can **critically hit** (katar crit bonus does not apply)

### Sonic Blow
- Damage: 540/580/620/660/700/740/780/820/860/900% (vanilla: 440–800%)
- Cast delay is **reduced by DEX and AGI**
- Can **critically hit** (katar crit bonus does not apply)

### Right-Hand Mastery
- Dual wield damage: 80/90/100/110/120% (vanilla: 60/70/80/90/100%)

### Left-Hand Mastery
- Dual wield damage: 60/70/80/90/100% (vanilla: 40/50/60/70/80%)

### Enchant Poison
- **Max level 5** (vanilla: 10)
- Duration: 60/120/180/240/300 sec (vanilla: 30–165 sec)
- Poison chance: 2/4/6/8/10% (vanilla: ~3–7.5%)
- Passive: **+2% damage to Poison element monsters per level**

### Venom Splasher
- **No gemstone requirement** (vanilla: Red Gemstone)
- **No HP threshold requirement** (vanilla: target must be below 3/4 HP)
- Cast range: **3 cells**
- Explosion timer: **2 seconds** at all levels (vanilla: 5–9.5 sec)
- Aftercast delay: **6 seconds** (vanilla: 8–12.5 sec)
- AoE range: **5×5** (vanilla: smaller)

### Venom Dust
- **No catalyst required** (vanilla: Red Gemstone)
- Area: **5×5** (vanilla: 2×2)
- Applies **Mailbreaker effect** (+10% damage taken) for 10 seconds — persists after leaving the area
- Max 4 instances active simultaneously

### Berserk Potion
- Assassins can use Berserk Potions

---

## Rogue

### Back Stab *(major rework)*
- **No strict positioning required** (vanilla: must hit from behind)
- Range: **2 cells**
- Can only be used with **dagger, 1H sword, or unarmed**
- Damage: **[200 + 40×SkillLv]%** — 600% at max (vanilla: ~300%; was 500% then buffed to 600%)
- **Opportunity mechanic**: deals **×1.4 damage** when enemy is not targeting caster (monster) or not facing caster (player)
- Prerequisite changed to **Snatcher Lv 4**
- Quickstep grants **Opportunist buff** — Backstab can trigger Opportunity even if conditions not met

### Raid
- Damage: **[100 + 100×SkillLv]%** — 600% at max (vanilla: 300%; was 300%, then 200/300/400/500/600)
- Applies **+10% physical damage taken debuff** for 10 seconds or 7 hits (100% chance)
- **Hammerfall** also applies Mailbreaker independently (can stack with Raid)
- Prerequisite changed to **Tunnel Drive Lv 3**

### Strip Weapon / Shield / Armor / Helm
- Success formula: **50% + 2%×(Rogue Lv − Target Lv)** (min 40%, max 90%)
- Cast time: **1 second** (DEX-reducible)
- Max level: **3**
- SP Cost: **30 − 6×SkillLv**
- Duration: **30 + 30×SkillLv** seconds
- Range: **1 cell + Vulture's Eye / 2**
- **Does not affect Boss monsters**
- Monster effects: Weapon −40% ATK, Shield −30% HardDEF, Armor −30% HardMDEF, Helm −40% base INT
- If **Full Strip** is learned: each Strip grants a Stolen Buff to the caster

### Sword Mastery (Rogue)
- Provides **+7% double attack chance with swords per level** (passive)

### Vulture's Eye (Rogue)
- Provides **+7% double attack chance with bows per level** (needs both Vulture's Eye and Double Attack)
- **Increases strip range by half its level**

### Double Strafe (Rogue)
- **Removed**, replaced by **Trick Arrow**

### Trick Arrow *(new skill)*
- Bow-only, Level 1
- **200% ATK** (2 hits of 100%)
- Triggers a **random status effect** (Slow, Bleed, Poison, Blind, or Silence) — can be resisted
- SP Cost: **20**
- Range: 9 + Vulture's Eye

### Steal Coin (Rogue)
- **Removed**, replaced by **Stolen Goods**

### Stolen Goods *(new platinum skill)*
- Gives Rogues a chance to obtain Stolen Coins from monsters
- Drop rate: 0.25% (lv 1–11), 0.5% (lv 12–39), 5% (lv 39+)
- Coins can be spent at the Black Market for exclusive items

### Gangster's Paradise *(reworked)*
- **No longer requires another Rogue nearby**
- Sit to create a healing & SP regen zone
- Enemies disengage after 5 seconds (non-boss)
- Benefits extend to party members sitting nearby
- Prerequisite changed to **Tunnel Drive Lv 3**

### Intimidate
- **Roots the target for 2 seconds** after teleporting (vanilla: no root)

### Quick Step / Quickstep *(new platinum skill)*
- SP Cost: **7** (was 10 at release)
- Cooldown: **4 seconds** (was 6)
- Range: 7 cells
- Relocates caster **2 cells behind the target**
- Grants **Opportunist buff** on cast (enables Backstab opportunity bonus)
- Deals 10% ATK when used on enemies; no damage when used on allies

### Gank / Snatcher
- Now works with **bows up to 4 cells away** at **50% proc rate**

### Preserve
- Cannot be reset by Dispel or Death
- Saved on logout
- Toggle-able

### Arrow Crafting
- Also learnable by Rogues (via same questline as Archer)

---

## Merchant

### Discount
- Also **reduces the Zeny cost of Mammonite** by 5% per level (up to −50%)

### Cart Revolution
- Flat **250% damage** at all times (vanilla: 150% + up to 100% based on cart weight)
- Job Level requirement: **15** (vanilla: 35)
- Quest requirement: **15 Iron Ore** (vanilla: 20 Iron)
- Element matches equipped weapon (no longer pseudo-neutral)

### Crazy Uproar
- Quest requirement: **1 Pearl** (vanilla: 7)

### Mammonite
- With **Zeny Pincher** active: 40% damage, no Zeny cost, no SP penalty

---

## Blacksmith

### Adrenaline Rush
- Duration: **70 + 40×SkillLv** seconds / 270 sec at max (vanilla: 30/level / 150 max)

### Weapon Perfection
- Duration: **70 + 40×SkillLv** seconds / 270 sec at max (vanilla: 10/level / 50 max)

### Power-Thrust
- Duration: **70 + 40×SkillLv** seconds / 270 sec at max (vanilla: 20/level / 100 max)
- Chance to break own weapon **removed**

### Skin Tempering
- Fire resistance: **+6×SkillLv%** (vanilla: +4×SkillLv Fire; was labeled differently on old wiki)
- Neutral resistance: **+4×SkillLv%** (vanilla: none)

### Hammer Fall
- Applies **Mailbreaker effect** (+10% damage taken) even if Stun fails

### Maximize Power
- No longer disables SP regeneration

### Zeny Pincher *(new platinum skill)*
- Toggleable
- While active: Mammonite does 40% damage, no Zeny cost, no SP penalty
- Obtainable from Master Merchant at Aldebaran

---

## Alchemist

### Axe Mastery
- **+5 ATK per level** + **ASPD +8% at max level** (vanilla: +3 ATK, no ASPD)

### Acid Terror
- Damage: **(100 + 80×SkillLv)%** — 500% at max (vanilla: ~300%; initially launched at lower value then buffed)
- SP Cost: **8** (vanilla: 10)
- Cast Time: **0.5 seconds** (vanilla: 1)
- **Acid Bottle optional** — consumed if in inventory; armor break only triggers if bottle used
- Aftercast delay: **0.22 seconds**

### Demonstration (Bomb)
- **No Bottle Grenade required** — consumed if in inventory; weapon break only triggers if bottle used
- SP Cost: **16**
- Cooldown: **5 seconds**
- Duration: **11.5 + 2.5×SkillLevel** seconds
- Damage ticks every **1 second**
- Damage doubled vs original
- Caster must be within 30 cells for damage to apply
- **Can be placed under players and monsters**
- Bottle Grenade recipe: **1 Empty Bottle + 1 Fabric + 1 Burning Heart** (vanilla: used Alcohol)

### Potion Pitcher (Aid Potion)
- Each level provides an additional effect on target:
  - Red Potion: also casts **Cure**
  - Orange Potion: also grants **Endure** for 10 seconds
  - Yellow Potion: also casts **Status Recovery**
  - White Potion: also casts **Renew Lv 2**
  - Blue Potion: also grants **Magnificat** for 60 seconds (target only, not party)

### Bio Cannibalize (Summon Flora)
- Cast Time: **1 second** (vanilla: 2)
- Each cast spawns **one plant** of the active type
- **No Plant Bottles required** for a limited number (Lv1: 5 Mandragoras, Lv2: 4 Hydras, Lv3: 3 Floras, Lv4: 2 Parasites, Lv5: 1 Geographer)
- Plant Bottles can add +1 of the current type or always spawn a Geographer
- Plant Bottles usable by Alchemists without knowing the skill
- Plant Bottles have 60-second cooldown
- Plant duration: 60 seconds

### Sphere Mine (Summon Marine Sphere)
- **Marine Sphere Bottle cost removed**
- Damage: **1000 + 200×SkillLv + 25×VIT** (vanilla: 2000 + 400×SkillLv)
- Fixed cooldown of **0.5 seconds** after cast
- **Marine Sphere is now Water Level 3**

### Remote Detonator *(new platinum skill)*
- Aftercast delay: **3 seconds** + fixed minimum **0.5 second** cooldown
- Immediately detonates all summoned Marine Spheres

### Herbicide *(new platinum skill)*
- Cast time: **0.5 seconds**, aftercast 0.1 seconds
- Can self-cast to destroy all summoned Plants (hold shift or /noshift)
- Marine Spheres killed this way do not explode

### Resource Roundup *(new platinum skill)*
- Chance to find brewing ingredients from killed non-boss monsters

---

## Super Novice

### HP Bonuses
- Receives bonus HP at every 10 levels from 40 onwards (ranging from +100 at Lv 40 to +1000 at Lv 99; +2400 total at max)

### SP Bonuses
- Bonus +10 SP every 10 base levels from 20 onwards; +30 SP at level 99

### Soul Harvest *(new platinum skill)*
- Chance to find Soul Fragments from non-boss monsters
- Drop rate: 0.25% (lv 1–11), 0.5% (lv 12–39), 5% (lv 39+)

---

## Ninja

### Ninja Mastery (SP Recovery)
- HP/SP recovery tick rate halved vs vanilla

### Ninja Aura
- Duration: **150 seconds** at max (vanilla: 90)
- STR/INT bonus: **+2×SkillLevel** (+10 at max; vanilla: +1/level)

### Throw Shuriken
- **+50 ATK bonus** at max (vanilla: +40)
- **Can auto-attack** (stopped by item use, skill use, or all shurikens consumed)
- No longer ignores Flee
- **HIT bonus**: +2 per Throwing Mastery level

### Throw Kunai
- Aftercast delay **reduced by AGI and DEX**
- Now benefits from +%ATK and weapon status cards

### Throw Huuma Shuriken
- Damage: **950% at max** (vanilla: 900%)
- Full damage to primary target; split to nearby enemies via formula: `Damage / (1 + (Targets−1)/2)`
- Cast time: **(0.5 + 0.5×SkillLevel)** seconds
- Aftercast delay reduced by AGI and DEX

### Throw Zeny *(formerly Throw Coins)*
- **5 skill levels** (vanilla: 10)
- Aftercast delay: **2 seconds** (vanilla: 5)
- Cooldown: **0.3 seconds**
- Zeny cost: **1000×SkillLevel** per cast (adjusted dynamically)
- **Full damage to Boss monsters** (vanilla: divided by 3)

### Throwing Mastery
- **+2 HIT per level** in addition to damage bonus (+20 at max)

### Flaming Petals
- Aftercast delay **removed**

### Blaze Shield
- **No longer requires Flame Stone**
- Single target: **50% Fire magic damage per hit**
- AoE (3×3 cluster): 3 hits consumed instead of 1; AoE damage is lower
- Hit formula: Lv 1–4 = 3 hits, Lv 5–8 = 6 hits, Lv 9–10 = 9 hits

### Exploding Dragon
- Prerequisite: **Ninja Mastery Lv 7** (vanilla: Lv 10)

### Freezing Spear
- Damage: **85% MATK per hit** (vanilla: 70%; was changed from 100% to 75% to 85%)

### Watery Evasion
- **5 skill levels** (vanilla: 10)
- Aftercast delay **removed**

### Snow Flake Draft
- Prerequisite: **Ninja Mastery Lv 7** (vanilla: Lv 10)
- **100% freeze chance** if target is standing on a water tile

### Lightning Jolt
- **No longer requires Wind Stone catalyst**

### Wind Blade
- Aftercast delay **removed**
- **8 hits at max level** (vanilla: 6)
- Range **+1 cell**

### First Wind
- Prerequisite: **Ninja Mastery Lv 7** (vanilla: Lv 10)

### Flip Tatami
- Duration: **2.5 + 0.5×SkillLevel** seconds (vanilla: 3 seconds flat)

### Cicada Skin Shed
- Duration: **90 seconds** at max (vanilla: 50)
- **Terminates Mirror Image** if active

### Mirror Image
- Requires **Ninja Aura** to cast; consumes 1 Shadow Orb
- Can block **single-target magic attacks**
- Cannot be active simultaneously with Cicada Skin Shed
- If active when using **Killing Stroke**: HP reduced to (5×AttacksLeft)% instead of 1; bonus damage based on remaining images

### Haze Slasher
- **5×5 AoE**, **5 hits**
- Aftercast delay reduced by AGI and DEX
- When used from **Hiding**: +40% damage bonus, SP cost halved
- Can be used without Hiding (deals full base damage)

### Shadow Jump *(formerly Shadow Leap)*
- **Does not require Hiding** to activate
- Upon use, caster **enters Hiding** for 3 seconds
- Range: **15 cells** at max (vanilla: 10)
- Aftercast delay: **0.75 seconds**
- SP Cost: **10** (flat)

### Shadow Slash
- **Does not require Hiding** but gains damage bonus when hidden
- Cannot innately crit unless **Shadow's Within** platinum skill is active
- When hidden: damage per level is higher (800% at max)
- When not hidden: reduced by 10–50% based on distance; range not reduced
- Aftercast delay reduced by AGI and DEX

### Killing Stroke
- If **Mirror Image** is active: reduces HP to (5×AttacksLeft)% instead of 1

### Shadow's Within *(new platinum skill)*
- Enables Shadow Slash to critically hit; +50% crit chance for Shadow Slash
- Turns target to face caster
- Shadow Slash cooldown extended to 3 seconds while active

---

## Gunslinger

*Note: Gunslinger launched Feb/Mar 2025 as a new class. All changes are vs vanilla iRO.*

### Single Action
- **+4 HIT per level** (vanilla: +2)
- ASPD: +1% per odd level (unchanged)

### Chain Action
- **7% double attack chance per level** (vanilla: 5%)

### Flip Coin
- Gains up to **2×SkillLevel coins** per cast — no randomness
- Cast time: **3 seconds** (reducible by DEX)
- SP Cost: **0**
- Zeny cost: **(CoinsGained)²** (minimum 4; adjusted dynamically for partial fills)

### Fling
- SP Cost: **0**

### Triple Action
- Damage: **420% total** (vanilla: 450%)
- Fixed minimum **0.45 second** delay
- SP Cost: **0**
- Prerequisite: Chain Action Lv 7 (vanilla: Lv 10)

### Barrage *(formerly Madness Canceller)*
- Reduces movement speed by **50%** (vanilla: prevented all movement)
- Increases **all damage by 30%** (vanilla: +100 flat ATK)
- Increases ASPD by **20%** (vanilla: 15%)
- Duration: **20 seconds**
- No cast time, no delay, no SP cost
- **Mutually exclusive with Run and Gun**
- Prerequisite: Flip Coin Lv 5 (simplified)

### Run and Gun *(formerly Gunslinger's Panic)*
- Increases movement speed for **5 seconds**
- Duration: **60 seconds** (then extended to 120 in later patch)
- **Reduces ranged damage taken by 30%**
- +30 FLEE
- No cast time, no delay, no SP cost, costs **1 coin**
- **Mutually exclusive with Barrage**
- Cooldown: **6 seconds**

### Gatling Fever
- Damage: **+40%** (vanilla: +120 flat ATK)
- No longer decreases FLEE
- Duration: up to **600 seconds** at max (vanilla: ~165 sec)

### Wing Clip
- Reduces target movement speed by **20% for 10 seconds** (duration reduced by target's AGI)
- No SP cost, no cast time

### Tranq Shot *(formerly Bull's Eye)*
- **140% chance to inflict Sleep for 6 seconds** (reducible by target's INT)
- Deals **100% damage** to Demi-Human and Brute (vanilla: 500%)
- No SP cost
- Prerequisite: Flip Coin Lv 5, Single Action Lv 5, Tracking Lv 10

### Disarm
- Reduces target damage by **20% for 16 seconds** (vanilla: 25% for 30 sec)
- **Can affect bosses** at 10% reduction for 8 seconds
- New success rate formula
- No SP cost
- Prerequisite: Single Action Lv 7 (was Tracking)

### Wounding Shot *(formerly Piercing Shot)*
- Damage: **100 + 20×SkillLv%** regardless of weapon (vanilla: varied by gun type)
- Works with **any gun**
- No cast time requirement
- Bleeding chance without coins: 3×SkillLv%; with coins: **20 + 5×SkillLv%** (costs 1 coin)
- SP Cost: **10**
- Prerequisite: Single Action Lv 5

### Tracking
- Damage: **160×SkillLv%** (vanilla: 200 + 100×SkillLv%)
- Cast time: **1 + 0.1×SkillLv** (vanilla: 1 + 0.2×SkillLv)
- SP Cost: **10 + 2×SkillLv**
- Affected by **Snake's Eye range**
- Can **critically hit**

### Rapid Shower
- Fixed **1 second delay**

### Desperado
- Damage: **100 + 20×SkillLv%** per hit (vanilla: 50 + 50×SkillLv%)
- **Average 6 hits** (vanilla: ~3 hits)
- SP Cost: **20 + 2×SkillLv**

### Dust
- Damage: **100 + 30×SkillLv%** (vanilla: 100 + 50×SkillLv%)
- Works with **shotgun or grenade launcher**
- SP Cost: **3×SkillLv** (unchanged); bullet consumption varies
- Max level bonus (lv 10): **+7% Neutral resistance** (shotgun/launcher only) + **+1 ATK per STR** (shotgun only)

### Full Buster
- Damage: **350 + 75×SkillLv%** (vanilla: 400 + 100×SkillLv%)
- No longer has self-Blind chance
- Consumes fewer bullets (5 at max vs 10)
- SP Cost: **5 + 4×SkillLv**
- Max level bonus: **+7% Neutral resistance**

### Spread Attack
- Damage: **200 + 20×SkillLv%** (vanilla: 80 + 20×SkillLv%)
- SP Cost: **5 + 2×SkillLv** (simplified from earlier values)
- Max level bonus: **+7% Neutral resistance**

### Ground Drift
- Damage: **200 + 60×SkillLv%** in **5×5 AoE** (vanilla: flat non-% damage, 3×3)
- Damage halved when hitting more than 1 target
- Forced Neutral element (exception: Ghosthunter Grenade)
- Prerequisite: Dust Lv 5

### Soul Bullet *(formerly Magic Bullet)*
- 3 hits dealing **Attack×(50+DEX+BaseLv)/100** Ghost element damage
- Costs **1% HP + 3% SP** per use (no longer 7 SP)
- Costs **1 coin**

### Increase Accuracy
- **Removed from skill tree**; HIT bonus transferred to Single Action, AGI/DEX to job bonuses

### Endows
- Gunslingers **cannot be endowed** and cannot benefit from elemental converters

---

*End of consolidated changes document.*
