"""
Verify Phase 1 output: checks all expected files exist and reports record counts.
"""
import os, json, sys, glob
sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

checks = [
    ('data/raw/weather/nasa_power_monthly_raw/', 'dir_json', 20),
    ('data/raw/crop_production/faostat_india_raw.json', 'json_file', None),
    ('data/raw/crop_production/faostat_provenance.json', 'json_file', None),
    ('data/raw/market/agmarknet_provenance.json', 'json_file', None),
    ('data/raw/market/real_des_historical/Time-Series-3rd-AE-2025-26-English.pdf', 'file', None),
    ('data/raw/market/raw_agmarknet_historical.json', 'json_file', None),
    ('data/catalog/dataset_catalog.csv', 'csv_file', None),
    ('data/catalog/data_quality_report.md', 'file', None),
    ('data/processed/master_district_profiles.csv', 'file', None),
    ('data/processed/historical_market/historical_mandi_prices.json', 'file', None),
    ('data/processed/crop_economics.json', 'file', None),
    ('data/README.md', 'file', None),
]

print('='*65)
print('PHASE 1 OUTPUT VERIFICATION')
print('='*65)

all_ok = True
for rel_path, kind, expected_count in checks:
    full = os.path.join(ROOT, rel_path)
    if kind == 'dir_json':
        files = glob.glob(os.path.join(full, '*.json'))
        count = len(files)
        ok = count >= (expected_count or 0)
        status = 'OK' if ok else 'FAIL'
        size = sum(os.path.getsize(f) for f in files) // 1024
        print(f'  [{status}] {rel_path}  ({count} files, {size} KB)')
    elif kind == 'csv_file':
        import pandas as pd
        ok = os.path.exists(full)
        if ok:
            df = pd.read_csv(full)
            print(f'  [OK ] {rel_path}  ({len(df)} rows, {os.path.getsize(full)//1024} KB)')
        else:
            print(f'  [FAIL] {rel_path}  NOT FOUND')
    elif kind == 'json_file':
        ok = os.path.exists(full)
        if ok:
            with open(full) as f:
                d = json.load(f)
            size = os.path.getsize(full) // 1024
            if isinstance(d, list):
                print(f'  [OK ] {rel_path}  ({len(d):,} records, {size} KB)')
            elif isinstance(d, dict):
                print(f'  [OK ] {rel_path}  (dict, keys={list(d.keys())[:4]}, {size} KB)')
        else:
            ok = False
            print(f'  [FAIL] {rel_path}  NOT FOUND')
    else:
        ok = os.path.exists(full)
        if ok:
            print(f'  [OK ] {rel_path}  ({os.path.getsize(full)//1024} KB)')
        else:
            print(f'  [FAIL] {rel_path}  NOT FOUND')
    all_ok = all_ok and ok

print()
print(f'Overall: {"ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED"}')
print('='*65)
