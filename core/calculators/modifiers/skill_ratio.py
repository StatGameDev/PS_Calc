from core.models.skill import SkillInstance
from core.models.damage import DamageResult
from core.models.build import PlayerBuild
from core.data_loader import loader
from pmf.operations import _scale_floor, pmf_stats

# Pre-renewal BF_WEAPON skill ratios from battle_calc_skillratio BF_WEAPON switch.
# Source: battle.c:2039 battle_calc_skillratio, case BF_WEAPON. Each lambda: (lv, tgt) → int ratio %.
# tgt is a Target instance (or None for skills that don't depend on target stats).
# Skills not listed fall back to ratio_base / ratio_per_level in skills.json, or default 100.
#
# Deferred to Q3 (special mechanics — not simple level-linear):
#   KN_PIERCE     — hit_count = tgt.size+1 (1/2/3 for Small/Med/Large, battle.c:4721); ratio only is 100+10*lv
#   AS_SPLASHER   — ratio 500+50*lv but adds 20*AS_POISONREACT mastery (battle.c:2249-2252); BF_WEAPON #ifndef RENEWAL (skill.c:5200)
#   RG_BACKSTAP   — ratio 300+40*lv but bow+penalty = 200+20*lv (battle.c:2152-2156)
#   BA_DISSONANCE — BF_MISC, not BF_WEAPON; flat 30+10*lv +MUSICALLESSON (battle.c:4260-4263)
#   TF_THROWSTONE — BF_MISC, flat 50 damage (battle.c:4257-4258)
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

    # --- Taekwon ---
    # battle.c:2281-2282
    "TK_STORMKICK":      lambda lv, tgt: 160 + 20 * lv,
    # battle.c:2278-2279
    "TK_DOWNKICK":       lambda lv, tgt: 160 + 20 * lv,
    # battle.c:2284-2285
    "TK_TURNKICK":       lambda lv, tgt: 190 + 30 * lv,
    # battle.c:2287-2288
    "TK_COUNTER":        lambda lv, tgt: 190 + 30 * lv,
}

# Hit count overrides for BF_WEAPON skills whose div_ is set to target-size+1 in battle.c.
# Each lambda: (lv, tgt) → int hit_count. Used instead of number_of_hits from skills.json.
# battle.c:4719-4722: wd.div_ = (wd.div_>0 ? tstatus->size+1 : -(tstatus->size+1))
# Target size: SZ_SMALL=0 → 1 hit, SZ_MEDIUM=1 → 2 hits, SZ_LARGE=2 → 3 hits.
# Falls back to skills.json number_of_hits (= max value) when target is None.
_BF_WEAPON_HIT_COUNT_FN: dict = {
    "KN_PIERCE": lambda lv, tgt: (tgt.size + 1) if tgt is not None else 3,
}

# BF_WEAPON skills with confirmed ratios implemented in this module.
# Automatically derived from _BF_WEAPON_RATIOS keys.
# BattlePipeline checks this set to set dps_valid=True only when ratio is known.
IMPLEMENTED_BF_WEAPON_SKILLS: frozenset[str] = frozenset(_BF_WEAPON_RATIOS.keys())

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

        # Priority: _BF_WEAPON_RATIOS dict (Q1+) → ratio_per_level in JSON → ratio_base → 100.
        ratio_fn = _BF_WEAPON_RATIOS.get(skill_name)
        if ratio_fn is not None:
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
        pmf = _scale_floor(pmf, hit_count, 1)

        mn, mx, av = pmf_stats(pmf)
        result.add_step(
            name=f"Skill Ratio (ID {skill.id} Lv {skill.level})",
            value=av,
            min_value=mn,
            max_value=mx,
            multiplier=ratio / 100.0,
            note=skill_data.get("description", "") if skill_data else "",
            formula=(f"dmg × {ratio}% × {display_hits} cosmetic hits   ({ratio_src})"
                     if cosmetic else
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