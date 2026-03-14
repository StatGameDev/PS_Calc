"""
D4 — Gear Bonus Aggregator.
Computes GearBonuses from all equipped items in a build.

Usage:
    bonuses = GearBonusAggregator.compute(build.equipped)

S-1: _apply() is now table-driven via BONUS1/BONUS2 from bonus_definitions.py.
     bAgiVit and bAgiDexStr are now correctly routed (previously silently dropped).
"""
from __future__ import annotations

from typing import Dict, Optional

from core.bonus_definitions import BONUS1, BONUS2
from core.data_loader import loader
from core.item_script_parser import parse_sc_start, parse_script
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

            bonuses.sc_effects.extend(parse_sc_start(script))

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
            defn = BONUS1.get(bt)
            if defn is None:
                return
            if defn.mode == "assign" and defn.field is not None:
                # Last-wins assignment; optional transform converts raw param to stored type.
                raw = p[0]
                v = defn.transform(raw) if defn.transform else raw
                if v is not None:
                    setattr(bonuses, defn.field, v)
            else:
                v = p[0] if isinstance(p[0], int) else 0
                if defn.mode == "multi" and defn.fields:
                    for f in defn.fields:
                        setattr(bonuses, f, getattr(bonuses, f) + v)
                elif defn.field is not None:
                    setattr(bonuses, defn.field, getattr(bonuses, defn.field) + v)

        elif eff.arity == 2 and len(p) >= 2:
            defn = BONUS2.get(bt)
            if defn is None or defn.field is None:
                return
            key = str(p[0])
            val = p[1] if isinstance(p[1], int) else 0
            if defn.mode == "dict":
                d = getattr(bonuses, defn.field)
                d[key] = d.get(key, 0) + val
            elif defn.mode == "add":
                setattr(bonuses, defn.field, getattr(bonuses, defn.field) + val)

        # arity 3: display-only, stored in all_effects only
