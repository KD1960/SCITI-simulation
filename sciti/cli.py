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
    es = sub.add_parser("estimate", help="estimated LLM calls and spend; makes no calls")
    es.add_argument("config")
    bt = sub.add_parser("batch", help="run many seeds and write results.csv")
    bt.add_argument("config")
    bt.add_argument("--seeds", required=True)
    bt.add_argument("--with-baseline", action="store_true")
    bt.add_argument("--confirm-spend", action="store_true")
    bt.add_argument("--out", default=None)
    vw = sub.add_parser("view", help="serve the replay web view for a run on 127.0.0.1")
    vw.add_argument("run_dir")
    vw.add_argument("--baseline", default=None)
    vw.add_argument("--port", type=int, default=8765)
    vw.add_argument("--no-open", action="store_true")
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
        from sciti.runner import commit_note, replay_run
        src = Path(args.run_dir)
        out = Path(args.out) if args.out else src.with_name(src.name + "_replay")
        diffs = replay_run(src, out)
        if diffs:
            print("replication: MISMATCH in " + ", ".join(diffs) + commit_note(src))
            return 1
        print(f"replication: exact ({out})")
        return 0
    if args.cmd == "estimate":
        import json as _json
        from sciti.batch import estimate
        from sciti.config import load_config
        print(_json.dumps(estimate(load_config(args.config)), indent=1))
        return 0
    if args.cmd == "batch":
        import csv
        from sciti.batch import SpendConfirmationRequired, parse_seeds, run_batch
        from sciti.config import load_config
        cfg = load_config(args.config)
        out = Path(args.out) if args.out else Path(cfg.output_dir) / f"batch_{cfg.name}"
        try:
            results_path = run_batch(cfg, parse_seeds(args.seeds), out, args.with_baseline, args.confirm_spend) / "results.csv"
            print(results_path)
            ok_count = 0
            failed_count = 0
            with open(results_path) as f:
                for row in csv.DictReader(f):
                    if row.get("status") == "ok":
                        ok_count += 1
                    elif row.get("status") == "failed":
                        failed_count += 1
            if failed_count > 0:
                print(f"{ok_count} ok, {failed_count} failed")
                return 1
            return 0
        except SpendConfirmationRequired as e:
            print(e)
            return 2
    if args.cmd == "view":
        import webbrowser
        from sciti.viewserver import make_server
        srv = make_server(Path(args.run_dir), Path(args.baseline) if args.baseline else None, args.port)
        url = f"http://127.0.0.1:{srv.server_address[1]}/"
        print(f"serving {args.run_dir} at {url} (Ctrl+C to stop)")
        if not args.no_open:
            webbrowser.open(url)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
