#!/usr/bin/env python3
"""
insight-detector: scans recent Claude Code friction signals and writes
suggestions[] into stats.json for Hannah to review on the dashboard.

STUB: Currently writes an empty suggestions array. Real pattern-mining logic
to come in v2. The scheduled-task wrapper can call this after aggregator.py
so stats.json ends up with both sections populated.
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", required=True, help="Path to stats.json produced by aggregator.py")
    args = ap.parse_args()

    path = Path(args.stats)
    data = json.loads(path.read_text())
    data["suggestions"] = []  # TODO v2: actual pattern detection
    path.write_text(json.dumps(data, indent=2))
    print(f"Updated {path} with {len(data['suggestions'])} suggestions")


if __name__ == "__main__":
    main()
