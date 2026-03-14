"""
core/build_applicator.py — S-2/S-3/S-5

Business logic extracted from MainWindow: applying aggregated gear bonuses and
computing SC stat bonuses belongs in core, not in the GUI layer.
"""
import dataclasses

from core.models.build import PlayerBuild
from core.models.gear_bonuses import GearBonuses


def compute_consumable_bonuses(consumable_buffs: dict) -> dict[str, int]:
    """Map consumable_buffs keys to stat deltas. Called inside apply_gear_bonuses().

    SC conflict routing: each SC slot takes the max of all sources.
    (Hercules sc_start blocks lower val1, status.c:7362-7363)
    Per-stat food, all-stat food, and Grilled Corn all write to the same
    SC_FOOD_STR/AGI/etc. slots → effective = max(food_X, food_all, grilled_corn_component).
    """
    cb = consumable_buffs
    result: dict[str, int] = {}

    # All-stats food baseline (contributes to every stat slot)
    food_all = int(cb.get("food_all", 0))

    # Grilled Corn: +2 STR/AGI/INT (SC_FOOD_*; competes with per-stat and all-stat food)
    grilled_corn = bool(cb.get("grilled_corn", False))
    gc = 2 if grilled_corn else 0

    # Stat foods: max() per SC slot (status.c:7362-7363)
    # food_str/agi/int also compete with grilled_corn; food_vit/dex/luk do not
    str_food = max(int(cb.get("food_str", 0)), food_all, gc)
    agi_food = max(int(cb.get("food_agi", 0)), food_all, gc)
    vit_food = max(int(cb.get("food_vit", 0)), food_all)
    int_food = max(int(cb.get("food_int", 0)), food_all, gc)
    dex_food = max(int(cb.get("food_dex", 0)), food_all)
    luk_food = max(int(cb.get("food_luk", 0)), food_all)

    if str_food: result["str"] = str_food
    if agi_food: result["agi"] = agi_food
    if vit_food: result["vit"] = vit_food
    if int_food: result["int"] = int_food
    if dex_food: result["dex"] = dex_food
    if luk_food: result["luk"] = luk_food

    # ASPD potions: SC_ATTHASTE_POTION1/2/3 (status.c:7851, 5661-5663)
    # aspd_rate -= 100/150/200 out of 1000 → 10/15/20% faster
    _ASPD_VALS = (0, 10, 15, 20)
    aspd_potion = int(cb.get("aspd_potion", 0))
    if aspd_potion:
        result["aspd_percent"] = _ASPD_VALS[aspd_potion]

    # HIT food: SC_FOOD_BASICHIT hit += val1 (status.c:4799-4800)
    hit_food = int(cb.get("hit_food", 0))
    if hit_food:
        result["hit"] = hit_food

    # FLEE food: SC_FOOD_BASICAVOIDANCE flee += val1 (status.c:4864-4865)
    flee_food = int(cb.get("flee_food", 0))
    if flee_food:
        result["flee"] = flee_food

    # CRI food: SC_FOOD_CRITICALSUCCESSVALUE critical += val1 (status.c:4751-4752, no 10× scale)
    if cb.get("cri_food"):
        result["cri"] = 7

    # ATK items: SC_PLUSATTACKPOWER batk += val1 (status.c:4476, #ifndef RENEWAL)
    atk_item = int(cb.get("atk_item", 0))
    if atk_item:
        result["batk"] = atk_item

    # MATK flat: SC_PLUSMAGICPOWER (matk_item) + SC_MATKFOOD (matk_food) — separate SC slots, stack
    # SC_PLUSMAGICPOWER: matk += val1 (status.c:4635-4636)
    # SC_MATKFOOD:       matk += val1 (status.c:4637-4638)
    matk_flat = int(cb.get("matk_item", 0))
    if cb.get("matk_food"):
        matk_flat += 10
    if matk_flat:
        result["matk_flat"] = matk_flat

    return result


def apply_gear_bonuses(build: PlayerBuild, gear_bonuses: GearBonuses) -> PlayerBuild:
    """Return a new PlayerBuild with all bonus sources stacked on top of base values.

    Sources stacked: gear scripts (GearBonuses) + Active Items (G46) + Manual Adj (G47)
    + SC stat buffs from support_buffs (SC_BLESSING, SC_INC_AGI, SC_GLORIA)
    + consumable buffs (S-5).

    The original build is unchanged so save_build always writes clean values.
    Caller must pass a GearBonuses already augmented with apply_passive_bonuses()
    if passive skill bonuses should feed into player_build_to_target.
    """
    gb = gear_bonuses
    ai = build.active_items_bonuses
    ma = build.manual_adj_bonuses
    sc = compute_sc_stat_bonuses(build.support_buffs)
    cons = compute_consumable_bonuses(build.consumable_buffs)
    return dataclasses.replace(
        build,
        bonus_str=build.bonus_str + gb.str_ + ai.get("str", 0) + ma.get("str", 0) + sc.get("str", 0) + cons.get("str", 0),
        bonus_agi=build.bonus_agi + gb.agi + ai.get("agi", 0) + ma.get("agi", 0) + sc.get("agi", 0) + cons.get("agi", 0),
        bonus_vit=build.bonus_vit + gb.vit + ai.get("vit", 0) + ma.get("vit", 0) + cons.get("vit", 0),
        bonus_int=build.bonus_int + gb.int_ + ai.get("int", 0) + ma.get("int", 0) + sc.get("int", 0) + cons.get("int", 0),
        bonus_dex=build.bonus_dex + gb.dex + ai.get("dex", 0) + ma.get("dex", 0) + sc.get("dex", 0) + cons.get("dex", 0),
        bonus_luk=build.bonus_luk + gb.luk + ai.get("luk", 0) + ma.get("luk", 0) + sc.get("luk", 0) + cons.get("luk", 0),
        bonus_batk=build.bonus_batk + gb.batk + ai.get("batk", 0) + ma.get("batk", 0) + cons.get("batk", 0),
        bonus_hit=build.bonus_hit + gb.hit + ai.get("hit", 0) + ma.get("hit", 0) + cons.get("hit", 0),
        bonus_flee=build.bonus_flee + gb.flee + ai.get("flee", 0) + ma.get("flee", 0) + cons.get("flee", 0),
        bonus_cri=build.bonus_cri + gb.cri + ai.get("cri", 0) + ma.get("cri", 0) + cons.get("cri", 0),
        equip_def=build.equip_def + gb.def_ + ai.get("def", 0) + ma.get("def", 0),
        equip_mdef=build.equip_mdef + gb.mdef_ + ai.get("mdef", 0) + ma.get("mdef", 0),
        bonus_maxhp=build.bonus_maxhp + gb.maxhp + ai.get("maxhp", 0) + ma.get("maxhp", 0),
        bonus_maxsp=build.bonus_maxsp + gb.maxsp + ai.get("maxsp", 0) + ma.get("maxsp", 0),
        bonus_aspd_percent=build.bonus_aspd_percent + gb.aspd_percent + ai.get("aspd_pct", 0) + ma.get("aspd_pct", 0) + cons.get("aspd_percent", 0),
        bonus_aspd_add=build.bonus_aspd_add + gb.aspd_add,
        bonus_crit_atk_rate=build.bonus_crit_atk_rate + gb.crit_atk_rate,
        bonus_matk_rate=build.bonus_matk_rate + gb.matk_rate,
        bonus_maxhp_rate=build.bonus_maxhp_rate + gb.maxhp_rate,
        bonus_matk_flat=build.bonus_matk_flat + cons.get("matk_flat", 0),
    )


def resolve_armor_element(armor_element_override: int, gear_bonuses: GearBonuses) -> int:
    """Resolve effective armor element using three-tier precedence.

    Precedence:
      1. armor_element_override (non-zero = user has explicitly set an element)
      2. gear_bonuses.script_def_ele (bDefEle from equipped item scripts, e.g. Pasana Card)
      3. 0 / Neutral (all armors are Neutral by default in pre-renewal)
    """
    if armor_element_override != 0:
        return armor_element_override
    if gear_bonuses.script_def_ele is not None:
        return gear_bonuses.script_def_ele
    return 0


def compute_sc_stat_bonuses(support_buffs: dict) -> dict[str, int]:
    """Compute SC stat bonuses from support_buffs for display + bonus rollup.

    Keys match the ai/ma stat key convention (str/agi/int/dex/luk).
    SC_BLESSING: STR/INT/DEX += level  (status.c:8271-8275)
    SC_INC_AGI:  AGI += 2+level        (status.c:7632)
    SC_GLORIA:   LUK += 30             (status.c:4273-4274)
    """
    sc: dict[str, int] = {}
    blessing_lv = int(support_buffs.get("SC_BLESSING", 0))
    if blessing_lv:
        sc["str"] = blessing_lv
        sc["int"] = blessing_lv
        sc["dex"] = blessing_lv
    inc_agi_lv = int(support_buffs.get("SC_INC_AGI", 0))
    if inc_agi_lv:
        sc["agi"] = 2 + inc_agi_lv
    if support_buffs.get("SC_GLORIA"):
        sc["luk"] = sc.get("luk", 0) + 30
    return sc
