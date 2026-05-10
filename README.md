# PP29 — Purchase Plan Automation

Replaces manual MS Access workflow for daily Purchase Plan generation from SAP text files. Fully portable — zero installation required.

## What It Does

- **Daily Mode:** Reads 13 SAP text files → generates daily Purchase Plan Excel (replaces Access)
- **Consolidate Mode:** Combines all daily Excels → comparison workbook with trends & day-over-day changes
- **Query Mode:** Lookup any item across dates, export comparison reports
- **Historical DB:** SQLite stores every day's data for permanent retrieval

## Quick Start

1. Copy `PP29_Tool/` folder to your machine or network drive
2. Edit `config.json` with your SAP download path
3. Double-click `run_daily.bat`

No admin rights, no software installation, no registry changes.

## Structure

```
PP29/
├── IMPLEMENTATION_PLAN.md    ← Full technical plan
├── src/                      ← Python scripts
├── config.example.json       ← Configuration template
├── run_daily.bat             ← One-click daily run
└── run_consolidate.bat       ← Multi-date comparison
```

## Requirements

- Windows 10/11 (Python embeddable included in tool folder)
- Network access to SAP download folder
- Write access to output folder
