"""
core/build_applicator.py — S-2

Business logic extracted from MainWindow: applying aggregated gear bonuses and
computing SC stat bonuses belongs in core, not in the GUI layer.
"""
import dataclasses

from core.models.build import PlayerBuild
from core.models.gear_bonuses import GearBonuses


def apply_gear_bonuses(build: PlayerBuild, gear_bonuses: GearBonuses) -> PlayerBuild:
    """Return a new PlayerBuild with all bonus sources stacked on top of base values.

    Sources stacked: gear scripts (GearBonuses) + Active Items (G46) + Manual Adj (G47)
    + SC stat buffs from support_buffs (SC_BLESSING, SC_INC_AGI, SC_GLORIA).

    The original build is unchanged so save_build always writes clean values.
    Caller must pass a GearBonuses already augmented with apply_passive_bonuses()
    if passive skill bonuses should feed into player_build_to_target.
    """
    gb = gear_bonuses
    ai = build.active_items_bonuses
    ma = build.manual_adj_bonuses
    sc = compute_sc_stat_bonuses(build.support_buffs)
    return dataclasses.replace(
        build,
        bonus_str=build.bonus_str + gb.str_ + ai.get("str", 0) + ma.get("str", 0) + sc.get("str", 0),
        bonus_agi=build.bonus_agi + gb.agi + ai.get("agi", 0) + ma.get("agi", 0) + sc.get("agi", 0),
        bonus_vit=build.bonus_vit + gb.vit + ai.get("vit", 0) + ma.get("vit", 0),
        bonus_int=build.bonus_int + gb.int_ + ai.get("int", 0) + ma.get("int", 0) + sc.get("int", 0),
        bonus_dex=build.bonus_dex + gb.dex + ai.get("dex", 0) + ma.get("dex", 0) + sc.get("dex", 0),
        bonus_luk=build.bonus_luk + gb.luk + ai.get("luk", 0) + ma.get("luk", 0) + sc.get("luk", 0),
        bonus_batk=build.bonus_batk + gb.batk + ai.get("batk", 0) + ma.get("batk", 0),
        bonus_hit=build.bonus_hit + gb.hit + ai.get("hit", 0) + ma.get("hit", 0),
        bonus_flee=build.bonus_flee + gb.flee + ai.get("flee", 0) + ma.get("flee", 0),
        bonus_cri=build.bonus_cri + gb.cri + ai.get("cri", 0) + ma.get("cri", 0),
        equip_def=build.equip_def + gb.def_ + ai.get("def", 0) + ma.get("def", 0),
        equip_mdef=build.equip_mdef + gb.mdef_ + ai.get("mdef", 0) + ma.get("mdef", 0),
        bonus_maxhp=build.bonus_maxhp + gb.maxhp + ai.get("maxhp", 0) + ma.get("maxhp", 0),
        bonus_maxsp=build.bonus_maxsp + gb.maxsp + ai.get("maxsp", 0) + ma.get("maxsp", 0),
        bonus_aspd_percent=build.bonus_aspd_percent + gb.aspd_percent + ai.get("aspd_pct", 0) + ma.get("aspd_pct", 0),
        bonus_aspd_add=build.bonus_aspd_add + gb.aspd_add,
        bonus_crit_atk_rate=build.bonus_crit_atk_rate + gb.crit_atk_rate,
        bonus_matk_rate=build.bonus_matk_rate + gb.matk_rate,
        bonus_maxhp_rate=build.bonus_maxhp_rate + gb.maxhp_rate,
    )


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
