# PS_Calc — Current State (Handoff)

_Updated: Session J-plan, 2026-03-08. For use when switching Claude instances._

---

## What was completed this session

**Session J-plan — taxonomy research and doc structure only. No code was written.**

1. Full Bard/Dancer buff taxonomy confirmed from Hercules source (skill.c + status.c).
2. Key architectural finding: **val position mapping** — songs are applied via `sc_start4`
   so `sg->val1` (set in `skill_unitsetting`) becomes `SC->val2`; `sg->val2` becomes `SC->val3`.
   Confirmed from `skill_unit_onplace_timer` (skill.c:~14278). All songs follow this rule.
3. `docs/BARD_DANCER_SONGS.md` deleted and replaced by `docs/buffs/` (6 separate files).
4. Data model drafted (not implemented): `song_state` dict + `support_buffs` dict on `PlayerBuild`.

All confirmed formulas are in `docs/buffs/songs_dances.md` — do not re-research them.

---

## Entry point for next session

**The user will provide a list of all skills with buff/debuff effects.**

Use that list to fill in stubs in:
- `docs/buffs/support_buffs.md` — Priest/Knight/etc party-cast buffs
- `docs/buffs/weapon_endow.md` — TK_SEVENWIND level→element table + any missed endow
- `docs/buffs/stat_foods.md` — specific consumable SC keys + stacking rules
- `docs/buffs/ground_effects.md` — Volcano/Deluge/ViolentGale formulas + any missed

For each stub entry: one targeted grep in Hercules status.c or skill.c to confirm.
Update confidence level from [stub] to [confirmed] or [explore] as appropriate.

Once the full list is processed, proceed to implementation (see Implementation Order below).

---

## Implementation order for Party Buffs (Session J proper)

**Step 1 — Data model** (`core/models/build.py`):
Add `song_state: dict = field(default_factory=dict)` and
`support_buffs: dict = field(default_factory=dict)`.
Add save/load round-trip in `core/build_manager.py`.

**Step 2 — New StatusData fields** (`core/models/status.py`):
- `cast_time_reduction_pct: int = 0`
- `after_cast_delay_reduction_pct: int = 0`
- `sp_cost_reduction_pct: int = 0`

**Step 3 — StatusCalculator** (`core/calculators/status_calculator.py`):
Apply all song/support effects in the correct stat blocks:
- ASPD block: SC_ASSNCROS (scaffolded — wire `song_state`)
- HIT block: SC_HUMMING, support HIT buffs
- FLEE block: SC_WHISTLE val2 (FLEE) + val3×10 (FLEE2 / perfect dodge)
- CRI block: SC_FORTUNE
- MaxHP block: SC_APPLEIDUN
- MaxSP block: SC_SERVICEFORYU val2
- New fields: SC_POEMBRAGI → cast/ACD; SC_SERVICEFORYU val3 → sp_cost
- Base stat blocks: SC_BLESSING (STR/INT/DEX), SC_INCREASEAGI (AGI), SC_GLORIA (+30 LUK), etc.

**Step 4 — Pipeline step for WATK bonuses**:
SC_DRUMBATTLE and SC_NIBELUNGEN add flat WATK. Confirm pipeline position before implementing.
(Open design question #2 in `docs/buffs/README.md`.)

**Step 5 — GUI** (`gui/sections/passive_section.py` or new section):
Party Buffs sub-group in PassiveSection:
- Song caster panel: AGI, LUK, VIT, DEX, INT spinboxes (1–99) + MusLesson + DanceLesson (0–10)
- Per-song rows: checkbox + level spinbox (1–10) for each confirmed song/dance/ensemble
- Support buff rows: checkbox or level spinbox per confirmed buff

**Step 6 — derived_section** (`gui/sections/derived_section.py`):
New display rows for cast_time_reduction_pct, after_cast_delay_reduction_pct, sp_cost_reduction_pct.

---

## Confirmed song formulas (do not re-research)

Full detail in `docs/buffs/songs_dances.md`. Quick reference:

| SC | stat | SC val | formula (from skill_unitsetting, pre-RE) |
|----|------|--------|------------------------------------------|
| SC_ASSNCROS | ASPD | val2 | `(MusLesson/2 + 10 + lv + agi/10) * 10` |
| SC_WHISTLE | FLEE | val2 | `lv + agi/10 + MusLesson` |
| SC_WHISTLE | FLEE2 | val3×10 | `(lv+1)/2 + luk/10 + MusLesson` |
| SC_POEMBRAGI | cast% | val2 | `3*lv + dex/10 + 2*MusLesson` |
| SC_POEMBRAGI | ACD% | val3 | `(lv<10?3*lv:50) + int/5 + 2*MusLesson` |
| SC_APPLEIDUN | MaxHP% | val2 | `5 + 2*lv + vit/10 + MusLesson` |
| SC_HUMMING | HIT | val2 | `2*lv + dex/10 + DanceLesson` (no x2 in pre-RE) |
| SC_FORTUNE | CRI | val2 | `(10 + lv + luk/10 + DanceLesson) * 10` |
| SC_SERVICEFORYU | MaxSP% | val2 | `15 + lv + int/10 + DanceLesson/2` |
| SC_SERVICEFORYU | SP cost% | val3 | `20 + 3*lv + int/10 + DanceLesson/2` |
| SC_DRUMBATTLE | WATK | val2 | `(lv+1)*25` (ensemble, level only) |
| SC_DRUMBATTLE | DEF | val3 | `(lv+1)*2` (ensemble, level only) |
| SC_NIBELUNGEN | WATK | val2 | `(lv+2)*25` (ensemble, level only) |
| SC_SIEGFRIED | subele% | val2 | `55 + lv*5` all elements (ensemble) |

---

## Open design questions (answer before implementing)

1. **SC_SIEGFRIED** — elemental resistance on buffed player, feeds into `target.sub_ele` for incoming. Scope now or defer?
2. **SC_DRUMBATTLE / SC_NIBELUNGEN WATK** — where in BF_WEAPON pipeline? Before or after SkillRatio? Needs one pipeline grep.
3. **SC_ETERNALCHAOS** — zeroes enemy def2. Hostile debuff on target. Scope or defer?
4. **Stat foods** — stay in G46 Active Items spinboxes, or separate Foods sub-section once list confirmed?

---

## Active known bugs

None.

---

## Key files for next session

| File | Purpose |
|------|---------|
| `docs/buffs/README.md` | Data model design, interface points, open questions |
| `docs/buffs/songs_dances.md` | All confirmed song/dance/ensemble formulas |
| `docs/buffs/support_buffs.md` | Stubs to fill from user's skill list |
| `docs/buffs/weapon_endow.md` | Stubs to fill |
| `docs/buffs/stat_foods.md` | Stubs to fill |
| `docs/buffs/ground_effects.md` | Stubs to fill |
| `docs/aspd.md` | ASPD system reference (1000-scale, SC_ASSNCROS wiring) |
| `core/calculators/status_calculator.py` | Where song effects wire in |
| `gui/sections/passive_section.py` | Where song GUI goes |
| `core/models/build.py` | Where `song_state` / `support_buffs` dicts go |
| `core/models/status.py` | Where new StatusData fields go |
