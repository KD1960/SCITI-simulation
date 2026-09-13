"""`sciti` command line (spec §4.1)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_XLSX = Path.home() / "Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sciti")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare", help="read the workbook once into data/baseline.json")
    p.add_argument("--xlsx", default=str(DEFAULT_XLSX))
    p.add_argument("--out", default="data")
    r = sub.add_parser("run", help="run one simulation")
    r.add_argument("config")
    r.add_argument("--run-dir", default=None)
    rp = sub.add_parser("replay", help="re-run from logged decisions and compare outputs")
    rp.add_argument("run_dir")
    rp.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    if args.cmd == "prepare":
        from sciti.data.loader import prepare
        prepare(Path(args.xlsx), Path(args.out))
        print(f"wrote {args.out}/baseline.json and {args.out}/validation_report.md")
        return 0
    if args.cmd == "run":
        from sciti.config import load_config
        from sciti.runner import run
        out = run(load_config(args.config), run_dir=Path(args.run_dir) if args.run_dir else None)
        print(out)
        return 0
    if args.cmd == "replay":
        from sciti.runner import replay_run
        src = Path(args.run_dir)
        out = Path(args.out) if args.out else src.with_name(src.name + "_replay")
        diffs = replay_run(src, out)
        if diffs:
            print("replication: MISMATCH in " + ", ".join(diffs))
            return 1
        print(f"replication: exact ({out})")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
