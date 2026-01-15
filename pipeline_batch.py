#!/usr/bin/env python3
"""
pipeline_batch.py
Batch-run ALS->profile->wf->rh for many footprints listed in a CSV.
CSV format expected: footprint_id,x,y,radius(optional)
Produces per-footprint outputs under 'results/<footprint_id>/' and a merged summary CSV.
Usage:
    python pipeline_batch.py --footprints data/footprints.csv --las path/to/area.laz --workers 4
"""
import argparse
import csv
import os
from pathlib import Path
import subprocess
import sys
from multiprocessing import Pool
import shutil

PY = sys.executable

def run_cmd(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def process_one(args):
    row, las_path, out_root, params = args
    fid = row.get("footprint_id") or row.get("id") or str(row.get("x"))+"_"+str(row.get("y"))
    x = float(row["x"])
    y = float(row["y"])
    r = float(row.get("radius", params["radius"]))
    outdir = out_root / str(fid)
    outdir.mkdir(parents=True, exist_ok=True)
    try:
        # 1. extract window
        csv_fp = outdir / "points.csv"
        cmd1 = [PY, "scripts/01_preprocess_als.py", "--las", str(las_path), "--x", str(x), "--y", str(y), "--r", str(r), "--out", str(csv_fp)]
        r1 = run_cmd(cmd1)
        if r1.returncode != 0:
            return (fid, False, f"extract error: {r1.stderr}")
        # 2. build profile
        prof_npz = outdir / "profile.npz"
        cmd2 = [PY, "scripts/02_build_profile.py", "--in_csv", str(csv_fp), "--dz", str(params["dz"]), "--sigma_fp", str(params["sigma_fp"]), "--out_npz", str(prof_npz)]
        r2 = run_cmd(cmd2)
        if r2.returncode != 0:
            return (fid, False, f"profile error: {r2.stderr}")
        # 3. simulate wf
        wf_npz = outdir / "wf.npz"
        cmd3 = [PY, "scripts/03_simulate_wf.py", "--profile_npz", str(prof_npz), "--k", str(params["k"]), "--pulse_sigma", str(params["pulse_sigma"]), "--dz", str(params["dz_wf"]), "--snr", str(params["snr"]), "--out_npz", str(wf_npz)]
        r3 = run_cmd(cmd3)
        if r3.returncode != 0:
            return (fid, False, f"wf error: {r3.stderr}")
        # 4. compute rh
        metrics_csv = outdir / "metrics.csv"
        cmd4 = [PY, "scripts/04_compute_rh.py", "--profile_npz", str(wf_npz), "--from_wf", "--out_csv", str(metrics_csv)]
        r4 = run_cmd(cmd4)
        if r4.returncode != 0:
            return (fid, False, f"metrics error: {r4.stderr}")
        # Success: return path to metrics
        return (fid, True, str(metrics_csv))
    except Exception as e:
        return (fid, False, str(e))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--footprints", required=True, help="CSV with columns: footprint_id,x,y[,radius]")
    p.add_argument("--las", required=True, help="path to LAS/LAZ file")
    p.add_argument("--out_root", default="results", help="output root folder")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--radius", type=float, default=15.0)
    p.add_argument("--dz", type=float, default=0.5)
    p.add_argument("--dz_wf", type=float, default=0.15)
    p.add_argument("--sigma_fp", type=float, default=5.5)
    p.add_argument("--k", type=float, default=0.028)
    p.add_argument("--pulse_sigma", type=float, default=0.6)
    p.add_argument("--snr", type=float, default=30.0)
    args = p.parse_args()

    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    # read footprints CSV
    rows = []
    with open(args.footprints, newline='') as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            if "x" not in r or "y" not in r:
                continue
            rows.append(r)

    params = {"radius": args.radius, "dz": args.dz, "dz_wf": args.dz_wf, "sigma_fp": args.sigma_fp,
              "k": args.k, "pulse_sigma": args.pulse_sigma, "snr": args.snr}

    pool_args = [(r, Path(args.las), out_root, params) for r in rows]
    results = []
    with Pool(processes=args.workers) as pool:
        for res in pool.imap_unordered(process_one, pool_args):
            results.append(res)
            fid, ok, info = res
            print(f"[{fid}] ok={ok} info={info}")

    # merge metrics into summary.csv
    summary = out_root / "summary_metrics.csv"
    import pandas as pd
    rows_out = []
    for fid, ok, info in results:
        if ok:
            try:
                df = pd.read_csv(info)
                df['footprint_id'] = fid
                rows_out.append(df.assign(footprint_id=fid))
            except Exception as e:
                print(f"Could not read metrics for {fid}: {e}")
    if rows_out:
        big = pd.concat(rows_out, ignore_index=True)
        big.to_csv(summary, index=False)
        print("Wrote summary to", summary)
    else:
        print("No successful results to summarize.")

if __name__ == "__main__":
    main()
