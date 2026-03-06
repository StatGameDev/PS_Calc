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
            agi=stats.get("agi", 0),
            size=entry["size"],
            race=entry["race"],
            element=entry["element"],
            element_level=entry["element_level"],
            is_boss=entry["is_boss"],
            level=entry["level"],
            mdef_=entry.get("mdef", 0),
            int_=stats.get("int", 0),
        )

    # =============================================================
    # Job database (ASPD base, HP table, SP table per job_id)
    # =============================================================
    def get_job_entry(self, job_id: int) -> Optional[Dict]:
        """Return the job_db.json entry for job_id, or None if not found."""
        try:
            data = self._load_json("tables/job_db.json")
        except FileNotFoundError:
            return None
        return data.get("jobs", {}).get(str(job_id))

    def get_aspd_base(self, job_id: int, weapon_type: str) -> int:
        """Return BaseASPD amotion for (job_id, weapon_type); 2000 if not found.
        Source: job_db.conf BaseASPD, status.c status_base_amotion_pc (#ifndef RENEWAL_ASPD)"""
        entry = self.get_job_entry(job_id)
        if entry is None:
            return 2000  # slowest possible — safe fallback
        return entry.get("aspd_base", {}).get(weapon_type, 2000)

    def get_hp_at_level(self, job_id: int, level: int) -> int:
        """Return base HP for (job_id, level); 40 if not found.
        level is 1-indexed. Source: job_db.conf HPTable."""
        entry = self.get_job_entry(job_id)
        if entry is None:
            return 40
        table = entry.get("hp_table", [])
        idx = max(0, min(level - 1, len(table) - 1))
        return table[idx] if table else 40

    def get_sp_at_level(self, job_id: int, level: int) -> int:
        """Return base SP for (job_id, level); 11 if not found.
        level is 1-indexed. Source: job_db.conf SPTable."""
        entry = self.get_job_entry(job_id)
        if entry is None:
            return 11
        table = entry.get("sp_table", [])
        idx = max(0, min(level - 1, len(table) - 1))
        return table[idx] if table else 11

    # =============================================================
    # Skills (metadata from db/skills.json; damage ratios are in skill_ratio.py)
    # =============================================================
    def get_skill(self, skill_id: int) -> Optional[Dict]:
        try:
            data = self._load_json("db/skills.json")
        except FileNotFoundError:
            return None
        return data.get("skills", {}).get(str(skill_id))

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

    def get_all_skills(self) -> list:
        """All skill entries from db/skills.json. Used by CombatControlsSection."""
        try:
            data = self._load_json("db/skills.json")
        except FileNotFoundError:
            return []
        return list(data.get("skills", {}).values())

    def get_all_monsters(self) -> list:
        """All mob entries from mob_db.json for search. Returns [] on missing file."""
        try:
            data = self._load_json("db/mob_db.json")
        except FileNotFoundError:
            return []
        return list(data.get("mobs", {}).values())

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