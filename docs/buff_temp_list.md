# Buff Skills Tracking List
_Working file. Full cross-reference of every skill in `docs/skill_lists/buff_skills.md`._
_Columns: ID · Constant · Category · Status · Note_
_Category: Self | Party | Song | Dance | Ensemble | Ground | Endow_
_Status: Done | Partial | Future | Deferred_

---

## Done

| ID | Constant | Category | Note |
|---|---|---|---|
| 7 | SM_MAGNUM | Self | SC_SUB_WEAPONPROPERTY; UI stub row (Session N); battle.c:996-1001 pipeline effect deferred |
| 8 | SM_ENDURE | Self | SC_ENDURE; mdef+=val1=lv (status.c:5149); UI+calc done Session N |
| 29 | AL_INCAGI | Party | SC_INC_AGI in support_buffs (Session M) |
| 33 | AL_ANGELUS | Party | SC_ANGELUS in support_buffs; vit_def scaled (Session M) |
| 34 | AL_BLESSING | Party | SC_BLESSING in support_buffs; STR/INT/DEX (Session M) |
| 45 | AC_CONCENTRATION | Self | SC_CONCENTRATION; UI stub row (Session N); agi/dex % boost (status.c:4007/4195) needs card-split — full calc deferred |
| 60 | KN_TWOHANDQUICKEN | Self | SC_TWOHANDQUICKEN — ASPD 300/1000-scale in status_calculator.py |
| 66 | PR_IMPOSITIO | Party | SC_IMPOSITIO in support_buffs; watk += lv×5 (Session M) |
| 75 | PR_GLORIA | Party | SC_GLORIA in support_buffs; LUK+30 (Session M) |
| 111 | BS_ADRENALINE | Party | SC_ADRENALINE in support_buffs; ASPD (Session M) |
| 114 | BS_MAXIMIZE | Self | SC_MAXIMIZEPOWER — base_damage.py; variance collapse |
| 135 | AS_CLOAKING | Self | SC_CLOAKING; UI stub row (Session N) |
| 139 | AS_POISONREACT | Self | SC_POISONREACT; UI stub row (Session N) |
| 146 | SM_AUTOBERSERK | Self | SC_AUTOBERSERK; UI stub row (Session N) |
| 155 | MC_LOUD | Self | SC_SHOUT; str+4 (status.c:3956); UI+calc done Session N |
| 157 | MG_ENERGYCOAT | Self | SC_ENERGYCOAT; UI stub row (Session N) |
| 249 | CR_AUTOGUARD | Self | SC_AUTOGUARD; UI stub row (Session N); party buff via CR_SHRINK future |
| 252 | CR_REFLECTSHIELD | Self | SC_REFLECTSHIELD; UI stub row (Session N); party buff via CR_SHRINK future |
| 257 | CR_DEFENDER | Self | SC_DEFENDER; aspd_rate+=val4=250-50×lv (status_calc_aspd_rate:5674); UI+calc Session N; incoming ATK reduction deferred |
| 258 | CR_SPEARQUICKEN | Self | SC_SPEARQUICKEN — status_calculator.py |
| 261 | MO_CALLSPIRITS | Self | No SC; MO_SPIRITBALL key; sphere count spinner 1-5 (Session N); affects skill ratios (future) |
| 268 | MO_STEELBODY | Self | SC_STEELBODY; aspd_rate+=250 (status_calc_aspd_rate:5670); def cap=90 (#ifndef RENEWAL); UI+calc Session N |
| 270 | MO_EXPLOSIONSPIRITS | Self | SC_EXPLOSIONSPIRITS; cri+=val2=75+25×lv (status.c:4753); UI+calc Session N |
| 285 | SA_VOLCANO | Ground | SC_VOLCANO; val2=lv*10 WATK; base_damage.py + Ground Effects combo (Session O) |
| 286 | SA_DELUGE | Ground | SC_DELUGE; val2=deluge_eff[lv-1]={5,9,12,14,15}% MaxHP; status_calculator.py + Ground Effects combo (Session O fix) |
| 287 | SA_VIOLENTGALE | Ground | SC_VIOLENTGALE; val2=lv*3 FLEE; status_calculator.py + Ground Effects combo (Session O) |
| 309 | BD_DRUMBATTLEFIELD | Ensemble | SC_DRUMBATTLE in base_damage.py (Session M2) |
| 310 | BD_RINGNIBELUNGEN | Ensemble | SC_NIBELUNGEN in base_damage.py (Session M2) |
| 313 | BD_SIEGFRIED | Ensemble | SC_SIEGFRIED ensemble stub (Session M2) |
| 319 | BA_WHISTLE | Song | SC_WHISTLE in status_calculator.py (Session M2) |
| 320 | BA_ASSASSINCROSS | Song | SC_ASSNCROS in status_calculator.py (Session M2) |
| 321 | BA_POEMBRAGI | Song | SC_POEMBRAGI in status_calculator.py (Session M2) |
| 322 | BA_APPLEIDUN | Song | SC_APPLEIDUN in status_calculator.py (Session M2) |
| 327 | DC_HUMMING | Dance | SC_HUMMING in status_calculator.py (Session M2) |
| 329 | DC_FORTUNEKISS | Dance | SC_FORTUNE in status_calculator.py (Session M2) |
| 330 | DC_SERVICEFORYOU | Dance | SC_SERVICEFORYU in status_calculator.py (Session M2) |
| 411 | TK_RUN | Self | SC_RUN; UI stub row (Session N); FLEE effect unconfirmed, full calc deferred |
| 495 | KN_ONEHAND | Self | SC_ONEHANDQUICKEN — status_calculator.py; Soul Link = non-Knight access, same SC |
| 500 | GS_GLITTERING | Self | No SC; GS_COINS key; coin count spinner 1-10 (Session N); affects GS skill ratios (future) |
| 504 | GS_MADNESSCANCEL | Self | SC_GS_MADNESSCANCEL; batk+100 (#ifndef RENEWAL); aspd_rate-=200 separate from max pool; UI+calc Session N |
| 505 | GS_ADJUSTMENT | Self | SC_GS_ADJUSTMENT; hit-30, flee+30; UI+calc Session N |
| 506 | GS_INCREASING | Self | SC_GS_ACCURACY; agi+4, dex+4, hit+20; UI+calc Session N |
| 517 | GS_GATLINGFEVER | Self | SC_GS_GATLINGFEVER; batk+20+10×lv; flee-5×lv; aspd val2=20×lv in max pool; UI+calc Session N |
| 543 | NJ_NEN | Self | SC_NJ_NEN; str+=lv, int+=lv (status.c:3962/4148); UI+calc Session N |
| 1005 | RG_CLOSECONFINE | Self | SC_RG_CCONFINE_M; flee+10 (status.c:4874); UI+calc Session N |

---

## Remaining

| ID | Constant | Category | Status | Note |
|---|---|---|---|---|
| 6 | SM_PROVOKE | Party / Debuff | Future | Debuff on enemies; SC_PROVOKE on player via Auto Berserk or Aloe Vera item. Session R for debuff side. |
| 67 | PR_SUFFRAGIUM | Party | Future | Cast time reduction — no damage effect; future party session |
| 68 | PR_ASPERSIO | Endow | Deferred | Weapon endow Holy — deferred; manual weapon element override sufficient |
| 69 | PR_BENEDICTIO | Endow | Deferred | Armor element change — deferred indefinitely |
| 74 | PR_MAGNIFICAT | Party | Future | SP regen party buff — no damage effect |
| 112 | BS_WEAPONPERFECT | Party | Future | Weapon Perfection; party-castable; affects size penalty |
| 113 | BS_OVERTHRUST | Party | Partial | SC_OVERTHRUST in skill_ratio.py — check whether party casting is modelled |
| 138 | AS_ENCHANTPOISON | Endow | Deferred | Weapon endow Poison — deferred; manual weapon element override sufficient |
| 256 | CR_PROVIDENCE | Party | Future | Resistant Souls; party-cast elemental resistance |
| 280 | SA_FIREELEMENT | Endow | Deferred | Weapon endow Fire — deferred; manual weapon element override sufficient |
| 281 | SA_WATERALIMENT | Endow | Deferred | Weapon endow Water — deferred; manual weapon element override sufficient |
| 282 | SA_WINDATTRIBUTE | Endow | Deferred | Weapon endow Wind — deferred; manual weapon element override sufficient |
| 283 | SA_EARTHATTRIBUTE | Endow | Deferred | Weapon endow Earth — deferred; manual weapon element override sufficient |
| 425 | (TK_SEVENWIND?) | Endow | Deferred | Changes weapon attribute by level — deferred; manual weapon element override sufficient |
| 446 | AM_BERSERKPITCHER | Party | Future | Throws consumable to target; Soul Link required |
| 459 | BS_ADRENALINE2 | Party | Future | Advanced Adrenaline Rush; Soul Link required |
| 538 | NJ_SUITON | Ground | Future | Water AoE ground; condition modifier for NJ skill 537 — defer to Session Q2 (NJ skill ratios) |
