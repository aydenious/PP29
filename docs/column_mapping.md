# Column Mapping: SAP Text Files → Excel Output

## Text File Columns (header row)

| # | Column Name | Description |
|---|---|---|
| 0 | Item code | 18-digit SAP material number |
| 1 | Material Status | Status code |
| 2 | Description | Material description |
| 3 | Old Material | Legacy material number |
| 4 | MRP Controller | Material Requirements Planning controller code |
| 5 | Material Type | **ROH** / **SFPB** / **SFUB** / **SUB** |
| 6 | Material Group | Grouping code (e.g., CSS1FA, BBS0AC) |
| 7 | Profit Center | Cost center code |
| 8 | Vendor | Supplier number |
| 9 | Vendor Description | Supplier name |
| 10 | Subcon To | Subcontractor code |
| 11 | Subcon To Description | Subcontractor name or "Internal & Other Requirements" |
| 12 | UoM | Unit of Measure (KG, M, PC, G, L) |
| 13 | PRICE | Unit price |
| 14-18 | BL PR/PO/PL/NORM/SVR | Balance/base values |
| 19-22 | NC/GD/SC/Vendor Consign | Status flags |
| 23+ | `YYYYMMDD` PR/PO/PL/NORM/SVR/ESTCB/AMOUNT/RATIO | Monthly projections |

## Row Types (per item)

| Row Type | Vendor | Subcon To Desc | Contains |
|---|---|---|---|
| **Aggregate** | *empty* | *empty* | ESTCB, AMOUNT, RATIO (total/item-level) |
| **Internal** | *empty* | "Internal & Other Requirements" | NORM, SVR (future subcontract needs) |
| **Vendor** | `0001XXXXXX` | *varies* | PR, PO, PL (vendor-specific POs) |

## Aggregation Rule (matching MS Access)

```
For each item:
  ESTCB  = from Aggregate row (not summed)
  AMOUNT = from Aggregate row (not summed)
  RATIO  = from Aggregate row (not summed)
  PR     = SUM(Internal row + all Vendor rows)
  PO     = SUM(Internal row + all Vendor rows)
  PL     = SUM(Internal row + all Vendor rows)
  NORM   = SUM(Internal row + all Vendor rows)
  SVR    = SUM(Internal row + all Vendor rows)
```

## Text → Excel Period Mapping

| Text Period | → | Excel Pivot Column |
|---|---|---|
| `20260210` (current month) | | 1st (period 1) |
| `20260301` (next month) | | 2nd (period 2) |
| `20260401` | | 3rd (period 3) |
| ... | | ... |
| Up to 16 periods | | 16th (period 16) |

## Text Column → Excel Pivot Metric

| Text Metric | → | Excel Metric | Description |
|---|---|---|---|
| PR | | `pr` / `sugg` | Purchase Requisition (Suggestion) |
| PO | | `po` | Purchase Order |
| PL | | `pl` | Planned Order |
| NORM | | `prod` | Production / Normal Demand |
| SVR | | `svr` | Subcontract Value Requirement |
| ESTCB | | `cb` | Estimated Cumulative Balance |
| AMOUNT | | `cbAmt` | CB Amount (= ESTCB × Unit Price) |
| RATIO | | `ratio` | Allocation ratio |

## Excel Output Structure (matching Access)

### Sheet "Data" (clean format)
```
ItemCode | Description | ... | BL_PR | BL_PO | ... | 20260210_PR | 20260210_PO | ...
```

### Sheet "PivotView" (matching Access Sheet4)
```
SubGroup | ItemCode | Desc | UnitPrc | blpr | blpo | 1stOB | 1stsugg | 1stpl | ...
```

## Entity → Material Type

| Entity Code | MatType | UoM | Description |
|---|---|---|---|
| CUS2100ROH | ROH | KG, M | Raw Materials |
| CUS2100SFPB1-8 | SFPB | PC | Semi-Finished Parts B |
| CUS2100SFPR | SFPB | PC | Semi-Finished Parts R (inactive) |
| CUS2100SFUB | SFUB | PC, M | Unfinished Body Parts |
| CUS2100SUB | SUB | PC, G, KG, L | Subcontract Materials |
