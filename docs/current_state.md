# PS_Calc — Current State (Handoff)

_Updated: Post-GUI-BuffLvl, 2026-03-12. For use when switching Claude instances._

---

## What was completed in recent sessions

**Q2 (skill ratios + DefenseFix specials)**
- `MO_FINGEROFFENSIVE`, `MO_INVESTIGATE`, `AM_ACIDTERROR` added to `_BF_WEAPON_RATIOS`
- `KN_CHARGEATK`, `MC_CARTREVOLUTION`, `MO_EXTREMITYFIST`, `TK_JUMPKICK` implemented as
  special-case blocks in `SkillRatio.calculate()` (require `build.skill_params` at runtime)
- `_BF_WEAPON_PARAM_SKILLS` frozenset tracks these 4 skills
- `DefenseFix`: NK_IGNORE_DEF flag read from `build.skill_params`; `pdef=2` (damage×1×def/100)
  and `def1=0` paths confirmed and implemented
- `IMPLEMENTED_BF_WEAPON_SKILLS` = 38 (all non-deferred Q1+Q2 skills)
- Context-sensitive `skill_params` UI row in `CombatControlsSection`

**GUI-BuffLvl**
- All `has_lv=True` self buffs converted from checkbox+spinbox → label+`LevelWidget` combo
- Bidirectional spirit sphere sync: `MO_SPIRITBALL` spinbox ↔ `MO_FINGEROFFENSIVE` sphere
  dropdown, via `spirit_spheres_changed` signals and `set_spirit_spheres()` setters

**Active known bug**
- **G69**: `MO_EXTREMITYFIST` ratio formula in `skill_ratio.py:228` is **WRONG**.
  Current (placeholder): `min(100 + 100*(8 + sp//10), 60000)`
  Must re-read `battle.c:2197-2206` `#ifndef RENEWAL` before fixing.
  The correct formula is NOT a simple `8 + sp//10` progression — see Hercules source.
  Also: per roadmap note, this skill should **ignore DEF** (NK_IGNORE_DEF or similar);
  confirm from the same source block.

---

## Entry point for Q3

**Q3 = Ninja hybrid + Gunslinger + G69 fix. All in one session.**

### Step 0 — Fix G69 first (before adding new skills)

Re-read `battle.c:2197-2206` `#ifndef RENEWAL`. The formula block is short.
Fix `skill_ratio.py:225-229`. If the block also sets `NK_IGNORE_DEF` or similar flag,
add that to `_BF_WEAPON_PARAM_SKILLS` or handle inline as needed.

### Step 1 — Verify G55 (Shuriken type string)

`mastery_fix.py:76` checks `weapon.weapon_type == "Shuriken"`.
Grep `item_db.json` for `"Shuriken"` weapon_type entries to confirm the string matches.
If it doesn't match, fix mastery_fix.py before implementing NJ skill ratios.

### Step 2 — NJ_* BF_WEAPON ratios (battle.c `calc_skillratio` NJ_* cases)

Source to grep: `skill.c` `calc_skillratio`, then NJ_* cases.
Skills and what to expect:

| Constant | ID | Notes |
|---|---|---|
| NJ_SYURIKEN | 523 | thrown; likely level-linear |
| NJ_KUNAI | 524 | thrown |
| NJ_HUUMA | 525 | thrown |
| NJ_KASUMIKIRI | 528 | |
| NJ_KIRIKAGE | 530 | |
| NJ_ZENYNAGE | 526 | Zeny-based damage — special formula |
| NJ_ISSEN | 544 | HP-based damage — special formula, may need build.skill_params |

**NJ_ZENYNAGE and NJ_ISSEN**: both require runtime values (current zeny / current HP).
If they need `build.skill_params`, add them to `_BF_WEAPON_PARAM_SKILLS` and the
special-case block in `SkillRatio.calculate()`, similar to KN_CHARGEATK/MO_EXTREMITYFIST.
Add corresponding `skill_params` UI rows in `CombatControlsSection` if needed.

### Step 3 — NJ_* BF_MAGIC ratios (skill.c `calc_skillratio` NJ_* cases)

| Constant | ID | Notes |
|---|---|---|
| NJ_KOUENKA | 534 | fire |
| NJ_KAENSIN | 535 | ground fire; may be complex |
| NJ_BAKUENRYU | 536 | |
| NJ_HYOUSENSOU | 537 | |
| NJ_HYOUSYOURAKU | 539 | |
| NJ_RAIGEKISAI | 541 | |
| NJ_KAMAITACHI | 542 | |

Add to `_BF_MAGIC_RATIOS` in `skill_ratio.py`. Use the same pattern as existing magic
ratios — lambda `(lv, tgt)` or special-case block.

### Step 4 — GS_* BF_WEAPON ratios (skill.c `calc_skillratio` GS_* cases)

| Constant | ID | Notes |
|---|---|---|
| GS_TRIPLEACTION | 502 | |
| GS_BULLSEYE | 503 | |
| GS_TRACKING | 512 | |
| GS_PIERCINGSHOT | 514 | |
| GS_RAPIDSHOWER | 515 | |
| GS_DESPERADO | 516 | |
| GS_DUST | 518 | |
| GS_FULLBUSTER | 519 | |
| GS_SPREADATTACK | 520 | |
| GS_FLING | 501 | DEF reduction + special damage — may need special casing |

**GS_FLING**: check if it reduces target DEF (similar to MO_INVESTIGATE pdef=2 path).
May need `build.skill_params` if it requires runtime context.

### Step 5 — GS_MAGICALBULLET (BF_MAGIC)

Add to `_BF_MAGIC_RATIOS`. Only gunslinger magic skill.

### Step 6 — BF_MISC scaffold (per roadmap)

After NJ/GS ratios are done, add to `skill_ratio.py`:
```python
_BF_MISC_RATIOS: dict = {}  # deferred — see session_roadmap.md Q3 notes
IMPLEMENTED_BF_MISC_SKILLS: frozenset = frozenset(_BF_MISC_RATIOS.keys())
```
Then add `IMPLEMENTED_BF_MISC_SKILLS` to `_IMPLEMENTED_SKILLS` in both:
- `gui/sections/combat_controls.py`
- `gui/dialogs/skill_browser.py`

### Step 7 — EOS docs maintenance

- `docs/gaps.md`: mark G63 [x], G69 [x], G55 [x]
- `docs/completed_work.md`: append Q3 section
- `docs/session_roadmap.md`: move Q3 to Completed, review Q4 scope

---

## Key files for Q3

| File | Purpose |
|---|---|
| `core/calculators/modifiers/skill_ratio.py` | All ratio changes go here |
| `Hercules/src/map/skill.c` | Primary source for NJ_*/GS_* ratio cases (`calc_skillratio`) |
| `Hercules/src/map/battle.c` | G69 fix source (line 2197-2206); also GS_FLING if special |
| `core/calculators/modifiers/mastery_fix.py` | G55 Shuriken type string check |
| `core/data/pre-re/db/item_db.json` | G55 verification grep target |
| `gui/sections/combat_controls.py` | skill_params UI rows (if NJ_ISSEN/NJ_ZENYNAGE need them) |
| `docs/session_roadmap.md` | Q3 full skill table + BF_MISC scaffold note |

---

## Architecture reminders

- NJ_* in `_BF_WEAPON_RATIOS` uses `lambda lv, tgt: ...` (same as all other weapon ratios)
- NJ_* in `_BF_MAGIC_RATIOS` uses `lambda lv, tgt: ...` (same as HW_*/WZ_* magic ratios)
- Runtime-context skills (zeny/HP/dist) go in `_BF_WEAPON_PARAM_SKILLS` and the
  special-case block above `_BF_WEAPON_RATIOS` dict lookup in `SkillRatio.calculate()`
- `IMPLEMENTED_BF_WEAPON_SKILLS = frozenset(_BF_WEAPON_RATIOS.keys()) | _BF_WEAPON_PARAM_SKILLS`
  is auto-derived — no manual update needed when adding to the dict or frozenset
- `IMPLEMENTED_BF_MAGIC_SKILLS` similarly auto-derived from `_BF_MAGIC_RATIOS`
- Hercules guard: NJ/GS skills are `#ifndef RENEWAL` (pre-re only) or no guard — always check

---

## Open gaps relevant to Q3

| Gap | Status | Description |
|---|---|---|
| G63 | [ ] | NJ_* + GS_* skill ratios (main Q3 work) |
| G69 | [ ] | MO_EXTREMITYFIST formula wrong in skill_ratio.py:228 — fix first |
| G55 | [ ] | NJ_TOBIDOUGU "Shuriken" weapon_type string unverified |
