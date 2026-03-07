# PS_Calc — Bard/Dancer Songs Reference

_Sources: Hercules/src/map/status.c, skill.c; core/data/pre-re/db/skills.json_

---

## Skill Categories

Bard/Dancer skills fall into three distinct categories, identifiable by `skill_info` and unit `flag`:

### 1. Solo Songs (BA_*) — Bard only
`skill_info: ["Song", "BlockedByStasis"]`
Unit flags: `UF_NOMOB + UF_SONG + UF_DUALMODE` (buff songs) or `UF_SONG` only (hostile songs)
`weapon_types: ["Instruments", "Whips"]`

| ID  | Name               | Description        | SC               | Target | Unit Flags                         |
|-----|--------------------|--------------------|------------------|--------|------------------------------------|
| 317 | BA_DISSONANCE      | Dissonance         | SC_DISSONANCE    | Enemy  | UF_SONG                            |
| 319 | BA_WHISTLE         | Perfect Tablature  | SC_WHISTLE       | All    | UF_NOMOB, UF_SONG, UF_DUALMODE     |
| 320 | BA_ASSASSINCROSS   | Impressive Riff    | SC_ASSNCROS      | All    | UF_NOMOB, UF_SONG, UF_DUALMODE     |
| 321 | BA_POEMBRAGI       | Magic Strings      | SC_POEMBRAGI     | All    | UF_NOMOB, UF_SONG, UF_DUALMODE     |
| 322 | BA_APPLEIDUN       | Apple of Idun      | SC_APPLEIDUN     | All    | UF_NOMOB, UF_SONG, UF_DUALMODE     |

Non-song BA_* skills (passive/offensive, not party buffs):
- BA_MUSICALLESSON (315) — passive, affects all Bard song formula values
- BA_MUSICALSTRIKE (316) — offensive
- BA_FROSTJOKE (318) — status skill

### 2. Solo Dances (DC_*) — Dancer only
`skill_info: ["Song", "BlockedByStasis"]` — note: "Song" in skills.json `skill_info` is used for both songs AND dances; the UF_SONG vs UF_DANCE distinction only appears at the unit level.
Unit flags: `UF_NOMOB + UF_DANCE + UF_DUALMODE` (buff dances) or `UF_DANCE + UF_DUALMODE` (hostile dances)
`weapon_types: ["Instruments", "Whips"]`

| ID  | Name               | Description        | SC               | Target | Unit Flags                         |
|-----|--------------------|--------------------|------------------|--------|------------------------------------|
| 327 | DC_HUMMING         | Focus Ballet       | SC_HUMMING       | All    | UF_NOMOB, UF_DANCE, UF_DUALMODE    |
| 328 | DC_DONTFORGETME    | Slow Grace         | SC_DONTFORGETME  | Enemy  | UF_DANCE, UF_DUALMODE              |
| 329 | DC_FORTUNEKISS     | Fortune's Kiss     | SC_FORTUNE       | All    | UF_NOMOB, UF_DANCE, UF_DUALMODE    |
| 330 | DC_SERVICEFORYOU   | Service for You    | SC_SERVICEFORYU  | All    | UF_NOMOB, UF_DANCE, UF_DUALMODE    |

Non-dance DC_* skills:
- DC_DANCINGLESSON (323) — passive, affects all Dancer dance formula values
- DC_THROWARROW (324) — offensive
- DC_UGLYDANCE (325) — status skill
- DC_SCREAM (326) — status skill

### 3. Ensembles (BD_*) — Bard + Dancer together
`skill_info: ["Ensemble"]`
Unit flags: `UF_ENSEMBLE` (± UF_NOMOB, UF_NOPC depending on skill)
`weapon_types: ["Instruments", "Whips"]` — both classes required adjacent at cast time.

All Ensemble skills are in scope for the calculator. Deeper effect research is deferred
until party buffs are being actively implemented.

| ID  | Name               | Description        | SC               | Target | Interval |
|-----|--------------------|--------------------|------------------|--------|----------|
| 306 | BD_LULLABY         | Lullaby            | —                | Enemy  | 6000     |
| 307 | BD_RICHMANKIM      | Mental Sensing     | SC_RICHMANKIM    | —      | —        |
| 308 | BD_ETERNALCHAOS    | Eternal Chaos      | —                | Enemy  | -1       |
| 309 | BD_DRUMBATTLEFIELD | Battle Theme       | —                | Party  | -1       |
| 310 | BD_RINGNIBELUNGEN  | Ring of Nibelungen | —                | Party  | -1       |
| 311 | BD_ROKISWEIL       | Roki's Scream      | —                | All    | -1       |
| 312 | BD_INTOABYSS       | Into the Abyss     | —                | Party  | -1       |
| 313 | BD_SIEGFRIED       | Marionette Control | —                | Party  | -1       |

Utility BD_* skills (not ensemble songs):
- BD_ADAPTATION (304) — "Amp", cancels current song/dance
- BD_ENCORE (305) — "Encore", SC_DANCING, replays last song/dance

---

## Soul Link (SL_BARDDANCER)

Soul Link allows a Bard to use paired Dancer songs (and vice versa), provided they
have that specific song skill at max level. No functional difference for the calculator:
the caster's own stats drive the formula regardless of class.

Does not need to be modelled in the calculation engine. Document in the GUI as a note
next to song buffs that apply cross-class (e.g. a Bard may have DC_HUMMING active via
Soul Link).

---

## Unit Field Meanings (from skills.json)

- `unit.layout` — radius of the skill area. Layout 3 = 7×7 cells (r=3), Layout 4 = 9×9 cells (r=4).
- `unit.interval` — ms between periodic ticks. -1 = no tick (effect applied on enter/leave only). 3000 = every 3s.
- `unit.target` — who can receive the effect: All / Enemy / Party.
- `skill_data1` — song area duration in ms. All buff solo songs: 120000 (2 min).
- `skill_data2` — aftercast buff duration in ms (SC lingers after leaving the area). All buff solo songs: 20000 (20 s).

---

## UF_* Flag Meanings

- `UF_SONG` — marks the unit as a Bard song. Used by the engine to detect song state on the Bard.
- `UF_DANCE` — marks the unit as a Dancer dance. Used by the engine to detect dance state on the Dancer.
- `UF_ENSEMBLE` — requires Bard+Dancer adjacent at cast time.
- `UF_DUALMODE` — SC applied on area-enter, removed on area-exit. Present on all buff songs/dances.
- `UF_NOMOB` — mobs cannot receive the buff (limits "All" target to players only).

---

## Party Buff Scope — Solo Song IDs

All solo Bard songs and Dancer dances are in scope for the Party Buffs UI section.
The caster's relevant stats (AGI, DEX, VIT, INT, LUK) and skill levels drive the
formula; the calculator needs a "song caster" stat input panel, not a class distinction.

**Known buff song IDs (to be expanded by user):**

| ID  | Skill              | Caster stat(s) used  | Passive level used     |
|-----|--------------------|----------------------|------------------------|
| 319 | BA_WHISTLE         | AGI, LUK             | BA_MUSICALLESSON       |
| 320 | BA_ASSASSINCROSS   | AGI                  | BA_MUSICALLESSON       |
| 321 | BA_POEMBRAGI       | DEX, INT             | BA_MUSICALLESSON       |
| 322 | BA_APPLEIDUN       | VIT                  | BA_MUSICALLESSON       |
| 327 | DC_HUMMING         | DEX (unconfirmed)    | DC_DANCINGLESSON       |
| 329 | DC_FORTUNEKISS     | LUK                  | DC_DANCINGLESSON       |
| 330 | DC_SERVICEFORYOU   | INT                  | DC_DANCINGLESSON       |

_User to append additional song IDs here as needed._

---

## Confirmed Song SC Formulas (pre-renewal)

All formulas computed at **cast time** from the caster's stats. The SC value is fixed
for the duration of that song instance regardless of who steps into the area.

Source: `skill_unitsetting` (skill.c:13072).

### BA_ASSASSINCROSS → SC_ASSNCROS (ASPD)

```
val1 = (BA_MUSICALLESSON_lv / 2) + 10 + song_lv + (caster_agi / 10)
val1 *= 10    # scale to 1000 = 100%
```
→ `SC_ASSNCROS.val2 = val1` (applied via `skill_unit_onplace_timer` line 14277)

Applied in `status_calc_aspd_rate`: `aspd_rate -= val2; amotion = amotion * aspd_rate / 1000`

Weapon restriction (status.c:5638): NOT applied to W_BOW, W_REVOLVER, W_RIFLE,
W_GATLING, W_SHOTGUN, W_GRENADE.

Example: song_lv=10, BA_MUSICALLESSON=10, caster_agi=99 → val2 = 340 (34% ASPD increase).

### BA_POEMBRAGI → SC_POEMBRAGI (cast time / after-cast delay reduction)

```
val1 = 3*song_lv + caster_dex/10                              # cast time % reduction
val2 = (song_lv < 10 ? 3*song_lv : 50) + caster_int/5        # after-cast delay % reduction
val1 += 2 * BA_MUSICALLESSON_lv
val2 += 2 * BA_MUSICALLESSON_lv
```

### BA_APPLEIDUN → SC_APPLEIDUN (MaxHP % bonus)

```
val1 = 5 + 2*song_lv + caster_vit/10
val1 += BA_MUSICALLESSON_lv
```
MaxHP bonus = val1 %.

### DC_DONTFORGETME → SC_DONTFORGETME (ASPD/move speed penalty, hostile)

```
val1 = caster_dex/10 + 3*song_lv + 5    # ASPD penalty (aspd_rate += 10*val2 in calc_aspd_rate)
val2 = caster_agi/10 + 3*song_lv + 5    # movement speed penalty
val1 += DC_DANCINGLESSON_lv
val2 += DC_DANCINGLESSON_lv
```

### DC_FORTUNEKISS → SC_FORTUNE (CRI bonus)

```
val1 = (10 + song_lv + caster_luk/10)
val1 += DC_DANCINGLESSON_lv
val1 *= 10    # crit uses 10× scale
```

### DC_SERVICEFORYOU → SC_SERVICEFORYU (MaxSP % / SP cost reduction)

```
val1 = 15 + song_lv + caster_int/10     # MaxSP % increase
val2 = 20 + 3*song_lv + caster_int/10  # SP cost % reduction
val1 += DC_DANCINGLESSON_lv / 2
val2 += DC_DANCINGLESSON_lv / 2
```

### BA_WHISTLE → SC_WHISTLE (HIT/FLEE bonus)
_Formula not yet read from Hercules source. Needs grep before implementation._

### DC_HUMMING → SC_HUMMING (HIT bonus)
_Formula not yet read from Hercules source. Needs grep before implementation._
