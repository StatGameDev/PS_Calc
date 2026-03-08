# PS_Calc — Party Buff System Index

_Last updated: Session J planning. Sources: Hercules/src/map/status.c, skill.c._

> **Categorization notice**: The current split into six categories reflects the information
> available at time of writing. Once the full skill list with buff/debuff effects is
> provided and researched, categories may be merged, split, or renamed if a better
> grouping emerges. Treat this structure as a working draft.

---

## Documents in this folder

| File | Category | Status |
|------|----------|--------|
| [songs_dances.md](songs_dances.md) | Bard/Dancer songs, dances, ensembles (BA_*, DC_*, BD_*) | Formulas confirmed |
| [support_buffs.md](support_buffs.md) | Priest / Knight / Sage / other party-cast stat buffs | Stubs — awaiting skill list |
| [weapon_endow.md](weapon_endow.md) | Weapon element assignment skills (SA_*, PR_ASPERSIO, AS_*, TK_*) | Partially confirmed |
| [stat_foods.md](stat_foods.md) | Consumable item stat bonuses (SC_FOOD_*, SC_INC*) | Stubs — awaiting skill list |
| [ground_effects.md](ground_effects.md) | Ground / zone AoE skill effects (Volcano, Deluge, etc.) | Stubs — awaiting skill list |

---

## Confidence levels used in these documents

- **[confirmed]** — Formula read directly from Hercules source in this session; line cited.
- **[explore]** — Found by Explore agent with line reference; not hand-verified. Verify before implementing.
- **[stub]** — Placeholder entry; formula not yet researched.

---

## Data model design (working)

Two new dicts on `PlayerBuild` (not yet implemented):

### `song_state: dict`
Covers all Bard/Dancer inputs — shared caster stats, lesson passives, per-song level.
```python
{
  # Shared caster stats (only relevant ones — all 5 needed by at least one song)
  "caster_agi": 1, "caster_luk": 1, "caster_vit": 1,
  "caster_dex": 1, "caster_int": 1,
  "mus_lesson": 0,     # BA_MUSICALLESSON caster level
  "dance_lesson": 0,   # DC_DANCINGLESSON caster level
  # Per-song: 0 = disabled, 1–10 = active at that song level
  "SC_ASSNCROS":    0, "SC_WHISTLE":      0,
  "SC_POEMBRAGI":   0, "SC_APPLEIDUN":    0,
  "SC_HUMMING":     0, "SC_FORTUNE":      0,
  "SC_SERVICEFORYU":0,
  # Ensembles (level only — no caster stats)
  "SC_DRUMBATTLE":  0, "SC_NIBELUNGEN":   0, "SC_SIEGFRIED":    0,
}
```

### `support_buffs: dict`
Covers all other received external buffs — priest buffs, endow, ground effects.
```python
{
  # Priest/support (level → formula → flat stat bonus)
  "SC_BLESSING":     0,     # level 0–10
  "SC_INCREASEAGI":  0,     # level 0–10
  "SC_GLORIA":       False, # bool; +30 LUK flat
  "SC_ANGELUS":      0,     # level 0–10; DEF% bonus
  # Weapon element endow (mutually exclusive; overrides item element)
  "endow_element":   None,  # int 0–9 or None
  # Ground effects (bool toggles)
  "SC_VOLCANO":      False,
  "SC_DELUGE":       False,
  "SC_VIOLENTGALE":  False,
  # ... extended once full skill list is processed
}
```
Stat foods continue to live in `active_items_bonuses` (G46 catch-all) as flat per-stat
spinboxes. If a dedicated Foods section turns out to be preferable, it can be split out.

---

## Interface points with the pipeline (summary)

| Buff | Stat modified | Pipeline / calculator location |
|------|--------------|-------------------------------|
| SC_ASSNCROS | ASPD (amotion) | `status_calculator.py` ASPD block — scaffolded |
| SC_WHISTLE | FLEE, FLEE2 | `status_calculator.py` — not started |
| SC_HUMMING | HIT | `status_calculator.py` — not started |
| SC_APPLEIDUN | MaxHP | `status_calculator.py` — not started |
| SC_FORTUNE | CRI | `status_calculator.py` — not started |
| SC_SERVICEFORYU | MaxSP, SP cost | `status_calculator.py` — not started |
| SC_POEMBRAGI | Cast time, ACD | New `StatusData` fields — not started |
| SC_DRUMBATTLE | WATK, DEF | `base_damage.py` new step or `BaseDamage` — TBD |
| SC_NIBELUNGEN | WATK | same as above |
| SC_SIEGFRIED | `sub_ele` (all) | `target.sub_ele` / incoming pipeline — TBD |
| SC_BLESSING | STR, INT, DEX | `status_calculator.py` stat block — not started |
| SC_INCREASEAGI | AGI | `status_calculator.py` stat block — not started |
| SC_GLORIA | LUK | `status_calculator.py` stat block — not started |
| SC_ANGELUS | DEF% | `status_calculator.py` DEF block — not started |
| endow_element | weapon element | `PlayerBuild.weapon_element` field (exists) — needs UI |
| SC_VOLCANO | WATK | `base_damage.py` — not started |
| SC_DELUGE | MaxHP% | `status_calculator.py` — not started |
| SC_VIOLENTGALE | FLEE | `status_calculator.py` — not started |

---

## Open design questions

1. **SC_DRUMBATTLE / SC_NIBELUNGEN WATK**: flat WATK bonus applied before or after
   SkillRatio? Needs Hercules pipeline trace before implementing.

2. **SC_SIEGFRIED**: elemental resistance on the *buffed player* — feeds into
   `target.sub_ele` for incoming damage. Scope now or defer?

3. **SC_ETERNALCHAOS**: zeroes enemy soft DEF (def2=0). Offensive field effect,
   applies to target not player. Scope or defer?

4. **Stat foods vs Active Items (G46)**: keep foods in G46 spinboxes, or add a
   dedicated "Foods" sub-section once the full food SC list is confirmed?
