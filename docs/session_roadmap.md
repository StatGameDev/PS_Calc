# PS_Calc — Session Roadmap
_Gap IDs reference `docs/gaps.md`. Pipeline specs in `docs/pipeline_specs.md`._
_GUI layout and widget specs in `docs/gui_plan.md`._
_Core system architecture in `docs/core_architecture.md`._

---

## Context Budget Reference (from actual session data)

| Session type | Est. tokens | Typical ctx% |
|---|---|---|
| Pure GUI / no Hercules | 20–30k | 40–60% |
| Mixed implementation | 30–40k | 60–80% |
| Investigation-heavy | 40–50k | 80–100% |

**Planning rule**: If a session requires Hercules greps, budget 1–2 greps max alongside
implementation. Never plan investigation + large GUI change + doc maintenance together.
Hit-limit risk rises sharply past 3 Hercules reads in one session.

Fixed overhead per session (CLAUDE.md + system + conversation): ~6k tokens.
Doc maintenance (gaps.md + completed_work.md + context_log.md update): ~3–5k.

---

## Completed Sessions (reference only)

| Session | Primary work | Key gaps closed |
|---|---|---|
| 1–5 | Foundation, GUI Phases 0–4, data scrapers | B3–B9, C3, D1–D5, E1, F2, F5, F6 |
| A | Target model, CardFix | G1–G3, G5, G6, G8, G11 |
| B | BF_MAGIC outgoing pipeline | G18–G25 |
| C | ASC_KATAR mastery, ASPD buffs, bAtkRate | G4, G9~, G10, G42 |
| D | armor_element field, mob ATK investigation | G27 |
| E | Incoming physical + magic pipelines, player_build_to_target | G7, G26–G29, G31–G32 |
| F | Incoming config controls + unified target selector | G43, G30 |
| G | Card slot UI + armor refine DEF | G12, G13 |
| H | PMF foundation: pmf/ package + damage.py + base_damage.py | — |
| I | PMF migration: all 9 modifiers + 4 pipelines; DamageRange removed | — |
| J1 | Skill combo job filter + skill_tree.json scraper | G34 |
| J2 | Equipment browser / monster browser / passives job filters | G35, G36, G37 |
| K | Katar second hit + forged weapon bonus | G16, G17 |
| K2 | ActiveItems + ManualAdj sections + bonus column redesign + skill_data bugfix | G15, G46, G47 |
| L | StepsBar tooltips + state persistence + inline dropdown + job ID system fix | G39, G40, G45 |
| M0 | Buff/Debuff UI scaffolding: CollapsibleSubGroup widget, buffs_section (8 sub-groups, Self Buffs wired), player_debuffs_section, Manual Adj into build_header, passive_section strip | G49~ |
| Design | Buff Architecture Q1–Q5 resolved; decisions written to core_architecture.md | — |
| M | Party Buffs: SC_BLESSING/INC_AGI/GLORIA/ANGELUS/IMPOSITIO/ADRENALINE; def_percent chain; bonus display "Buffs" column | G49~ |
| M2 | Bard/Dancer songs: song_state on PlayerBuild; SC_ASSNCROS/WHISTLE/APPLEIDUN/POEMBRAGI/HUMMING/FORTUNE/SERVICEFORYU in StatusCalculator; SC_DRUMBATTLE+SC_NIBELUNGEN in base_damage.py; Bard Songs+Dancer Dances+Ensembles UI; job visibility filter | G9, G49~ |
| N | Self-Buffs: 10 SCs in StatusCalculator (stat/BATK/CRI/HIT/FLEE/ASPD/MDEF); 3 ASPD bugs fixed (MADNESSCANCEL not in max pool, STEELBODY/DEFENDER scale corrected); 22 new _SELF_BUFFS rows in buffs_section.py | G49~ |
| O | Ground Effects: SC_VOLCANO (base_damage.py, lv * 10 WATK); SC_VIOLENTGALE (status_calculator.py, lv * 3 FLEE); SC_DELUGE (UI only, MaxHP no damage effect); Ground Effects sub-group wired (QComboBox+QSpinBox). Endows deferred (manual element override sufficient). | G49~ |
| GUI-Adj | Spinbox→dropdowns/toggles, no-wheel on all combos, refine cap +10 | — |
| P | Passive skills: hp/sp regen in StatusData+StatusCalculator+DerivedSection; 16 new passive_section rows; stat/HIT/FLEE/ASPD/regen passives in StatusCalculator; GearBonusAggregator.apply_passive_bonuses() (sub_ele/add_race/sub_race); NJ_TOBIDOUGU in mastery_fix.py. Deferred: G52 dual-wield, G53 falcon, G55 Shuriken type verify. | G50~ |
| G54 | Double-hit procs (TF_DOUBLE/GS_CHAINACTION) + DPS stat: AttackDefinition + SelectionStrategy (Markov seam); correct probability tree; katar combined; DPS row in SummarySection. New gaps G56 (skill timing) + G57 (Markov). | G54 |
| G52 | Dual-wield pipeline (complete): AS_RIGHT/AS_LEFT passives, LH forge fields+widgets, lh_normal/lh_crit, dual-wield branch, LH card EQP fix, perfect_dodge=0, proc×RH-only + ATK_RATER on double_hit branches, ASPD (RH+LH)×7/10. | G52 |
| Q0 | Skill timing calculator: calculate_skill_timing() (new file); GearBonuses castrate/delayrate/skill_castrate; bCastrate/bVarCastrate/bDelayrate routed; SC_SUFFRAGIUM party buff; amotion period for skills; BF_MAGIC DPS; dps_valid frozensets; Speed (actions/s) in SummarySection. | G56, G59, G60 |
| Q1 | 31 BF_WEAPON ratios in `_BF_WEAPON_RATIOS` + `_BF_WEAPON_HIT_COUNT_FN`. All level-linear skills + KN_PIERCE (hit_count=tgt.size+1, battle.c:4719-4722). IMPLEMENTED_BF_WEAPON_SKILLS=31. Deferred to Q3: AS_SPLASHER (+mastery), RG_BACKSTAP (bow split), BF_MISC traps/TF_THROWSTONE/BA_DISSONANCE. | G61 |
| GUI-Rework | `gui/widgets/` package: `NoWheelCombo`, `NoWheelSpin`, `LevelWidget`. 9 files swept. `combat_controls`: `_sync_level_widget` + `_on_skill_changed`. `passive_section`: `LevelWidget` for masteries. `buffs_section`: full overhaul — lesson combos extracted to `_bard_lesson`/`_dancer_lesson`, `isinstance` guard eliminated. | — |
| GUI-CompactRework2 | `compact_mode: str` → `compact_modes: list[str]`; two flags: `"slim_content"` (compact widget in slim, correct toggle) + `"header_summary"` (always-visible header label, auto-collapses). Base class owns all frame/state; subclass hooks only show/hide widget. passive + buffs → header_summary. New doc: `docs/compact_modes.md`. | — |
| Q2 | MO_FINGEROFFENSIVE/MO_INVESTIGATE/AM_ACIDTERROR ratios; DefenseFix NK_IGNORE_DEF + pdef=2 + def1=0. KN_CHARGEATK/MC_CARTREVOLUTION/MO_EXTREMITYFIST/TK_JUMPKICK ratios via skill_params; context-sensitive params UI row. IMPLEMENTED_BF_WEAPON_SKILLS=38. | G62 |
| GUI-BuffLvl | All has_lv=True self buffs → combo-only (label + LevelWidget, no checkbox). Bidirectional sphere sync: MO_SPIRITBALL ↔ MO_FINGEROFFENSIVE sphere dropdown via new spirit_spheres_changed signals + set_spirit_spheres() setters. Known bug G69 (MO_EXTREMITYFIST formula) flagged for Q3. | — |
| Q3 | G69 arch fix (SkillInstance hydrated before _run_branch; nk_ignore_def/flee/name fields; DefenseFix/MasteryFix take skill param). G55 mastery fix (NJ_TOBIDOUGU skill-based + NJ_KUNAI +60). 9 GS BF_WEAPON + 5 NJ BF_WEAPON (incl. NJ_SYURIKEN +4×lv flat) + 7 NJ BF_MAGIC ratios + BF_MISC infra. KN_PIERCE size crash fix. NJ BF_MAGIC roadmap table was wrong — corrected from source read. Charm bonuses deferred (G71). IMPLEMENTED_BF_WEAPON_SKILLS=55, BF_MAGIC=30. | G63, G55, G69 |

---

## Session R — Target Debuff System

**Goal**: Full target/player debuff system plus all deferred gui_plan.md Session R items.
**Gap IDs**: G48, G70. G72 and G73 are already closed (planning session greps).
**NO Hercules greps needed** — all formulas pre-confirmed below.

---

### Pre-Confirmed Formulas (do not re-grep)

**SC_DEC_AGI** (Decrease AGI on target or player):
- `val2 = 2 + skill_lv` → `agi -= val2` (status.c:7633, 4025-4026)
- Effect: AGI reduced by `2+lv`; FLEE drops as a consequence via StatusCalculator

**SC_PROVOKE** (player casts on target, lives in `support_buffs["SC_PROVOKE"]`):
- `val3 = 2+3*lv` → target `atk_percent += val3` (status.c:8361, 4327-4328)
- `val4 = 5+5*lv` → target `def_percent -= val4` (status.c:8362, 4401-4402)
- Effect: target ATK raised (doesn't affect outgoing pipeline), target DEF% reduced

**SC_ETERNALCHAOS** (player casts on target, `support_buffs["SC_ETERNALCHAOS"]`):
- Returns 0 from `status_calc_def2` (status.c:5090) → target `def2 = 0`
- Effect: zeroes target's soft DEF (VIT-derived DEF)

**SC_CURSE** (player debuff, `player_active_scs["SC_CURSE"]`):
- LUK = 0 (status.c:4261)
- ATK% -= 25 (status.c:4345-4346)
- Movement speed dramatically reduced (not modelled in damage pipeline)
- No STR reduction in pre-renewal

**SC_BLIND** (player debuff, `player_active_scs["SC_BLIND"]`):
- HIT -= HIT * 25 / 100 (status.c:4817-4818)
- FLEE -= FLEE * 25 / 100 (status.c:4902-4903)

**SC_STONE** on target (status ailment, `target_active_scs["SC_STONE"]`):
- Element overridden → Earth Lv1 (status.c:5882-5883, 5901-5903)
- Hard DEF halved: `def >>= 1` (`#ifndef RENEWAL`, status.c:5013-5014)
- Hard MDEF +25%: `mdef += 25*mdef/100` (status.c:5153-5154)
- Force-hit: battle.c:5014-5015 `opt1 != OPT1_STONEWAIT` → `flag.hit = 1` → hit_chance = 100%
- Applies only in OPT1_STONE state (fully hardened), not OPT1_STONEWAIT (transition)

**SC_FREEZE** on target (status ailment, `target_active_scs["SC_FREEZE"]`):
- Element overridden → Water Lv1 (status.c:5880-5881, 5901-5902)
- Hard DEF halved: `def >>= 1` (`#ifndef RENEWAL`, status.c:5015-5016)
- Hard MDEF +25%: `mdef += 25*mdef/100` (status.c:5155-5156)
- Force-hit: battle.c:5014-5015 → hit_chance = 100%

**SC_STUN** on target (status ailment, `target_active_scs["SC_STUN"]`):
- No element change, no DEF/MDEF change
- Force-hit: battle.c:5014-5015 (OPT1_STUN) → hit_chance = 100%

**SC_SIEGFRIED** (player receives from party, `support_buffs["SC_SIEGFRIED"]`):
- `sc_val2 = 55 + 5*lv` (elemental resist %; max lv5 → 80%) (skill.c:13330, 13753)
- Adds `val2` to `sd->subele[]` for all non-Neutral elements (status.c:2233-2241):
  Water, Earth, Fire, Wind, Poison, Holy, Dark, Ghost
- Effect: reduces incoming elemental damage by `55+5*lv`% for each element
- Only applies when player is in a party (status.c:7159-7162)
- Pipeline: add `support_buffs["SC_SIEGFRIED"]` level → compute `55+5*lv` → pass as
  `target.sub_ele_bonus` (flat % added to all non-Neutral sub_ele in CardFix for incoming)

**Val-shift pattern** (for reference — no greps needed):
All song/ensemble ground-tile SCs use `sc_start4(ss, bl, type, 100, sg->skill_lv, sg->val1, sg->val2, 0, ...)` (skill.c:13753), so:
- `sc_val1 = skill_lv`, `sc_val2 = sg->val1` (primary effect), `sc_val3 = sg->val2` (secondary)
This explains why status.c reads `val2` for the primary effect on all these SCs.

---

### Architecture

**Data model** (all already stubbed in correct files):
- `PlayerBuild.support_buffs` — holds player-cast debuffs on enemy: SC_PROVOKE (int lv), SC_ETERNALCHAOS (bool), SC_DECREASEAGI (int lv), SC_SIEGFRIED (int lv)
- `PlayerBuild.player_active_scs` — holds enemy-cast debuffs on player: SC_CURSE (bool), SC_BLIND (bool), SC_DECREASEAGI (int lv)
- `Target.target_active_scs: dict[str,int]` — **NEW field** on Target dataclass; holds status ailments: SC_STONE, SC_FREEZE, SC_STUN (bool/int); also SC_ETERNALCHAOS, SC_PROVOKE, SC_DECREASEAGI if treating as target-state rather than support_buffs

**Routing decision** (follow gui_plan.md):
- "Applied Debuffs" (player-cast, e.g. Provoke, EternalChaos) → `support_buffs`; pipeline reads them to modify target effective stats
- "Status Ailments" (monster state, e.g. Stone/Freeze/Stun) → `Target.target_active_scs`; target_state_section's Monster State sub-group writes to Target directly

**New pipeline integration points** (no new modifier files needed):
1. `DefenseFix`: read `support_buffs["SC_ETERNALCHAOS"]` → set target `def2 = 0` (already supported conceptually via def2=0 path)
2. `DefenseFix`: read `support_buffs["SC_PROVOKE"]` → `def_percent -= (5+5*lv)`
3. `hit_chance.py`: if `target.target_active_scs` contains SC_STONE/SC_FREEZE/SC_STUN → return 100%
4. `AttrFix` or pipeline setup: if `target.target_active_scs` has SC_STONE → override element to Earth Lv1; SC_FREEZE → Water Lv1
5. `DefenseFix` (or new inline step): SC_STONE/SC_FREEZE → halve target hard DEF; MDEF +25%
6. `StatusCalculator` (player-side): SC_DEC_AGI in `player_active_scs` → agi -= 2+lv; SC_CURSE → luk=0, atk_pct-=25; SC_BLIND → hit×0.75, flee×0.75
7. Incoming pipeline: SC_SIEGFRIED → add `55+5*lv` to all non-Neutral sub_ele before CardFix

**G70 fix** — Skill List filter: one-line fix, trivial; likely the initial signal connection
fires before job_id is set. Inspect `combat_controls.py` — probably just needs to call
`_on_job_changed(self._job_combo.currentData())` in `__init__` after populating.

---

### GUI Work

**`target_state_section.py`** — new file (not yet created). Full spec in `docs/gui_plan.md`.

Layout: flat rows (no CollapsibleSubGroups). One widget per row — `QCheckBox` for boolean, `LevelWidget(max_lv, include_off=True)` for leveled. No row has both.

Structure:
- Applied Debuffs rows: SC_ETERNALCHAOS (checkbox), SC_PROVOKE (LevelWidget 1-10), SC_DECREASEAGI (LevelWidget 1-10), PR_LEXAETERNA (checkbox)
- `QFrame(shape=HLine)` separator
- Status Ailments rows: SC_STUN/SC_FREEZE/SC_STONE/SC_POISON (all checkboxes; Freeze↔Stone mutually exclusive)
- Monster State rows (hidden when player target): Element QComboBox + Strip/Divest checkboxes (Weapon/Armor/Shield/Helm)
- `collect_into(build, target)` — debuffs → support_buffs, ailments → target.target_active_scs, element → target.element_override
- `state_changed = Signal()` → triggers pipeline re-run
- Add entry to `layout_config.json` at combat position 4 (before step_breakdown)

**`player_debuffs_section.py`** — already scaffolded, add actual rows (same one-widget pattern):
- SC_ETERNALCHAOS (checkbox), SC_CURSE (checkbox), SC_BLIND (checkbox), SC_DECREASEAGI (LevelWidget 1-10)
- Update `collect_into` and `load_build` to round-trip all four

**`main_window.py`** wiring:
- `target_state_section.state_changed` → `_on_build_changed()`
- Pass target_state data through to pipeline (via Target fields + build support_buffs)

---

### Strip/Divest
Zeroing mechanism per piece:
- Weapon stripped → target weapon ATK = 0 (affects BaseDamage atk range for mob: mob.atk_min/max = 0)
- Armor stripped → target equip_def = 0 (in DefenseFix: hard DEF component)
- Shield stripped → target equip_def shield portion = 0 (approximate: halve hard DEF; or separate field)
- Helm stripped → same as shield (approximation acceptable for now)
Note: exact per-slot DEF breakdown not tracked on Target — use a single `target_stripped_def_pct: float` override (0.0–1.0) or per-piece bool + 25% reduction per piece as approximation.

---

### PR_LEXAETERNA
- Doubles the next magic hit (SC_LEXAETERNA): `damage *= 2` as a post-pipeline multiplier on next BF_MAGIC hit
- `support_buffs["PR_LEXAETERNA"]` bool → MagicPipeline applies ×2 multiplier when True
- No Hercules grep needed: this is a simple ×2 modifier; already documented in game mechanics

---

**Estimated tokens**: 30–40k (no Hercules greps; pure implementation + UI).

---

## Session S — Item Scripts Pass

**STUB**: This Session still needs to be planned out
Ensure all scripts work properly and begin implementing consumables.
The Hercules file detailing item scripts is "C:\Projects\PS_Calc\Hercules\doc\item_bonus.md"
That directory has a lot of useful documents in general

---

## Session TW — Job Stat Bonuses + Stat Planner

**Goal**: Two foundational features that share a stat data focus and fit one context window.

**Job Stat Bonuses (G64 + G65)**:
- Job bonus table from Hercules `pc.c` — stat gain per job level per job.
- Apply in StatusCalculator per `job_id` / `job_level`.
- Bonus stat display column updated to show job bonus as a named source.

**Stat Planner (Phase 5 partial)**:
- Stat point cost curve: each successive point in a stat costs more points
  (Hercules `pc.c` `pc_gets_status_point` or equivalent).
- New UI widget in StatsSection (or dedicated sub-section): shows remaining
  stat points, cost of next point per stat, and current total spent.
- No "what-if" mode. No comparison. Budget display only.

**Estimated tokens**: 30–40k (2 Hercules reads + implementation + UI).

---

## Session S — Item Scripts Pass

**STUB**: Needs planning sub-session (read `Hercules/doc/item_bonus.md` first).
Ensure all scripts work correctly and begin implementing consumable effects.
Scope to be finalised in a dedicated planning step before implementation begins.

---

## Session Scale — UI Scaling

**Goal**: App scales correctly across common resolutions and provides a manual override.

- Auto-detect active monitor DPI / resolution; derive a base scale factor.
- Apply scale factor to fonts, widget sizes, and layout spacing via QSS variables
  or programmatic scaling at startup.
- Manual adjustment slider in a settings area: further multiplies the auto-derived scale.
- Verify layout at 1280×720, 1920×1080, and at least one HiDPI config.
- `ui_scale_override: float` persisted in settings JSON.

**Estimated tokens**: 20–35k depending on how many layout fixes are needed.

---

## Alpha Test

---

## Post-Alpha: UX Pass *(parallel with Payon Stories Config work)*

### Session U (and U2, U3 … as needed) — Blacksmith + Guild Buffs + Alpha Bug Fixes

**Goal**: Fix all bugs surfaced during alpha; implement remaining known mechanics gaps.
Scope is intentionally open-ended — one session per logical cluster of bugs/fixes.

Confirmed pre-load items:
- **G66** — Blacksmith: Weaponry Mastery ATK bonus, Overthrust cap→5,
  Adrenaline Rush self/party split, Skin Tempering DEF+resistance,
  Cart Revolution in skill list, Mammonite ratio.
- **G49 remainder** — Guild Buffs sub-group (`GD_BATTLEORDER`).
- Alpha bug fixes as discovered during testing.

Each U-session is scoped at session start once bugs are known.

---

### Session UX-1 — GUI/UX Polish

Visual consistency, tooltip completeness, section ordering review, accessibility basics.
Scope defined after alpha feedback is collected.

---

### Session UX-2 — Easy Gimme Features

Low-hanging advanced features that don't require new architecture:
- **G67** — Equipment section card field rework.
- **G58** — Card browser edge cases.
- **G14** — bWeaponAtk (weapon-type ATK%).
- **G68** — pdef=1 card bonuses (def_ratio_atk_ele/race).
- **G50 remainder** — HT_STEELCROW, AC_VULTURE/GS_SNAKEEYE range tracking.
- **G53** — Falcon/Blitz Beat proc system (if in scope by then).
- **G44** — Forge toggle restriction (if DB consolidation resolved).
- **G51** — SC_NIBELUNGEN DEF bypass (if Hercules devs have responded).
- **G74** — NJ_ISSEN HP-based damage formula.
- **G75** — NJ_ZENYNAGE / GS_FLING BF_MISC wiring.
- **G76** — GS_MAGICALBULLET: pass StatusData into SkillRatio (architectural) + implementation.

---

## Payon Stories Config

**Scale**: Comparable in total effort to all pre-alpha work combined.
Toggleable deviations from stock Hercules pre-renewal — custom skill behaviour,
stat changes, mob modifications, and server-rate overrides specific to the
Payon Stories private server. Individual sessions to be planned as work begins.

Sessions to be defined here as scope is understood. Each session will follow the
standard Source Verification rule: every custom value must be traced to the
Payon Stories config files or patch notes, not inferred.

---

## Post-Config

### Session Comparison — Multi-Variant Builds (Phase 6)

Multiple build variants stored within a single save file, toggled via buttons.
Side-by-side diff view showing delta between active variant and a reference variant.
Exact UI placement TBD (likely a toolbar row above the builder panel).

### Session Histogram — Distribution Graph (Phase 7)

pyqtgraph TTK distribution histogram: median, 10th/90th percentile,
normal vs crit overlay. Requires PMF variance tuple structure to be correct first.

---

## Advanced Combat Modelling *(last)*

### Session Adv-1 — Turn-Sequence + Combo System

Turn-sequence infrastructure. Stance-state modelling. Combo skill chains.
AttackDefinition `state_requirement` / `next_state` seam becomes live.
Also includes: **GD_BLOODLUST** (HP drain on hit) and **SC_DEVOTION** (Crusader damage
redirect) — both require post-hit event modelling that this session's infrastructure enables.

### Session Adv-2 — Status Ailments (Advanced)

Proc chance, turn interaction, debuff-on-hit mechanics.
Upgrades the simple-toggle ailment toggles from Session R to full modelling.

### Session Adv-3 — Markov DPS Steady-State (G57)

Replace `FormulaSelectionStrategy` with `MarkovSelectionStrategy`
(eigenvector of transition matrix). Requires Adv-1 combo system as prerequisite.

---

## Deferred Indefinitely

| Item | Reason |
|---|---|
| **G41 — PC VIT DEF discrepancy** | Hercules comment vs C code disagree. Investigate vs official server data before any fix. Currently following C implementation. |
| **Rebirth / Star Gladiator / Soul Linker** | Out of scope until content expansion. |
| **Healing calculator** | Separate feature mode; deferred until core is stable. |
