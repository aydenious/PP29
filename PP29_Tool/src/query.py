#!/usr/bin/env python3
"""
query.py — Ad-hoc queries against the PP29 historical database

Look up individual items, compare dates, find changes.

=== DATABASE PATH ===
  Configured via config.json → db_path
  Default: ".\\data\\pp29_history.db"

=== USAGE ===
  python query.py --item 30001144                          # Item history
  python query.py --item 30001144 --dates 20260201,20260210 # Compare 2 dates
  python query.py --top-changes --limit 20                  # Top movers
  python query.py --dates-summary                           # All dates summary
"""

import os
import sys
import json
import argparse
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_database, get_item_history, get_dates_in_db, get_all_data_for_dates


def load_config(config_path: str = None) -> dict:
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    search = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json'),
        os.path.join(os.getcwd(), 'config.json'),
    ]
    for p in search:
        if os.path.exists(p):
            with open(p, 'r') as f:
                return json.load(f)
    print("ERROR: config.json not found.")
    sys.exit(1)


def show_item_history(conn, item_code: str):
    """Display all dates/periods for a specific item."""
    rows = get_item_history(conn, item_code)
    if not rows:
        print(f"No data found for item: {item_code}")
        return

    print(f"\n{'='*80}")
    print(f"Item: {item_code}")
    print(f"Description: {rows[0][2]}")
    print(f"Type: {rows[0][3]} | MRP: {rows[0][4]} | Price: {rows[0][5]} | UoM: {rows[0][6]}")
    print(f"{'='*80}")

    dates = sorted(set(r[0] for r in rows))
    print(f"\nDates available: {', '.join(dates)}")
    print(f"\n{'Date':<12} {'Period':<10} {'PR':>10} {'PO':>10} {'NORM':>10} {'ESTCB':>10} {'AMOUNT':>12}")
    print("-" * 75)

    for r in rows:
        print(f"{r[0]:<12} {r[7]:<10} {r[8]:>10.0f} {r[9]:>10.0f} "
              f"{r[11]:>10.0f} {r[12]:>10.0f} {r[13]:>12.2f}")


def compare_items(conn, item_code: str, dates: List[str]):
    """Compare an item's values between two dates."""
    if len(dates) != 2:
        print("Need exactly 2 dates to compare. Use: --dates D1,D2")
        return

    all_rows = get_item_history(conn, item_code)
    rows_d1 = [r for r in all_rows if r[0] == dates[0]]
    rows_d2 = [r for r in all_rows if r[0] == dates[1]]

    print(f"\n{'='*80}")
    print(f"Item: {item_code} — {rows_d1[0][2] if rows_d1 else 'N/A'}")
    print(f"Comparing: {dates[0]} → {dates[1]}")
    print(f"{'='*80}")

    # Build lookup by period
    d1_by_period = {r[7]: r for r in rows_d1}
    d2_by_period = {r[7]: r for r in rows_d2}

    all_periods = sorted(set(list(d1_by_period.keys()) + list(d2_by_period.keys())))

    print(f"{'Period':<10} {'D1_PO':>10} {'D2_PO':>10} {'Delta':>10} "
          f"{'D1_ESTCB':>12} {'D2_ESTCB':>12} {'DeltaCB':>12}")
    print("-" * 80)

    for pd in all_periods:
        d1 = d1_by_period.get(pd, [0]*14)
        d2 = d2_by_period.get(pd, [0]*14)
        delta_po = (d2[9] or 0) - (d1[9] or 0)
        delta_cb = (d2[12] or 0) - (d1[12] or 0)
        marker = ' ◄' if abs(delta_po) > 0.01 or abs(delta_cb) > 0.01 else ''
        print(f"{pd:<10} {(d1[9] or 0):>10.0f} {(d2[9] or 0):>10.0f} "
              f"{delta_po:>+10.0f} {(d1[12] or 0):>12.0f} {(d2[12] or 0):>12.0f} "
              f"{delta_cb:>+12.0f}{marker}")


def show_top_changes(conn, limit: int = 20):
    """Show items with the biggest changes between first and last date."""
    dates = get_dates_in_db(conn)
    if len(dates) < 2:
        print("Need at least 2 dates in database to compare.")
        return

    first, last = dates[0], dates[-1]

    query = """
        SELECT
            r.item_code, r.description, r.material_type,
            SUM(CASE WHEN r.date = ? THEN p.amount ELSE 0 END) as first_amt,
            SUM(CASE WHEN r.date = ? THEN p.amount ELSE 0 END) as last_amt
        FROM raw_items r
        JOIN period_data p ON p.item_id = r.id
        WHERE r.date IN (?, ?) AND p.period_date = (
            SELECT MIN(period_date) FROM period_data WHERE item_id = r.id
        )
        GROUP BY r.item_code
        HAVING ABS(last_amt - first_amt) > 0.01
        ORDER BY ABS(last_amt - first_amt) DESC
        LIMIT ?
    """
    rows = conn.execute(query, (first, last, first, last, limit)).fetchall()

    print(f"\nTop {limit} Changes: {first} → {last}")
    print(f"{'Item':<16} {'Desc':<40} {'FirstAmt':>12} {'LastAmt':>12} {'Change':>12}")
    print("-" * 95)

    for r in rows:
        delta = (r[4] or 0) - (r[3] or 0)
        print(f"{r[0]:<16} {str(r[1])[:39]:<40} "
              f"{r[3] or 0:>12.2f} {r[4] or 0:>12.2f} {delta:>+12.2f}")


def show_dates_summary(conn):
    """Show summary of all dates in the database."""
    dates = get_dates_in_db(conn)

    print(f"\n{'='*80}")
    print(f"Dates in Database ({len(dates)} total)")
    print(f"{'='*80}")
    print(f"{'Date':<12} {'Items':>8} {'Total PR':>12} {'Total PO':>12} "
          f"{'Total ESTCB':>14} {'Total Amount':>14}")
    print("-" * 75)

    for d in dates:
        row = conn.execute("""
            SELECT
                COUNT(DISTINCT item_code),
                SUM(pr), SUM(po), SUM(estcb), SUM(amount)
            FROM raw_items r
            JOIN period_data p ON p.item_id = r.id
            WHERE r.date = ?
        """, (d,)).fetchone()

        print(f"{d:<12} {row[0]:>8} {row[1] or 0:>12.0f} {row[2] or 0:>12.0f} "
              f"{row[3] or 0:>14.0f} {row[4] or 0:>14.2f}")


def main():
    parser = argparse.ArgumentParser(description='PP29 Query Tool')
    parser.add_argument('--item', '-i', help='Item code to look up')
    parser.add_argument('--dates', '-d', help='Comma-separated dates for comparison')
    parser.add_argument('--top-changes', action='store_true',
                        help='Show items with biggest changes')
    parser.add_argument('--limit', type=int, default=20,
                        help='Limit for top changes')
    parser.add_argument('--dates-summary', action='store_true',
                        help='Show summary of all dates in database')
    parser.add_argument('--config', '-c', help='Path to config.json')

    args = parser.parse_args()

    config = load_config(args.config)
    # DATABASE PATH — from config.json → db_path
    db_path = config.get('db_path', '.\\data\\pp29_history.db')
    conn = init_database(db_path)

    if args.item and args.dates:
        compare_items(conn, args.item, [d.strip() for d in args.dates.split(',')])
    elif args.item:
        show_item_history(conn, args.item)
    elif args.top_changes:
        show_top_changes(conn, args.limit)
    elif args.dates_summary:
        show_dates_summary(conn)
    else:
        parser.print_help()

    conn.close()


if __name__ == '__main__':
    main()
