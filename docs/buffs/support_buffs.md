# PS_Calc — Support / Party-Cast Stat Buffs

_Sources: Hercules/src/map/status.c, skill.c_
_Confidence: [confirmed] = directly read; [explore] = Explore agent finding, verify before implementing; [stub] = not yet researched_

> **Stub notice**: Most entries here are placeholders based on the Explore agent pass.
> Formulas marked [explore] need a direct Hercules grep before implementation.
> This document will be expanded once the full skill buff list is provided.

---

## Priest / Acolyte Buffs

### AL_BLESSING → SC_BLESSING [explore]

**Effect**: +val1 to STR, INT, DEX (all three simultaneously)
**Formula**: `val1 = skill_lv` (max lv 10)
**Hercules ref**: status.c ~line 3964 (stat application), skill.c ~line 7333 (SC start)
**Note**: on Undead/Demon *mobs* the bonus is halved; on PCs it is always full.
This calculator targets PCs as attackers, so always apply full value.
**Caster stats needed**: none — level only.
**Inputs needed**: level spinbox (0–10)

---

### AL_INCREASEAGI → SC_INCREASEAGI [stub]

**Effect**: +val to AGI
**Formula**: _needs grep_
**Hercules ref**: status.c stat section
**Inputs needed**: level spinbox (0–10)

---

### PR_GLORIA → SC_GLORIA [explore]

**Effect**: +30 LUK flat (unconditional, no level scaling)
**Formula**: `luk += 30` (status.c:~4273–4274)
**Inputs needed**: checkbox (on/off)

---

### PR_ANGELUS → SC_ANGELUS [explore]

**Effect**: DEF% increase
**Formula**: `val2 = 5 * skill_lv` (% bonus to DEF) — status.c ~line 8320–8321
**Inputs needed**: level spinbox (0–10)
**Note**: This affects hard DEF (equipment DEF). Application point in DefenseFix TBD.

---

### PR_MAGNIFICAT → SC_MAGNIFICAT [explore]

**Effect**: SP regen ×2
**Hercules ref**: status.c ~line 2854–2856
**Damage relevance**: none — not relevant to this calculator. Out of scope.

---

### PR_IMPOSITIO → SC_IMPOSITIO [confirmed — already implemented]

**Effect**: flat WATK bonus
**Formula**: `val2 = 5 * skill_lv`
**Status**: implemented in `core/calculators/modifiers/base_damage.py` (Session A, G1)

---

## Knight / Crusader Buffs

### LK_CONCENTRATION / CR_CONCENTRATION → SC_CONCENTRATION [explore]

**Effect**: DEX and AGI bonus (% of base stat, excluding equipment bonuses)
**Formula**: `dex += (dex - val4) * val2 / 100; agi += (agi - val3) * val2 / 100`
where `val2 = 2 + skill_lv`, val3/val4 = card/equipment bonuses at buff time.
**Hercules ref**: status.c ~4195–4196, 4007–4008
**Inputs needed**: level spinbox (0–10)
**Note**: complex — requires knowing equipment bonuses at buff time. May need simplification.

---

## Sage / Scholar Buffs

### SA_VOLCANO / SA_DELUGE / SA_VIOLENTGALE
Ground effects — see [ground_effects.md](ground_effects.md).

---

## Other Known Party Buffs — Stubs

The following are known to exist from general RO knowledge but have not been researched
in Hercules source yet. Formulas and SC keys to be filled in once skill list is provided.

| Skill | SC key | Expected effect | Status |
|-------|--------|----------------|--------|
| AL_DECAGI (Decrease AGI) | SC_DECREASEAGI | AGI debuff | [stub] |
| AL_CURE | — | removes debuffs | out of scope |
| PR_LEXDIVINA | SC_SILENCE | silence | out of scope |
| PR_SANCTUARY | — | HP regen on ground | out of scope |
| PR_ASPERSIO | SC_ASPERSIO | weapon endow Holy | see weapon_endow.md |
| MO_EXPLOSIONSPIRITS | SC_EXPLOSIONSPIRITS | CRI bonus | [stub] |
| SN_WINDWALK | SC_WINDWALK | FLEE bonus | [stub] |
| SN_TRUESIGHT | SC_TRUESIGHT | HIT + CRI + all base stats | [stub] |
| GS_ACCURACY | SC_GS_ACCURACY | HIT +20 | [stub] |

---

## Implementation status

| SC | Formula confirmed | Calculator | GUI |
|----|------------------|-----------|-----|
| SC_IMPOSITIO | yes | done (base_damage.py) | passive_section |
| SC_BLESSING | explore | not started | — |
| SC_INCREASEAGI | stub | not started | — |
| SC_GLORIA | explore | not started | — |
| SC_ANGELUS | explore | not started | — |
| SC_CONCENTRATION | explore | not started | — |
| all others | stub | not started | — |
