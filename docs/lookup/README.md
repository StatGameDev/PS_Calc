# docs/lookup — Reference Lookup Tables

All files are **tab-separated (TSV)** with a two-line comment header.
Lines starting with `#` are comments; all other lines are data rows.
Files are sorted by numeric ID ascending.

---

## Files

### skill_ref.tsv
`id  constant  description  category  notes`

- **id** — numeric skill ID (matches skills.json key)
- **constant** — Hercules skill constant (e.g. `KN_TWOHANDQUICKEN`)
- **description** — short display name from skills.json
- **category** — effect category code(s) from `docs/skill_lists/skills_by_job.md`
  (`B`=buff · `P`=passive · `O`=offensive · `D`=debuff · `S`=status · `H`=heal · `C`=combo · `M`=modifier · `X`=other/irrelevant)
  Blank if the skill has not yet been categorised.
- **notes** — planning/implementation notes from `docs/skill_lists/skills_by_job.md`.
  Blank if none.

### item_ref.tsv
`id  aegis_name  name  type  script  on_equip_script  on_unequip_script  notes`

- **id** — numeric item ID
- **aegis_name** — internal Hercules name (unique key used in item_db.json)
- **name** — display name
- **type** — `IT_WEAPON` · `IT_ARMOR` · `IT_CARD` · `IT_AMMO`
- **script** — equip/passive script body (newlines collapsed to spaces); empty if none
- **on_equip_script** — armour on-equip script; empty if none
- **on_unequip_script** — armour on-unequip script; empty if none
- **notes** — free-form notes; blank by default, add manually

### mob_ref.tsv
`id  sprite_name  name  notes`

- **id** — numeric mob ID
- **sprite_name** — all-caps Hercules sprite identifier
- **name** — display name
- **notes** — free-form notes; blank by default

### job_ref.tsv
`id  name  notes`

- **id** — numeric job ID (Hercules `Job_*` constant value)
- **name** — display name from job_db.json
- **notes** — free-form notes; blank by default

### job_skill_map.tsv
`job_id  skill_id  skill_constant`

- One row per job–skill pair.
- Derived from `skill_tree.json` (which lists all skills available to each job,
  including inherited base-class skills).
- `skill_id` is `?` for any skill constant not found in skills.json (should be none).
- Rogue (17) and Stalker (4018) include inherited trees per the scraper note in
  skill_tree.json.

---

## Usage

**ID → Name lookup** (e.g. "what is mob 1002?"):
```
grep "^1002\t" docs/lookup/mob_ref.tsv
```

**Name → ID lookup** (e.g. "what ID is Poring?"):
```
grep -i "poring" docs/lookup/mob_ref.tsv
```

**What skills does job 7 (Knight) have?**
```
grep "^7\t" docs/lookup/job_skill_map.tsv
```

**What items have a specific SC in their script?**
```
grep "sc_start SC_INCREASEAGI" docs/lookup/item_ref.tsv
```

---

## Regeneration

All files are generated from the JSON databases by an inline Python script.
Re-run after updating Hercules or re-scraping any DB:

```
# skill_ref.tsv + mob_ref.tsv + job_ref.tsv + job_skill_map.tsv
# source: core/data/pre-re/db/skills.json, mob_db.json, tables/job_db.json,
#         tables/skill_tree.json, docs/skill_lists/skills_by_job.md

# item_ref.tsv
# source: core/data/pre-re/db/item_db.json
```

The generation script was last run inline; if a standalone script is needed,
extract from the conversation history or re-derive from the column specs above.

---

## Notes field convention

- Leave blank if nothing is known.
- Add short free-form text for planning notes (e.g. "pre-renewal only", "see G48").
- Do **not** duplicate info already in skill_lists/ or gaps.md — cross-reference instead.
