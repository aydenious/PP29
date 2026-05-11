"""
db.py — SQLite database for historical purchase plan storage.

Stores every day's data permanently so users can query across dates
without needing to load all Excel files.

DATABASE PATH:
  Configured via config.json → db_path
  Default: ".\\data\\pp29_history.db"
  This is a single-file database, fully portable — no server needed.

SCHEMA:
  raw_items       — One row per item per date (aggregated from 13 text files)
  period_data     — One row per item per date per period (unpivoted)
  run_log         — Execution audit trail
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_database(db_path: str) -> sqlite3.Connection:
    """
    Initialize the SQLite database with required tables.
    Creates the database file and directory if they don't exist.

    Args:
        db_path: DATABASE FILE PATH — where to store pp29_history.db
                 (from config.json → db_path)

    Returns:
        sqlite3.Connection object
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")       # better concurrent access
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        -- Core item data: one row per item per date (aggregated)
        CREATE TABLE IF NOT EXISTS raw_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            source_entity TEXT NOT NULL,
            item_code TEXT NOT NULL,
            description TEXT,
            old_material TEXT,
            mrp_controller TEXT,
            material_type TEXT,
            material_group TEXT,
            profit_center TEXT,
            uom TEXT,
            unit_price REAL,
            bl_pr REAL DEFAULT 0.0,
            bl_po REAL DEFAULT 0.0,
            bl_pl REAL DEFAULT 0.0,
            bl_norm REAL DEFAULT 0.0,
            bl_svr REAL DEFAULT 0.0,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(date, source_entity, item_code)
        );

        -- Period data: unpivoted monthly projections
        -- Each row = one metric value for one period for one item
        CREATE TABLE IF NOT EXISTS period_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            period_date TEXT NOT NULL,
            pr REAL DEFAULT 0.0,
            po REAL DEFAULT 0.0,
            pl REAL DEFAULT 0.0,
            norm REAL DEFAULT 0.0,
            svr REAL DEFAULT 0.0,
            estcb REAL DEFAULT 0.0,
            amount REAL DEFAULT 0.0,
            ratio REAL DEFAULT 0.0,
            FOREIGN KEY (item_id) REFERENCES raw_items(id) ON DELETE CASCADE,
            UNIQUE(item_id, period_date)
        );

        -- Execution audit log
        CREATE TABLE IF NOT EXISTS run_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT DEFAULT (datetime('now')),
            mode TEXT,
            date_processed TEXT,
            files_found INTEGER,
            items_processed INTEGER,
            periods_processed INTEGER,
            status TEXT,
            error_message TEXT,
            output_file TEXT
        );

        -- Indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_raw_items_date ON raw_items(date);
        CREATE INDEX IF NOT EXISTS idx_raw_items_item ON raw_items(item_code);
        CREATE INDEX IF NOT EXISTS idx_raw_items_type ON raw_items(material_type);
        CREATE INDEX IF NOT EXISTS idx_period_data_item ON period_data(item_id);
        CREATE INDEX IF NOT EXISTS idx_period_data_date ON period_data(period_date);
    """)

    conn.commit()
    return conn


# ============================================================
# INSERT OPERATIONS
# ============================================================

def insert_daily_data(
    conn: sqlite3.Connection,
    date_str: str,
    items: List[Dict],
    period_dates: List[str]
) -> int:
    """
    Insert one day's aggregated data into the database.

    Uses INSERT OR REPLACE to handle re-runs for the same date.

    Args:
        conn:          Active database connection
        date_str:      Date in YYYYMMDD format
        items:         Aggregated item rows from text_reader
        period_dates:  Sorted period date strings

    Returns:
        Number of items inserted
    """
    cursor = conn.cursor()
    count = 0

    for item in items:
        # Insert/update raw_items
        cursor.execute("""
            INSERT OR REPLACE INTO raw_items
                (date, source_entity, item_code, description, old_material,
                 mrp_controller, material_type, material_group, profit_center,
                 uom, unit_price, bl_pr, bl_po, bl_pl, bl_norm, bl_svr)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date_str,
            item.get('SourceEntity', ''),
            item.get('ItemCode', ''),
            item.get('Description', ''),
            item.get('OldMaterial', ''),
            item.get('MRPController', ''),
            item.get('MaterialType', ''),
            item.get('MaterialGroup', ''),
            item.get('ProfitCenter', ''),
            item.get('UoM', ''),
            item.get('UnitPrice', 0.0),
            item.get('BL_PR', 0.0),
            item.get('BL_PO', 0.0),
            item.get('BL_PL', 0.0),
            item.get('BL_NORM', 0.0),
            item.get('BL_SVR', 0.0),
        ))
        item_id = cursor.lastrowid

        # Insert period data
        for pd in period_dates:
            cursor.execute("""
                INSERT OR REPLACE INTO period_data
                    (item_id, period_date, pr, po, pl, norm, svr, estcb, amount, ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id, pd,
                item.get(f'{pd}_PR', 0.0),
                item.get(f'{pd}_PO', 0.0),
                item.get(f'{pd}_PL', 0.0),
                item.get(f'{pd}_NORM', 0.0),
                item.get(f'{pd}_SVR', 0.0),
                item.get(f'{pd}_ESTCB', 0.0),
                item.get(f'{pd}_AMOUNT', 0.0),
                item.get(f'{pd}_RATIO', 0.0),
            ))

        count += 1

    conn.commit()
    return count


def log_run(
    conn: sqlite3.Connection,
    mode: str,
    date_processed: str,
    files_found: int,
    items_processed: int,
    periods_processed: int,
    status: str,
    error_message: str = '',
    output_file: str = ''
):
    """Record an execution in the run_log table."""
    conn.execute("""
        INSERT INTO run_log
            (mode, date_processed, files_found, items_processed,
             periods_processed, status, error_message, output_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (mode, date_processed, files_found, items_processed,
          periods_processed, status, error_message, output_file))
    conn.commit()


# ============================================================
# QUERY OPERATIONS (used by query.py and consolidate.py)
# ============================================================

def get_dates_in_db(conn: sqlite3.Connection) -> List[str]:
    """Return all distinct dates stored in the database."""
    rows = conn.execute(
        "SELECT DISTINCT date FROM raw_items ORDER BY date"
    ).fetchall()
    return [r[0] for r in rows]


ITEM_HISTORY_COLUMNS = [
    'date', 'item_code', 'description', 'material_type',
    'mrp_controller', 'unit_price', 'uom',
    'period_date', 'pr', 'po', 'pl', 'norm', 'svr',
    'estcb', 'amount', 'ratio',
]


def get_item_history(
    conn: sqlite3.Connection,
    item_code: str
) -> List[Dict]:
    """
    Get all dates/periods for a specific item.

    Returns list of dicts keyed by ITEM_HISTORY_COLUMNS.
    """
    rows = conn.execute("""
        SELECT
            r.date, r.item_code, r.description, r.material_type,
            r.mrp_controller, r.unit_price, r.uom,
            p.period_date, p.pr, p.po, p.pl, p.norm, p.svr,
            p.estcb, p.amount, p.ratio
        FROM raw_items r
        JOIN period_data p ON p.item_id = r.id
        WHERE r.item_code = ?
        ORDER BY r.date, p.period_date
    """, (item_code,)).fetchall()

    return [dict(zip(ITEM_HISTORY_COLUMNS, row)) for row in rows]


def get_all_data_for_dates(
    conn: sqlite3.Connection,
    dates: List[str]
) -> List[Dict]:
    """
    Get all item data for specified dates (used by consolidate mode).

    Returns flattened rows with period data joined in.
    """
    placeholders = ','.join('?' * len(dates))
    query = f"""
        SELECT
            r.date, r.item_code, r.description, r.material_type AS mat_type,
            r.mrp_controller, r.unit_price, r.uom,
            p.period_date, p.pr, p.po, p.pl, p.norm, p.svr,
            p.estcb, p.amount, p.ratio
        FROM raw_items r
        JOIN period_data p ON p.item_id = r.id
        WHERE r.date IN ({placeholders})
        ORDER BY r.date, r.item_code, p.period_date
    """
    rows = conn.execute(query, dates).fetchall()

    results = []
    for row in rows:
        results.append({
            'Date': row[0],
            'ItemCode': row[1],
            'Desc': row[2],
            'MatType': row[3],
            'MRPController': row[4],
            'UnitPrc': row[5],
            'UoM': row[6],
            'PeriodDate': row[7],
            'PR': row[8],
            'PO': row[9],
            'PL': row[10],
            'NORM': row[11],
            'SVR': row[12],
            'ESTCB': row[13],
            'AMOUNT': row[14],
            'RATIO': row[15],
        })
    return results
