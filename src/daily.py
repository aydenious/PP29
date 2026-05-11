#!/usr/bin/env python3
"""
daily.py — Daily Purchase Plan Generator (replaces MS Access)

Reads the 13 SAP text files from the network drive, aggregates vendor-level
data into item-level rows, generates the daily Excel output, and stores
everything in the SQLite historical database.

=== NETWORK / FILE PATH CONFIGURATION ===
All paths are read from config.json. Edit config.json to set:

  sap_input_path          — Where SAP auto-downloads the 13 .txt files
                            Example: "N:\\SAP_Downloads\\PP29_Readdone"

  daily_output_path       — Where to save the generated daily Excel
                            Example: ".\\output\\daily"

  db_path                 — SQLite database for historical storage
                            Example: ".\\data\\pp29_history.db"

  log_path                — Where execution logs are written
                            Example: ".\\logs"

=== USAGE ===
  python daily.py                          # Process today's date
  python daily.py --date 20260210          # Process a specific date
  python daily.py --date 20260210 --no-db  # Skip database insert
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta

# Add parent to path so we can import sibling modules when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from text_reader import read_daily_files
from excel_writer import write_daily_excel
from db import init_database, insert_daily_data, log_run
from config import load_config


# ============================================================
# MAIN DAILY PROCESS
# ============================================================

def run_daily(
    config: dict,
    date_str: str,
    use_db: bool = True
) -> bool:
    """
    Execute the daily purchase plan generation.

    Steps:
      1. Read 13 SAP text files for the given date
      2. Aggregate vendor rows → item-level rows
      3. Write daily Excel (.xlsx)
      4. Insert into SQLite database (if enabled)
      5. Log execution

    Returns True on success.
    """
    # ═══════════════════════════════════════════════════════
    # PATH CONFIGURATION — Edit in config.json, not here
    # ═══════════════════════════════════════════════════════
    sap_folder = config['sap_input_path']
    output_dir = config['daily_output_path']
    db_path = config.get('db_path', '.\\data\\pp29_history.db')
    log_dir = config.get('log_path', '.\\logs')
    entities = config.get('entities', [
        "CUS2100ROH", "CUS2100SFPB1", "CUS2100SFPB2", "CUS2100SFPB3",
        "CUS2100SFPB4", "CUS2100SFPB5A", "CUS2100SFPB5B", "CUS2100SFPB6",
        "CUS2100SFPB7", "CUS2100SFPB8", "CUS2100SFPR", "CUS2100SFUB",
        "CUS2100SUB"
    ])
    # ═══════════════════════════════════════════════════════

    # Setup logging
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"daily_{date_str}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)

    logger.info(f"=== PP29 Daily Generator ===")
    logger.info(f"Date: {date_str}")
    logger.info(f"SAP folder: {sap_folder}")
    logger.info(f"Output folder: {output_dir}")

    # Step 1: Read text files
    logger.info("Step 1/4: Reading SAP text files...")
    try:
        items, period_dates = read_daily_files(sap_folder, date_str, entities)
    except Exception as e:
        logger.error(f"Failed to read text files: {e}")
        if use_db:
            conn = init_database(db_path)
            log_run(conn, 'daily', date_str, 0, 0, 0, 'FAILED', str(e))
            conn.close()
        return False

    if not items:
        logger.error(f"No data found for date {date_str}")
        return False

    logger.info(f"  Aggregated {len(items)} items across {len(period_dates)} periods")

    # Step 2: Write daily Excel
    logger.info("Step 2/4: Generating daily Excel...")
    try:
        output_file = write_daily_excel(items, period_dates, output_dir, date_str)
        logger.info(f"  Saved: {output_file}")
    except Exception as e:
        logger.error(f"Failed to write Excel: {e}")
        if use_db:
            conn = init_database(db_path)
            log_run(conn, 'daily', date_str, 13, len(items),
                    len(period_dates), 'FAILED', str(e))
            conn.close()
        return False

    # Step 3: Insert into database
    if use_db:
        logger.info("Step 3/4: Inserting into database...")
        try:
            conn = init_database(db_path)
            inserted = insert_daily_data(conn, date_str, items, period_dates)
            log_run(conn, 'daily', date_str, 13, inserted,
                    len(period_dates), 'SUCCESS', '', output_file)
            conn.close()
            logger.info(f"  {inserted} items stored in database")
        except Exception as e:
            logger.error(f"Database error (non-fatal): {e}")

    # Step 4: Done
    logger.info("Step 4/4: Complete!")
    logger.info(f"Output: {output_file}")
    return True


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='PP29 Daily Purchase Plan Generator'
    )
    parser.add_argument(
        '--date', '-d',
        help='Date to process (YYYYMMDD). Default: today',
        default=None
    )
    parser.add_argument(
        '--config', '-c',
        help='Path to config.json',
        default=None
    )
    parser.add_argument(
        '--no-db',
        help='Skip database insertion',
        action='store_true'
    )

    args = parser.parse_args()

    # Determine date
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime('%Y%m%d')

    # Load config
    config = load_config(args.config)

    # Run
    success = run_daily(config, date_str, use_db=not args.no_db)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
