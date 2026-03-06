"""
D4 — Gear Bonus Aggregator.
Computes GearBonuses from all equipped items in a build.

Usage:
    bonuses = GearBonusAggregator.compute(build.equipped)
"""
from __future__ import annotations

from typing import Dict, Optional

from core.data_loader import loader
from core.item_script_parser import parse_script
from core.models.gear_bonuses import GearBonuses
from core.models.item_effect import ItemEffect


class GearBonusAggregator:

    @staticmethod
    def compute(equipped: Dict[str, Optional[int]]) -> GearBonuses:
        """
        Parse scripts for all equipped item IDs and aggregate into GearBonuses.
        Slots with None or unknown IDs are silently skipped.
        """
        bonuses = GearBonuses()

        for slot, item_id in equipped.items():
            if item_id is None:
                continue
            item = loader.get_item(item_id)
            if item is None:
                continue
            script = item.get("script") or ""
            if not script:
                continue

            effects = parse_script(script)
            bonuses.all_effects.extend(effects)

            for eff in effects:
                GearBonusAggregator._apply(bonuses, eff)

        return bonuses

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
    "bMaxHP":    lambda b, v: setattr(b, "maxhp", b.maxhp + v),
    "bMaxSP":    lambda b, v: setattr(b, "maxsp", b.maxsp + v),
    "bAspdRate": lambda b, v: setattr(b, "aspd_percent", b.aspd_percent + v),
    "bAspd":     lambda b, v: setattr(b, "aspd_add",     b.aspd_add     + v),
}


def _apply_all_stats(b: GearBonuses, v: int) -> None:
    b.str_ += v
    b.agi  += v
    b.vit  += v
    b.int_ += v
    b.dex  += v
    b.luk  += v
