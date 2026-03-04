from pathlib import Path
from typing import Dict, Any, Optional, ClassVar
import json
from functools import lru_cache

from core.models.build import PlayerBuild
from core.models.target import Target
from core.models.weapon import Weapon


class DataLoader:
    """
    SINGLE SOURCE OF TRUTH for all pre-renewal data.
    Loaded exclusively from core/data/pre-re (exact mirror of Hercules DB structure).
    No simplifications. No invented values. Only files confirmed in the repo.
    """

    # Class-level declarations so type checker knows the attributes exist
    _instance: ClassVar[Optional["DataLoader"]] = None
    base_path: Path
    _cache: Dict[str, Any]

    def __new__(cls, base_path: str = "core/data/pre-re"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.base_path = Path(base_path)
            cls._instance._cache = {}   # no annotation here
        return cls._instance

    @lru_cache(maxsize=None)
    def _load_json(self, relative_path: str) -> Dict:
        """Internal cached loader – fails fast if file missing"""
        full_path = self.base_path / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Missing required data file: {full_path}")
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # =============================================================
    # Item database
    # =============================================================
    def get_item(self, item_id: int) -> Optional[Dict]:
        """Look up an item by numeric ID from db/item_db.json.
        Returns None if the ID is not found or if item_db.json does not exist yet."""
        try:
            data = self._load_json("db/item_db.json")
        except FileNotFoundError:
            return None
        return data.get("items", {}).get(str(item_id))

    def get_items_by_type(self, item_type: str) -> list:
        """Return all items of a given type (e.g. 'IT_ARMOR', 'IT_CARD', 'IT_WEAPON').
        Used by the equipment browser GUI. Returns [] if item_db.json is absent."""
        try:
            data = self._load_json("db/item_db.json")
        except FileNotFoundError:
            return []
        return [v for v in data.get("items", {}).values() if v.get("type") == item_type]

    # =============================================================
    # Monster database
    # =============================================================
    def get_monster_data(self, mob_id: int) -> Optional[Dict]:
        """Raw mob_db entry for GUI display (hp, atk_min/max, mdef, etc.).
        Returns None if mob_id is not found — caller decides how to handle."""
        try:
            data = self._load_json("db/mob_db.json")
        except FileNotFoundError:
            return None
        return data.get("mobs", {}).get(str(mob_id))

    def get_monster(self, mob_id: int) -> "Target":
        """Returns a Target populated from mob_db for pipeline use.
        Logs WARNING and returns a safe neutral default Target on missing ID.
        Default mirrors Unarmed convention: no modifiers, pipeline never crashes."""
        entry = self.get_monster_data(mob_id)
        if entry is None:
            print(
                f"WARNING: Mob ID {mob_id} not found in mob_db. Using default Target.",
                file=__import__("sys").stderr,
            )
            return Target()  # all-default: DEF 0, VIT 0, Medium, Formless, Neutral/1, not boss, level 1
        stats = entry.get("stats", {})
        return Target(
            def_=entry["def_"],
            vit=stats.get("vit", entry.get("vit", 0)),
            luk=stats.get("luk", 0),
            size=entry["size"],
            race=entry["race"],
            element=entry["element"],
            element_level=entry["element_level"],
            is_boss=entry["is_boss"],
            level=entry["level"],
        )

    # =============================================================
    # Skills (used by skill_ratio.py, NK flags, hit_count – exact from skills.json)
    # =============================================================
    def get_skill(self, skill_id: int) -> Optional[Dict]:
        data = self._load_json("skills.json")
        for s in data.get("skills", []):
            if s["id"] == skill_id:
                return s
        return None

    # =============================================================
    # Tables – only size_fix for now (exact from repo)
    # =============================================================
    def get_size_fix_multiplier(self, weapon_type: str, target_size: str) -> int:
        """Exact lookup from db/pre-re/size_fix.txt (via JSON)"""
        data = self._load_json("tables/size_fix.json")
        try:
            w_idx = data["weapon_types"].index(weapon_type)
            s_idx = data["sizes"].index(target_size)
            return data["table"][s_idx][w_idx]
        except (ValueError, IndexError):
            return 100  # fallback only if index missing – never invented

    # =============================================================
    # Refine bonuses
    # =============================================================
    @lru_cache(maxsize=None)
    def get_refine_bonus(self, weapon_level: int, refine: int) -> int:
        """Exact pre-renewal weapon refine bonus.
        Source: battle_calc_base_damage2 + status_calc_pc_equip + refine_get_bonus"""
        if weapon_level < 1 or weapon_level > 4 or refine < 0:
            return 0
        data = self._load_json("tables/refine_weapon.json")
        rate = data["bonus"][weapon_level]
        return rate * refine

    @lru_cache(maxsize=None)
    def get_overrefine(self, weapon_level: int, refine: int) -> int:
        """Compute sd->right_weapon.overrefine from refine level and weapon level.
        status.c: wd->overrefine = refine->get_randombonus_max(wlv, r) / 100;
        refine.c: rnd_bonus[level] = rnd_bonus_v * (level - rnd_bonus_lv + 2);
                  where level is 0-indexed, rnd_bonus_lv is 1-indexed RandomBonusStartLevel.
        Simplified: randombonus_max = rnd_bonus_v * (refine - safe_start + 1)  (when refine >= safe_start)
        """
        if weapon_level < 1 or weapon_level > 4 or refine <= 0:
            return 0
        data = self._load_json("tables/refine_weapon.json")
        safe_start = data["safe_refine_start"][weapon_level]
        rnd_bonus_v = data["random_bonus_value"][weapon_level]
        if safe_start == 0 or rnd_bonus_v == 0 or refine < safe_start:
            return 0
        randombonus_max = rnd_bonus_v * (refine - safe_start + 1)
        return randombonus_max // 100

    # =============================================================
    # Mastery bonuses
    # =============================================================

    def get_mastery_multiplier(self, mastery_key: str, build: "PlayerBuild") -> int:
        """Returns the correct per-level multiplier for the current mount state.
        Uses the extended JSON schema; falls back to default if no conditional matches.
        Mirrors the exact if/else order in battle.c for KN_SPEARMASTERY."""
        data = self._load_json("tables/mastery_fix.json")
        mastery = data.get("masteries", {}).get(mastery_key)
        if not mastery:
            return 1
        if build.is_riding_peco and "riding_peco" in mastery:
            return mastery["riding_peco"]
        return mastery.get("default", 1)
    
    # =============================================================
    # Attributes
    # =============================================================

    def get_element_name(self, element_id: int) -> str:
        """Maps element ID (0-9) to name exactly as used in battle.c / status.c."""
        names = {
            0: "Neutral",
            1: "Water",
            2: "Earth",
            3: "Fire",
            4: "Wind",
            5: "Poison",
            6: "Holy",
            7: "Dark",
            8: "Ghost",
            9: "Undead"
        }
        return names.get(element_id, "Neutral")

    def get_attr_fix_multiplier(self, weapon_element: str, target_element: str, element_level: int) -> int:
        """Looks up the elemental damage multiplier from attr_fix.json.
        Returns integer percentage (100 = no change, 150 = 150% damage, etc.)."""
        data = self._load_json("tables/attr_fix.json")
        level = str(element_level or 1)
        return data.get("table", {}).get(target_element, {}).get(level, {}).get(weapon_element, 100)

    def get_mastery_weapon_map(self) -> dict:
        """Returns the weapon_type → mastery_key mapping from mastery_weapon_map.json."""
        data = self._load_json("tables/mastery_weapon_map.json")
        return data.get("mapping", {})

    # =============================================================
    # Active status bonuses
    # =============================================================

    def get_active_status_config(self, status_key: str) -> dict:
        """Returns the complete config dict for a given SC_* key from active_status_bonus.json.
        Full mechanic support (all SCs from the investigation) – used by ActiveStatusBonus class.
        Exact mirror of get_mastery_multiplier and get_size_fix_multiplier pattern."""
        data = self._load_json("tables/active_status_bonus.json")
        return data.get("bonuses", {}).get(status_key, {})

    # =============================================================
    # Cache control (for hot-reload during development)
    # =============================================================
    def clear_cache(self):
        self._cache.clear()
        DataLoader.get_size_fix_multiplier.cache_clear()  # type: ignore[attr-defined]

    def reload_all(self):
        self.clear_cache()
        print("DataLoader reloaded from disk.")


# Global singleton – import as: from core.data_loader import loader
loader = DataLoader()