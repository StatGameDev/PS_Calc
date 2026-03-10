# Buff Skills Tracking List
_Working file. Full cross-reference of every skill in `docs/skill_lists/buff_skills.md`._
_Columns: ID · Constant · Category · Status · Note_
_Category: Self = self-only | Party = can target others | Session O = weapon endow/ground | Done = already implemented_
_Status: Done | Confirmed (formula known, not yet coded) | Partial (some formula found) | Unknown SC (key not in status.c) | Stub (UI only, no calc effect) | Future_

| ID | Constant | Category | Status | Note |
|---|---|---|---|---|
| 6 | SM_PROVOKE | Item / Debuff | Future | Debuff on enemies; SC_PROVOKE on player via Auto Berserk (146) or consumable item Aloe Vera. Session R for debuff side. Item side future session. |
| 7 | SM_MAGNUM | Self | Done | SC_SUB_WEAPONPROPERTY; UI stub row added Session N; battle.c:996-1001 pipeline effect deferred |
| 8 | SM_ENDURE | Self | Done | SC_ENDURE; mdef+=val1=lv (status.c:5149); UI+calc done Session N |
| 29 | AL_INCAGI | Party | Done | Session M — SC_INC_AGI in support_buffs |
| 33 | AL_ANGELUS | Party | Done | Session M — SC_ANGELUS in support_buffs; vit_def scaled |
| 34 | AL_BLESSING | Party | Done | Session M — SC_BLESSING in support_buffs; STR/INT/DEX |
| 45 | AC_CONCENTRATION | Self | Done | SC_CONCENTRATION; UI stub row added Session N; agi/dex % boost (status.c:4007/4195) needs card-split — deferred |
| 60 | KN_TWOHANDQUICKEN | Self | Done | SC_TWOHANDQUICKEN — ASPD 300/1000-scale in status_calculator.py |
| 66 | PR_IMPOSITIO | Party | Done | Session M — SC_IMPOSITIO in support_buffs; watk += lv×5 |
| 67 | PR_SUFFRAGIUM | Party | Future | Cast time reduction on target — skipped in Session M, future party session |
| 68 | PR_ASPERSIO | Session O | Future | Weapon endow Holy |
| 69 | PR_BENEDICTIO | Session O | Future | Armor element change |
| 74 | PR_MAGNIFICAT | Party | Future | SP regen party buff |
| 75 | PR_GLORIA | Party | Done | Session M — SC_GLORIA in support_buffs; LUK+30 |
| 111 | BS_ADRENALINE | Party | Done | Session M — SC_ADRENALINE in support_buffs; ASPD |
| 112 | BS_WEAPONPERFECT | Party | Future | Weapon Perfection; can target party members |
| 113 | BS_OVERTHRUST | Party | Incorrectly done as self | SC_OVERTHRUST — skill_ratio.py; check for party effect |
| 114 | BS_MAXIMIZE | Self | Done | SC_MAXIMIZEPOWER — base_damage.py; variance collapse |
| 135 | AS_CLOAKING | Self | Done | SC_CLOAKING; UI stub row added Session N |
| 138 | AS_ENCHANTPOISON | Session O | Future | Weapon endow Poison + poison% |
| 139 | AS_POISONREACT | Self | Done | SC_POISONREACT; UI stub row added Session N |
| 146 | SM_AUTOBERSERK | Self | Done | SC_AUTOBERSERK; UI stub row added Session N |
| 155 | MC_LOUD | Self | Done | SC_SHOUT; str+4 (status.c:3956); UI+calc done Session N |
| 157 | MG_ENERGYCOAT | Self | Done | SC_ENERGYCOAT; UI stub row added Session N |
| 249 | CR_AUTOGUARD | Self | Done | SC_AUTOGUARD; UI stub row added Session N; party buff via 255 future |
| 252 | CR_REFLECTSHIELD | Self | Done | SC_REFLECTSHIELD; UI stub row added Session N; party buff via 255 future |
| 256 | CR_PROVIDENCE | Party | Future | Resistant Souls; can cast on party — future party buff session |
| 257 | CR_DEFENDER | Self | Done | SC_DEFENDER; aspd_rate+=val4=250-50×lv (status_calc_aspd_rate:5674); UI+calc done Session N; incoming ATK reduction deferred |
| 258 | CR_SPEARQUICKEN | Self | Done | SC_SPEARQUICKEN — status_calculator.py |
| 261 | MO_CALLSPIRITS | Self | Done | No SC; MO_SPIRITBALL key; sphere count spinner 1-5 added Session N; affects skill ratios (future) |
| 268 | MO_STEELBODY | Self | Done | SC_STEELBODY; aspd_rate+=250 (status_calc_aspd_rate:5670); def cap=90 (#ifndef RENEWAL); UI+calc done Session N |
| 270 | MO_EXPLOSIONSPIRITS | Self | Done | SC_EXPLOSIONSPIRITS; cri+=val2=75+25×lv (status.c:4753); UI+calc done Session N |
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
| 411 | TK_RUN | Self | Done | SC_RUN; UI stub row added Session N; FLEE effect unconfirmed, deferred |
| 425 | (unknown) | Session O | Future | Changes weapon attribute — Session O |
| 446 | AM_BERSERKPITCHER | Party | Future | Throws consumable to target; Soul Link required; model by allowing any job to use berserk potion with note |
| 459 | BS_ADRENALINE2 | Party | Future | Advanced Adrenaline Rush; Soul Link required |
| 495 | KN_ONEHAND | Self | Done | SC_ONEHANDQUICKEN — status_calculator.py; Soul Link = non-Knight access, same SC |
| 500 | GS_GLITTERING | Self | Done | No SC; GS_COINS key; coin count spinner 1-10 added Session N; affects GS skill ratios (future) |
| 504 | GS_MADNESSCANCEL | Self | Done | SC_GS_MADNESSCANCEL; batk+100 (#ifndef RENEWAL); aspd_rate-=200 separate from max pool; UI+calc done Session N |
| 505 | GS_ADJUSTMENT | Self | Done | SC_GS_ADJUSTMENT; hit-30, flee+30; UI+calc done Session N |
| 506 | GS_INCREASING | Self | Done | SC_GS_ACCURACY; agi+4, dex+4, hit+20; UI+calc done Session N |
| 517 | GS_GATLINGFEVER | Self | Done | SC_GS_GATLINGFEVER; batk+20+10×lv; flee-5×lv; aspd val2=20×lv in max pool; UI+calc done Session N |
| 538 | NJ_SUITON | Session O | Future | Ground-based, modifier for NJ skill 537 |
| 543 | NJ_NEN | Self | Done | SC_NJ_NEN; str+=lv, int+=lv (status.c:3962/4148); val1=skill_lv confirmed; UI+calc done Session N |
| 1005 | RG_CLOSECONFINE | Self | Done | SC_RG_CCONFINE_M; flee+10 (status.c:4874); UI+calc done Session N |
