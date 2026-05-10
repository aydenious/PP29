# PP29 — Purchase Plan Consolidation & Automation

## Overview

Replace the manual Microsoft Access workflow that generates daily Purchase Plan Excel files from 13 SAP-downloaded text files. Automate consolidation, enable historical comparison, and run fully portable — zero software installation required.

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

```
PP29_Tool/                          ← single folder on network drive or USB
├── python.exe                      ← Python embeddable (Windows)
├── python3xx.zip                   ← standard library
├── python3xx._pth                  ← site-packages path config
├── Lib/
│   └── site-packages/
│       ├── openpyxl/               ← Excel .xlsx read/write
│       ├── xlrd/                   ← Excel .xls read (old format)
│       └── et_xmlfile/             ← openpyxl dependency
├── config.json                     ← user-editable paths/settings
├── src/
│   ├── daily.py                    ← daily generator (replaces Access)
│   ├── consolidate.py              ← multi-date consolidation
│   ├── query.py                    ← ad-hoc queries
│   ├── text_reader.py              ← parse SAP .txt files
│   ├── excel_writer.py             ← write formatted .xlsx
│   └── db.py                       ← SQLite read/write
├── data/
│   └── pp29_history.db             ← SQLite historical database
├── output/                         ← generated files land here
├── logs/                           ← execution logs
└── run_daily.bat                   ← double-click to run daily
```

### Config File (`config.json`)

```json
{
    "sap_input_path": "N:\\SAP_Downloads\\PP29_Readdone",
    "excel_output_path": ".\\output",
    "db_path": ".\\data\\pp29_history.db",
    "log_path": ".\\logs"
}
```

### SQLite Schema

```sql
-- Raw data from text files (every row, every day)
CREATE TABLE raw_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    entity TEXT NOT NULL,
    item_code TEXT NOT NULL,
    description TEXT,
    mat_type TEXT,
    mat_group TEXT,
    mrp_controller TEXT,
    profit_center TEXT,
    vendor TEXT,
    vendor_desc TEXT,
    subcon_to TEXT,
    uom TEXT,
    unit_price REAL,
    -- Balance
    bl_pr REAL, bl_po REAL, bl_pl REAL, bl_norm REAL, bl_svr REAL,
    -- Monthly projections (stored as JSON for flexibility)
    periods TEXT
);

-- Daily execution log
CREATE TABLE run_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT,
    mode TEXT,
    files_processed INTEGER,
    rows_total INTEGER,
    status TEXT,
    error TEXT
);
```

---

## Implementation Phases

### Phase 1: Core Daily Generator (replaces Access) — Week 1

**Goal:** Produce identical Excel output to current Access process.

- [ ] Parse 13 SAP .txt files → unified data structure
- [ ] Map text file columns to Excel pivot columns:
  - PR → pr/sugg, PO → po, PL → pl, NORM → prod, SVR → svr
  - ESTCB → cb, AMOUNT → cbAmt, RATIO → ratio
- [ ] Aggregate vendor-level rows → item-level (match Access logic)
- [ ] Convert monthly periods → 16 weekly period buckets
- [ ] Write to .xlsx with same sheet layout (Sheet1 headers, Sheet4 pivot)
- [ ] Log execution to run_log table

### Phase 2: Historical Database — Week 1-2

- [ ] Create SQLite database with schema above
- [ ] On each daily run, append all rows to `raw_data` table
- [ ] Add deduplication (skip if same date+entity already loaded)
- [ ] Add --backfill mode to import existing historical .xls files

### Phase 3: Consolidation & Comparison — Week 2

- [ ] Read all available daily .xlsx files
- [ ] Combine into master "All Data" sheet
- [ ] Generate "Summary by Date" sheet with trend charts
- [ ] Generate "Day Changes" sheet (deltas, color-coded)
- [ ] Generate "Top Monthly Changes" sheet
- [ ] Handle column variance between dates (106 vs 108 cols)

### Phase 4: Query Mode & Polish — Week 2-3

- [ ] Item lookup: "show all dates for item X"
- [ ] Date range comparison: "compare Feb 10 vs Feb 27"
- [ ] Vendor analysis: "which vendors had PO changes?"
- [ ] Export results to formatted Excel

### Phase 5: Automation — Week 3

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

## Risk Register

| Risk | Mitigation |
|---|---|
| Access pivot logic not fully understood | Phase 1: compare script output byte-by-byte with Access output for same date |
| Text file format changes from SAP | Schema validation on read; alert on mismatch |
| Column count variance (106 vs 108) | Dynamic column mapping with fallback defaults |
| Network drive unavailable | Retry logic; local cache of last successful run |
| Large data volume over years | SQLite handles millions of rows; archive old periods |

---

## Success Metrics

- [ ] Daily Excel output matches Access output (100% row match, <1% value difference)
- [ ] Daily run completes in <30 seconds
- [ ] Historical database covers all dates from Feb 2026 onwards
- [ ] User can compare any two dates in <10 seconds
- [ ] Works on company laptop with zero software installation

---

## Repository Structure

```
PP29/
├── README.md
├── IMPLEMENTATION_PLAN.md          ← this file
├── src/
│   ├── daily.py
│   ├── consolidate.py
│   ├── query.py
│   ├── text_reader.py
│   ├── excel_writer.py
│   └── db.py
├── config.example.json
├── run_daily.bat
├── run_consolidate.bat
├── tests/
│   └── test_data/
└── docs/
    └── column_mapping.md
```

---

*Last updated: 2026-05-10*
