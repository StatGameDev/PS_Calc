# Buff Skills Tracking List
_Working file. Full cross-reference of every skill in `docs/skill_lists/buff_skills.md`._
_Columns: ID · Constant · Category · Status · Note_
_Category: Self = self-only | Party = can target others | Session O = weapon endow/ground | Done = already implemented_
_Status: Done | Confirmed (formula known, not yet coded) | Partial (some formula found) | Unknown SC (key not in status.c) | Stub (UI only, no calc effect) | Future_

| ID | Constant | Category | Status | Note |
|---|---|---|---|---|
| 6 | SM_PROVOKE | Party / Debuff | Future | Debuff on enemies; SC_PROVOKE on player via Auto Berserk (146). Session R for debuff side. Party buff side future session. |
| 7 | SM_MAGNUM | Self | Unknown SC | SC key not found in status.c this session |
| 8 | SM_ENDURE | Self | Partial | MDEF+val1 (status.c:5149); val1 definition not checked |
| 29 | AL_INCAGI | Party | Done | Session M — SC_INC_AGI in support_buffs |
| 33 | AL_ANGELUS | Party | Done | Session M — SC_ANGELUS in support_buffs; vit_def scaled |
| 34 | AL_BLESSING | Party | Done | Session M — SC_BLESSING in support_buffs; STR/INT/DEX |
| 45 | AC_CONCENTRATION | Self | Unknown SC | SC key not found in status.c this session |
| 60 | KN_TWOHANDQUICKEN | Self | Done | SC_TWOHANDQUICKEN — ASPD 300/1000-scale in status_calculator.py |
| 66 | PR_IMPOSITIO | Party | Done | Session M — SC_IMPOSITIO in support_buffs; watk += lv×5 |
| 67 | PR_SUFFRAGIUM | Party | Future | Cast time reduction on target — skipped in Session M, future party session |
| 68 | PR_ASPERSIO | Session O | Future | Weapon endow Holy |
| 69 | PR_BENEDICTIO | Session O | Future | Armor element change |
| 74 | PR_MAGNIFICAT | Party | Future | SP regen party buff |
| 75 | PR_GLORIA | Party | Done | Session M — SC_GLORIA in support_buffs; LUK+30 |
| 111 | BS_ADRENALINE | Party | Done | Session M — SC_ADRENALINE in support_buffs; ASPD |
| 112 | BS_WEAPONPERFECT | Party | Future | Weapon Perfection; can target party members |
| 113 | BS_OVERTHRUST | Self | Done | SC_OVERTHRUST — skill_ratio.py |
| 114 | BS_MAXIMIZE | Self | Done | SC_MAXIMIZEPOWER — base_damage.py; variance collapse |
| 135 | AS_CLOAKING | Self | Stub | Hide state — no outgoing damage effect |
| 138 | AS_ENCHANTPOISON | Session O | Future | Weapon endow Poison + poison% |
| 139 | AS_POISONREACT | Self | Stub | Counter attack mechanic — no direct outgoing damage effect |
| 146 | SM_AUTOBERSERK | Self | Stub | Toggle; auto-applies SC_PROVOKE when HP<25%; no direct StatusCalculator formula |
| 155 | MC_LOUD | Self | Unknown SC | SC key not found in status.c this session |
| 157 | MG_ENERGYCOAT | Self | Stub | SP absorbs incoming damage — incoming pipeline only |
| 249 | CR_AUTOGUARD | Self | Stub | Block chance — incoming pipeline only |
| 252 | CR_REFLECTSHIELD | Self | Stub | Reflect melee damage — incoming/advanced |
| 256 | CR_PROVIDENCE | Party | Future | Resistant Souls; cast on party members — future party buff session |
| 257 | CR_DEFENDER | Self | Partial | ASPD −val4/10 (status.c:5503); incoming ATK penalty; val4 definition not checked |
| 258 | CR_SPEARQUICKEN | Self | Done | SC_SPEARQUICKEN — status_calculator.py |
| 261 | MO_CALLSPIRITS | Self | Unknown SC | SC key unconfirmed; spirit sphere count spinbox feeds SC_EXPLOSIONSPIRITS |
| 268 | MO_STEELBODY | Self | Partial | ASPD −25 (status.c:5501) confirmed; damage-to-1 is incoming pipeline only |
| 270 | MO_EXPLOSIONSPIRITS | Self | Confirmed | SC_EXPLOSIONSPIRITS; critical += val2 (status.c:4754); val2 definition not yet checked |
| 280 | SA_FIREELEMENT | Session O | Future | Weapon endow Fire |
| 281 | SA_WATERALIMENT | Session O | Future | Weapon endow Water |
| 282 | SA_WINDATTRIBUTE | Session O | Future | Weapon endow Wind |
| 283 | SA_EARTHATTRIBUTE | Session O | Future | Weapon endow Earth |
| 285 | SA_VOLCANO | Session O | Future | Ground effect |
| 286 | SA_DELUGE | Session O | Future | Ground effect |
| 287 | SA_VIOLENTGALE | Session O | Future | Ground effect |
| 309 | BD_DRUMBATTLEFIELD | Done | Done | Session M2 — SC_DRUMBATTLE in base_damage.py |
| 310 | BD_RINGNIBELUNGEN | Done | Done | Session M2 — SC_NIBELUNGEN in base_damage.py |
| 313 | BD_SIEGFRIED | Done | Done | Session M2 — SC_SIEGFRIED ensemble stub |
| 319 | BA_WHISTLE | Done | Done | Session M2 — SC_WHISTLE in status_calculator.py |
| 320 | BA_ASSASSINCROSS | Done | Done | Session M2 — SC_ASSNCROS in status_calculator.py |
| 321 | BA_POEMBRAGI | Done | Done | Session M2 — SC_POEMBRAGI in status_calculator.py |
| 322 | BA_APPLEIDUN | Done | Done | Session M2 — SC_APPLEIDUN in status_calculator.py |
| 327 | DC_HUMMING | Done | Done | Session M2 — SC_HUMMING in status_calculator.py |
| 329 | DC_FORTUNEKISS | Done | Done | Session M2 — SC_FORTUNE in status_calculator.py |
| 330 | DC_SERVICEFORYOU | Done | Done | Session M2 — SC_SERVICEFORYU in status_calculator.py |
| 411 | TK_RUN | Self | Partial | Movement speed +55 (status.c:5375); FLEE/stat effect unconfirmed |
| 425 | (unknown) | Session O | Future | Changes weapon attribute — Session O |
| 446 | AM_BERSERKPITCHER | Party | Future | Throws consumable to target; Soul Link required; model by allowing any job to use berserk potion with note |
| 459 | BS_ADRENALINE2 | Party | Future | Advanced Adrenaline Rush; Soul Link required |
| 495 | KN_ONEHAND | Self | Done | SC_ONEHANDQUICKEN — status_calculator.py; Soul Link = non-Knight access, same SC |
| 500 | GS_GLITTERING | Self | Unknown SC | SC key not found; coin count spinbox needed |
| 504 | GS_MADNESSCANCEL | Self | Confirmed | SC_GS_MADNESSCANCEL; batk += 100 (#ifndef RENEWAL, status.c:4479); ASPD skill1 bonus=20, scale ambiguous |
| 505 | GS_ADJUSTMENT | Self | Confirmed | SC_GS_ADJUSTMENT; hit −= 30; flee += 30 (status.c:4809, 4878) |
| 506 | GS_INCREASING | Self | Confirmed | SC key = SC_GS_ACCURACY; hit += 20 (status.c:4810) |
| 517 | GS_GATLINGFEVER | Self | Confirmed | SC_GS_GATLINGFEVER; batk += 20+10×lv (#ifndef RENEWAL, status.c:4480); flee −= 5×lv (status.c:4883); ASPD rate += val1; val2=20×lv per init block |
| 538 | NJ_SUITON | Session O | Future | Ground-based, modifier for NJ skill 537 |
| 543 | NJ_NEN | Self | Confirmed | SC_NJ_NEN; str += val1; int_ += val1 (status.c:3963, 4149); val1 definition not yet checked |
| 1005 | RG_CLOSECONFINE | Self | Confirmed | SC key = SC_RG_CCONFINE_M; flee += 10 (status.c:4831) |
