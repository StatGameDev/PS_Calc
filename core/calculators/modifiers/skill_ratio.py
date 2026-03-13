from core.models.skill import SkillInstance
from core.models.damage import DamageResult
from core.models.build import PlayerBuild
from core.data_loader import loader
from pmf.operations import _scale_floor, _add_flat, pmf_stats

# Pre-renewal BF_WEAPON skill ratios from battle_calc_skillratio BF_WEAPON switch.
# Source: battle.c:2039 battle_calc_skillratio, case BF_WEAPON. Each lambda: (lv, tgt) → int ratio %.
# tgt is a Target instance (or None for skills that don't depend on target stats).
# Skills not listed fall back to ratio_base / ratio_per_level in skills.json, or default 100.
#
# Deferred (special mechanics — not simple level-linear):
#   AS_SPLASHER   — ratio 500+50*lv but adds 20*AS_POISONREACT mastery (battle.c:2249-2252); BF_WEAPON #ifndef RENEWAL (skill.c:5200)
#   RG_BACKSTAP   — ratio 300+40*lv but bow+penalty = 200+20*lv (battle.c:2152-2156)
#   NJ_ISSEN      — #ifndef RENEWAL: wd.damage = 40*STR + lv*(HP/10 + 35) (replaces base damage; needs skill_params: current HP input)
#   GS_MAGICALBULLET — BF_WEAPON dispatch (skill.c:4862) with ATK_ADD(MATK) #ifndef RENEWAL (battle.c:5503-5505); needs StatusData in SkillRatio
#   BA_DISSONANCE — BF_MISC, not BF_WEAPON; flat 30+10*lv +MUSICALLESSON (battle.c:4260-4263)
#   TF_THROWSTONE — BF_MISC, flat 50 damage (battle.c:4257-4258)
#   NJ_ZENYNAGE   — BF_MISC dispatch (skill.c:5550); zeny-cost random damage (battle.c:4341-4349)
#   GS_FLING      — BF_MISC dispatch (skill.c:5548); damage = job_level (battle.c:4350)
#   HT_LANDMINE   — BF_MISC, lv*(dex+75)*(100+int)/100 (battle.c:4228-4230)
#   HT_BLASTMINE  — BF_MISC, lv*(dex/2+50)*(100+int)/100 (battle.c:4232-4233)
#   HT_CLAYMORETRAP — BF_MISC, lv*(dex/2+75)*(100+int)/100 (battle.c:4235-4236)
_BF_WEAPON_RATIOS: dict = {
    # --- Swordman / Knight / Crusader ---
    # battle.c:2042-2044
    "SM_BASH":           lambda lv, tgt: 100 + 30 * lv,
    # battle.c:2046-2048; BF_LONG (range=9 in skill_db); fire endow handled separately via SC
    "SM_MAGNUM":         lambda lv, tgt: 100 + 20 * lv,
    # battle.c:2091-2095; primary target only (flag=0); AoE ring cells use flag 1/2/3 (Q3)
    "KN_BRANDISHSPEAR":  lambda lv, tgt: 100 + 20 * lv,
    # battle.c:2085-2086
    "KN_SPEARSTAB":      lambda lv, tgt: 100 + 20 * lv,
    # battle.c:2088-2089; BF_LONG from lv2 (range=[3,5,7,9,11])
    "KN_SPEARBOOMERANG": lambda lv, tgt: 100 + 50 * lv,
    # battle.c:2078-2080; hit_count overridden by _BF_WEAPON_HIT_COUNT_FN below (tgt.size+1)
    "KN_PIERCE":         lambda lv, tgt: 100 + 10 * lv,
    # battle.c:2104-2106
    "KN_BOWLINGBASH":    lambda lv, tgt: 100 + 40 * lv,
    # battle.c:2164-2165
    "CR_SHIELDCHARGE":   lambda lv, tgt: 100 + 20 * lv,
    # battle.c:2167-2168; BF_LONG from lv2 (range=[3,5,7,9,11])
    "CR_SHIELDBOOMERANG": lambda lv, tgt: 100 + 30 * lv,
    # battle.c:2170-2179; RENEWAL adds 2hspear bonus — not applicable in pre-re
    "CR_HOLYCROSS":      lambda lv, tgt: 100 + 35 * lv,

    # --- Merchant ---
    # battle.c:2050-2051
    "MC_MAMMONITE":      lambda lv, tgt: 100 + 50 * lv,

    # --- Thief / Assassin / Rogue ---
    # No case in switch → default ratio=100. Include for dps_valid. battle.c:no case
    "TF_POISON":         lambda lv, tgt: 100,
    # battle.c:2117-2118
    "TF_SPRINKLESAND":   lambda lv, tgt: 130,
    # battle.c:2114-2115; skills.json number_of_hits=-8 (cosmetic); ratio encodes full damage
    "AS_SONICBLOW":      lambda lv, tgt: 400 + 40 * lv,
    # battle.c:2108-2109
    "AS_GRIMTOOTH":      lambda lv, tgt: 100 + 20 * lv,
    # No case in switch → default ratio=100 (atk=Misc in skill_db but BF_WEAPON in castend). battle.c:no case
    "AS_VENOMKNIFE":     lambda lv, tgt: 100,
    # battle.c:2158-2159
    "RG_RAID":           lambda lv, tgt: 100 + 40 * lv,
    # battle.c:2161-2162; "copies skill" is a gameplay mechanic, ratio itself is level-linear
    "RG_INTIMIDATE":     lambda lv, tgt: 100 + 30 * lv,

    # --- Archer / Hunter ---
    # battle.c:2056-2058; BF_LONG (range=-9 → bow weapon)
    "AC_DOUBLE":         lambda lv, tgt: 100 + 10 * (lv - 1),
    # battle.c:2060-2066 #else RENEWAL
    "AC_SHOWER":         lambda lv, tgt: 75 + 5 * lv,
    # battle.c:2068-2070; BF_LONG
    "AC_CHARGEARROW":    lambda lv, tgt: 150,
    # battle.c:2357-2358; BF_LONG
    "HT_PHANTASMIC":     lambda lv, tgt: 150,

    # --- Monk ---
    # battle.c:2211-2212
    "MO_CHAINCOMBO":     lambda lv, tgt: 150 + 50 * lv,
    # battle.c:2214-2215
    "MO_COMBOFINISH":    lambda lv, tgt: 240 + 60 * lv,
    # battle.c:2360-2361
    "MO_BALKYOUNG":      lambda lv, tgt: 300,

    # --- Bard / Dancer ---
    # battle.c:2217-2219; both share same case; BF_LONG (range=9)
    "BA_MUSICALSTRIKE":  lambda lv, tgt: 125 + 25 * lv,
    "DC_THROWARROW":     lambda lv, tgt: 125 + 25 * lv,

    # --- Alchemist ---
    # battle.c:2181-2182; complex MATK+ATK formula is #ifdef RENEWAL only; pre-re: standard pipeline
    "AM_DEMONSTRATION":  lambda lv, tgt: 100 + 20 * lv,
    # battle.c:2184-2189 #else (pre-re): skillratio += 40*lv; def1 forced to 0 in DefenseFix (battle.c:1474 #ifndef RENEWAL)
    "AM_ACIDTERROR":     lambda lv, tgt: 100 + 40 * lv,

    # --- Hunter traps ---
    # battle.c:2073-2077 #ifndef RENEWAL
    "HT_FREEZINGTRAP":   lambda lv, tgt: 50 + 10 * lv,

    # --- Knight ---
    # battle.c: no case in skillratio switch → default 100; BF_NORMAL flag + halved amotion (timing only)
    "KN_AUTOCOUNTER":    lambda lv, tgt: 100,

    # --- Monk ---
    # battle.c:2191-2192; hit_count = spirit spheres held (battle.c:4698-4704: wd.div_ = sd->spiritball_old)
    "MO_FINGEROFFENSIVE": lambda lv, tgt: 100 + 50 * lv,
    # battle.c:2194-2195; flag.pdef=flag.pdef2=2 (battle.c:4759) → DEF reversal handled in DefenseFix
    "MO_INVESTIGATE":    lambda lv, tgt: 100 + 75 * lv,

    # --- Taekwon ---
    # battle.c:2281-2282
    "TK_STORMKICK":      lambda lv, tgt: 160 + 20 * lv,
    # battle.c:2278-2279
    "TK_DOWNKICK":       lambda lv, tgt: 160 + 20 * lv,
    # battle.c:2284-2285
    "TK_TURNKICK":       lambda lv, tgt: 190 + 30 * lv,
    # battle.c:2287-2288
    "TK_COUNTER":        lambda lv, tgt: 190 + 30 * lv,

    # --- Gunslinger ---
    # battle.c:2300-2302: skillratio += 50*lv
    "GS_TRIPLEACTION":   lambda lv, tgt: 100 + 50 * lv,
    # battle.c:2303-2308: +400 vs Brute/Demi-Human non-boss only (#ifndef RENEWAL guard not present)
    "GS_BULLSEYE":       lambda lv, tgt: 100 + (400 if (tgt and tgt.race in ("Brute", "Demi-Human") and not tgt.is_boss) else 0),
    # battle.c:2309-2311: skillratio += 100*(lv+1) → 200+100*lv
    "GS_TRACKING":       lambda lv, tgt: 200 + 100 * lv,
    # battle.c:2313-2315 #ifndef RENEWAL: skillratio += 20*lv
    "GS_PIERCINGSHOT":   lambda lv, tgt: 100 + 20 * lv,
    # battle.c:2317-2318: skillratio += 10*lv
    "GS_RAPIDSHOWER":    lambda lv, tgt: 100 + 10 * lv,
    # battle.c:2320-2323: skillratio += 50*(lv-1); SC_FALLEN_ANGEL×2 is renewal-only → 50+50*lv
    "GS_DESPERADO":      lambda lv, tgt: 50 + 50 * lv,
    # battle.c:2325-2326: skillratio += 50*lv
    "GS_DUST":           lambda lv, tgt: 100 + 50 * lv,
    # battle.c:2328-2329: skillratio += 100*(lv+2) → 300+100*lv
    "GS_FULLBUSTER":     lambda lv, tgt: 300 + 100 * lv,
    # battle.c:2331-2337 #ifndef RENEWAL: skillratio += 20*(lv-1)
    "GS_SPREADATTACK":   lambda lv, tgt: 100 + 20 * (lv - 1),

    # --- Ninja BF_WEAPON ---
    # battle.c:2338-2339: skillratio += 50 + 150*lv → 150+150*lv
    "NJ_HUUMA":          lambda lv, tgt: 150 + 150 * lv,
    # battle.c:2344-2345: skillratio += 10*lv
    "NJ_KASUMIKIRI":     lambda lv, tgt: 100 + 10 * lv,
    # battle.c:2347-2348: skillratio += 100*(lv-1) → 100*lv
    "NJ_KIRIKAGE":       lambda lv, tgt: 100 * lv,
    # No case in calc_skillratio → default 100%; mastery +60 in MasteryFix (battle.c:852-855 #ifndef RENEWAL)
    "NJ_KUNAI":          lambda lv, tgt: 100,
    # No case in calc_skillratio → default 100%; ATK_ADD(4*lv) applied as flat below (battle.c:5506 #ifndef RENEWAL)
    "NJ_SYURIKEN":       lambda lv, tgt: 100,
}

# Hit count overrides for BF_WEAPON skills whose div_ is set to target-size+1 in battle.c.
# Each lambda: (lv, tgt) → int hit_count. Used instead of number_of_hits from skills.json.
# battle.c:4719-4722: wd.div_ = (wd.div_>0 ? tstatus->size+1 : -(tstatus->size+1))
# Target size: SZ_SMALL=0 → 1 hit, SZ_MEDIUM=1 → 2 hits, SZ_LARGE=2 → 3 hits.
# Falls back to skills.json number_of_hits (= max value) when target is None.
_SIZE_TO_HITS = {"Small": 1, "Medium": 2, "Large": 3}
_BF_WEAPON_HIT_COUNT_FN: dict = {
    # battle.c:4719-4722: wd.div_ = tstatus->size+1; SZ_SMALL=0→1hit, SZ_MEDIUM=1→2, SZ_LARGE=2→3
    "KN_PIERCE": lambda lv, tgt: _SIZE_TO_HITS.get(tgt.size, 2) if tgt is not None else 3,
}

# Q2-cont: Skills whose ratio depends on build.skill_params (runtime combat context).
# Cannot be plain lambdas — require 'build' as well as 'lv' and 'tgt'.
# Handled via special-case blocks in SkillRatio.calculate() before the dict lookup.
# Formulas confirmed from Hercules source (no re-read needed — see session_roadmap.md Q2):
#   KN_CHARGEATK:     ratio = 100 + 100*min((dist-1)//3, 2)  (battle.c:2350-2359)
#   MC_CARTREVOLUTION: ratio = 150 + cart_pct                 (battle.c:2120-2127; +50+100*w/wmax)
#   MO_EXTREMITYFIST: ratio = min(100+100*(8+sp//10), 60000)  (battle.c:2197-2206 #ifndef RENEWAL)
#   TK_JUMPKICK:      ratio = (30+10*lv [+10*lv//3 if combo]) * (2 if running)  (battle.c:2290-2300)
_BF_WEAPON_PARAM_SKILLS: frozenset[str] = frozenset({
    "KN_CHARGEATK",
    "MC_CARTREVOLUTION",
    "MO_EXTREMITYFIST",
    "TK_JUMPKICK",
})

# BF_WEAPON skills with confirmed ratios implemented in this module.
# Automatically derived from _BF_WEAPON_RATIOS keys + param-skill set.
# BattlePipeline checks this set to set dps_valid=True only when ratio is known.
IMPLEMENTED_BF_WEAPON_SKILLS: frozenset[str] = (
    frozenset(_BF_WEAPON_RATIOS.keys()) | _BF_WEAPON_PARAM_SKILLS
)

# BF_MISC skills (traps, throw, zeny attacks). Populated when BF_MISC is implemented.
_BF_MISC_RATIOS: dict = {}
IMPLEMENTED_BF_MISC_SKILLS: frozenset[str] = frozenset(_BF_MISC_RATIOS.keys())

# Pre-renewal magic skill ratios from battle_calc_skillratio BF_MAGIC switch.
# Source: battle.c:1631-1785 #else not RENEWAL.
# All unlisted skills use default ratio = 100.
# ELE_UNDEAD = 9 (map.h). Default undead_detect_type=0 → element check only.
_BF_MAGIC_RATIOS = {
    "MG_NAPALMBEAT":   lambda lv, tgt: 70 + 10 * lv,
    "MG_FIREBALL":     lambda lv, tgt: 70 + 10 * lv,   # pre-re: same formula as napalmbeat
    "MG_SOULSTRIKE":   lambda lv, tgt: 100 + (5 * lv if (tgt and tgt.element == 9) else 0),
    "MG_FIREWALL":     lambda lv, tgt: 50,
    "MG_THUNDERSTORM": lambda lv, tgt: 80,              # pre-re: skillratio -= 20
    "MG_FROSTDIVER":   lambda lv, tgt: 100 + 10 * lv,
    "AL_HOLYLIGHT":    lambda lv, tgt: 125,
    "AL_RUWACH":       lambda lv, tgt: 145,
    "WZ_FROSTNOVA":    lambda lv, tgt: (100 + 10 * lv) * 2 // 3,
    "WZ_FIREPILLAR":   lambda lv, tgt: 40 + 20 * lv,   # lv <= 10; lv > 10 not in pre-re
    "WZ_SIGHTRASHER":  lambda lv, tgt: 100 + 20 * lv,
    "WZ_WATERBALL":    lambda lv, tgt: 100 + 30 * lv,
    "WZ_STORMGUST":    lambda lv, tgt: 100 + 40 * lv,
    "HW_NAPALMVULCAN": lambda lv, tgt: 70 + 10 * lv,
    "WZ_VERMILION":    lambda lv, tgt: 80 + 20 * lv,   # pre-re: #else RENEWAL (20*lv-20)
    # battle.c:1631-1785 BF_MAGIC switch — no case for these skills → default ratio 100.
    # Multi-hit comes from number_of_hits in skills.json (lv hits each).
    # battle.c:4005-4007 (bolt spell section, inside default: block which calls calc_skillratio)
    "MG_COLDBOLT":     lambda lv, tgt: 100,
    "MG_FIREBOLT":     lambda lv, tgt: 100,
    "MG_LIGHTNINGBOLT": lambda lv, tgt: 100,
    # WZ_JUPITEL: no case in BF_MAGIC switch; multi-hit by level from skills.json
    "WZ_JUPITEL":      lambda lv, tgt: 100,
    # WZ_EARTHSPIKE: no case in BF_MAGIC switch; single-hit each cast
    "WZ_EARTHSPIKE":   lambda lv, tgt: 100,
    # WZ_HEAVENDRIVE/WZ_METEOR: case only in #ifdef RENEWAL block; pre-re uses default 100
    "WZ_HEAVENDRIVE":  lambda lv, tgt: 100,
    "WZ_METEOR":       lambda lv, tgt: 100,
    # PR_MAGNUS: no case in BF_MAGIC switch; standard MATK × 100%; targets Undead/Demon only
    "PR_MAGNUS":       lambda lv, tgt: 100,

    # --- Ninja BF_MAGIC ---
    # battle.c:1699-1702: skillratio -= 10 → base 90.
    # NOTE: +20*charm_count if CHARM_TYPE_FIRE active (sd->charm_type/charm_count) — DEFERRED (charm not implemented).
    "NJ_KOUENKA":      lambda lv, tgt: 90,
    # battle.c:1704-1708: skillratio -= 50 → base 50.
    # NOTE: +10*charm_count if CHARM_TYPE_FIRE — DEFERRED.
    "NJ_KAENSIN":      lambda lv, tgt: 50,
    # battle.c:1709-1713: skillratio += 50*(lv-1) → 50+50*lv.
    # NOTE: +15*charm_count if CHARM_TYPE_FIRE — DEFERRED.
    "NJ_BAKUENRYU":    lambda lv, tgt: 50 + 50 * lv,
    # battle.c:1715-1720: case is #ifdef RENEWAL only → pre-re default 100.
    "NJ_HYOUSENSOU":   lambda lv, tgt: 100,
    # battle.c:1723-1726: skillratio += 50*lv → 100+50*lv.
    # NOTE: +25*charm_count if CHARM_TYPE_WATER — DEFERRED.
    "NJ_HYOUSYOURAKU": lambda lv, tgt: 100 + 50 * lv,
    # battle.c:1728-1731: skillratio += 60+40*lv → 160+40*lv.
    # NOTE: +15*charm_count if CHARM_TYPE_WIND — DEFERRED.
    "NJ_RAIGEKISAI":   lambda lv, tgt: 160 + 40 * lv,
    # battle.c:1733-1755: falls through to NPC_ENERGYDRAIN: skillratio += 100*lv → 100+100*lv.
    # NOTE: +10*charm_count if CHARM_TYPE_WIND applied before fall-through — DEFERRED.
    "NJ_KAMAITACHI":   lambda lv, tgt: 100 + 100 * lv,
}

# BF_MAGIC skills with confirmed ratios implemented above.
# Derived from _BF_MAGIC_RATIOS keys; Q2+ will add more entries as ratios are verified.
# BattlePipeline checks this set to set dps_valid=True for magic skills.
IMPLEMENTED_BF_MAGIC_SKILLS: frozenset[str] = frozenset(_BF_MAGIC_RATIOS.keys())


class SkillRatio:
    """Exact Skill Ratio step.
    Source lines (verbatim from repo):
    battle.c: int ratio = battle_calc_skillratio(src, bl, skill_id, skill_lv,
    (skill_get_type(skill_id) == BF_WEAPON) ?
    skill_get_damage(skill_id, skill_lv) : 100);
    battle.c: wd.damage = (int64)wd.damage * ratio / 100;"""

    @staticmethod
    def calculate(skill: SkillInstance, pmf: dict, build: PlayerBuild, result: DamageResult,
                  target=None) -> dict:
        """Applies skill ratio and hit count to the PMF.

        target is passed through to ratio lambdas so Q2 stat-dependent skills
        (MO_INVESTIGATE, MO_EXTREMITYFIST, etc.) can access target DEF / HP.
        """
        skill_data = loader.get_skill(skill.id)
        skill_name = skill_data.get("name", "") if skill_data else ""

        # Priority: param skills (read build.skill_params) → _BF_WEAPON_RATIOS dict → JSON → default 100.
        params = getattr(build, 'skill_params', {})
        flat_add = 0  # ATK_ADD flat bonus applied after ratio scaling (NJ_SYURIKEN)
        if skill_name == "KN_CHARGEATK":
            # battle.c:2350-2359: skillratio += 100*(k ? (k-1)/3 : 0); capped at 300.
            # dist = cell distance (1–3→100%, 4–6→200%, 7+→300%).
            dist = params.get("KN_CHARGEATK_dist", 1)
            ratio = 100 + 100 * min((dist - 1) // 3, 2)
            ratio_src = f"KN_CHARGEATK dist={dist} (battle.c:2350-2359)"
        elif skill_name == "MC_CARTREVOLUTION":
            # battle.c:2120-2127: skillratio += 50 + 100*cart_weight/cart_weight_max.
            # cart_pct is 0–100 (weight %).
            cart_pct = params.get("MC_CARTREVOLUTION_pct", 0)
            ratio = 150 + cart_pct
            ratio_src = f"MC_CARTREVOLUTION cart={cart_pct}% (battle.c:2120-2127)"
        elif skill_name == "MO_EXTREMITYFIST":
            # battle.c:2197-2206 #ifndef RENEWAL: skillratio = min(100+100*(8+sp/10), 60000).
            sp = params.get("MO_EXTREMITYFIST_sp", 0)
            ratio = min(100 + 100 * (8 + sp // 10), 60000)
            ratio_src = f"MO_EXTREMITYFIST sp={sp} (battle.c:2197-2206 #ifndef RENEWAL)"
        elif skill_name == "TK_JUMPKICK":
            # battle.c:2290-2300: base=30+10*lv; +10*lv/3 if SC_COMBOATTACK; ×2 if SC_STRUP.
            combo = bool(params.get("TK_JUMPKICK_combo", False))
            running = bool(params.get("TK_JUMPKICK_running", False))
            ratio = 30 + 10 * skill.level + (10 * skill.level // 3 if combo else 0)
            if running:
                ratio *= 2
            ratio_src = (f"TK_JUMPKICK lv={skill.level} combo={combo} running={running}"
                         " (battle.c:2290-2300)")
        elif skill_name == "NJ_SYURIKEN":
            # battle.c:5506 #ifndef RENEWAL: ATK_ADD(4*skill_lv) in constant-additions block
            # after calc_skillratio returns; ratio itself has no case → default 100.
            ratio = 100
            flat_add = 4 * skill.level
            ratio_src = f"NJ_SYURIKEN ratio=100 +{flat_add} flat ATK (battle.c:5506 #ifndef RENEWAL)"
        elif (ratio_fn := _BF_WEAPON_RATIOS.get(skill_name)) is not None:
            ratio = ratio_fn(skill.level, target)
            ratio_src = f"_BF_WEAPON_RATIOS[{skill_name!r}]"
        elif skill_data and skill_data.get("ratio_per_level"):
            ratio_list = skill_data["ratio_per_level"]
            ratio = ratio_list[skill.level - 1] if skill.level <= len(ratio_list) else skill_data.get("ratio_base", 100)
            ratio_src = f"ratio_per_level[lv{skill.level}]"
        else:
            ratio = skill_data.get("ratio_base", 100) if skill_data else 100
            ratio_src = "ratio_base (default 100)"

        # SC_MAXIMIZEPOWER forces ratio = 100 (exact rule from battle_calc_skillratio)
        active = getattr(build, 'active_status_levels', {})
        if "SC_MAXIMIZEPOWER" in active:
            ratio = 100
            ratio_src = "SC_MAXIMIZEPOWER override"

        # SC_OVERTHRUST / SC_OVERTHRUSTMAX add to skillratio (not flat ATK).
        # status.c: SC_OVERTHRUST val3 = 5*val1 (self-cast, pre-renewal)
        # status.c: SC_OVERTHRUSTMAX val2 = 20*val1
        # SC_OVERTHRUSTMAX cancels SC_OVERTHRUST in the emulator — both can't be active.
        # battle.c:2919-2922 inside battle_calc_skillratio (no RENEWAL guard):
        #   if(sc->data[SC_OVERTHRUST])    skillratio += sc->data[SC_OVERTHRUST]->val3;
        #   if(sc->data[SC_OVERTHRUSTMAX]) skillratio += sc->data[SC_OVERTHRUSTMAX]->val2;
        if "SC_OVERTHRUST" in active:
            ratio += 5 * active["SC_OVERTHRUST"]
        if "SC_OVERTHRUSTMAX" in active:
            ratio += 20 * active["SC_OVERTHRUSTMAX"]

        # NK flags (loaded here – ready for future NK_IGNORE_DEF etc. checks)
        nk_flags = skill_data.get("nk_flags", []) if skill_data else []  # noqa: F841

        # Multi-hit from number_of_hits field.
        # Negative = cosmetic (ratio already encodes full damage; do NOT multiply pmf).
        # Positive = actual multi-hit (each hit is separate; multiply pmf × n).
        # Source: battle.c:3823 damage_div_fix macro.
        hit_count_raw = 1
        if skill_name == "MO_FINGEROFFENSIVE":
            # battle.c:4698-4704: wd.div_ = sd->spiritball_old (spheres held at cast).
            # Priority: skill_params override → active_status_levels["MO_SPIRITBALL"] (buffs area) → mastery fallback.
            spheres = params.get("MO_FINGEROFFENSIVE_spheres")
            if spheres is None:
                active_sl = getattr(build, 'active_status_levels', {})
                spheres = active_sl.get("MO_SPIRITBALL",
                          build.mastery_levels.get("MO_CALLSPIRITS", 1))
            hit_count_raw = max(1, spheres)
        else:
            hit_count_fn = _BF_WEAPON_HIT_COUNT_FN.get(skill_name)
            if hit_count_fn is not None:
                # Override: target-size-dependent hit count (e.g. KN_PIERCE: tgt.size+1).
                hit_count_raw = hit_count_fn(skill.level, target)
            elif skill_data:
                noh = skill_data.get("number_of_hits")
                if noh and skill.level <= len(noh):
                    hit_count_raw = noh[skill.level - 1]
        hit_count = hit_count_raw if hit_count_raw > 0 else 1
        display_hits = abs(hit_count_raw)
        cosmetic = hit_count_raw < 0

        # Two sequential scale() calls — keep separate to preserve Hercules integer rounding.
        # battle.c: wd.damage = (int64)wd.damage * ratio / 100;  (then × hit_count separately)
        pmf = _scale_floor(pmf, ratio, 100)
        if flat_add > 0:
            # ATK_ADD: applied after skillratio scale, before damage_div_fix (battle.c:5506 #ifndef RENEWAL)
            pmf = _add_flat(pmf, flat_add)
        pmf = _scale_floor(pmf, hit_count, 1)

        mn, mx, av = pmf_stats(pmf)
        result.add_step(
            name=f"Skill Ratio (ID {skill.id} Lv {skill.level})",
            value=av,
            min_value=mn,
            max_value=mx,
            multiplier=ratio / 100.0,
            note=skill_data.get("description", "") if skill_data else "",
            formula=(f"dmg × {ratio}% + {flat_add} × {display_hits} cosmetic hits   ({ratio_src})"
                     if (cosmetic and flat_add) else
                     f"dmg × {ratio}% × {display_hits} cosmetic hits   ({ratio_src})"
                     if cosmetic else
                     f"dmg × {ratio}% + {flat_add} × {hit_count} hits   ({ratio_src})"
                     if flat_add else
                     f"dmg × {ratio}% × {hit_count} hits   ({ratio_src})"),
            hercules_ref="battle.c: battle_calc_skillratio — BF_WEAPON ratio from _BF_WEAPON_RATIOS dict\n"
                         "battle.c:2919-2922: if(sc->data[SC_OVERTHRUST]) skillratio += SC_OVERTHRUST->val3;\n"
                         "battle.c:2921-2922: if(sc->data[SC_OVERTHRUSTMAX]) skillratio += SC_OVERTHRUSTMAX->val2;\n"
                         "battle.c: wd.damage = (int64)wd.damage * ratio / 100;\n"
                         "battle.c:3823: damage_div_fix: div>1 → dmg*=div; div<0 → cosmetic (unchanged)"
        )
        return pmf

    @staticmethod
    def calculate_magic(skill: SkillInstance, pmf: dict, build: PlayerBuild, target,
                        result: DamageResult) -> tuple:
        """Applies BF_MAGIC skill ratio (per-hit only). Returns (pmf, hit_count).

        hit_count is returned separately so the caller can apply it AFTER defense and
        attr_fix, matching the exact Hercules source order:
          MATK_RATE(skillratio) → calc_defense → attr_fix → × ad.div_
        Source: battle_calc_magic_attack, battle.c:1631-1785 (#else not RENEWAL).
        """
        skill_data = loader.get_skill(skill.id)
        skill_name = skill_data.get("name", "") if skill_data else ""

        ratio_fn = _BF_MAGIC_RATIOS.get(skill_name)
        ratio = ratio_fn(skill.level, target) if ratio_fn else 100

        # Raw hit count from skills.json number_of_hits — sign is significant:
        #   positive (e.g. +5): actual multi-hit — caller multiplies dmg × n after defense+attrfix
        #   negative (e.g. -3): cosmetic multi-hit — animation shows n hits, dmg is NOT multiplied
        # Source: battle.c:3823 damage_div_fix macro:
        #   if (div > 1) dmg *= div;          ← actual multi-hit
        #   else if (div < 0) div *= -1;      ← cosmetic: just flip sign for display, dmg unchanged
        hit_count_raw = 1
        if skill_data:
            noh = skill_data.get("number_of_hits")
            if noh and skill.level <= len(noh):
                hit_count_raw = noh[skill.level - 1]   # raw, NOT abs()

        pmf = _scale_floor(pmf, ratio, 100)

        display_hits = abs(hit_count_raw)
        cosmetic = hit_count_raw < 0
        mn, mx, av = pmf_stats(pmf)
        result.add_step(
            name=f"Magic Skill Ratio (ID {skill.id} Lv {skill.level})",
            value=av,
            min_value=mn,
            max_value=mx,
            multiplier=ratio / 100.0,
            note=skill_data.get("description", "") if skill_data else "",
            formula=(f"MATK × {ratio}%  ({display_hits} cosmetic hits — dmg not multiplied)"
                     if cosmetic else
                     f"MATK × {ratio}%  ({display_hits} hits applied after defense)"),
            hercules_ref="battle.c:1631-1785: battle_calc_skillratio BF_MAGIC switch (#else not RENEWAL)\n"
                         "battle.c:3823: damage_div_fix: div>1 → dmg*=div; div<0 → cosmetic (div negated, dmg unchanged)"
        )
        return pmf, hit_count_raw