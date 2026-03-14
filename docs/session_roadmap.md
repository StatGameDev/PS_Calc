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
| R | Target debuff system: target_active_scs on Target; TargetStateSection UI; SC_STONE/FREEZE/STUN/PROVOKE/EC in defense_fix + hit_chance; PR_LEXAETERNA in magic_pipeline; SC_SIEGFRIED moved to support_buffs; G70 skill combo fix on load. | G48, G70 |
| Arch | Debuff routing fix: `collect_target_player_scs()` on TargetStateSection; new `target_utils.apply_mob_scs()`; pvp path feeds stat-cascade SCs into pvp_eff before StatusCalculator. | G78 |
| SC1 | Target debuffs: SC_BLIND/CURSE/SLEEP/POISON/QUAGMIRE/MINDBREAKER/CRUCIS/BLESSING in apply_mob_scs + StatusCalculator player path. SC_DONTFORGETME with dancer AGI QSpinBox (val2=agi/10+3×lv+5, skill.c:13270; aspd_rate+=10×val2, status.c:5667). Boss protocol: set_is_boss() disables immune widgets; apply_mob_scs guards per-SC. New Target fields: str/dex/hit/def_percent/mdef_percent/matk_percent/aspd_rate. | G79, G81 |
| SC2 | Player debuffs + G77. Full player_debuffs_section.py UI (14 widgets). StatusCalculator: SC_POISON (def_percent−25), SC_PROVOKE (def_percent−(5+5lv)), SC_ETERNALCHAOS (def2=0), SC_DONTFORGETME (aspd_rate+=10×val2), SC_MINDBREAKER (matk boost). player_build_to_target(): STUN/FREEZE/STONE/SLEEP → target_active_scs + FREEZE→Water/STONE→Earth element. G77: Lex Aeterna ×2 in _run_branch() after FinalRateBonus (all BF_WEAPON). | G77, G80 |
| S-1 – S-6 | Item Scripts Pass (complete). S-1: bonus_definitions.py table-driven refactor + bAgiVit/bAgiDexStr fix. S-2: bMatkRate/bMaxHPrate wired; build_applicator.py extracted. S-3: bAtkEle/bDefEle element precedence; resolve_armor_element(); DerivedSection ATK/DEF Ele rows. S-4: scraper expanded (3837 items); SCEffect model + parse_sc_start(). S-5: consumable_buffs + bonus_matk_flat; consumables_section.py. S-6 + G82: dual-wield LH element routing (script_atk_ele_rh/lh, lr_flag, pc.c:2588-2609); skill element in AttrFix (battle.c:4807 skill->get_ele). | G82 |
| T | Job Stat Bonuses (G64, G65): job_db2.txt parsed in DataLoader; get_job_bonus_stats() applied in StatusCalculator; StatsSection gains Next+ column, stat points spent/remaining label, job bonus in tooltip; JOBL_UPPER +52 for trans jobs. Stat cost formula: 1+(v+9)//10 (pc.c:7191). | G64, G65 |

---



---

## Session Pre-Alpha-2 — Consumables Format-Change Bug

**Symptom:** Expanding the Consumables section causes the Base Stats section to change visual format (appears to switch to compact/slim layout unexpectedly).

**Investigation so far (Pre-Alpha-1):**
- `consumables_section.py` — clean; no cross-section signals, `expand_requested` never emitted.
- `panel_container.py` — `set_slim_mode` only called from `set_focus_state()`; no path from consumables expanding to slim mode.
- `panel.py` — builder panel uses `QScrollArea(ScrollBarAsNeeded vertical)`; when consumables expands, vertical scrollbar may appear, narrowing viewport by ~15px.
- Root cause not confirmed.

**Next step:** Add `print(..., file=sys.stderr)` to `StatsSection._enter_slim()`. Ask user to open consumables and report whether the print fires. If it fires → slim mode is being triggered somewhere unexpected; trace back the `set_slim_mode(True)` call. If it does not fire → the format change is a grid/layout reflow from the viewport width change, not a compact-mode switch.

**Estimated tokens:** 10–20k (likely quick once runtime confirms or denies slim mode path).

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
