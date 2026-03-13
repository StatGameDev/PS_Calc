# SC1 Implementation — Resume Point
_Written before auto-compact. All source reads done. No more greps needed._

## Completed This Session

- **CLAUDE.md**: Added "Stop and Ask" rule (stop immediately at genuine decision points; resolve with source + best practices otherwise).
- **target.py**: Added fields `str`, `dex`, `hit`, `mdef_percent=100`, `matk_percent=100`, `aspd_rate=1000`, updated `flee` and `def_percent` comments.
- **data_loader.py**: `get_monster()` now populates `str`, `dex`, `flee=level+agi`, `hit=level+dex` from mob_db stats.
- **target_utils.py**: Full rewrite of `apply_mob_scs(target, status)` with all SC1 debuffs + G81 boss immunity guards.
- **hit_chance.py**: SC_SLEEP added to force-hit condition; uses `target.flee` directly (falls back for default Target()).

## Still To Implement

### 1. crit_chance.py
Replace:
```python
    # 5. SC_SLEEP: skipped — no SC system yet
```
With:
```python
    # 5. SC_SLEEP: cri <<= 1 when target has SC_SLEEP (battle.c:4959)
    if "SC_SLEEP" in target.target_active_scs:
        cri <<= 1
```

### 2. defense_fix.py — two changes

**A) Mob path — apply target.def_percent to vit_def** (currently only PC path does this).
After the existing `prov_lv` block in the mob `else` branch (around line 153-157), add:
```python
            mob_dp = target.def_percent
            if mob_dp != 100:
                vd_min = vd_min * mob_dp // 100
                vd_max = vd_max * mob_dp // 100
                vd_avg = vd_avg * mob_dp // 100
```
Source: status.c:4431-4432 (SC_POISON def_percent -= 25, no guard → applies to mobs too).

**B) calculate_magic() — apply target.mdef_percent to hard mdef**
After `mdef = max(0, min(100, target.mdef_))`, add:
```python
        if target.mdef_percent != 100:
            mdef = max(0, min(100, mdef * target.mdef_percent // 100))
```
Source: status.c:4453-4454 (SC_MINDBREAKER mdef_percent -= 12*lv).

### 3. status_calculator.py — player path for new SCs
Add these blocks after the SC_BLIND block (around line 229):

```python
        # SC_QUAGMIRE: agi -= val2, dex -= val2; val2=10*lv (status.c:4027-4028, 4211-4212)
        if "SC_QUAGMIRE" in player_scs:
            val2 = 10 * int(player_scs["SC_QUAGMIRE"])
            status.agi = max(0, status.agi - val2)
            status.dex = max(0, status.dex - val2)
```

Then in the ASPD section, after the `SC_DEFENDER` block, add:
```python
        # SC_DONTFORGETME: aspd_rate += 10*val2; val2=caster_agi/10+3*lv+5 (#else pre-renewal)
        # On player path, the caster's agi is not available here — use skill_lv only (val2 approx).
        # Full formula requires caster agi; flagged for SC2 when architecture supports it.
        if "SC_DONTFORGETME" in player_scs:
            lv = int(player_scs["SC_DONTFORGETME"])
            val2 = 3 * lv + 5  # approximate: caster agi not available in StatusCalculator
            sc_aspd_rate += 10 * val2
```

Then in the MDEF section, after SC_ENDURE:
```python
        # SC_MINDBREAKER: mdef_percent -= 12*lv (status.c:4453-4454)
        if "SC_MINDBREAKER" in player_scs:
            lv = int(player_scs["SC_MINDBREAKER"])
            status.mdef = max(0, status.mdef * (100 - 12 * lv) // 100)
```

### 4. target_state_section.py — UI additions + routing

**New UI rows to add in `__init__`:**

Applied Debuffs section (persisted — add to collect_into/load_build):
- Blind: QCheckBox
- Curse: QCheckBox
- Sleep: QCheckBox (also Status Ailment, mutually exclusive with other ailments? No — just a checkbox)
- Quagmire: LevelWidget(5, include_off=True, item_prefix="Lv ")
- Don't Forget Me: LevelWidget(5, include_off=True, item_prefix="Lv ")
- Mind Breaker: LevelWidget(5, include_off=True, item_prefix="Lv ")

Monster-only (inside `_monster_state_widget`, persisted):
- Signum Crucis: LevelWidget(10, include_off=True, item_prefix="Lv ")
- Blessing Debuff: QCheckBox (label "Blessing (Undead/Demon)")

Status Ailments section (session-only, already has Stun/Freeze/Stone/Poison — add):
- Blind: QCheckBox (move from Applied Debuffs if desired, or keep separate)
- Curse: QCheckBox
- Sleep: QCheckBox

**Simplest approach**: put Blind/Curse/Sleep in Status Ailments (session-only, like Stun/Freeze/Stone/Poison). Put Quagmire/DontForgetMe/MindBreaker in Applied Debuffs (persisted, like Provoke/DecreaseAgi). SC_CRUCIS and SC_BLESSING debuff in Monster State (monster-only, session-only).

**collect_into** — add:
```python
        for key in ("SC_QUAGMIRE", "SC_DONTFORGETME", "SC_MINDBREAKER"):
            support.pop(key, None)
        qua_lv = self._lw_quagmire.value()
        if qua_lv:
            support["SC_QUAGMIRE"] = qua_lv
        dfm_lv = self._lw_dontforgetme.value()
        if dfm_lv:
            support["SC_DONTFORGETME"] = dfm_lv
        mb_lv = self._lw_mindbreaker.value()
        if mb_lv:
            support["SC_MINDBREAKER"] = mb_lv
```

**collect_target_player_scs** — add SC_BLIND, SC_CURSE, SC_SLEEP, SC_QUAGMIRE, SC_DONTFORGETME, SC_MINDBREAKER:
```python
        if self._chk_blind.isChecked():
            scs["SC_BLIND"] = 1
        if self._chk_curse.isChecked():
            scs["SC_CURSE"] = 1
        if self._chk_sleep.isChecked():
            scs["SC_SLEEP"] = 1
        qua_lv = self._lw_quagmire.value()
        if qua_lv:
            scs["SC_QUAGMIRE"] = qua_lv
        dfm_lv = self._lw_dontforgetme.value()
        if dfm_lv:
            scs["SC_DONTFORGETME"] = dfm_lv
        mb_lv = self._lw_mindbreaker.value()
        if mb_lv:
            scs["SC_MINDBREAKER"] = mb_lv
```

**apply_to_target** — add to scs dict:
```python
        if self._chk_blind.isChecked():
            scs["SC_BLIND"] = 1
        if self._chk_curse.isChecked():
            scs["SC_CURSE"] = 1
        if self._chk_sleep.isChecked():
            scs["SC_SLEEP"] = 1
        qua_lv = self._lw_quagmire.value()
        if qua_lv:
            scs["SC_QUAGMIRE"] = qua_lv
        dfm_lv = self._lw_dontforgetme.value()
        if dfm_lv:
            scs["SC_DONTFORGETME"] = dfm_lv
        mb_lv = self._lw_mindbreaker.value()
        if mb_lv:
            scs["SC_MINDBREAKER"] = mb_lv
        # Monster-only
        if not target.is_pc:
            crucis_lv = self._lw_crucis.value()
            if crucis_lv:
                scs["SC_CRUCIS"] = crucis_lv
            if self._chk_blessing.isChecked():
                scs["SC_BLESSING"] = 1
```

**Add `set_is_boss(is_boss: bool)` method** — disables boss-blocked widgets:
```python
    def set_is_boss(self, is_boss: bool) -> None:
        """Disable SC_COMMON and NoBoss SCs when target is a boss (G81)."""
        boss_blocked = [
            self._chk_stun, self._chk_freeze, self._chk_stone,
            self._chk_sleep, self._chk_poison, self._chk_blind, self._chk_curse,
            self._lw_provoke, self._lw_decagi,
        ]
        for w in boss_blocked:
            w.setEnabled(not is_boss)
            if is_boss:
                if hasattr(w, 'setChecked'):
                    w.setChecked(False)
                else:
                    w.setValue(0)
```

### 5. main_window.py — three wiring changes

**A)** Pass status to apply_mob_scs (line ~524):
```python
        if not target.is_pc:
            target_utils.apply_mob_scs(target, status)
```

**B)** Pass matk_percent to IncomingMagicPipeline (line ~563):
```python
                magic_result = self._incoming_magic_pipeline.calculate(
                    mob_id=mob_id,
                    player_target=player_target,
                    gear_bonuses=gear_bonuses,
                    build=eff_build,
                    ele_override=ele_override,
                    ratio_override=ratio_override,
                    mob_matk_bonus_rate=target.matk_percent - 100,
                )
```

**C)** Call set_is_boss after set_target_type (line ~521):
```python
        self._target_state.set_target_type(target.is_pc)
        self._target_state.set_is_boss(target.is_boss)
```

## All Source Lines Confirmed (no more greps needed)

| SC | Effect | Source |
|---|---|---|
| SC_BLIND | hit/flee ×75% | status.c:4817, 4903 |
| SC_CURSE | luk=0 | status.c:4261-4262 |
| SC_POISON | def_percent −= 25 | status.c:4431-4432 |
| SC_SLEEP | force-hit (opt1, battle.c:5014); crit×2 (battle.c:4959) | confirmed |
| SC_QUAGMIRE | agi/dex −= 10×lv | status.c:4027,4211,8343 |
| SC_BLESSING debuff | str>>=1, dex>>=1, mob Undead/Demon only | status.c:3964,4213,8271 |
| SC_CRUCIS | def −= def×(10+4×lv)/100, mob Undead/Demon only | status.c:5022,7662 |
| SC_MINDBREAKER | matk_percent += 20×lv; mdef_percent −= 12×lv | status.c:4376,4453,8379 |
| SC_DONTFORGETME | aspd_rate += 10×(agi/10+3×lv+5) | status.c:5667, skill.c:13270 |
| G81 Boss Protocol | SC_COMMON + NoBoss immune | status.c:7472, sc_config.conf |

## Gaps to Close After Implementation
- G79: close [x]
- G81: close [x]
