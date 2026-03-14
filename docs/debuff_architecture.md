# PS_Calc — Debuff Architecture

_Written after Session SC2. Purpose: audit surface for fixing routing inconsistencies._

---

## Design Intent

Every debuff SC has exactly one effect type:
- **Stat debuff** — mutates AGI/DEX/LUK/STR etc. → flows into all downstream derived stats
- **DEF/MDEF debuff** — reduces def_percent or def2 → flows into incoming damage pipeline
- **Damage multiplier** — doubles or scales outgoing/incoming damage → injected at the right pipeline step
- **Force-hit** — makes the next hit land regardless of FLEE → flag on Target.target_active_scs

The routing for target-side and player-side should be **symmetrical**:
- Target-side: TargetStateSection → data store → consumed by pipeline
- Player-side: PlayerDebuffsSection → data store → consumed by same pipeline steps, mirrored roles

---

## Target-Side Routing (debuffs the player applies to the enemy)

### Data Store: `build.support_buffs` (via `TargetStateSection.collect_into`)
These are persisted across sessions because they represent deliberate player choices:
- `SC_ETERNALCHAOS` → stored as `support_buffs["SC_ETERNALCHAOS"]`
- `SC_PROVOKE` (level) → stored as `support_buffs["SC_PROVOKE"]`
- `SC_DECREASEAGI` (level) → stored as `support_buffs["SC_DECREASEAGI"]`
- `PR_LEXAETERNA` → stored as `support_buffs["PR_LEXAETERNA"]`
- `SC_QUAGMIRE` (level) → stored as `support_buffs["SC_QUAGMIRE"]`
- `SC_MINDBREAKER` (level) → stored as `support_buffs["SC_MINDBREAKER"]`

### Data Store: `target.target_active_scs` (via `TargetStateSection.apply_to_target`)
Session-only flags written directly to the resolved Target before pipeline runs:
- `SC_STUN`, `SC_FREEZE`, `SC_STONE`, `SC_SLEEP` → force-hit flags
- `SC_POISON`, `SC_BLIND`, `SC_CURSE` → also set here (consumed by apply_mob_scs)
- `SC_DONTFORGETME` (level) + `SC_DONTFORGETME_agi` → mob ASPD slowdown
- `SC_MINDBREAKER`, `SC_QUAGMIRE`, `SC_DECREASEAGI` → also set here
- `SC_CRUCIS`, `SC_BLESSING` → mob-only (set only when `not target.is_pc`)

### Mob path: `core/calculators/target_utils.apply_mob_scs(target)`
Reads `target.target_active_scs`, mutates mob Target fields directly:
- SC_DECREASEAGI → agi−=2+lv, flee propagated
- SC_BLIND → hit×75%, flee×75%
- SC_CURSE → luk=0
- SC_POISON → def_percent−=25
- SC_QUAGMIRE → agi−=10lv, dex−=10lv, flee/hit propagated
- SC_BLESSING → str>>=1, dex>>=1 (Undead/Demon only)
- SC_CRUCIS → def−=def×val2/100 (Undead/Demon only)
- SC_MINDBREAKER → matk_percent+=20lv, mdef_percent−=12lv
- SC_DONTFORGETME → aspd_rate+=10×val2
- SC_SLEEP: NO stat mutation — force-hit via hit_chance.py, crit×2 via crit_chance.py

### PvP target path: `TargetStateSection.collect_target_player_scs()`
For player targets: returns stat-cascade SCs → merged into `pvp_eff.player_active_scs`
before StatusCalculator runs on the enemy player build:
- SC_DECREASEAGI, SC_BLIND, SC_CURSE, SC_SLEEP, SC_QUAGMIRE, SC_MINDBREAKER

### ⚠️ Inconsistency: some target SCs bypass target_active_scs
These go to `support_buffs` and are read directly from `build` in modifier files,
**not** through `target_active_scs` / `apply_mob_scs`:
- `SC_ETERNALCHAOS` → read in `defense_fix.py`: `build.support_buffs.get("SC_ETERNALCHAOS")` → `def2=0`
- `SC_PROVOKE` → read in `defense_fix.py`: `build.support_buffs.get("SC_PROVOKE")` → scales vit_def by `(100-(5+5*lv))/100`
- `PR_LEXAETERNA` → read in `magic_pipeline.py` and `battle_pipeline._run_branch()`: `build.support_buffs.get("PR_LEXAETERNA")` → ×2 multiplier

These three were implemented before the target_active_scs architecture existed and were
never migrated. They should ideally be moved to go through `target_active_scs` and
`apply_mob_scs` (for mob targets) and `collect_target_player_scs` (for PvP targets),
but doing so requires touching defense_fix.py, magic_pipeline.py, battle_pipeline.py,
and the section files.

---

## Player-Side Routing (debuffs the enemy applies to the local player)

### Data Store: `build.player_active_scs` (via `PlayerDebuffsSection.collect_into`)
All player debuffs are persisted. Keys:
- `SC_CURSE`, `SC_BLIND` → stat debuffs (luk/hit/flee)
- `SC_DECREASEAGI` (level) → agi reduction
- `SC_QUAGMIRE` (level) → agi+dex reduction
- `SC_MINDBREAKER` (level) → mdef reduction + matk boost
- `SC_POISON` → def_percent reduction
- `SC_PROVOKE` (level) → def_percent reduction
- `SC_ETERNALCHAOS` → def2=0
- `SC_DONTFORGETME` (level) + `SC_DONTFORGETME_agi` → ASPD slowdown
- `SC_STUN`, `SC_FREEZE`, `SC_STONE`, `SC_SLEEP` → force-hit flags

### Effect routing: `StatusCalculator.calculate()` (reads `build.player_active_scs`)
Applied before derived stats so all downstream picks them up:
- SC_DECREASEAGI → agi−=2+lv
- SC_CURSE → luk=0, batk×75%
- SC_BLIND → hit×75%, flee×75% (applied after HIT/FLEE computed)
- SC_QUAGMIRE → agi−=10lv, dex−=10lv (applied in HIT/FLEE section)
- SC_POISON → def_percent−=25 (DEF section)
- SC_PROVOKE → def_percent−=(5+5lv) (DEF section)
- def2 display scaling on `def_percent != 100` (DEF section)
- SC_ETERNALCHAOS → def2=0 (after def_percent scaling)
- SC_DONTFORGETME → sc_aspd_rate+=10×val2 (ASPD slowdown section)
- SC_MINDBREAKER → matk×(100+20lv)//100 (MATK section); mdef×(100−12lv)//100 (MDEF section)

### Effect routing: `BuildManager.player_build_to_target()` (reads `build.player_active_scs`)
Force-hit ailments propagated to `target.target_active_scs` for incoming hit_chance.py:
- SC_STUN, SC_FREEZE, SC_STONE, SC_SLEEP → target_scs dict → Target.target_active_scs
- SC_FREEZE → element=1 (Water) override on player Target
- SC_STONE → element=2 (Earth) override on player Target

### ⚠️ Player side has no equivalent of apply_mob_scs
The target side has `apply_mob_scs()` as a single place where all mob stat mutations happen.
The player side distributes effects across StatusCalculator (stats/def/aspd/matk/mdef)
and player_build_to_target() (force-hit). This is correct given the architecture (player
goes through StatusCalculator; mobs don't), but worth noting for symmetry.

---

## Hit Chance / Force-Hit (shared code, both paths)

`core/calculators/modifiers/hit_chance.py`:
- Checks `target.target_active_scs` for SC_STUN, SC_FREEZE, SC_STONE, SC_SLEEP
- Any of these present → force-hit (attacker always lands)
- Works for both mob targets (set by apply_to_target) and player targets (set by player_build_to_target)

`core/calculators/modifiers/crit_chance.py`:
- SC_SLEEP in `target.target_active_scs` → crit×2 (battle.c:4959)

---

## Lex Aeterna Routing (specific to G77)

`PR_LEXAETERNA` is stored in `build.support_buffs` (target state section → collect_into).

Applied in TWO places:
1. `magic_pipeline.py` — after FinalRateBonus, for BF_MAGIC
2. `battle_pipeline._run_branch()` — after FinalRateBonus, for BF_WEAPON (added SC2)

Both read the same key: `build.support_buffs.get("PR_LEXAETERNA")`.

This is consistent between the two pipelines but is architecturally in the wrong bucket
(should be in target_active_scs like other debuffs that affect "the enemy"). Left as-is
since moving it requires more pipeline plumbing.

---

## Summary Table

| SC | Target store | Target consumer | Player store | Player consumer |
|---|---|---|---|---|
| SC_STUN | target_active_scs | hit_chance.py | player_active_scs | player_build_to_target → target_active_scs → hit_chance.py |
| SC_FREEZE | target_active_scs + element | hit_chance.py | player_active_scs | player_build_to_target → target_active_scs + element |
| SC_STONE | target_active_scs + element | hit_chance.py | player_active_scs | player_build_to_target → target_active_scs + element |
| SC_SLEEP | target_active_scs | hit_chance.py, crit_chance.py | player_active_scs | player_build_to_target → target_active_scs |
| SC_POISON | target_active_scs | apply_mob_scs (def_percent) | player_active_scs | StatusCalculator (def_percent) |
| SC_BLIND | target_active_scs | apply_mob_scs (hit/flee) | player_active_scs | StatusCalculator (hit/flee) |
| SC_CURSE | target_active_scs | apply_mob_scs (luk/batk) | player_active_scs | StatusCalculator (luk/batk) |
| SC_DECREASEAGI | support_buffs + target_active_scs | apply_mob_scs (agi) | player_active_scs | StatusCalculator (agi) |
| SC_QUAGMIRE | support_buffs + target_active_scs | apply_mob_scs (agi/dex) | player_active_scs | StatusCalculator (agi/dex) |
| SC_MINDBREAKER | support_buffs + target_active_scs | apply_mob_scs (matk/mdef%) | player_active_scs | StatusCalculator (matk/mdef) |
| SC_DONTFORGETME | target_active_scs | apply_mob_scs (aspd_rate) | player_active_scs | StatusCalculator (aspd_rate) |
| SC_ETERNALCHAOS | **support_buffs** ⚠️ | **defense_fix.py direct** ⚠️ | player_active_scs | StatusCalculator (def2=0) |
| SC_PROVOKE | **support_buffs** ⚠️ | **defense_fix.py direct** ⚠️ | player_active_scs | StatusCalculator (def_percent) |
| PR_LEXAETERNA | **support_buffs** ⚠️ | **magic_pipeline + battle_pipeline direct** ⚠️ | N/A (player applies it to target) | N/A |
| SC_CRUCIS | target_active_scs | apply_mob_scs (def reduction) | N/A (BL_PC blocked) | N/A |
| SC_BLESSING | target_active_scs | apply_mob_scs (str/dex halve) | N/A (BL_PC blocked) | N/A |

⚠️ = routing inconsistency vs the majority pattern; candidates for refactor.
