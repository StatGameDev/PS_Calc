#!/usr/bin/env python3
"""
tools/import_skill_tree.py

Scraper: reads Hercules/db/pre-re/skill_tree.conf and writes
core/data/pre-re/tables/skill_tree.json.

Output: job_id → sorted list of skill names available to that job,
with all inherited skills resolved.

Usage:
    python tools/import_skill_tree.py            # write output
    python tools/import_skill_tree.py --dry-run  # print sample, no write

Run from the PS_Calc/ project root.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

CONF_PATH = Path("Hercules/db/pre-re/skill_tree.conf")
OUT_PATH  = Path("core/data/pre-re/tables/skill_tree.json")

# skill_tree.conf job names → build_header.py job_ids
# Only jobs in this table are emitted.
_JOB_NAME_TO_ID: dict[str, int] = {
    "Novice":          0,
    "Swordsman":       1,
    "Magician":        2,
    "Archer":          3,
    "Acolyte":         4,
    "Merchant":        5,
    "Thief":           6,
    "Knight":          7,
    "Priest":          8,
    "Wizard":          9,
    "Blacksmith":      10,
    "Hunter":          11,
    "Assassin":        12,
    "Crusader":        14,
    "Monk":            15,
    "Sage":            16,
    "Rogue":           17,
    "Alchemist":       18,
    "Bard":            19,
    "Dancer":          20,
    "Lord_Knight":     23,
    "Assassin_Cross":  24,
    "High_Wizard":     25,
    "Sniper":          26,
    "Whitesmith":      27,
    "High_Priest":     28,
    "Paladin":         29,
    "Clown":           30,
    "Champion":        31,
    "Professor":       32,
    "Creator":         33,
    "Stalker":         34,
    "Gypsy":           35,
}


def strip_comments(text: str) -> str:
    """Remove // line comments."""
    lines = []
    for line in text.splitlines():
        idx = line.find("//")
        if idx >= 0:
            line = line[:idx]
        lines.append(line)
    return "\n".join(lines)


def extract_block(text: str, brace_pos: int) -> str:
    """Return content inside the { } starting at brace_pos (exclusive of braces)."""
    assert text[brace_pos] == "{"
    depth, i, n = 1, brace_pos + 1, len(text)
    while i < n and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[brace_pos + 1: i - 1]


def mask_nested(text: str) -> str:
    """Replace all content inside { } blocks with spaces (flattens to depth-0)."""
    result, depth = list(text), 0
    for i, ch in enumerate(text):
        if ch == "{":
            depth += 1
            result[i] = " "
        elif ch == "}":
            result[i] = " "
            depth -= 1
        elif depth > 0:
            result[i] = " "
    return "".join(result)


def parse_all_jobs(text: str) -> dict[str, dict]:
    """
    Parse every job block in text.
    Returns {job_name: {"inherit": [names], "own_skills": set[str]}}.
    """
    jobs: dict[str, dict] = {}
    for m in re.finditer(r"^(\w+)\s*:\s*\{", text, re.MULTILINE):
        name = m.group(1)
        content = extract_block(text, m.end() - 1)

        # inherit: ( "Parent1", "Parent2" );
        inherit: list[str] = []
        inh_m = re.search(r'\binherit\s*:\s*\(([^)]*)\)', content)
        if inh_m:
            inherit = [s.strip().strip('"') for s in inh_m.group(1).split(",")
                       if s.strip().strip('"')]

        # skills: { SKILL_NAME: int_or_block ... }
        own_skills: set[str] = set()
        sk_m = re.search(r'\bskills\s*:\s*\{', content)
        if sk_m:
            sk_content = extract_block(content, sk_m.end() - 1)
            # Mask nested { } so only top-level keys are visible
            flat = mask_nested(sk_content)
            # Skill names are ALL_CAPS_WITH_UNDERSCORES keys (no lowercase letters)
            for sm in re.finditer(r"\b([A-Z][A-Z0-9_]{2,})\s*:", flat):
                own_skills.add(sm.group(1))

        jobs[name] = {"inherit": inherit, "own_skills": own_skills}
    return jobs


def resolve(job_name: str, jobs: dict, cache: dict) -> set[str]:
    """
    Return full skill set for job_name including inherited skills.
    cache is populated in-place; in-progress entries guard against cycles.
    """
    if job_name in cache:
        return cache[job_name]
    if job_name not in jobs:
        return set()
    entry = jobs[job_name]
    skills: set[str] = set(entry["own_skills"])
    cache[job_name] = skills          # in-progress sentinel
    for parent in entry["inherit"]:
        skills |= resolve(parent, jobs, cache)
    cache[job_name] = skills
    return skills


def main(dry_run: bool = False) -> None:
    if not CONF_PATH.exists():
        sys.exit(f"ERROR: {CONF_PATH} not found. Run from PS_Calc/ root.")

    text = strip_comments(CONF_PATH.read_text(encoding="utf-8"))
    jobs = parse_all_jobs(text)
    print(f"Parsed {len(jobs)} job blocks from {CONF_PATH}")

    result: dict[str, list[str]] = {}
    cache: dict[str, set] = {}
    for job_name, job_id in _JOB_NAME_TO_ID.items():
        if job_name not in jobs:
            print(f"  WARNING: {job_name!r} not found in skill_tree.conf", file=sys.stderr)
            result[str(job_id)] = []
            continue
        skills = resolve(job_name, jobs, cache)
        result[str(job_id)] = sorted(skills)
        print(f"  {job_name:<18} (id={job_id:>2}): {len(skills):>3} skills")

    output = {
        "_source":     "Scraped from Hercules/db/pre-re/skill_tree.conf",
        "_scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "_note": (
            "Maps job_id (str) → sorted list of skill names available to that job, "
            "including all inherited skills. Rogue (17) and Stalker (34) inherit their "
            "base trees; AllowPlagiarism skills from other jobs are added by the GUI filter."
        ),
        "jobs": result,
    }

    if dry_run:
        print(f"\n[DRY RUN] Would write {OUT_PATH}")
        for name in ("Swordsman", "Knight", "Assassin_Cross"):
            jid = _JOB_NAME_TO_ID.get(name)
            if jid is not None:
                s = result.get(str(jid), [])
                print(f"  {name}: {s[:6]}...")
        return

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
