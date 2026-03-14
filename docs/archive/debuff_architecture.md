# PS_Calc — Debuff / SC Routing Reference

_Last updated: Session SC2-Arch (2026-03-14)_

---

## Design Principles

Every debuff SC has exactly one effect type:

- **Stat debuff** — mutates AGI/DEX/LUK/STR etc.; flows into all downstream derived stats
- **DEF/MDEF debuff** — reduces `def_percent` or `def2`; flows into the defense pipeline
- **Damage multiplier** — doubles or scales outgoing/incoming damage at the right pipeline step
- **Force-hit** — makes the next hit land regardless of FLEE; flag on `target.target_active_scs`

Target-side and player-side routing are symmetrical by design:

- **Target-side**: `TargetStateSection` → `target.target_active_scs` → consumed by pipeline
- **Player-side**: `PlayerDebuffsSection` → `build.player_active_scs` → consumed by same pipeline steps

---

## Target-Side Routing (debuffs applied to the enemy)

### Persistence: `build.target_debuffs`

Written by `TargetStateSection.collect_into()`; read back by `load_build()`.
The pipeline never reads this dict — it is only for save/load round-trip.

Keys: `SC_ETERNALCHAOS`, `SC_PROVOKE` (level), `SC_DECREASEAGI` (level),
`SC_QUAGMIRE` (level), `SC_MINDBREAKER` (level), `PR_LEXAETERNA`.

`support_buffs` carries no target-side debuff keys.

### Pipeline flags: `target.target_active_scs`

Written by `TargetStateSection.apply_to_target()` after target resolution.
Re-populated from scratch each pipeline run (no restore needed).

| Key | Effect |
|---|---|
| `SC_STUN` | force-hit flag → hit_chance.py |
| `SC_FREEZE` | force-hit flag + element=Water override |
| `SC_STONE` | force-hit flag + element=Earth override |
| `SC_SLEEP` | force-hit flag → hit_chance.py; crit×2 → crit_chance.py |
| `SC_POISON` | def_percent−=25 via apply_mob_scs |
| `SC_BLIND` | hit×75%, flee×75% via apply_mob_scs |
| `SC_CURSE` | luk=0 via apply_mob_scs |
| `SC_DECREASEAGI` (level) | agi−=(2+lv), flee propagated via apply_mob_scs |
| `SC_QUAGMIRE` (level) | agi/dex−=10×lv, flee/hit propagated via apply_mob_scs |
| `SC_PROVOKE` (level) | def_percent−=(5+5×lv) via apply_mob_scs [NoBoss] |
| `SC_MINDBREAKER` (level) | matk_percent+=20×lv, mdef_percent−=12×lv via apply_mob_scs |
| `SC_DONTFORGETME` (level) + `_agi` | aspd_rate+=10×val2 via apply_mob_scs |
| `SC_ETERNALCHAOS` | def2=0; read directly from target_active_scs by defense_fix.py |
| `PR_LEXAETERNA` | ×2 damage multiplier; read by battle_pipeline and magic_pipeline |
| `SC_CRUCIS` (level) | def−=def×val2/100 via apply_mob_scs [Undead/Demon only] |
| `SC_BLESSING` | str>>=1, dex>>=1 via apply_mob_scs [Undead/Demon only] |

### Mob execution path

```
apply_to_target(target)       → populates target.target_active_scs
target_utils.apply_mob_scs()  → mutates target fields (agi, dex, luk, def_percent, etc.)
pipeline modifiers             → read already-mutated target fields
```

`SC_ETERNALCHAOS` has no stat mutation in apply_mob_scs — defense_fix.py reads the flag
directly from `target_active_scs` and zeroes `def2` there.

### PvP target execution path

```
collect_target_player_scs()         → returns stat-cascade SCs as dict
merge into pvp_eff.player_active_scs
StatusCalculator(pvp_eff)           → applies all stat/def/aspd/matk effects
player_build_to_target(pvp_eff)     → Target with already-mutated stat fields
apply_to_target(target)             → populates target_active_scs (force-hit + LEX flags)
pipeline modifiers                  → read target fields and target_active_scs
```

SCs returned by `collect_target_player_scs()`:
SC_DECREASEAGI, SC_BLIND, SC_CURSE, SC_SLEEP, SC_QUAGMIRE, SC_MINDBREAKER,
SC_ETERNALCHAOS, SC_PROVOKE.

---

## Player-Side Routing (debuffs applied to the local player)

### Persistence: `build.player_active_scs`

Written by `PlayerDebuffsSection.collect_into()`; read by `StatusCalculator` and
`player_build_to_target()`.

### StatusCalculator execution order

Applied in this order so all downstream derived stats pick up the penalties:

1. **Stats** — SC_DECREASEAGI (agi), SC_CURSE (luk), SC_NJ_NEN, SC_GS_ACCURACY, etc.
2. **BATK** — SC_CURSE (batk×75%), SC_GS_MADNESSCANCEL, SC_GS_GATLINGFEVER
3. **DEF** — SC_POISON (def_percent−25), SC_PROVOKE (def_percent−(5+5×lv)),
   SC_ETERNALCHAOS (def2=0 after scaling)
4. **CRI** — derived from luk (already modified above)
5. **HIT/FLEE** — SC_BLIND (hit/flee ×75%), SC_QUAGMIRE (agi/dex−=10×lv, after HIT/FLEE set)
6. **ASPD** — SC_DONTFORGETME (aspd_rate+=10×val2)
7. **MATK/MDEF** — SC_MINDBREAKER (matk%, mdef%)

### player_build_to_target propagation

`player_build_to_target()` propagates these from `player_active_scs` to `target_active_scs`
on the resulting player Target, so the incoming pipeline sees them:

- SC_STUN, SC_FREEZE, SC_STONE, SC_SLEEP → force-hit flags
- SC_ETERNALCHAOS → def2=0 flag for defense_fix.py on the incoming path
- SC_FREEZE → element=1 (Water) override
- SC_STONE → element=2 (Earth) override

---

## Summary Table

| SC | Target store | Target consumer | Player store | Player consumer |
|---|---|---|---|---|
| SC_STUN | target_active_scs | hit_chance.py | player_active_scs | player_build_to_target → target_active_scs |
| SC_FREEZE | target_active_scs + element | hit_chance.py | player_active_scs | player_build_to_target → target_active_scs + element |
| SC_STONE | target_active_scs + element | hit_chance.py | player_active_scs | player_build_to_target → target_active_scs + element |
| SC_SLEEP | target_active_scs | hit_chance.py, crit_chance.py | player_active_scs | player_build_to_target → target_active_scs |
| SC_POISON | target_active_scs | apply_mob_scs (def_percent) | player_active_scs | StatusCalculator (def_percent) |
| SC_BLIND | target_active_scs | apply_mob_scs (hit/flee) | player_active_scs | StatusCalculator (hit/flee) |
| SC_CURSE | target_active_scs | apply_mob_scs (luk) | player_active_scs | StatusCalculator (luk, batk) |
| SC_DECREASEAGI | target_active_scs | apply_mob_scs (agi) | player_active_scs | StatusCalculator (agi) |
| SC_QUAGMIRE | target_active_scs | apply_mob_scs (agi/dex) | player_active_scs | StatusCalculator (agi/dex) |
| SC_PROVOKE | target_active_scs | apply_mob_scs (def_percent) | player_active_scs | StatusCalculator (def_percent) |
| SC_MINDBREAKER | target_active_scs | apply_mob_scs (matk/mdef%) | player_active_scs | StatusCalculator (matk/mdef) |
| SC_DONTFORGETME | target_active_scs | apply_mob_scs (aspd_rate) | player_active_scs | StatusCalculator (aspd_rate) |
| SC_ETERNALCHAOS | target_active_scs | defense_fix.py (def2=0 flag) | player_active_scs | StatusCalculator (def2=0); player_build_to_target propagates flag |
| PR_LEXAETERNA | target_active_scs | battle_pipeline + magic_pipeline (×2) | N/A | N/A |
| SC_CRUCIS | target_active_scs | apply_mob_scs (def%) [Undead/Demon] | N/A (BL_PC blocked) | N/A |
| SC_BLESSING | target_active_scs | apply_mob_scs (str/dex) [Undead/Demon] | N/A (BL_PC blocked) | N/A |
