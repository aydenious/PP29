# PP29 — Purchase Plan Automation

Replaces manual MS Access workflow for daily Purchase Plan generation from SAP text files. Fully portable — zero installation required.

## What It Does

- **Daily Mode:** Reads 13 SAP text files → generates daily Purchase Plan Excel (replaces Access)
- **Consolidate Mode:** Combines all daily Excels → comparison workbook with trends & day-over-day changes
- **Query Mode:** Lookup any item across dates, export comparison reports
- **Historical DB:** SQLite stores every day's data for permanent retrieval

## Quick Start

1. Copy this folder to your machine or network drive
2. Double-click `setup.bat` (downloads portable Python + dependencies in-place)
3. Copy `config.example.json` → `config.json` and edit the paths
4. Double-click `run_daily.bat`

No admin rights, no system-wide installation, no registry changes.

## Structure

```
PP29/
├── IMPLEMENTATION_PLAN.md    ← Full technical plan
├── README.md
├── src/                      ← Python scripts (canonical source)
├── docs/                     ← Column mapping reference
├── config.example.json       ← Configuration template
├── setup.bat                 ← One-time: install portable Python here
├── fix_pth.bat               ← Repair tool if setup leaves a broken ._pth
├── run_daily.bat             ← One-click daily run
├── run_consolidate.bat       ← Multi-date comparison
└── run_query.bat             ← Interactive query menu
```

After `setup.bat` runs, the folder also contains `python.exe`, `Lib/site-packages/`,
plus the runtime `data/`, `output/`, `logs/` directories — all gitignored.

## Requirements

- Windows 10/11 (Python embeddable downloaded by `setup.bat`)
- Network access to SAP download folder
- Write access to this folder
