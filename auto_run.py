#!/usr/bin/env python3
"""
auto_run.py (updated)
- supports auto-generation of footprints from LAS if footprints.csv missing
- main accepts argv for testability
"""
import argparse
import subprocess
import sys
from pathlib import Path
import csv
import datetime
import os

PY = sys.executable

def log(msg):
    ts = datetime.datetime.now().isoformat()
    print(f"[{ts}] {msg}")

def safe_run(cmd, check=True):
    log(" ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)} ; returncode={res.returncode}")
    return res

def find_first_las(als_dir):
    p = Path(als_dir)
    if not p.exists():
        raise FileNotFoundError(f"No ALS folder: {als_dir}")
    for ext in ("*.laz", "*.las"):
        for f in sorted(p.glob(ext)):
            return f
    raise FileNotFoundError(f"No LAS/LAZ files in {als_dir}")

def find_h5_files(gedi_dir):
    p = Path(gedi_dir)
    if not p.exists():
        return []
    return sorted([str(x) for x in p.glob("*.h5")])

def validate_footprints(fp_path):
    if not fp_path.exists():
        raise FileNotFoundError(f"Footprints file not found: {fp_path}")
    with fp_path.open(newline='') as f:
        rdr = csv.DictReader(f)
        hdr = rdr.fieldnames or []
        if "x" not in hdr or "y" not in hdr:
            raise ValueError("footprints.csv must contain headers 'x' and 'y' (and optionally footprint_id, radius).")

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--inputs", default="inputs", help="inputs folder (default: inputs)")
    p.add_argument("--als_sub", default="als", help="subfolder under inputs for las/laz files")
    p.add_argument("--gedi_sub", default="gedi", help="subfolder under inputs for GEDI h5 files")
    p.add_argument("--footprints", default="footprints.csv", help="footprints csv name in inputs folder")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--out_root", default="results", help="output root")
    p.add_argument("--radius", type=float, default=15.0)
    p.add_argument("--dz", type=float, default=0.5)
    p.add_argument("--dz_wf", type=float, default=0.15)
    p.add_argument("--sigma_fp", type=float, default=5.5)
    p.add_argument("--k", type=float, default=0.028)
    p.add_argument("--pulse_sigma", type=float, default=0.6)
    p.add_argument("--snr", type=float, default=30.0)
    p.add_argument("--generate_spacing", type=float, default=30.0, help="if footprints missing: spacing (m) for generator")
    p.add_argument("--generate_min_count", type=int, default=5, help="if footprints missing: min ALS points to accept center")
    args = p.parse_args(argv)

    inputs = Path(args.inputs)
    footprints = inputs / args.footprints
    als_dir = inputs / args.als_sub
    gedi_dir = inputs / args.gedi_sub
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    # check LAS presence
    las_file = find_first_las(als_dir)
    log(f"Using LAS file: {las_file}")

    # if footprints missing, generate automatically from LAS
    if not footprints.exists():
        log(f"Footprints file {footprints} not found — generating from LAS")
        # call generator script
        gen_cmd = [PY, "scripts/generate_footprints_from_las.py",
                   "--las", str(las_file),
                   "--out", str(footprints),
                   "--spacing", str(args.generate_spacing),
                   "--radius", str(args.radius),
                   "--min_count", str(args.generate_min_count)]
        safe_run(gen_cmd, check=True)
        log(f"Generated footprints at {footprints}")

    # validate footprints
    validate_footprints(footprints)

    # check GEDI HDF5 files and optionally convert to CSV
    h5s = find_h5_files(gedi_dir)
    gedi_csv = inputs / "gedi_table.csv"
    if h5s:
        log(f"Found {len(h5s)} GEDI h5 files. Converting to CSV (merged) -> {gedi_csv}")
        tmp_csvs = []
        for i, h5 in enumerate(h5s):
            tmp = inputs / f"gedi_tmp_{i}.csv"
            try:
                # run reader; it may be mocked in tests (no actual tmp file created)
                safe_run([PY, "scripts/read_gedi_h5.py", "--h5", str(h5), "--out", str(tmp)], check=True)
                # only append tmp if file actually exists
                if tmp.exists():
                    tmp_csvs.append(tmp)
                else:
                    log(f"Warning: reader returned success but {tmp} not created; skipping")
            except Exception as e:
                log(f"Warning: failed reading {h5}: {e} — skipping this file")
        if tmp_csvs:
            with gedi_csv.open("w", newline='') as out_f:
                writer = None
                for t in tmp_csvs:
                    import csv as _csv
                    with t.open(newline='') as inf:
                        rdr = _csv.DictReader(inf)
                        if writer is None:
                            writer = _csv.DictWriter(out_f, fieldnames=rdr.fieldnames)
                            writer.writeheader()
                        for row in rdr:
                            writer.writerow(row)
            for t in tmp_csvs:
                try: t.unlink()
                except Exception: pass
            log(f"Wrote merged GEDI CSV: {gedi_csv}")
        else:
            log("No successful GEDI CSVs produced; continuing without GEDI comparison.")
            gedi_csv = None
    else:
        log("No GEDI h5 files found; will run pipeline without GEDI comparison.")
        gedi_csv = None

    # call pipeline_batch.py
    cmd = [
        PY, "pipeline_batch.py",
        "--footprints", str(footprints),
        "--las", str(las_file),
        "--out_root", str(out_root),
        "--workers", str(args.workers),
        "--radius", str(args.radius),
        "--dz", str(args.dz),
        "--dz_wf", str(args.dz_wf),
        "--sigma_fp", str(args.sigma_fp),
        "--k", str(args.k),
        "--pulse_sigma", str(args.pulse_sigma),
        "--snr", str(args.snr)
    ]
    try:
        safe_run(cmd, check=True)
    except Exception as e:
        log(f"ERROR running pipeline_batch: {e}")
        raise

    # attempt merge if GEDI table and summary exist
    summary = out_root / "summary_metrics.csv"
    if gedi_csv and summary.exists():
        log("Merging summary_metrics.csv with gedi_table.csv by footprint_id if possible.")
        try:
            import pandas as pd
            s = pd.read_csv(summary)
            g = pd.read_csv(gedi_csv)
            if "footprint_id" in g.columns:
                merged = pd.merge(s, g, on="footprint_id", how="inner")
                merged.to_csv(out_root / "merged_summary.csv", index=False)
                log("Wrote merged_summary.csv")
            else:
                log("GEDI table has no footprint_id — cannot auto-merge.")
        except Exception as e:
            log(f"Warning: failed merging summary and GEDI CSV: {e}")

    log("Auto-run finished successfully.")

if __name__ == "__main__":
    main()
