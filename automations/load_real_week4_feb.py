#!/usr/bin/env python3
"""
Load 'Real Week 4 four feb' PNL data into all station tables.

Reads from OneDrive 'Real Week 4 four feb' folder.
Files were printed 01 March 2026 - these are the final February readings.
calculate_week_number() correctly assigns Week 4 to Feb data when
report_date is March (past month end + February = Week 4).
"""
import os
import sys
import django
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automations.settings')
django.setup()

from django.db import connection
from psycopg2.extras import execute_values
from dashboard.onedrive_sync import (
    list_files_in_folder, download_file,
    process_ppg_excel_file, process_dor_excel_file,
    process_con_excel_file, process_atl_excel_file,
    process_hnl_excel_file, process_jfk_excel_file,
    process_ccc_excel_file, process_ccd_excel_file,
    process_fax_excel_file, process_imp_excel_file,
    process_hou_excel_file, process_ics_excel_file,
    process_lax_excel_file, process_lcl_excel_file,
    process_ord_excel_file,
)

REAL_WEEK4_FOLDER = '/Automation Platform/Real Week 4 four feb'

# Map filename prefix → (table_name, process_func, division_override)
# division_override: if set, replaces division column in all rows
# (needed for DOR and CON which process_* returns 'PPG' as division)
STATION_MAP = {
    'ATL': ('atl_pnl', process_atl_excel_file, None),    # already returns 'IMP' division
    'CCC': ('ccc_pnl', process_ccc_excel_file, None),    # already returns 'CCC'
    'CCD': ('ccd_pnl', process_ccd_excel_file, None),    # already returns 'CCD'
    'CON': ('con_pnl', process_con_excel_file, 'CON'),   # returns 'PPG', override to 'CON'
    'DOR': ('dor_pnl', process_dor_excel_file, 'DOR'),   # returns 'PPG', override to 'DOR'
    'FAX': ('fax_pnl', process_fax_excel_file, None),    # already returns 'FAX'
    'HNL': ('hnl_pnl', process_hnl_excel_file, None),    # already returns 'HNL'
    'HOU': ('hou_pnl', process_hou_excel_file, None),    # already returns 'HOU'
    'ICS': ('ics_pnl', process_ics_excel_file, None),    # already returns 'ICS'
    'IMP': ('imp_pnl', process_imp_excel_file, None),    # already returns 'IMP'
    'JFK': ('jfk_pnl', process_jfk_excel_file, None),    # already returns 'JFK'
    'LAX': ('lax_pnl', process_lax_excel_file, None),    # already returns 'LAX'
    'LCL': ('lcl_pnl', process_lcl_excel_file, None),    # already returns 'LCL'
    'ORD': ('ord_pnl', process_ord_excel_file, None),    # already returns 'ORD'
    'PPG': ('ppg_pnl', process_ppg_excel_file, None),    # already returns 'PPG'
}


def insert_station_data(table_name, all_rows, is_dor=False):
    """Delete old Week data for affected (month, week) combos, then insert new rows + Total copies."""
    if not all_rows:
        print(f"  No rows to insert for {table_name}")
        return 0

    if is_dor:
        # Deduplicate DOR rows (3 sub-files may have overlapping account rows)
        deduped = {}
        for row in all_rows:
            key = (row[0], row[1], row[3], row[5], row[6])  # div, acct, date, budget_actual, week
            deduped[key] = row
        all_rows = list(deduped.values())
        print(f"  After dedup: {len(all_rows)} rows")

    with connection.cursor() as cur:
        unique_month_weeks = set((row[3], row[6]) for row in all_rows)
        unique_months = set(row[3] for row in all_rows)

        # Show current state
        print(f"  Current weeks in {table_name} for affected months:")
        for month in sorted(unique_months):
            cur.execute(
                f"SELECT week, COUNT(*) FROM {table_name} WHERE date = %s AND budget_actual = 'Actual' GROUP BY week ORDER BY week",
                (month,)
            )
            weeks = cur.fetchall()
            if weeks:
                print(f"    {month}: " + ", ".join(f"{w}({c})" for w, c in weeks))
            else:
                print(f"    {month}: (no data)")

        # Delete old Actual week records for the affected (month, week) combos
        for month, week in unique_month_weeks:
            cur.execute(
                f"DELETE FROM {table_name} WHERE date = %s AND week = %s AND budget_actual = 'Actual'",
                (month, week)
            )

        # Delete old Actual Total records for the affected months
        for month in unique_months:
            cur.execute(
                f"DELETE FROM {table_name} WHERE date = %s AND week = 'Total' AND budget_actual = 'Actual'",
                (month,)
            )

        print(f"  Deleted old data for {sorted(unique_month_weeks)}")

        # Insert new week rows
        week_query = f"""
            INSERT INTO {table_name} (division, account_name, value, date, date_fixed, budget_actual, week, report_date)
            VALUES %s
        """
        execute_values(cur, week_query, all_rows)
        print(f"  Inserted {len(all_rows)} week rows")

        # Insert Total copies (per month)
        rows_by_month = defaultdict(list)
        for row in all_rows:
            rows_by_month[row[3]].append(row)

        total_count = 0
        for month, month_rows in rows_by_month.items():
            total_rows = [(row[0], row[1], row[2], row[3], row[4], row[5], 'Total', row[7]) for row in month_rows]
            execute_values(cur, week_query, total_rows)
            total_count += len(total_rows)

        print(f"  Inserted {total_count} Total rows")

        # Show new state
        print(f"  New weeks in {table_name}:")
        for month in sorted(unique_months):
            cur.execute(
                f"SELECT week, COUNT(*) FROM {table_name} WHERE date = %s AND budget_actual = 'Actual' GROUP BY week ORDER BY week",
                (month,)
            )
            weeks = cur.fetchall()
            if weeks:
                print(f"    {month}: " + ", ".join(f"{w}({c})" for w, c in weeks))

    return len(all_rows)


def main():
    print("=" * 70)
    print("  LOADING REAL WEEK 4 FEBRUARY PNL DATA")
    print(f"  Folder: {REAL_WEEK4_FOLDER}")
    print("=" * 70)

    # List files
    files = list_files_in_folder(REAL_WEEK4_FOLDER)
    excel_files = [f for f in files if f['name'].lower().endswith(('.xlsx', '.xls'))]

    print(f"\nFound {len(excel_files)} Excel files:")
    for f in excel_files:
        print(f"  {f['name']}")

    if not excel_files:
        print("\nNo files found. Check the folder path and OneDrive token.")
        return

    # Group files by station prefix
    station_files = defaultdict(list)
    unmatched = []
    for f in excel_files:
        name_upper = f['name'].upper()
        matched = False
        for prefix in STATION_MAP:
            if name_upper.startswith(prefix):
                station_files[prefix].append(f)
                matched = True
                break
        if not matched:
            unmatched.append(f['name'])

    if unmatched:
        print(f"\nWARNING: Unmatched files (skipped): {unmatched}")

    print(f"\nStations to process: {sorted(station_files.keys())}")

    # Collect all rows per station
    station_rows = defaultdict(list)

    for prefix, file_list in sorted(station_files.items()):
        table_name, process_func, division_override = STATION_MAP[prefix]
        print(f"\n{'='*60}")
        print(f"  {prefix} -> {table_name} ({len(file_list)} file(s))")
        print(f"{'='*60}")

        for file_info in file_list:
            print(f"\nDownloading: {file_info['name']}")
            content = download_file(file_info['id'])
            if not content:
                print(f"  ERROR: Could not download {file_info['name']}")
                continue

            rows = process_func(content, file_info['name'])

            if division_override:
                rows = [(division_override,) + row[1:] for row in rows]

            print(f"  Extracted {len(rows)} rows")
            if rows:
                # Show which months/weeks were detected
                months_weeks = set((r[3], r[6]) for r in rows)
                for m, w in sorted(months_weeks):
                    count = sum(1 for r in rows if r[3] == m and r[6] == w)
                    print(f"    {m} {w}: {count} rows")

            station_rows[prefix].extend(rows)

    # Insert all stations
    print(f"\n{'='*70}")
    print("  INSERTING INTO DATABASE")
    print(f"{'='*70}")

    results = {}
    for prefix in sorted(station_rows.keys()):
        table_name, _, _ = STATION_MAP[prefix]
        rows = station_rows[prefix]
        print(f"\n--- {prefix} ({table_name}): {len(rows)} rows ---")
        is_dor = (prefix == 'DOR')
        n = insert_station_data(table_name, rows, is_dor=is_dor)
        results[prefix] = n

    # Summary
    print(f"\n{'='*70}")
    print("  SUMMARY")
    print(f"{'='*70}")
    total = 0
    for prefix in sorted(results.keys()):
        table_name, _, _ = STATION_MAP[prefix]
        n = results[prefix]
        print(f"  {prefix:4s} ({table_name:10s}): {n} rows")
        total += n
    print(f"\n  TOTAL: {total} rows inserted")

    missing = [p for p in STATION_MAP if p not in results]
    if missing:
        print(f"\n  WARNING: No data loaded for: {missing}")

    print("=" * 70)
    print("  DONE - Real Week 4 February data loaded")
    print("=" * 70)


if __name__ == '__main__':
    main()
