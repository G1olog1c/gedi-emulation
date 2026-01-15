#!/usr/bin/env python3
"""
04_compute_rh.py
- Compute RH metrics from profile or from waveform (after ground detection).
"""
import argparse
import numpy as np
from scripts.utils import compute_rh_metrics, foliage_height_diversity

def detect_ground_from_wf(z, wf):
    # naive ground detection: lowest significant peak within lower z-range
    # simply pick first z where wf > threshold*max
    thresh = 0.05 * np.max(wf)
    idx = np.where(wf >= thresh)[0]
    if idx.size == 0:
        return None
    return z[idx[0]]

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--profile_npz", required=True)
    p.add_argument("--from_wf", action='store_true')
    p.add_argument("--out_csv", default="metrics.csv")
    args = p.parse_args()
    data = np.load(args.profile_npz)
    z = data['z']
    if args.from_wf and 'wf' in data:
        wf = data['wf']
        # use wf as proxy for profile: baseline remove
        prof = np.maximum(wf - np.median(wf[:10]), 0.0)
    else:
        prof = data['profile']
    rh = compute_rh_metrics(z, prof)
    fhd = foliage_height_diversity(prof)
    import pandas as pd
    d = rh
    d['FHD'] = fhd
    df = pd.DataFrame([d])
    df.to_csv(args.out_csv, index=False)
    print("Saved metrics to", args.out_csv)
