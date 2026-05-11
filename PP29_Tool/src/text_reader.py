"""
text_reader.py — Parse SAP-downloaded text files into structured data.

Reads the 13 daily .txt files (tab-delimited) from the SAP network folder,
extracts item-level data including monthly projection periods.

Expected text file format (tab-delimited):
  Row 1: Header (column names)
  Row 2+: Data — each item appears in multiple rows:
          - Aggregate row (no vendor): contains ESTCB/AMOUNT/RATIO totals
          - Vendor rows: contain PR/PO/PL/NORM/SVR per vendor

NETWORK DRIVE PATH:
  Configured via config.json → sap_input_path
  Example: "N:\\SAP_Downloads\\PP29_Readdone"
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ============================================================
# TEXT FILE PARSING
# ============================================================

def parse_text_file(filepath: str) -> Tuple[List[str], List[Dict]]:
    """
    Parse a single SAP text file into header + rows.

    Args:
        filepath: Full path to the .txt file

    Returns:
        (header_columns, list_of_row_dicts) where each row dict maps
        column name → value for that row
    """
    rows = []

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        # First line is the header
        header_line = f.readline()
        headers = header_line.strip().split('\t')

        for line in f:
            cols = line.strip().split('\t')
            if len(cols) < 14:
                continue  # skip malformed rows

            row = {}
            for i, h in enumerate(headers):
                row[h] = cols[i] if i < len(cols) else ''

            # Only include rows with an item code
            if row.get('Item code', '').strip():
                rows.append(row)

    return headers, rows


def extract_period_columns(headers: List[str]) -> List[str]:
    """
    Identify the monthly period date columns (format: YYYYMMDD)
    from the text file header.

    Period columns have names like '20260210 PR', '20260301 PO', etc.
    Returns sorted unique date prefixes.
    """
    period_dates = set()
    for h in headers:
        match = re.match(r'^(\d{8})\s+(PR|PO|PL|NORM|SVR|ESTCB|AMOUNT|RATIO)$', h.strip())
        if match:
            period_dates.add(match.group(1))
    return sorted(period_dates)


def get_period_values(row: Dict, period_date: str) -> Dict[str, float]:
    """
    Extract all metric values for a specific period from a row.

    Returns dict with keys: PR, PO, PL, NORM, SVR, ESTCB, AMOUNT, RATIO
    """
    metrics = {}
    for suffix in ['PR', 'PO', 'PL', 'NORM', 'SVR', 'ESTCB', 'AMOUNT', 'RATIO']:
        col_name = f"{period_date} {suffix}"
        val = row.get(col_name, '0').strip()
        try:
            metrics[suffix] = float(val) if val else 0.0
        except ValueError:
            metrics[suffix] = 0.0
    return metrics


# ============================================================
# AGGREGATION LOGIC (matching MS Access behavior)
# ============================================================

def aggregate_item_rows(rows: List[Dict], period_dates: List[str]) -> List[Dict]:
    """
    Aggregate vendor-level rows into item-level rows.

    Each item in the text file appears in up to 3 row types:
      1. AGGREGATE row:  Vendor='', Subcon To Desc=''
         -> Contains ESTCB, AMOUNT, RATIO totals for the item
      2. INTERNAL row:   Vendor='', Subcon To Desc='Internal & Other Req...'
         -> Contains NORM, SVR (internal/subcontract requirements)
      3. VENDOR rows:    Vendor!=''
         -> Contains PR, PO, PL (purchase orders to specific vendors)

    Access aggregation logic:
      - ESTCB/AMOUNT/RATIO -> taken from aggregate row only
      - PR/PO/PL/NORM/SVR  -> summed across ALL detail rows (vendor + internal)

    Returns one row per unique item.
    """
    # Group rows by item code
    item_groups: Dict[str, List[Dict]] = {}
    for row in rows:
        item_code = row.get('Item code', '').strip()
        if item_code not in item_groups:
            item_groups[item_code] = []
        item_groups[item_code].append(row)

    aggregated = []
    for item_code, group in item_groups.items():
        # Classify each row by Vendor and Subcon To Description
        agg_row = None       # ESTCB/AMOUNT/RATIO source
        detail_rows = []     # PR/PO/PL/NORM/SVR source (vendor + internal)

        for r in group:
            vendor = r.get('Vendor', '').strip()
            subcon_desc = r.get('Subcon To Description', '').strip()

            if not vendor and not subcon_desc:
                # Aggregate/total row — source of ESTCB/AMOUNT/RATIO
                agg_row = r
            else:
                # Detail row: vendor-specific OR internal requirements
                detail_rows.append(r)

        if agg_row is None:
            agg_row = group[0]  # fallback: use first row

        # Build the aggregated item row
        item = {
            'ItemCode': item_code,
            'Description': agg_row.get('Description', '').strip(),
            'OldMaterial': agg_row.get('Old Material', '').strip(),
            'MRPController': agg_row.get('MRP Controller', '').strip(),
            'MaterialType': agg_row.get('Material Type', '').strip(),
            'MaterialGroup': agg_row.get('Material Group', '').strip(),
            'ProfitCenter': agg_row.get('Profit Center', '').strip(),
            'UoM': agg_row.get('UoM', '').strip(),
            'UnitPrice': _safe_float(agg_row.get('PRICE', '0')),
        }

        # For each period:
        #   - Sum PR/PO/PL/NORM/SVR from ALL detail rows
        #   - Take ESTCB/AMOUNT/RATIO from aggregate row
        for pd in period_dates:
            # Sum ALL detail rows (vendor + internal) for quantity metrics
            detail_sums = {'PR': 0.0, 'PO': 0.0, 'PL': 0.0,
                          'NORM': 0.0, 'SVR': 0.0}
            for dr in detail_rows:
                dm = get_period_values(dr, pd)
                for k in detail_sums:
                    detail_sums[k] += dm[k]

            # Aggregate row metrics (ESTCB, AMOUNT, RATIO)
            am = get_period_values(agg_row, pd)

            for k in detail_sums:
                item[f"{pd}_{k}"] = detail_sums[k]
            item[f"{pd}_ESTCB"] = am['ESTCB']
            item[f"{pd}_AMOUNT"] = am['AMOUNT']
            item[f"{pd}_RATIO"] = am['RATIO']

        # Also extract balance/base values from aggregate row
        item['BL_PR'] = _safe_float(agg_row.get('BL PR', '0'))
        item['BL_PO'] = _safe_float(agg_row.get('BL PO', '0'))
        item['BL_PL'] = _safe_float(agg_row.get('BL PL', '0'))
        item['BL_NORM'] = _safe_float(agg_row.get('BL NORM', '0'))
        item['BL_SVR'] = _safe_float(agg_row.get('BL SVR', '0'))

        aggregated.append(item)

    return aggregated


# ============================================================
# MAIN READER — called by daily.py
# ============================================================

def read_daily_files(
    folder_path: str,
    date_str: str,
    entities: List[str]
) -> Tuple[List[Dict], List[str]]:
    """
    Read all 13 entity text files for a given date.

    Args:
        folder_path:  NETWORK DRIVE PATH — where SAP .txt files land
                      (from config.json → sap_input_path)
        date_str:     Date to read in YYYYMMDD format (e.g., '20260210')
        entities:     List of entity codes to look for (e.g., ['CUS2100ROH', ...])

    Returns:
        (aggregated_items, period_dates) — all items combined from all
        13 files, with vendor rows already aggregated
    """
    all_items = []
    all_period_dates = set()
    files_found = 0

    for entity in entities:
        # SAP files are named: PP29_{ENTITY}_{DATE}_*.txt
        # Find matching file in the folder
        pattern = f"PP29_{entity}_{date_str}"
        matches = []
        for fname in os.listdir(folder_path):
            if fname.startswith(pattern) and fname.endswith('.txt'):
                matches.append(fname)

        if not matches:
            print(f"  [WARN] No file found for {entity} on {date_str}, skipping")
            continue

        # Use the first match (there should be exactly one)
        filepath = os.path.join(folder_path, matches[0])
        print(f"  Reading: {matches[0]}")

        headers, rows = parse_text_file(filepath)
        period_dates = extract_period_columns(headers)
        all_period_dates.update(period_dates)

        aggregated = aggregate_item_rows(rows, period_dates)
        for item in aggregated:
            item['SourceEntity'] = entity  # track which entity file it came from

        all_items.extend(aggregated)
        files_found += 1

    sorted_periods = sorted(all_period_dates)
    print(f"  Total: {files_found} files, {len(all_items)} items, "
          f"{len(sorted_periods)} periods")

    return all_items, sorted_periods


# ============================================================
# HELPERS
# ============================================================

def _safe_float(val: str) -> float:
    """Convert string to float, returning 0.0 on failure."""
    try:
        return float(val.strip()) if val.strip() else 0.0
    except ValueError:
        return 0.0


# ============================================================
# STANDALONE TEST (run: python text_reader.py)
# ============================================================

if __name__ == '__main__':
    import sys

    # ─── CONFIGURE TEST PATH HERE ───────────────────────────
    # NETWORK DRIVE PATH: Where SAP text files are located
    # Example: "N:\\SAP_Downloads\\PP29_Readdone"
    test_folder = "/home/adam/Downloads/PP29_Readdone_Feb'26"
    test_date = "20260210"
    # ────────────────────────────────────────────────────────

    test_entities = [
        "CUS2100ROH", "CUS2100SFPB1", "CUS2100SFPB2", "CUS2100SFPB3",
        "CUS2100SFPB4", "CUS2100SFPB5A", "CUS2100SFPB5B", "CUS2100SFPB6",
        "CUS2100SFPB7", "CUS2100SFPB8", "CUS2100SFPR", "CUS2100SFUB",
        "CUS2100SUB"
    ]

    print(f"Testing text_reader on {test_date}...")
    items, periods = read_daily_files(test_folder, test_date, test_entities)

    print(f"\nSample aggregated items (first 3):")
    for item in items[:3]:
        print(f"  {item['ItemCode']}: {item['Description'][:50]}")
        print(f"    MRPC={item['MRPController']}, "
              f"MatType={item['MaterialType']}, "
              f"Price={item['UnitPrice']}")
        for pd in periods[:2]:
            print(f"    Period {pd}: PR={item.get(f'{pd}_PR',0):.0f}, "
                  f"PO={item.get(f'{pd}_PO',0):.0f}, "
                  f"ESTCB={item.get(f'{pd}_ESTCB',0):.0f}")
