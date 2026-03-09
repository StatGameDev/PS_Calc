# Skills by Job

Organises every skill_list entry by source job ID.
**Category codes**: B=buff · P=passive · O=offensive · D=debuff · S=status · H=heal · C=combo · M=modifier · X=other
Skill IDs are the primary key. Constant names included for reference only.
Skills listed under "not yet" are excluded (Rebirth jobs, Star Gladiator, Soul Linker).
Skill IDs may appear in multiple category lists; all applicable codes shown here.

---

## Job 1 — Swordsman
_Skills accessible to Job 1, 7 (Knight), 14 (Crusader)_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 2 | SM_SWORD | P | — |
| 3 | SM_TWOHAND | P | — |
| 4 | SM_RECOVERY | P | — |
| 5 | SM_BASH | O, S | Status only via SM_FATALBLOW (145) on Bash lv 6+ |
| 6 | SM_PROVOKE | B, D | Cannot be used on allies; treat as debuff unless applied by item |
| 7 | SM_MAGNUM | B, O | Fire element for 10 hits |
| 8 | SM_ENDURE | B | — |
| 144 | SM_MOVINGRECOVERY | M | HP regen while walking; unaffected by SM_RECOVERY (4) |
| 145 | SM_FATALBLOW | M | Adds stun to Bash lv 6+; base 5%*(lv-5), modified by BaseLV |
| 146 | SM_AUTOBERSERK | B | Applies Provoke (6) to user when HP < 25%; model as toggle |

---

## Job 2 — Mage
_Skills accessible to Job 2, 9 (Wizard), 16 (Sage)_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 9 | MG_SRECOVERY | P | — |
| 10 | MG_SIGHT | X | Must be active for WZ_SIGHTRASHER (81) |
| 11 | MG_NAPALMBEAT | O | — |
| 12 | MG_SAFETYWALL | X | Prevents melee hits; advanced combat modelling |
| 13 | MG_SOULSTRIKE | O | — |
| 14 | MG_COLDBOLT | O | — |
| 15 | MG_FROSTDIVER | O, S | — |
| 16 | MG_STONECURSE | S | — |
| 17 | MG_FIREBALL | O | — |
| 18 | MG_FIREWALL | O | Requires target to walk into cells; advanced modelling |
| 19 | MG_FIREBOLT | O | — |
| 20 | MG_LIGHTNINGBOLT | O | — |
| 21 | MG_THUNDERSTORM | O | — |
| 157 | MG_ENERGYCOAT | B | — |

---

## Job 3 — Archer
_Skills accessible to Job 3, 11 (Hunter), 19 (Bard), 20 (Dancer)_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 43 | AC_OWL | P | — |
| 44 | AC_VULTURE | P | — |
| 45 | AC_CONCENTRATION | B | — |
| 46 | AC_DOUBLE | O | — |
| 47 | AC_SHOWER | O | — |
| 147 | AC_MAKINGARROW | X | Creates items; maybe list arrow crafting recipes |
| 148 | AC_CHARGEARROW | O | — |

---

## Job 4 — Acolyte
_Skills accessible to Job 4, 8 (Priest), 15 (Monk)_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 22 | AL_DP | P | — |
| 23 | AL_DEMONBANE | P | — |
| 24 | AL_RUWACH | O | Requires target to be hiding or cloaked |
| 25 | AL_PNEUMA | X | Blocks all ranged hits for duration; advanced modelling |
| 26 | AL_TELEPORT | X | No effect in calculator |
| 27 | AL_WARP | X | No effect in calculator |
| 28 | AL_HEAL | H, O | Offensive vs Undead attribute |
| 29 | AL_INCAGI | B | — |
| 30 | AL_DECAGI | D | — |
| 31 | AL_HOLYWATER | X | Creates item |
| 32 | AL_CRUCIS | D | Ground-based |
| 33 | AL_ANGELUS | B | — |
| 34 | AL_BLESSING | B | Different effect on self vs party members |
| 35 | AL_CURE | X | Removes some statuses |

---

## Job 5 — Merchant
_Skills accessible to Job 5, 10 (Blacksmith), 18 (Alchemist)_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 36 | MC_INCCARRY | P | Only useful for weight capacity modelling |
| 37 | MC_DISCOUNT | P | Not relevant |
| 38 | MC_OVERCHARGE | P | Not relevant |
| 39 | MC_PUSHCART | P | Only useful for movement speed modelling |
| 40 | MC_IDENTIFY | X | Not relevant |
| 41 | MC_VENDING | X | Not relevant |
| 42 | MC_MAMMONITE | O | — |
| 153 | MC_CARTREVOLUTION | O | Damage depends on cart weight; allow manual weight input |
| 154 | MC_CHANGECART | X | Not relevant |
| 155 | MC_LOUD | B | — |

---

## Job 6 — Thief
_Skills accessible to Job 6, 12 (Assassin), 17 (Rogue)_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 48 | TF_DOUBLE | P | — |
| 49 | TF_MISS | P | — |
| 50 | TF_STEAL | X | Maybe add steal chance calculator as advanced feature |
| 51 | TF_HIDING | X | Hide status relevant for RG_RAID (214); advanced modelling |
| 52 | TF_POISON | O, S | — |
| 53 | TF_DETOXIFY | X | Removes poison status |
| 149 | TF_SPRINKLESAND | O, S | — |
| 150 | TF_BACKSLIDING | X | Not relevant |
| 151 | TF_PICKSTONE | X | Creates item |
| 152 | TF_THROWSTONE | O | — |

---

## Job 7 — Knight
_Skills exclusive to Job 7, accessible to Job 14 (Crusader) via cross-class tree_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 55 | KN_SPEARMASTERY | P | — |
| 56 | KN_PIERCE | O | Hit count depends on target size |
| 57 | KN_BRANDISHSPEAR | O | Bugged in vanilla; Payon Stories double-damage vs terrain |
| 58 | KN_SPEARSTAB | O | — |
| 59 | KN_SPEARBOOMERANG | O | — |
| 60 | KN_TWOHANDQUICKEN | B | — |
| 61 | KN_AUTOCOUNTER | O | Check implementation; advanced combat modelling |
| 62 | KN_BOWLINGBASH | O | — |
| 63 | KN_RIDING | P | Toggle Peco Peco mount |
| 64 | KN_CAVALIERMASTERY | P | — |
| 495 | KN_ONEHAND | B | Soul Link required for non-Knight builds |
| 1001 | KN_CHARGEATK | O | Allow manual distance setting |

---

## Job 8 — Priest
_Skills exclusive to Job 8_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 65 | PR_MACEMASTERY | P | — |
| 66 | PR_IMPOSITIO | B | — |
| 67 | PR_SUFFRAGIUM | B | — |
| 68 | PR_ASPERSIO | B | Weapon endow → Holy; model via element override |
| 69 | PR_BENEDICTIO | B | Changes armor attribute; model via armor element override |
| 70 | PR_SANCTUARY | H, O | Healing ground; offensive vs Undead |
| 71 | PR_SLOWPOISON | X | Not directly relevant |
| 72 | PR_STRECOVERY | S, X | Removes some statuses; listed in status_skills (Undead attribute only) |
| 73 | PR_KYRIE | X | Prevents hit count; advanced combat modelling |
| 74 | PR_MAGNIFICAT | B | — |
| 75 | PR_GLORIA | B, S | — |
| 76 | PR_LEXDIVINA | S | — |
| 77 | PR_TURNUNDEAD | O | — |
| 78 | PR_LEXAETERNA | D | — |
| 79 | PR_MAGNUS | O | — |
| 1014 | PR_REDEMPTIO | X | Not relevant |

---

## Job 9 — Wizard
_Skills exclusive to Job 9_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 80 | WZ_FIREPILLAR | O | Requires special handling; Payon Stories push vs terrain |
| 81 | WZ_SIGHTRASHER | O | Requires MG_SIGHT (10) active |
| 83 | WZ_METEOR | O | — |
| 84 | WZ_JUPITEL | O | — |
| 85 | WZ_VERMILION | O | — |
| 86 | WZ_WATERBALL | O | Allow manual setting of active water cells |
| 87 | WZ_ICEWALL | X | Relevant for ice wall prison advanced modelling |
| 88 | WZ_FROSTNOVA | O, S | — |
| 89 | WZ_STORMGUST | O, S | — |
| 90 | WZ_EARTHSPIKE | O | — |
| 91 | WZ_HEAVENDRIVE | O | — |
| 92 | WZ_QUAGMIRE | D, O | Ground-based; modifier for incoming |
| 93 | WZ_ESTIMATION | X | Not relevant |
| 1006 | WZ_SIGHTBLASTER | O | Relevant for trap + fire pillar push; advanced modelling |

---

## Job 10 — Blacksmith
_Skills exclusive to Job 10_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 94–104 | BS_IRON … BS_SPEAR | X | Forging skills; creates items; not relevant |
| 105 | BS_HILTBINDING | P | — |
| 106 | BS_FINDINGORE | X | Not relevant |
| 107 | BS_WEAPONRESEARCH | P | — |
| 108 | BS_REPAIRWEAPON | X | Not relevant |
| 109 | BS_SKINTEMPER | P | — |
| 110 | BS_HAMMERFALL | S | — |
| 111 | BS_ADRENALINE | B | — |
| 112 | BS_WEAPONPERFECT | B | — |
| 113 | BS_OVERTHRUST | B | — |
| 114 | BS_MAXIMIZE | B | — |
| 459 | BS_ADRENALINE2 | B | Soul Link required for non-Blacksmith use |
| 496–498 | AM_TWILIGHT1–3 | X | Creates items; advanced uses/s modelling |

---

## Job 11 — Hunter
_Skills exclusive to Job 11_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 115 | HT_SKIDTRAP | X | Trap; not relevant |
| 116 | HT_LANDMINE | O | Trap |
| 117 | HT_ANKLESNARE | X | Trap; maybe show duration on target |
| 118 | HT_SHOCKWAVE | X | Trap; not relevant |
| 119 | HT_SANDMAN | S | Trap |
| 120 | HT_FLASHER | S | Trap |
| 121 | HT_FREEZINGTRAP | O, S | Trap |
| 122 | HT_BLASTMINE | O | Trap |
| 123 | HT_CLAYMORETRAP | O | Trap |
| 124 | HT_REMOVETRAP | X | Not relevant |
| 125 | HT_TALKIEBOX | X | Not relevant |
| 126 | HT_BEASTBANE | P | — |
| 127 | HT_FALCON | P | Toggle Falcon |
| 128 | HT_STEELCROW | P | — |
| 129 | HT_BLITZBEAT | P | Auto-proc; requires auto spell system to model |
| 130 | HT_DETECTING | X | Not relevant |
| 131 | HT_SPRINGTRAP | X | Not relevant |
| 1009 | HT_PHANTASMIC | O | — |

---

## Job 12 — Assassin
_Skills exclusive to Job 12_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 132 | AS_RIGHT | P | — |
| 133 | AS_LEFT | P | — |
| 134 | AS_KATAR | P | — |
| 135 | AS_CLOAKING | B | Mostly relevant for advanced combat modelling |
| 136 | AS_SONICBLOW | O, S | — |
| 137 | AS_GRIMTOOTH | O | — |
| 138 | AS_ENCHANTPOISON | B | Weapon endow → Poison; model via element override; also poison % |
| 139 | AS_POISONREACT | B | Mostly relevant for advanced combat modelling |
| 140 | AS_VENOMDUST | S | Ground effect causing Poison status |
| 141 | AS_SPLASHER | O | — |
| 1003 | AS_SONICACCEL | P | — |
| 1004 | AS_VENOMKNIFE | O, S | Allows Assassins to equip ammo |

---

## Job 14 — Crusader
_Skills exclusive to Job 14_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 248 | CR_TRUST | P | — |
| 249 | CR_AUTOGUARD | B | Relevant for incoming damage modelling; advanced multi-hit |
| 250 | CR_SHIELDCHARGE | O, S | — |
| 251 | CR_SHIELDBOOMERANG | O | — |
| 252 | CR_REFLECTSHIELD | B | Reflect damage; advanced combat modelling |
| 253 | CR_HOLYCROSS | O, S | — |
| 254 | CR_GRANDCROSS | O | Exceedingly complicated; likely requires entire session |
| 255 | CR_DEVOTION | X | Allows transfer of some Crusader buffs; separate section if implemented |
| 256 | CR_PROVIDENCE | B | — |
| 257 | CR_DEFENDER | B | Has debuff side-effect (slows movement/ranged) |
| 258 | CR_SPEARQUICKEN | B | — |
| 1002 | CR_SHRINK | X | Only for advanced combat modelling |

---

## Job 15 — Monk
_Skills exclusive to Job 15_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 259 | MO_IRONHAND | P | — |
| 260 | MO_SPIRITSRECOVERY | P | Primarily useful for sitting SP Regen |
| 261 | MO_CALLSPIRITS | B | With 1015 allows any build to obtain spirit sphere buff |
| 262 | MO_ABSORBSPIRITS | X | Not relevant |
| 263 | MO_TRIPLEATTACK | P, C | Passive; causes distinct attack delay depending on MO_CHAINCOMBO (272) |
| 264 | MO_BODYRELOCATION | X | Not relevant |
| 265 | MO_DODGE | P | — |
| 266 | MO_INVESTIGATE | O | — |
| 267 | MO_FINGEROFFENSIVE | O | — |
| 268 | MO_STEELBODY | B | — |
| 269 | MO_BLADESTOP | C | Technically a status; effectively for combos |
| 270 | MO_EXPLOSIONSPIRITS | B | — |
| 271 | MO_EXTREMITYFIST | O, C | Allowed after 269 or 273, or standalone via 1015 |
| 272 | MO_CHAINCOMBO | O, C | Requires 263 or 269; leads into 273 |
| 273 | MO_COMBOFINISH | O, C | Requires 272; leads into 271 |
| 1015 | MO_KITRANSLATION | X | Allow manual spirit sphere count for any build |
| 1016 | MO_BALKYOUNG | O, S | — |

---

## Job 16 — Sage
_Skills exclusive to Job 16_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 274 | SA_ADVANCEDBOOK | P | — |
| 275 | SA_CASTCANCEL | X | Not relevant |
| 276 | SA_MAGICROD | X | Not relevant for basic calc |
| 277 | SA_SPELLBREAKER | O | Mostly relevant for advanced combat modelling |
| 278 | SA_FREECAST | P | — |
| 279 | SA_AUTOSPELL | P, M | Requires auto spell system to model |
| 280 | SA_FLAMELAUNCHER | B | Weapon endow → Fire; model via element override |
| 281 | SA_FROSTWEAPON | B | Weapon endow → Water; model via element override |
| 282 | SA_LIGHTNINGLOADER | B | Weapon endow → Wind; model via element override |
| 283 | SA_SEISMICWEAPON | B | Weapon endow → Earth; model via element override |
| 284 | SA_DRAGONOLOGY | P | — |
| 285 | SA_VOLCANO | B | Ground effect (AttrFix-adjacent) |
| 286 | SA_DELUGE | B | Ground effect |
| 287 | SA_VIOLENTGALE | B | Ground effect |
| 288 | SA_LANDPROTECTOR | X | Not relevant |
| 289 | SA_DISPELL | X | Removes most buffs and debuffs |
| 290 | SA_ABRACADABRA | X | Not relevant |
| 1007 | SA_CREATECON | X | Creates Elemental Converter; advanced uses/s modelling |
| 1008 | SA_ELEMENTWATER | S | Changes target attribute; treat as debuff |
| 1017 | SA_ELEMENTGROUND | S | Changes target attribute; treat as debuff |
| 1018 | SA_ELEMENTFIRE | S | Changes target attribute; treat as debuff |
| 1019 | SA_ELEMENTWIND | S | Changes target attribute; treat as debuff |

---

## Job 17 — Rogue
_Skills exclusive to Job 17_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 210 | RG_SNATCHER | P | — |
| 211 | RG_STEALCOIN | X | Not relevant |
| 212 | RG_BACKSTAP | O | — |
| 213 | RG_TUNNELDRIVE | X | Not relevant |
| 214 | RG_RAID | O, S | Requires hiding status |
| 215 | RG_STRIPWEAPON | D | — |
| 216 | RG_STRIPSHIELD | D | — |
| 217 | RG_STRIPARMOR | D | — |
| 218 | RG_STRIPHELM | D | — |
| 219 | RG_INTIMIDATE | O | — |
| 220–224 | RG_GRAFFITI … RG_COMPULSION | X | Not relevant |
| 225 | RG_PLAGIARISM | M | Allows use of any skill with relevant flag |
| 1005 | RG_CLOSECONFINE | B | — |

---

## Job 18 — Alchemist
_Skills exclusive to Job 18_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 226 | AM_AXEMASTERY | P | — |
| 227 | AM_LEARNINGPOTION | P | — |
| 228 | AM_PHARMACY | X | Creates item |
| 229 | AM_DEMONSTRATION | O | — |
| 230 | AM_ACIDTERROR | O, S | — |
| 231 | AM_POTIONPITCHER | H | — |
| 232 | AM_CANNIBALIZE | X | Summons mobs; maybe model Geographer heal |
| 233 | AM_SPHEREMINE | X | Summons self-destruct mob; model summon HP and damage |
| 234–238 | AM_CP_* / AM_BIOETHICS | X | Not relevant |
| 243–244 | AM_CALLHOMUN / AM_REST | X | Not relevant |
| 247 | AM_RESURRECTHOMUN | X | Not relevant |
| 446 | AM_BERSERKPITCHER | B | Soul Link required for non-Alchemist use |
| 496–498 | AM_TWILIGHT1–3 | X | Creates items |

---

## Job 19 — Bard
_Skills exclusive to Job 19 (duet BD_* require both Bard and Dancer)_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 304 | BD_ADAPTATION | X | Only useful for modelling SP usage |
| 305 | BD_ENCORE | X | SP usage |
| 306 | BD_LULLABY | S | Duet (Bard + Dancer) |
| 307 | BD_RICHMANKIM | X | Not relevant for damage |
| 308 | BD_ETERNALCHAOS | D | Duet |
| 309 | BD_DRUMBATTLEFIELD | B | Duet |
| 310 | BD_RINGNIBELUNGEN | B | Duet |
| 311 | BD_ROKISWEIL | X | Not relevant |
| 312 | BD_INTOABYSS | X | Not relevant |
| 313 | BD_SIEGFRIED | B | Duet |
| 315 | BA_MUSICALLESSON | P | — |
| 316 | BA_MUSICALSTRIKE | O | — |
| 317 | BA_DISSONANCE | S, O | — |
| 318 | BA_FROSTJOKE | S | — |
| 319 | BA_WHISTLE | B | — |
| 320 | BA_ASSASSINCROSS | B | SC_ASSNCROS |
| 321 | BA_POEMBRAGI | B | SC_POEMBRAGI; cast time + after-cast delay |
| 322 | BA_APPLEIDUN | B | SC_APPLEIDUN; MaxHP% |

---

## Job 20 — Dancer
_Skills exclusive to Job 20 (duet BD_* require both Bard and Dancer)_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 323 | DC_DANCINGLESSON | P | — |
| 324 | DC_THROWARROW | O | — |
| 325 | DC_UGLYDANCE | D | SP drain debuff |
| 326 | DC_SCREAM | S | — |
| 327 | DC_HUMMING | B | — |
| 328 | DC_DONTFORGETME | D | Slows movement and attack speed |
| 329 | DC_FORTUNEKISS | B | — |
| 330 | DC_SERVICEFORYOU | B | MaxSP% + SP cost reduction |

---

## Job 23 — Super Novice
_No skill_list entries yet_

---

## Job 24 — Gunslinger
_Skills exclusive to Job 24_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 500 | GS_GLITTERING | B | — |
| 501 | GS_FLING | O, D | — |
| 502 | GS_TRIPLEACTION | O | — |
| 503 | GS_BULLSEYE | O, S | Coma status irrelevant; other statuses apply |
| 504 | GS_MADNESSCANCEL | B | — |
| 505 | GS_ADJUSTMENT | B | — |
| 506 | GS_INCREASING | B | — |
| 507 | GS_MAGICALBULLET | O | — |
| 508 | GS_CRACKER | S | — |
| 509 | GS_SINGLEACTION | P | — |
| 510 | GS_SNAKEEYE | P | — |
| 511 | GS_CHAINACTION | P | — |
| 512 | GS_TRACKING | O | — |
| 513 | GS_DISARM | D | — |
| 514 | GS_PIERCINGSHOT | O, S | — |
| 515 | GS_RAPIDSHOWER | O | — |
| 516 | GS_DESPERADO | O | — |
| 517 | GS_GATLINGFEVER | B | — |
| 518 | GS_DUST | O | — |
| 519 | GS_FULLBUSTER | O, S | — |
| 520 | GS_SPREADATTACK | O | — |
| 521 | GS_GROUNDDRIFT | O | Trap-like; special handling for advanced modelling |

---

## Job 25 — Ninja
_Skills exclusive to Job 25_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 522 | NJ_TOBIDOUGU | P | — |
| 523 | NJ_SYURIKEN | O | — |
| 524 | NJ_KUNAI | O | — |
| 525 | NJ_HUUMA | O | — |
| 526 | NJ_ZENYNAGE | O | — |
| 527 | NJ_TATAMIGAESHI | O | Secondary ranged damage blocking; advanced |
| 528 | NJ_KASUMIKIRI | O | — |
| 530 | NJ_KIRIKAGE | O | — |
| 531 | NJ_UTSUSEMI | X | Prevents hits; advanced combat modelling |
| 532 | NJ_BUNSINJYUTSU | X | Prevents hits; advanced combat modelling |
| 533 | NJ_NINPOU | P | — |
| 534 | NJ_KOUENKA | O | — |
| 535 | NJ_KAENSIN | O | Ground fire; relevant for target walking into effect |
| 536 | NJ_BAKUENRYU | O | — |
| 537 | NJ_HYOUSENSOU | O | — |
| 538 | NJ_SUITON | B | Ground-based; required for NJ_HYOUSENSOU (537) water bonus |
| 539 | NJ_HYOUSYOURAKU | O, S | — |
| 540 | NJ_HUUJIN | O | — |
| 541 | NJ_RAIGEKISAI | O | — |
| 542 | NJ_KAMAITACHI | O | — |
| 543 | NJ_NEN | B | — |
| 544 | NJ_ISSEN | O | Model with Max HP or manually set HP |

---

## Taekwon (Job 4046)
_TK_* skills — not yet in skill_lists for Star Gladiator (Job 4047) extensions_

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 411 | TK_RUN | B | — |
| 412 | TK_READYSTORM | C | Tornado Stance |
| 413 | TK_STORMKICK | O, C | — |
| 414 | TK_READYDOWN | C | Heel Drop Stance |
| 415 | TK_DOWNKICK | O, C, S | — |
| 416 | TK_READYTURN | C | Roundhouse Stance |
| 417 | TK_TURNKICK | O, C, S | — |
| 418 | TK_READYCOUNTER | C | Counter Kick Stance |
| 419 | TK_COUNTER | O, C | — |
| 420 | TK_DODGE | P | — |
| 421 | TK_JUMPKICK | O | Exceedingly complicated; model with current SP |
| 422 | TK_HPTIME | P | Sitting HP regen modelling |
| 423 | TK_SPTIME | P | Sitting SP regen; maybe add tooltip for happy status |
| 424 | TK_POWER | P | Allow manual setting of party member count |
| 425 | TK_SEVENWIND | B | Weapon endow → element (7 choices); model via element override |
| 426 | TK_HIGHJUMP | X | Not relevant |
| 493 | TK_MISSION | X | Ranker status; not relevant for basic; advanced only |

---

## All-Job / Shared Skills

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 1 | NV_BASIC | X | Not relevant |
| 54 | ALL_RESURRECTION | O, H | Offensive vs Undead (instant kill mechanic) |

## Job 5 (Merchant) — Additional

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 2544 | MC_CARTDECORATE | X | Not relevant |

## All-Job — Miscellaneous

| ID | Constant | Cat | Notes |
|---|---|---|---|
| 2535 | ALL_BUYING_STORE | X | Not relevant |
