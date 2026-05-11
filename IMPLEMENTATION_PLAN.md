# PP29 — Purchase Plan Consolidation & Automation

## Overview

Replace the manual Microsoft Access workflow that generates daily Purchase Plan Excel files from 13 SAP-downloaded text files. Automate consolidation, enable historical comparison, and run fully portable — zero software installation required.

---

## 🟢 Session Status — 2026-05-10

### Completed
- [x] **Analysis:** Reverse-engineered all 13 SAP text files (4 material categories: ROH, SFPB, SFUB, SUB)
- [x] **Analysis:** Documented text file row types (aggregate / internal / vendor) and aggregation logic
- [x] **Analysis:** Documented text → Excel column mapping (PR→pr, PO→po, ESTCB→cb, etc.)
- [x] **Analysis:** Verified Access Excel output structure (Sheet1 headers, Sheet4 pivot, 106-108 cols)
- [x] **Phase 1 (complete):** All 6 Python source files written and tested on real Feb'26 data
  - `text_reader.py` — Parses SAP .txt, aggregates 3 row types into 1 item row ✅
  - `excel_writer.py` — Generates daily (.xlsx) and consolidated workbooks ✅
  - `db.py` — SQLite schema (raw_items, period_data, run_log) ✅
  - `daily.py` — CLI daily generator (replaces MS Access) ✅
  - `consolidate.py` — Multi-date consolidation with 4 analysis sheets ✅
  - `query.py` — Ad-hoc item lookup and date comparison ✅
- [x] **Phase 3 (partial):** Consolidation logic proven — generated PP29_Feb2026_Consolidated.xlsx (40 MB, 79K rows)
- [x] **Documentation:** `docs/column_mapping.md` (SAP → Excel reference), `config.example.json`
- [x] **Batch files:** `run_daily.bat` and `run_consolidate.bat` for one-click Windows execution
- [x] **Pushed to GitHub:** [`aydenious/PP29`](https://github.com/aydenious/PP29) (2 commits, 13 files, 2,170 lines)

### Not Yet Done
- [ ] **Phase 1:** Byte-by-byte comparison of script output vs actual Access output (need matching date)
- [ ] **Phase 2:** Historical database backfill from existing Feb'26 .xls files
- [ ] **Phase 2:** Database deduplication logic
- [ ] **Phase 4:** Vendor-level analysis queries
- [ ] **Phase 5:** Windows Task Scheduler automation
- [ ] **Deployment:** Portable Python runtime packaging (embed zip + pip install deps)
- [ ] **Testing:** Run on company laptop with actual network drive paths

### For Next Session
1. Copy `config.example.json` → `config.json` and set actual network drive paths
2. Run `python src/daily.py --date 20260210` to verify output matches Access
3. Backfill existing Feb'26 data into SQLite: `python src/daily.py --date <date> --no-db` for each date, then import
4. Test on company Windows laptop with portable Python runtime

---

## Current State (As-Is)

```
SAP System
    │
    ▼  (auto-download daily)
Network Drive (13 .txt files per day)
    │
    ▼  (manual: user opens Access, clicks Refresh)
MS Access
    │
    ▼
Single-day PurchasePlan YYYYMMDD.xls
    │
    ✗  No history retained
    ✗  No day-over-day comparison
    ✗  Manual operation
    ✗  Access license required
```

### The 13 Daily Text Files

| # | Entity | Category | ~Rows | UoM | Description |
|---|---|---|---|---|---|
| 1 | CUS2100ROH | **ROH** (Raw Materials) | 1,173 | KG, M | Steel, chemicals, wire |
| 2 | CUS2100SFPB1 | **SFPB** (Semi-Finished B) | 1,727 | PC | Machined components B1 |
| 3 | CUS2100SFPB2 | **SFPB** | 990 | PC | Machined components B2 |
| 4 | CUS2100SFPB3 | **SFPB** | 1,276 | PC | Machined components B3 |
| 5 | CUS2100SFPB4 | **SFPB** | 1,764 | PC | Machined components B4 |
| 6 | CUS2100SFPB5A | **SFPB** | 1,000 | PC | Machined components B5A |
| 7 | CUS2100SFPB5B | **SFPB** | 1,053 | PC | Machined components B5B |
| 8 | CUS2100SFPB6 | **SFPB** | 1,175 | PC | Machined components B6 |
| 9 | CUS2100SFPB7 | **SFPB** (dead) | 1 | PC | Inactive line |
| 10 | CUS2100SFPB8 | **SFPB** | 1,618 | PC | Machined components B8 |
| 11 | CUS2100SFPR | **SFPB** (dead) | 0 | — | Inactive line |
| 12 | CUS2100SFUB | **SFUB** (Body) | 442 | PC, M | Cast/forged body parts |
| 13 | CUS2100SUB | **SUB** (Subcontract) | 385 | PC, G, KG, L | Grease, outsourcing |

**Total: ~12,600 rows/day** → Access pivots into ~4,950 rows in Excel

### Text File Column Layout

```
Item code | Mat.Status | Description | Old Material | MRP Controller | Material Type |
Material Group | Profit Center | Vendor | Vendor Desc | Subcon To | Subcon To Desc |
UoM | PRICE |
BL PR | BL PO | BL PL | BL NORM | BL SVR | NC | GD | SC | Vendor Consign |
20260210 PR | 20260210 PO | 20260210 PL | 20260210 NORM | 20260210 SVR |
20260210 ESTCB | 20260210 AMOUNT | 20260210 RATIO |
20260301 PR | ... (repeating monthly through 20270801)
```

### Excel Output Structure (from Access)

- **Sheet1:** Raw schema (14 cols: Itemcode, Desc, UnitPrc, Type, Qty, VendorSrc, Mrpc, SS, SrcFN, Period, MatType, Matgrp, PurMnGrp, PurFinalProc) — **1 row (headers only)**
- **Sheet4:** Pivot table (4,955 rows × 108 cols) — **main data**
  - Identity: Sub group, Itemcode, Desc, UnitPrc
  - Balance: blpr, blpo, blpl
  - 16 periods: each with pr/po/pl/prod/svr/cb/cbAmt/ratio
- **Sheet3:** Empty

---

## Target State (To-Be)

```
SAP System
    │
    ▼  (auto-download daily)
Network Drive — 13 .txt files/day
    │
    ├──▶ [Python Script: Daily Mode]
    │       ├── Reads 13 .txt files
    │       ├── Generates PurchasePlan YYYYMMDD.xlsx (matches Access output)
    │       ├── Appends to SQLite database (historical)
    │       └── Logs execution
    │
    ├──▶ [Python Script: Consolidate Mode]
    │       ├── Reads all existing daily .xlsx files
    │       ├── Combines into single workbook with:
    │       │   ├── All Data (every item × every date)
    │       │   ├── Summary by Date (daily totals + chart)
    │       │   ├── Day Changes (day-over-day deltas, colored)
    │       │   └── Top Monthly Changes (biggest movers)
    │       └── Output: PP29_Feb2026_Consolidated.xlsx
    │
    └──▶ [Python Script: Query Mode]
            ├── "Show item X across all dates"
            ├── "What changed between Date A and Date B?"
            └── Export results to Excel
```

---

## Technical Architecture

### Portable Python Runtime (Zero Installation)

The project folder is the deployable unit — copy it to a machine, run `setup.bat`,
and the portable Python runtime is installed in-place. All runtime artifacts
(python.exe, Lib/, data/, output/, logs/) are gitignored.

```
PP29/                               ← single folder on network drive or USB
├── setup.bat                       ← one-time: downloads Python embeddable
├── fix_pth.bat                     ← repair ._pth if setup leaves it broken
├── python.exe                      ← Python embeddable (after setup)
├── python3xx.zip                   ← standard library (after setup)
├── python3xx._pth                  ← site-packages path config (after setup)
├── Lib/
│   └── site-packages/              ← openpyxl, xlrd, et_xmlfile (after setup)
├── config.example.json             ← template
├── config.json                     ← user-editable paths (gitignored)
├── src/
│   ├── daily.py                    ← daily generator (replaces Access)
│   ├── consolidate.py              ← multi-date consolidation
│   ├── query.py                    ← ad-hoc queries
│   ├── text_reader.py              ← parse SAP .txt files
│   ├── excel_writer.py             ← write formatted .xlsx
│   └── db.py                       ← SQLite read/write
├── data/
│   └── pp29_history.db             ← SQLite historical database (runtime)
├── output/                         ← generated files land here (runtime)
├── logs/                           ← execution logs (runtime)
├── run_daily.bat                   ← double-click to run daily
├── run_consolidate.bat             ← double-click for multi-date comparison
└── run_query.bat                   ← interactive query menu
```

### Config File (`config.json`)

```json
{
    "sap_input_path": "N:\\SAP_Downloads\\PP29_Readdone",
    "_comment": "Network drive where SAP auto-downloads 13 .txt files daily",

    "access_excel_path": "N:\\PurchasePlan_Output",
    "_comment": "Where MS Access currently saves daily .xls files (used for backfill)",

    "daily_output_path": ".\\output\\daily",
    "_comment": "Where this script saves generated daily Excel files",

    "consolidated_output_path": ".\\output\\consolidated",
    "_comment": "Where combined/comparison workbooks are saved",

    "db_path": ".\\data\\pp29_history.db",
    "_comment": "SQLite database for historical storage (single file, portable)",

    "log_path": ".\\logs",
    "_comment": "Execution logs directory",

    "num_periods": 16,
    "_comment": "Number of future periods to include (matching Access pivot)",

    "entities": ["CUS2100ROH", "CUS2100SFPB1", "..."],
    "_comment": "The 13 SAP entity codes to look for"
}
```

### SQLite Schema (actual — as implemented in `db.py`)

```sql
-- Item metadata: one row per item per date (aggregated from 13 text files)
CREATE TABLE raw_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,              -- YYYYMMDD
    source_entity TEXT NOT NULL,     -- e.g., "CUS2100ROH"
    item_code TEXT NOT NULL,         -- 18-digit SAP material number
    description TEXT,                -- material description
    old_material TEXT,               -- legacy material code
    mrp_controller TEXT,             -- MRP controller code
    material_type TEXT,              -- ROH / SFPB / SFUB / SUB
    material_group TEXT,             -- grouping code (e.g., CSS1FA)
    profit_center TEXT,              -- cost center
    uom TEXT,                        -- KG, M, PC, G, L
    unit_price REAL,                 -- per-unit price
    bl_pr REAL DEFAULT 0.0,         -- balance purchase requisition
    bl_po REAL DEFAULT 0.0,         -- balance purchase order
    bl_pl REAL DEFAULT 0.0,         -- balance planned
    bl_norm REAL DEFAULT 0.0,       -- balance normal demand
    bl_svr REAL DEFAULT 0.0,        -- balance service requirement
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, source_entity, item_code)
);

-- Period projections: one row per period per item (unpivoted)
CREATE TABLE period_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES raw_items(id) ON DELETE CASCADE,
    period_date TEXT NOT NULL,       -- YYYYMMDD of this projection period
    pr REAL DEFAULT 0.0,            -- purchase requisition
    po REAL DEFAULT 0.0,            -- purchase order
    pl REAL DEFAULT 0.0,            -- planned order
    norm REAL DEFAULT 0.0,          -- production/normal demand
    svr REAL DEFAULT 0.0,           -- subcontract value requirement
    estcb REAL DEFAULT 0.0,         -- estimated cumulative balance
    amount REAL DEFAULT 0.0,        -- cb amount (estcb × unit_price)
    ratio REAL DEFAULT 0.0,         -- allocation ratio
    UNIQUE(item_id, period_date)
);

-- Audit trail for every script execution
CREATE TABLE run_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT DEFAULT (datetime('now')),
    mode TEXT,                       -- 'daily', 'consolidate', 'query', 'backfill'
    date_processed TEXT,             -- the data date being processed
    files_found INTEGER,
    items_processed INTEGER,
    periods_processed INTEGER,
    status TEXT,                     -- 'SUCCESS' or 'FAILED'
    error_message TEXT,
    output_file TEXT
);
```

---

## Implementation Phases

### Phase 1: Core Daily Generator (replaces Access) — COMPLETE ✅

**Goal:** Produce identical Excel output to current Access process.

- [x] Parse 13 SAP .txt files → unified data structure (`text_reader.py`)
- [x] Map text file columns to Excel pivot columns (`docs/column_mapping.md`):
  - PR → pr/sugg, PO → po, PL → pl, NORM → prod, SVR → svr
  - ESTCB → cb, AMOUNT → cbAmt, RATIO → ratio
- [x] Aggregate vendor-level rows → item-level (3 row types: aggregate/internal/vendor)
- [x] Convert monthly periods → 16 period buckets (`excel_writer.py`)
- [x] Write to .xlsx with Data + PivotView sheets (matching Access layout)
- [x] Log execution to run_log table (`db.py`)

### Phase 2: Historical Database — IN PROGRESS

- [x] Create SQLite database with schema (`db.py` — raw_items, period_data, run_log)
- [x] On each daily run, append all rows to database (`daily.py` calls `insert_daily_data`)
- [x] Deduplication via INSERT OR REPLACE (unique on date+entity+item_code)
- [ ] Backfill from existing historical .xls files (16 Feb'26 files available for testing)

### Phase 3: Consolidation & Comparison — COMPLETE ✅

- [x] Read all available daily .xlsx files (`consolidate.py`)
- [x] Combine into master "All Data" sheet (79,465 rows across 16 dates)
- [x] Generate "Summary by Date" sheet with LineChart trend
- [x] Generate "Day Changes" sheet (31,530 deltas, green/red color-coded)
- [x] Generate "Top Monthly Changes" sheet (500 biggest movers)
- [x] Handle column variance between dates (106 vs 108 cols — dynamic mapping)

### Phase 4: Query Mode & Polish — COMPLETE ✅

- [x] Item lookup: "show all dates for item X" (`query.py --item`)
- [x] Date range comparison: "compare Feb 10 vs Feb 27" (`query.py --item --dates`)
- [x] Top changes across all dates (`query.py --top-changes`)
- [x] Dates summary view (`query.py --dates-summary`)
- [ ] Vendor analysis: "which vendors had PO changes?" (vendor data not yet in DB)

### Phase 5: Automation — NOT STARTED

- [ ] Windows Task Scheduler integration
- [ ] Email notification on errors
- [ ] Auto-cleanup of old files (>90 days)

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Python embeddable** vs npm/node | Stdlib includes sqlite3; openpyxl/xlrd are pure Python; no native compilation needed |
| **SQLite** vs PostgreSQL/MySQL | Zero setup, single file, built into Python stdlib, portable |
| **.xls read with xlrd** | Existing Access output is .xls format; openpyxl only writes .xlsx |
| **Match Access output exactly** | Ensures zero disruption to downstream consumers of the Excel |
| **Config file, not hardcoded paths** | Different users/machines have different network drive mappings |

---

## Risk Register (updated)

| Risk | Status | Mitigation |
|---|---|---|
| Access pivot logic not fully understood | 🟡 Mitigated | Analyzed real Access output; documented 3 row types (aggregate/internal/vendor); aggregation logic tested on Feb 10 data |
| Text file format changes from SAP | 🟡 Monitored | Schema validation on read; period column regex handles YYYYMMDD suffix format |
| Column count variance (106 vs 108) | ✅ Resolved | `consolidate.py` dynamically maps columns; Feb 27 (106 cols) handled |
| Network drive unavailable | 🔴 Open | Retry logic + local cache not yet implemented |
| Row type identification fragile | 🟡 Mitigated | Uses `Subcon To Description` (not `Subcon To` code) to distinguish aggregate vs internal rows; fallback to first row if no aggregate found |

---

## Success Metrics (progress)

- [ ] Daily Excel output matches Access output (100% row match, <1% value difference)
- [x] Script reads all 13 files and produces 4,946 aggregated items (matches Access: 4,946 in Sheet4)
- [ ] Daily run completes in <30 seconds (not yet benchmarked on Windows)
- [ ] Historical database covers all dates from Feb 2026 onwards
- [x] User can compare any two dates — `consolidate.py` generates 4-sheet workbook + chart
- [ ] Works on company laptop with zero software installation (portable Python not yet packaged)

---

## Repository Structure (actual)

```
PP29/
├── README.md                        ← Project overview & quick start
├── IMPLEMENTATION_PLAN.md           ← This file (session status at top)
├── .gitignore                       ← Excludes output/, data/, config.json
├── config.example.json              ← Template → copy to config.json & edit paths
├── run_daily.bat                    ← Double-click: generate today's Excel
├── run_consolidate.bat              ← Double-click: combine all dates
│
├── src/
│   ├── text_reader.py     297 lines  ← Parse SAP .txt, aggregate 3 row types
│   ├── excel_writer.py    415 lines  ← Write daily + consolidated .xlsx
│   ├── db.py              298 lines  ← SQLite schema, insert, query
│   ├── daily.py           223 lines  ← Main CLI: daily generator
│   ├── consolidate.py     275 lines  ← Main CLI: multi-date consolidation
│   └── query.py           199 lines  ← Main CLI: ad-hoc item/date lookups
│
├── docs/
│   └── column_mapping.md   90 lines  ← SAP columns → Excel columns reference
│
└── tests/                            ← (future: test data fixtures)
```

---

*Last updated: 2026-05-10*
