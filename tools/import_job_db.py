"""Scraper for Hercules db/pre-re/job_db.conf → core/data/pre-re/tables/job_db.json

Extracts BaseASPD, HPTable, SPTable for each job and resolves Inherit chains.
Run from project root: python tools/import_job_db.py
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# Mapping: job_db.conf job name → job_id (Hercules constants.conf Job_* values).
# Only pre-renewal jobs are included; unknown names are silently skipped.
# --------------------------------------------------------------------------
JOB_NAME_TO_ID: dict[str, int] = {
    "Novice": 0,
    "Swordsman": 1,
    "Magician": 2,
    "Archer": 3,
    "Acolyte": 4,
    "Merchant": 5,
    "Thief": 6,
    "Knight": 7,
    "Priest": 8,
    "Wizard": 9,
    "Blacksmith": 10,
    "Hunter": 11,
    "Assassin": 12,
    # 13 = Knight on Peco (internal variant, not directly selectable)
    "Crusader": 14,
    "Monk": 15,
    "Sage": 16,
    "Rogue": 17,
    "Alchemist": 18,
    "Bard": 19,
    "Dancer": 20,
    # 21 = Crusader on Peco, 22 = Wedding (not playable)
    "Super_Novice": 23,
    "Gunslinger": 24,
    "Ninja": 25,
    # Transcendent (renewal-promoted) classes — 4xxx IDs from Hercules constants.conf
    "Lord_Knight": 4008,
    "High_Priest": 4009,
    "High_Wizard": 4010,
    "Whitesmith": 4011,  # displayed as "Mastersmith" in many localizations
    "Sniper": 4012,
    "Assassin_Cross": 4013,
    "Paladin": 4015,
    "Champion": 4016,
    "Professor": 4017,   # displayed as "Scholar" in many localizations
    "Stalker": 4018,
    "Creator": 4019,
    "Clown": 4020,
    "Gypsy": 4021,
}

# --------------------------------------------------------------------------
# Mapping: job_db.conf BaseASPD key → weapon_type string used in item_db
# Defaults to 2000 (= no bonus) for any weapon type not listed.
# --------------------------------------------------------------------------
ASPD_KEY_TO_WEAPON_TYPE: dict[str, str] = {
    "Fist":            "Unarmed",
    "Dagger":          "Knife",
    "Sword":           "1HSword",
    "TwoHandSword":    "2HSword",
    "Spear":           "1HSpear",
    "TwoHandSpear":    "2HSpear",
    "Axe":             "1HAxe",
    "TwoHandAxe":      "2HAxe",
    "Mace":            "Mace",
    "TwoHandMace":     "2HMace",
    "Rod":             "Staff",
    "TwoHandRod":      "2HStaff",
    "Bow":             "Bow",
    "Knuckle":         "Knuckle",
    "Instrumen":       "MusicalInstrument",  # typo in job_db.conf
    "Whip":            "Whip",
    "Book":            "Book",
    "Katar":           "Katar",
    "Revolver":        "Revolver",
    "Rifle":           "Rifle",
    "GatlingGun":      "Gatling",
    "Shotgun":         "Shotgun",
    "GrenadeLauncher": "Grenade",
    "FuumaShuriken":   "Fuuma",
}

# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------

def strip_line_comments(line: str) -> str:
    """Remove // line comments, preserving content inside strings (simplified)."""
    idx = line.find("//")
    if idx >= 0:
        return line[:idx]
    return line


def parse_job_db(path: Path) -> dict[str, dict]:
    """Parse job_db.conf and return a dict keyed by job name (as in the conf file).
    Each entry has: aspd_base (dict), hp_table (list), sp_table (list),
    inherit (str|None), inherit_hp (str|None), inherit_sp (str|None).
    """
    text = path.read_text(encoding="utf-8")

    # Strip /* */ block comments first
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    lines = text.splitlines()

    jobs: dict[str, dict] = {}

    # State
    STATE_OUTSIDE = 0
    STATE_IN_JOB = 1
    STATE_IN_ASPD = 2
    STATE_IN_ARRAY = 3   # accumulating HPTable or SPTable

    state = STATE_OUTSIDE
    current_job: str | None = None
    current_array_key: str | None = None
    array_buf: str = ""
    brace_depth = 0  # tracks nested braces inside a job block

    # Patterns
    JOB_OPEN = re.compile(r"^([A-Za-z][A-Za-z_0-9]*):\s*\{")
    ASPD_OPEN = re.compile(r"BaseASPD:\s*\{")
    ASPD_ENTRY = re.compile(r"(\w+):\s*(\d+)")
    HP_OPEN = re.compile(r"HPTable:\s*(\[.*)")
    SP_OPEN = re.compile(r"SPTable:\s*(\[.*)")
    INHERIT = re.compile(r"Inherit:\s*\(\s*\"([^\"]+)\"\s*\)")
    INHERIT_HP = re.compile(r"InheritHP:\s*\(\s*\"([^\"]+)\"\s*\)")
    INHERIT_SP = re.compile(r"InheritSP:\s*\(\s*\"([^\"]+)\"\s*\)")

    def flush_array() -> list[int]:
        """Parse accumulated array buffer into list[int]."""
        # Remove [ ] and commas, split on whitespace
        content = array_buf.strip().lstrip("[").rstrip("]")
        return [int(x) for x in re.findall(r"\d+", content)]

    for raw_line in lines:
        line = strip_line_comments(raw_line).strip()
        if not line:
            continue

        if state == STATE_OUTSIDE:
            m = JOB_OPEN.match(line)
            if m:
                name = m.group(1)
                if name == "Job_Name":
                    continue  # skip the header comment block
                current_job = name
                jobs[name] = {
                    "aspd_base": {},
                    "hp_table": [],
                    "sp_table": [],
                    "inherit": None,
                    "inherit_hp": None,
                    "inherit_sp": None,
                }
                state = STATE_IN_JOB
                brace_depth = 1

        elif state == STATE_IN_JOB:
            # Track brace depth to find job block end
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0:
                state = STATE_OUTSIDE
                current_job = None
                continue

            if ASPD_OPEN.search(line):
                state = STATE_IN_ASPD
                continue

            m = HP_OPEN.search(line)
            if m:
                current_array_key = "hp_table"
                array_buf = m.group(1)
                if "]" in array_buf:
                    jobs[current_job]["hp_table"] = flush_array()
                    array_buf = ""
                    current_array_key = None
                else:
                    state = STATE_IN_ARRAY
                continue

            m = SP_OPEN.search(line)
            if m:
                current_array_key = "sp_table"
                array_buf = m.group(1)
                if "]" in array_buf:
                    jobs[current_job]["sp_table"] = flush_array()
                    array_buf = ""
                    current_array_key = None
                else:
                    state = STATE_IN_ARRAY
                continue

            m = INHERIT.search(line)
            if m:
                jobs[current_job]["inherit"] = m.group(1)
                continue
            m = INHERIT_HP.search(line)
            if m:
                jobs[current_job]["inherit_hp"] = m.group(1)
                continue
            m = INHERIT_SP.search(line)
            if m:
                jobs[current_job]["inherit_sp"] = m.group(1)
                continue

        elif state == STATE_IN_ASPD:
            if "}" in line:
                state = STATE_IN_JOB
                brace_depth -= line.count("}")  # close of BaseASPD block
                brace_depth += line.count("{")
                # Recalculate: the "}" for BaseASPD was counted once above;
                # revert that since we handle it here
                continue
            for m in ASPD_ENTRY.finditer(line):
                key = m.group(1)
                val = int(m.group(2))
                wtype = ASPD_KEY_TO_WEAPON_TYPE.get(key)
                if wtype:
                    jobs[current_job]["aspd_base"][wtype] = val

        elif state == STATE_IN_ARRAY:
            array_buf += " " + line
            if "]" in line:
                jobs[current_job][current_array_key] = flush_array()
                array_buf = ""
                current_array_key = None
                state = STATE_IN_JOB

    return jobs


def resolve_inherit(jobs: dict[str, dict]) -> None:
    """Resolve Inherit / InheritHP / InheritSP chains in-place."""

    def get_hp(name: str, visited: set) -> list[int]:
        if name not in jobs or name in visited:
            return []
        j = jobs[name]
        if j["hp_table"]:
            return j["hp_table"]
        visited.add(name)
        src = j["inherit_hp"] or j["inherit"]
        if src:
            return get_hp(src, visited)
        return []

    def get_sp(name: str, visited: set) -> list[int]:
        if name not in jobs or name in visited:
            return []
        j = jobs[name]
        if j["sp_table"]:
            return j["sp_table"]
        visited.add(name)
        src = j["inherit_sp"] or j["inherit"]
        if src:
            return get_sp(src, visited)
        return []

    def get_aspd(name: str, visited: set) -> dict[str, int]:
        if name not in jobs or name in visited:
            return {}
        j = jobs[name]
        if j["aspd_base"]:
            return j["aspd_base"]
        visited.add(name)
        src = j["inherit"]
        if src:
            return get_aspd(src, visited)
        return {}

    for name, j in jobs.items():
        if not j["hp_table"]:
            src = j["inherit_hp"] or j["inherit"]
            if src:
                j["hp_table"] = get_hp(src, {name})
        if not j["sp_table"]:
            src = j["inherit_sp"] or j["inherit"]
            if src:
                j["sp_table"] = get_sp(src, {name})
        if not j["aspd_base"]:
            src = j["inherit"]
            if src:
                j["aspd_base"] = get_aspd(src, {name})


def extend_table(table: list[int], target_len: int) -> list[int]:
    """Extend a HP/SP table to target_len entries using linear extrapolation.
    Mirrors Hercules behaviour: average increase per level * remaining levels.
    Source: job_db.conf comment — "average increase per level".
    """
    n = len(table)
    if n == 0 or n >= target_len:
        return table[:target_len]
    if n == 1:
        return table + [table[0]] * (target_len - 1)
    avg_increase = (table[-1] - table[0]) / (n - 1)
    result = list(table)
    for i in range(n, target_len):
        result.append(round(table[-1] + avg_increase * (i - n + 1)))
    return result


def main() -> None:
    src = Path("Hercules/db/pre-re/job_db.conf")
    dst = Path("core/data/pre-re/tables/job_db.json")

    print(f"Parsing {src} ...")
    all_jobs = parse_job_db(src)
    resolve_inherit(all_jobs)

    out: dict[str, dict] = {}
    for job_name, job_id in JOB_NAME_TO_ID.items():
        if job_name not in all_jobs:
            print(f"  WARNING: job '{job_name}' not found in conf", file=sys.stderr)
            continue
        j = all_jobs[job_name]
        hp = extend_table(j["hp_table"], 150)
        sp = extend_table(j["sp_table"], 150)
        out[str(job_id)] = {
            "name": job_name,
            "aspd_base": j["aspd_base"],  # {weapon_type: amotion}
            "hp_table": hp,               # list[int] length 150
            "sp_table": sp,               # list[int] length 150
        }

    result = {
        "_scraped_at": datetime.now(timezone.utc).isoformat(),
        "_source": "Hercules/db/pre-re/job_db.conf",
        "jobs": out,
    }

    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Written {len(out)} jobs to {dst}")
    for jid, jdata in sorted(out.items(), key=lambda x: int(x[0])):
        aspd_count = len(jdata["aspd_base"])
        hp_count = len(jdata["hp_table"])
        sp_count = len(jdata["sp_table"])
        print(f"  [{jid:>2}] {jdata['name']:<20} aspd={aspd_count:>2} hp={hp_count} sp={sp_count}")


if __name__ == "__main__":
    main()
