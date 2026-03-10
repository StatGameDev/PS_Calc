"""
D4 — Gear Bonus Aggregator.
Computes GearBonuses from all equipped items in a build.

Usage:
    bonuses = GearBonusAggregator.compute(build.equipped)
"""
from __future__ import annotations

from typing import Dict, Optional, Union

from core.data_loader import loader
from core.item_script_parser import parse_script
from core.models.gear_bonuses import GearBonuses
from core.models.item_effect import ItemEffect


class GearBonusAggregator:

    @staticmethod
    def compute(
        equipped: Dict[str, Optional[int]],
        refine_levels: Optional[Dict[str, int]] = None,
    ) -> GearBonuses:
        """
        Parse scripts for all equipped item IDs and aggregate into GearBonuses.
        Slots with None or unknown IDs are silently skipped.

        refine_levels: build.refine_levels — used to compute armor refine DEF (G12).
          If None, armor refine DEF is skipped (backward-compatible).
        """
        bonuses = GearBonuses()
        refinedef_units = 0  # G12: accumulated raw units; rounding applied once after loop

        for slot, item_id in equipped.items():
            if item_id is None:
                continue
            item = loader.get_item(item_id)
            if item is None:
                continue

            if item.get("type") == "IT_ARMOR":
                # F2: sum base DEF from IT_ARMOR items (item["def"] field)
                bonuses.def_ += item.get("def", 0)
                # G12: armor refine DEF — accumulate raw units, round aggregate at end
                # status.c ~1655: refinedef += refine->get_bonus(REFINE_TYPE_ARMOR, r)
                if refine_levels is not None:
                    r = refine_levels.get(slot, 0)
                    if r > 0:
                        refinedef_units += loader.get_armor_refine_units(r)

            script = item.get("script") or ""
            if not script:
                continue

            effects = parse_script(script)
            bonuses.all_effects.extend(effects)

            for eff in effects:
                GearBonusAggregator._apply(bonuses, eff)

        # G12: status.c ~1713: bstatus->def += (refinedef + 50) / 100
        if refinedef_units > 0:
            bonuses.def_ += (refinedef_units + 50) // 100

        return bonuses

    @staticmethod
    def apply_passive_bonuses(bonuses: GearBonuses, mastery_levels: dict) -> None:
        """Augment GearBonuses in-place with resist/race bonuses from passive skills.
        Call immediately after compute() wherever gear_bonuses feeds CardFix or DefenseFix.
        Source: status_calc_pc_ (status.c, #ifndef RENEWAL guards noted).
        """
        # CR_TRUST: subele[Ele_Holy] += lv*5 (status.c:2187)
        cr_trust_lv = mastery_levels.get("CR_TRUST", 0)
        if cr_trust_lv:
            bonuses.sub_ele["Ele_Holy"] = bonuses.sub_ele.get("Ele_Holy", 0) + cr_trust_lv * 5

        # BS_SKINTEMPER: subele[Ele_Neutral] += lv; subele[Ele_Fire] += lv*4 (status.c:2189–2192)
        bs_skin_lv = mastery_levels.get("BS_SKINTEMPER", 0)
        if bs_skin_lv:
            bonuses.sub_ele["Ele_Neutral"] = bonuses.sub_ele.get("Ele_Neutral", 0) + bs_skin_lv
            bonuses.sub_ele["Ele_Fire"]    = bonuses.sub_ele.get("Ele_Fire", 0)    + bs_skin_lv * 4

        # SA_DRAGONOLOGY: #ifndef RENEWAL addrace[RC_Dragon] += lv*4 (weapon+magic); subrace[RC_Dragon] += lv*4
        # (status.c:2197–2210)
        sa_dragon_lv = mastery_levels.get("SA_DRAGONOLOGY", 0)
        if sa_dragon_lv:
            bonuses.add_race["RC_Dragon"] = bonuses.add_race.get("RC_Dragon", 0) + sa_dragon_lv * 4
            bonuses.sub_race["RC_Dragon"] = bonuses.sub_race.get("RC_Dragon", 0) + sa_dragon_lv * 4

    @staticmethod
    def _apply(bonuses: GearBonuses, eff: ItemEffect) -> None:
        """Route one ItemEffect into the appropriate GearBonuses field."""
        bt = eff.bonus_type
        p = eff.params

        if eff.arity == 1 and p:
            v = p[0] if isinstance(p[0], int) else 0
            _BONUS1_ROUTES.get(bt, _noop)(bonuses, v)

        elif eff.arity == 2 and len(p) >= 2:
            key = str(p[0])
            val = p[1] if isinstance(p[1], int) else 0

            if bt == "bAddRace":
                bonuses.add_race[key] = bonuses.add_race.get(key, 0) + val
            elif bt == "bSubEle":
                bonuses.sub_ele[key] = bonuses.sub_ele.get(key, 0) + val
            elif bt == "bSubRace":
                bonuses.sub_race[key] = bonuses.sub_race.get(key, 0) + val
            elif bt == "bAddSize":
                bonuses.add_size[key] = bonuses.add_size.get(key, 0) + val
            elif bt == "bAddEle":
                bonuses.add_ele[key] = bonuses.add_ele.get(key, 0) + val
            elif bt == "bIgnoreDefRate":
                bonuses.ignore_def_rate[key] = bonuses.ignore_def_rate.get(key, 0) + val
            elif bt == "bIgnoreMdefRate":
                bonuses.ignore_mdef_rate[key] = bonuses.ignore_mdef_rate.get(key, 0) + val
            elif bt == "bSkillAtk":
                bonuses.skill_atk[key] = bonuses.skill_atk.get(key, 0) + val

        # bonus3 and the rest — stored in all_effects only (tooltip use)


def _noop(_b: GearBonuses, _v: int) -> None:
    pass


# Flat arity-1 routes: bonus_type → (GearBonuses, int) → None
_BONUS1_ROUTES: dict[str, object] = {
    "bStr":      lambda b, v: setattr(b, "str_",  b.str_  + v),
    "bAgi":      lambda b, v: setattr(b, "agi",   b.agi   + v),
    "bVit":      lambda b, v: setattr(b, "vit",   b.vit   + v),
    "bInt":      lambda b, v: setattr(b, "int_",  b.int_  + v),
    "bDex":      lambda b, v: setattr(b, "dex",   b.dex   + v),
    "bLuk":      lambda b, v: setattr(b, "luk",   b.luk   + v),
    "bAllStats": lambda b, v: _apply_all_stats(b, v),
    "bBaseAtk":  lambda b, v: setattr(b, "batk",  b.batk  + v),
    "bHit":      lambda b, v: setattr(b, "hit",   b.hit   + v),
    "bFlee":     lambda b, v: setattr(b, "flee",  b.flee  + v),
    "bFlee2":    lambda b, v: setattr(b, "flee2", b.flee2 + v),
    "bCritical": lambda b, v: setattr(b, "cri",   b.cri   + v),
    "bCritAtkRate": lambda b, v: setattr(b, "crit_atk_rate", b.crit_atk_rate + v),
    "bLongAtkRate": lambda b, v: setattr(b, "long_atk_rate", b.long_atk_rate + v),
    "bDef":      lambda b, v: setattr(b, "def_",  b.def_  + v),
    "bMdef":     lambda b, v: setattr(b, "mdef_", b.mdef_ + v),
    "bMaxHP":    lambda b, v: setattr(b, "maxhp", b.maxhp + v),
    "bMaxSP":    lambda b, v: setattr(b, "maxsp", b.maxsp + v),
    "bAspdRate":    lambda b, v: setattr(b, "aspd_percent",     b.aspd_percent     + v),
    "bAspd":        lambda b, v: setattr(b, "aspd_add",         b.aspd_add         + v),
    "bNearAtkDef":  lambda b, v: setattr(b, "near_atk_def_rate", b.near_atk_def_rate + v),
    "bLongAtkDef":  lambda b, v: setattr(b, "long_atk_def_rate", b.long_atk_def_rate + v),
    "bMagicDefRate": lambda b, v: setattr(b, "magic_def_rate",   b.magic_def_rate   + v),
    "bAtkRate":     lambda b, v: setattr(b, "atk_rate",          b.atk_rate         + v),
}


def _apply_all_stats(b: GearBonuses, v: int) -> None:
    b.str_ += v
    b.agi  += v
    b.vit  += v
    b.int_ += v
    b.dex  += v
    b.luk  += v
