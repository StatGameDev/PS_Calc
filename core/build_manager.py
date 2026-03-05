import json
from pathlib import Path
from typing import Dict, List, Optional

from core.models.build import PlayerBuild
from core.models.weapon import Weapon, RANGED_WEAPON_TYPES

DEFAULT_SAVES_DIR = "saves"



def effective_is_ranged(build: PlayerBuild, weapon: Weapon) -> bool:
    """Return the effective is_ranged flag for a build+weapon pair.

    Honour build.is_ranged_override when explicitly set (True/False).
    Fall back to weapon_type membership in RANGED_WEAPON_TYPES when None.
    """
    if build.is_ranged_override is not None:
        return build.is_ranged_override
    return weapon.weapon_type in RANGED_WEAPON_TYPES


class BuildManager:
    """
    Responsible for save/load of user build files and resolving equipped item IDs
    to model objects via the item database.

    DataLoader owns static databases (item_db, skill tables, etc.).
    BuildManager owns user-saved build files and item resolution.

    Resolution follows C1 pattern: load_build returns a PlayerBuild with item IDs
    embedded in build.equipped. Callers obtain the resolved Weapon (or future
    armour/accessory objects) by calling resolve_weapon separately. This keeps
    PlayerBuild a pure data container and the resolution pattern extensible to
    all future equip slot types.
    """

    @staticmethod
    def save_build(build: PlayerBuild, path: str) -> None:
        """Serialise a PlayerBuild to the canonical save schema JSON."""
        data = {
            "name": build.name,
            "job_id": build.job_id,
            "base_level": build.base_level,
            "job_level": build.job_level,
            "base_stats": {
                "str": build.base_str,
                "agi": build.base_agi,
                "vit": build.base_vit,
                "int": build.base_int,
                "dex": build.base_dex,
                "luk": build.base_luk,
            },
            "bonus_stats": {
                # Flat stat bonuses from gear/cards/foods/buffs — manually entered
                # until the item database is complete enough to derive them.
                "str": build.bonus_str,
                "agi": build.bonus_agi,
                "vit": build.bonus_vit,
                "int": build.bonus_int,
                "dex": build.bonus_dex,
                "luk": build.bonus_luk,
                "hit": build.bonus_hit,
                "flee": build.bonus_flee,
                "cri": build.bonus_cri,
                "batk": build.bonus_batk,
                "def": build.equip_def,        # hard DEF total from equipment
                "def2": build.bonus_def2,       # extra soft DEF from items/foods/SCs
                "aspd_percent": build.bonus_aspd_percent,
            },
            "target_mob_id": build.target_mob_id,
            "equipped": build.equipped,
            "refine": build.refine_levels,
            "weapon_element": build.weapon_element,
            "active_buffs": build.active_status_levels,
            "mastery_levels": build.mastery_levels,
            "flags": {
                "is_ranged_override": build.is_ranged_override,  # null = derive from weapon_type
                "is_riding_peco": build.is_riding_peco,
                "no_sizefix": build.no_sizefix,
            },
            "server": build.server,
        }
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load_build(path: str) -> PlayerBuild:
        """
        Parse a save-schema JSON file into a PlayerBuild.

        Item IDs in build.equipped are populated as-is. Any ID not found in
        item_db is warned about here so the problem is surfaced at load time.
        The actual Weapon object is not constructed here — call resolve_weapon
        when the weapon is needed (pipeline, GUI display, etc.).
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        bs = data.get("base_stats", {})
        bn = data.get("bonus_stats", {})
        flags = data.get("flags", {})
        equipped: Dict[str, Optional[int]] = data.get("equipped", {})
        build_name = data.get("name", path)

        # Warn on any equipped item ID that cannot be resolved.
        # Resolution is deferred to resolve_weapon; warning fires here so
        # callers know at load time rather than silently getting Unarmed later.
        from core.data_loader import loader  # local import — avoids circular dependency
        for slot, item_id in equipped.items():
            if item_id is not None and loader.get_item(item_id) is None:
                print(
                    f'WARNING: Item ID {item_id} not found in item_db. '
                    f'Using Unarmed defaults. Build: "{build_name}"'
                )

        return PlayerBuild(
            name=data.get("name", ""),
            job_id=data.get("job_id", 0),
            base_level=data.get("base_level", 1),
            job_level=data.get("job_level", 1),
            base_str=bs.get("str", 1),
            base_agi=bs.get("agi", 1),
            base_vit=bs.get("vit", 1),
            base_int=bs.get("int", 1),
            base_dex=bs.get("dex", 1),
            base_luk=bs.get("luk", 1),
            bonus_str=bn.get("str", 0),
            bonus_agi=bn.get("agi", 0),
            bonus_vit=bn.get("vit", 0),
            bonus_int=bn.get("int", 0),
            bonus_dex=bn.get("dex", 0),
            bonus_luk=bn.get("luk", 0),
            bonus_hit=bn.get("hit", 0),
            bonus_flee=bn.get("flee", 0),
            bonus_cri=bn.get("cri", 0),
            bonus_batk=bn.get("batk", 0),
            equip_def=bn.get("def", 0),
            bonus_def2=bn.get("def2", 0),
            bonus_aspd_percent=bn.get("aspd_percent", 0),
            target_mob_id=data.get("target_mob_id"),
            equipped=equipped,
            refine_levels=data.get("refine", {}),
            weapon_element=data.get("weapon_element", None),
            # Old files used "weapon_elements": {"right_hand": N} — silently falls back to None.
            active_status_levels=data.get("active_buffs", {}),
            mastery_levels=data.get("mastery_levels", {}),
            is_ranged_override=flags.get("is_ranged_override", None),
            is_riding_peco=flags.get("is_riding_peco", False),
            no_sizefix=flags.get("no_sizefix", False),
            server=data.get("server", "standard"),
        )

    @staticmethod
    def list_builds(directory: str = DEFAULT_SAVES_DIR) -> List[str]:
        """Return stem names of all build files found in directory."""
        return [p.stem for p in Path(directory).glob("*.json")]

    @staticmethod
    def resolve_weapon(
        item_id: Optional[int],
        refine: int = 0,
        element_override: Optional[int] = None,
    ) -> Weapon:
        """
        Resolve an item ID to a Weapon via item_db.

        Returns Unarmed defaults (ATK 0, level 1, neutral, no refine) if:
        - item_id is None (slot unequipped)
        - the item ID is not found in item_db

        element_override replaces the item_db element when not None (used for
        elemental imbues until a proper SC/item imbue system is implemented).
        """
        from core.data_loader import loader  # local import — avoids circular dependency

        if item_id is None:
            return Weapon()  # Unarmed: atk=0, level=1, element=0, weapon_type="Unarmed"

        item = loader.get_item(item_id)
        if item is None:
            print(
                f'WARNING: Item ID {item_id} not found in item_db. '
                f'Using Unarmed defaults.'
            )
            return Weapon()

        element = element_override if element_override is not None else item.get("element", 0)

        return Weapon(
            atk=item.get("atk", 0),
            refine=refine,
            level=item.get("level", 1),
            element=element,
            weapon_type=item.get("weapon_type", "Unarmed"),
            hand="right",
            aegis_name=item.get("aegis_name", ""),
            refineable=item.get("refineable", True),
        )
