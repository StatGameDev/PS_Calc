# PS_Calc — Bard/Dancer Songs, Dances & Ensembles

_Sources: Hercules/src/map/skill.c (skill_unitsetting ~13072, sc_start4 ~14278), status.c_
_All formulas confirmed [confirmed] by direct Hercules source read unless marked otherwise._

---

## Skill Categories

### Solo Songs — BA_* (Bard only)
`skill_info: ["Song", "BlockedByStasis"]`
Unit flags: `UF_NOMOB + UF_SONG + UF_DUALMODE` (buff songs)

### Solo Dances — DC_* (Dancer only)
`skill_info: ["Song", "BlockedByStasis"]` — "Song" tag is shared; distinction is UF_SONG vs UF_DANCE.
Unit flags: `UF_NOMOB + UF_DANCE + UF_DUALMODE` (buff dances)

### Ensembles — BD_* (Bard + Dancer together)
`skill_info: ["Ensemble"]`
Unit flags: `UF_ENSEMBLE` (± UF_NOMOB, UF_NOPC depending on skill).
No caster-stat formulas — effect is purely level-dependent.

---

## Critical: val position mapping

Songs are applied to targets via `sc_start4` in `skill_unit_onplace_timer` (skill.c:~14278):

```c
sc_start4(src, bl, type, 100, sg->skill_lv, sg->val1, sg->val2, 0, sg->limit, skill_id);
//                              ^^^^^^^^^^^  ^^^^^^^^  ^^^^^^^^
//                              SC->val1     SC->val2  SC->val3
```

`skill_unitsetting` stores results in `sg->val1` / `sg->val2`. These become SC->val2 / SC->val3
when the SC is applied. SC->val1 is always the song level.

**Rule: formula result stored as `val1` in skill_unitsetting → lands in `SC->val2` in status.c.**

---

## Passive skill levels (caster's own)

- `BA_MUSICALLESSON` (315) — affects all Bard song formulas
- `DC_DANCINGLESSON` (323) — affects all Dancer dance formulas

Both are queried via `pc->checkskill(sd, BA_MUSICALLESSON)` in `skill_unitsetting`.
These are the **caster's** levels, stored separately from the receiving player's own mastery.

---

## Soul Link (SL_BARDDANCER)

Allows a Bard to use paired Dancer skills and vice versa, provided that specific song
is at max level. No formula difference — caster's own stats drive the formula regardless.
Not modelled in the calculation engine; document as a GUI note.

---

## Solo Song Buff Reference — BA_*

### BA_ASSASSINCROSS (320) → SC_ASSNCROS [confirmed]

**Caster stats**: AGI, BA_MUSICALLESSON
**skill_unitsetting** (skill.c:13296–13307, `#else` pre-renewal block):
```c
val1 = pc->checkskill(sd, BA_MUSICALLESSON) / 2;
val1 += 10 + skill_lv + (bard_st->agi / 10);
val1 *= 10;  // scale to 1000 = 100%
```
**SC val**: SC->val2 = formula result above
**Applied in**: `status_calc_aspd_rate` (status.c)
**Effect**: ASPD increase — competes with other quicken SCs via `max()`, 1000-scale
**Weapon restriction** [confirmed] (status.c:5467–5483): NOT applied to W_BOW, W_REVOLVER,
W_RIFLE, W_GATLING, W_SHOTGUN, W_GRENADE.
**Example**: song_lv=10, MusLesson=10, caster_agi=99 → (5+10+10+9)*10 = 340 (34% ASPD)
**See also**: `docs/aspd.md` for full ASPD system + 1000-scale explanation

---

### BA_WHISTLE (319) → SC_WHISTLE [confirmed]

**Caster stats**: AGI, LUK, BA_MUSICALLESSON
**skill_unitsetting** (skill.c:13245–13251):
```c
val1 = skill_lv + st->agi/10;           // FLEE increase  → SC->val2
val2 = ((skill_lv+1)/2) + st->luk/10;  // FLEE2 increase → SC->val3
if (sd) {
    val1 += pc->checkskill(sd, BA_MUSICALLESSON);
    val2 += pc->checkskill(sd, BA_MUSICALLESSON);
}
```
**Applied in** (status.c):
- `flee  += sc->data[SC_WHISTLE]->val2` (~line 4866)
- `flee2 += sc->data[SC_WHISTLE]->val3 * 10` (~line 4952)  ← *perfect dodge; ×10 scale*

---

### BA_POEMBRAGI (321) → SC_POEMBRAGI [confirmed]

**Caster stats**: DEX, INT, BA_MUSICALLESSON
**skill_unitsetting** (skill.c:13261–13267):
```c
val1 = 3*skill_lv + st->dex/10;                           // cast time % → SC->val2
val2 = (skill_lv < 10 ? 3*skill_lv : 50) + st->int_/5;  // ACD %       → SC->val3
if (sd) {
    val1 += 2 * pc->checkskill(sd, BA_MUSICALLESSON);
    val2 += 2 * pc->checkskill(sd, BA_MUSICALLESSON);
}
```
**Applied in** (skill.c):
- Cast time:     `time -= time * sc->data[SC_POEMBRAGI]->val2 / 100` (line ~17253)
- After-cast delay: `time -= time * sc->data[SC_POEMBRAGI]->val3 / 100` (line ~17486)
**StatusData fields needed**: `cast_time_reduction_pct`, `after_cast_delay_reduction_pct`
**Note**: cast/ACD reduction are display-only stats for this calculator (no action speed sim).

---

### BA_APPLEIDUN (322) → SC_APPLEIDUN [confirmed]

**Caster stats**: VIT, BA_MUSICALLESSON
**skill_unitsetting** (skill.c:13283–13286):
```c
val1 = 5 + 2*skill_lv + st->vit/10;  // MaxHP % → SC->val2
if (sd)
    val1 += pc->checkskill(sd, BA_MUSICALLESSON);
```
**Applied in** (status.c:5766–5767):
```c
maxhp += maxhp * sc->data[SC_APPLEIDUN]->val2 / 100;
```

---

## Solo Dance Buff Reference — DC_*

### DC_HUMMING (327) → SC_HUMMING [confirmed]

**Caster stats**: DEX, DC_DANCINGLESSON
**skill_unitsetting** (skill.c:13253–13260):
```c
val1 = 2*skill_lv + st->dex/10;  // HIT increase → SC->val2
// #ifdef RENEWAL: val1 *= 2;  ← PRE-RENEWAL: no doubling
if (sd)
    val1 += pc->checkskill(sd, DC_DANCINGLESSON);
```
**Applied in** (status.c:~4803–4804):
```c
hit += sc->data[SC_HUMMING]->val2;
```

---

### DC_FORTUNEKISS (329) → SC_FORTUNE [confirmed]

**Caster stats**: LUK, DC_DANCINGLESSON
**skill_unitsetting** (skill.c:13309–13313):
```c
val1 = 10 + skill_lv + (st->luk/10);
if (sd)
    val1 += pc->checkskill(sd, DC_DANCINGLESSON);
val1 *= 10;  // crit uses 10× scale → SC->val2
```
**Applied in** (status.c:~4755–4756):
```c
critical += sc->data[SC_FORTUNE]->val2;
```
**Note**: `critical` is in 10× scale (same as rest of crit system; 100 = 10 crit points).

---

### DC_SERVICEFORYOU (330) → SC_SERVICEFORYU [confirmed]

**Caster stats**: INT, DC_DANCINGLESSON
**skill_unitsetting** (skill.c:13288–13294):
```c
val1 = 15 + skill_lv + (st->int_/10);         // MaxSP %         → SC->val2
val2 = 20 + 3*skill_lv + (st->int_/10);       // SP cost reduc % → SC->val3
if (sd) {
    val1 += pc->checkskill(sd, DC_DANCINGLESSON) / 2;
    val2 += pc->checkskill(sd, DC_DANCINGLESSON) / 2;
}
```
**Applied in** (status.c:~5847–5848):
```c
maxsp += maxsp * sc->data[SC_SERVICEFORYOU]->val2 / 100;
```
**SP cost reduction** (val3): applied in skill cast cost checks — display-only for this calculator.
**StatusData field needed**: `sp_cost_reduction_pct`

---

## Hostile Solo Songs/Dances (debuffs — not player buffs)

### DC_DONTFORGETME (328) → SC_DONTFORGETME [confirmed]

Hostile. Applied to enemies in the dance area. Pre-renewal formula (skill.c:13270–13281):
```c
// #else (pre-renewal):
val1 = st->dex/10 + 3*skill_lv + 5 + DC_DANCINGLESSON;  // ASPD penalty → SC->val2
val2 = st->agi/10 + 3*skill_lv + 5 + DC_DANCINGLESSON;  // move penalty → SC->val3
```
**Applied in** (status.c): `aspd_rate += 10 * SC_DONTFORGETME->val2` (ASPD slows target).
Not a player buff. Relevant if implementing mob ASPD (out of scope for now).

### BA_DISSONANCE (317) → SC_DISSONANCE, DC_UGLYDANCE (325) → SC_UGLYDANCE
Hostile area effects. Not player buffs. Out of scope.

---

## Ensemble Reference — BD_*

Ensembles require Bard + Dancer adjacent at cast time. No caster-stat formulas.
All effects are `#else` (pre-renewal) unless noted.

### BD_DRUMBATTLEFIELD (309) → SC_DRUMBATTLE [confirmed]

**skill_unitsetting** (skill.c:13315–13321, `#else` block):
```c
val1 = (skill_lv+1)*25;  // WATK increase → SC->val2
val2 = (skill_lv+1)*2;   // DEF increase  → SC->val3
```
**Applied in** (status.c):
- `watk += sc->data[SC_DRUMBATTLE]->val2` (~line 4564)
- `def  += sc->data[SC_DRUMBATTLE]->val3` (~line 4999)
**Note**: requires party membership check at SC start (status.c:7156–7158).

---

### BD_RINGNIBELUNGEN (310) → SC_NIBELUNGEN [confirmed]

**skill_unitsetting** (skill.c:13324–13325):
```c
val1 = (skill_lv+2)*25;  // WATK increase → SC->val2
```
**Applied in** (status.c:~4589–4596): `watk += SC_NIBELUNGEN->val2`
(Conditional on weapon upgrade level — exact condition TBD, needs verify.)

---

### BD_SIEGFRIED (313) → SC_SIEGFRIED [confirmed]

**skill_unitsetting** (skill.c:13330):
```c
val1 = 55 + skill_lv*5;  // elemental resistance % → SC->val2
val2 = skill_lv*10;       // status ailment resist % → SC->val3
```
**Applied in** (status.c:~2233–2244): adds `SC->val2` to `sd->subele[*]` for ALL elements.
**Effect on calc**: reduces incoming elemental damage on the buffed player.
**Implementation note**: feeds into `target.sub_ele` in incoming-damage scenarios.

---

### BD_RICHMANKIM (307) → SC_RICHMANKIM
EXP bonus only (`val1 = 25 + 11*skill_lv`). Not relevant to damage calculation.

### BD_INTOABYSS (312) → SC_INTOABYSS
No stat effect found in status.c (only a party membership check). Out of scope.

### BD_LULLABY (306)
Causes sleep on enemies. Hostile AoE, not a player buff. Out of scope.

### BD_ETERNALCHAOS (308) → SC_ETERNALCHAOS [confirmed]
Sets target's `def2 = 0` (removes VIT soft DEF). Hostile AoE applied to enemies.
Relevant only if implementing enemy-debuff state — deferred.

### BD_ROKISWEIL (311) → SC_ROKISWEIL
Prevents skill use by targets in the area. No stat modification. Out of scope.

---

## Caster inputs required — summary

| Stat | Used by |
|------|---------|
| AGI | SC_ASSNCROS, SC_WHISTLE |
| LUK | SC_WHISTLE, SC_FORTUNE |
| VIT | SC_APPLEIDUN |
| DEX | SC_HUMMING, SC_POEMBRAGI |
| INT | SC_POEMBRAGI, SC_SERVICEFORYU |
| BA_MUSICALLESSON | SC_ASSNCROS, SC_WHISTLE, SC_POEMBRAGI, SC_APPLEIDUN |
| DC_DANCINGLESSON | SC_HUMMING, SC_FORTUNE, SC_SERVICEFORYU |

All 5 base stats are needed. Minimum GUI panel: 5 stat spinboxes + 2 lesson spinboxes.

---

## Implementation status

| SC | Formula | Calculator | GUI |
|----|---------|-----------|-----|
| SC_ASSNCROS | confirmed | scaffolded (does nothing) | checkbox exists in passive_section |
| SC_WHISTLE | confirmed | not started | — |
| SC_POEMBRAGI | confirmed | not started | — |
| SC_APPLEIDUN | confirmed | not started | — |
| SC_HUMMING | confirmed | not started | — |
| SC_FORTUNE | confirmed | not started | — |
| SC_SERVICEFORYU | confirmed | not started | — |
| SC_DRUMBATTLE | confirmed | not started | — |
| SC_NIBELUNGEN | confirmed (partial) | not started | — |
| SC_SIEGFRIED | confirmed | not started | — |
