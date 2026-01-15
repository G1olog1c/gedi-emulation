#!/usr/bin/env python3
"""
02_build_profile.py
- Build vertical profile rho(z) from extracted points (csv or direct).
"""
import argparse
import numpy as np
import pandas as pd
from scripts.utils import footprint_weight

def build_profile_from_points(csv_path, dz=0.5, sigma_fp=5.5, weight_mode='uniform'):
    df = pd.read_csv(csv_path)
    xs = df['dx'].values
    ys = df['dy'].values
    zs = df['z'].values
    # z grid
    zmin = max(0.0, np.floor(zs.min() - 1.0))
    zmax = np.ceil(zs.max() + 1.0)
    z = np.arange(zmin, zmax + dz, dz)
    wxy = footprint_weight(xs, ys, sigma_fp=sigma_fp)
    # choose per-point weight
    if weight_mode == 'uniform':
        wp = wxy
    else:
        wp = wxy  # placeholder for 'intensity' or '1/n_returns'
    profile = np.zeros_like(z)
    # binning points into z-bins
    idx = np.floor((zs - zmin) / dz).astype(int)
    valid = (idx >= 0) & (idx < len(z))
    for i, ii in enumerate(idx[valid]):
        profile[ii] += wp[valid][i]
    # normalization optional:
    if profile.sum() > 0:
        profile = profile / profile.sum()
    return z, profile

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--in_csv", required=True)
    p.add_argument("--dz", type=float, default=0.5)
    p.add_argument("--sigma_fp", type=float, default=5.5)
    p.add_argument("--out_npz", default="profile.npz")
    args = p.parse_args()
    z, prof = build_profile_from_points(args.in_csv, dz=args.dz, sigma_fp=args.sigma_fp)
    np.savez(args.out_npz, z=z, profile=prof)
    print("Saved profile to", args.out_npz)
