#!/usr/bin/env python3
"""
G12 — Armor refine DEF scraper.
Reads Hercules/db/pre-re/refine_db.conf and extracts Armors.StatsPerLevel.
Output: core/data/pre-re/tables/refine_armor.json

Formula applied by game server:
  refinedef += refine->get_bonus(REFINE_TYPE_ARMOR, r)   per armor slot
  bstatus->def += (refinedef + 50) / 100                 aggregate rounding
  status.c ~1655, ~1713

For pre-renewal Armors block: StatsPerLevel=66, no per-level Bonus overrides.
get_bonus returns refine_level * StatsPerLevel.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONF = ROOT / "Hercules/db/pre-re/refine_db.conf"
OUT  = ROOT / "core/data/pre-re/tables/refine_armor.json"


def parse_armors_stats_per_level(text: str) -> int:
    """Extract StatsPerLevel from the Armors { ... } block (not WeaponLevel*)."""
    m = re.search(r'^Armors:\s*\{[^}]*?StatsPerLevel:\s*(\d+)', text, re.MULTILINE | re.DOTALL)
    if not m:
        raise ValueError("Could not find Armors.StatsPerLevel in refine_db.conf")
    return int(m.group(1))


def main() -> None:
    text = CONF.read_text(encoding="utf-8")
    stats_per_level = parse_armors_stats_per_level(text)

    data = {
        "_scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "_source": "Hercules/db/pre-re/refine_db.conf :: Armors.StatsPerLevel",
        "stats_per_level": stats_per_level,
    }

    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"stats_per_level = {stats_per_level}")
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
