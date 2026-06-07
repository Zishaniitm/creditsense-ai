"""
etl_runner.py
Master ETL orchestrator for CreditSense AI.
Runs the full pipeline: Clean → Encode → Engineer → Load
Usage: python pipeline/scripts/etl_runner.py
"""
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
import subprocess
import os
from datetime import datetime

SCRIPTS = [
    ("Data Cleaner",           "pipeline/scripts/cleaner.py"),
    ("Encoder",                "pipeline/scripts/encoder.py"),
    ("Feature Engineer",       "pipeline/scripts/feature_engineer.py"),
    ("Database Loader",        "pipeline/scripts/loader.py"),
]


def run_script(name, path):
    print(f"\n{'─'*60}")
    print(f"  ▶ Running: {name}")
    print(f"{'─'*60}")
    start = datetime.now()

    result = subprocess.run(
        [sys.executable, path],
        capture_output=False,
        text=True
    )

    elapsed = (datetime.now() - start).seconds
    if result.returncode == 0:
        print(f"\n  ✅ {name} completed in {elapsed}s")
        return True
    else:
        print(f"\n  ❌ {name} FAILED (exit code {result.returncode})")
        return False


def main():
    print("=" * 60)
    print("  CreditSense AI — ETL Pipeline Runner")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}
    for name, path in SCRIPTS:
        success = run_script(name, path)
        results[name] = success
        if not success:
            print(f"\n  ⛔ Pipeline stopped at: {name}")
            print("  Fix the error above and re-run.")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("  ETL PIPELINE COMPLETE")
    print("=" * 60)
    for name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status}  {name}")
    print(f"\n  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()