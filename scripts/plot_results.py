#!/usr/bin/env python3
"""
plot_results.py
Simple plotting helper: reads summary CSV (merged sim vs GEDI) and plots scatter RH_sim vs RH_gedi,
and writes RMSE/bias table per percentile.
Usage:
    python scripts/plot_results.py --summary results/summary_metrics.csv --gedi gedi_table.csv --out figures/
"""
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def compute_stats(x, y):
    mask = (~np.isnan(x)) & (~np.isnan(y))
    if mask.sum() == 0:
        return {}
    x = x[mask]; y = y[mask]
    bias = np.mean(x - y)
    rmse = np.sqrt(np.mean((x - y)**2))
    r2 = np.corrcoef(x, y)[0,1] if x.size>1 else np.nan
    return {"n": int(mask.sum()), "bias": float(bias), "rmse": float(rmse), "r2": float(r2)}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--summary", required=True)
    p.add_argument("--gedi", required=False, help="optional gedi csv to merge (by footprint id)")
    p.add_argument("--out", default="figures")
    args = p.parse_args()
    outdir = args.out
    os.makedirs(outdir, exist_ok=True)
    sim = pd.read_csv(args.summary)
    if args.gedi:
        gedi = pd.read_csv(args.gedi)
        df = pd.merge(sim, gedi, on="footprint_id", how="inner", suffixes=("_sim","_gedi"))
    else:
        df = sim

    # find percentile columns that exist both sides
    percentiles = []
    for col in df.columns:
        if col.startswith("RH") or col.lower().startswith("rh_"):
            percentiles.append(col)
    # try common names like RH98_sim / rh_98_gedi
    # we'll detect pairs
    sim_cols = [c for c in df.columns if c.endswith("_sim")]
    gedi_cols = [c for c in df.columns if c.endswith("_gedi")]
    pairs = []
    if sim_cols and gedi_cols:
        for s in sim_cols:
            base = s[:-4]
            g = base + "_gedi"
            if g in df.columns:
                pairs.append((s,g))
    else:
        # fallback: look for rh_98 and RH98 columns
        for suffix in ["98","50","25","75","90"]:
            simc = f"RH{suffix}_sim" if f"RH{suffix}_sim" in df.columns else f"rh_{suffix}_sim"
            gedic = f"RH{suffix}_gedi" if f"RH{suffix}_gedi" in df.columns else f"rh_{suffix}_gedi"
            if simc in df.columns and gedic in df.columns:
                pairs.append((simc, gedic))

    # plot each pair
    stats_rows = []
    for simc, gedic in pairs:
        x = df[simc].values
        y = df[gedic].values
        s = compute_stats(x, y)
        s["metric"] = simc.replace("_sim","")
        stats_rows.append(s)
        plt.figure(figsize=(5,5))
        plt.scatter(y, x, s=10, alpha=0.6)
        plt.plot([np.nanmin(y),np.nanmax(y)],[np.nanmin(y),np.nanmax(y)], '--', linewidth=1)
        plt.xlabel(f"{gedic}")
        plt.ylabel(f"{simc}")
        plt.title(f"{simc} vs {gedic}\n n={s.get('n',0)} bias={s.get('bias',np.nan):.2f} rmse={s.get('rmse',np.nan):.2f}")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, f"scatter_{simc}_vs_{gedic}.png"), dpi=200)
        plt.close()

    # save stats
    stats_df = pd.DataFrame(stats_rows)
    stats_df.to_csv(os.path.join(outdir, "stats_summary.csv"), index=False)
    print("Plots + stats written to", outdir)
