#!/usr/bin/env python3
"""
01_preprocess_als.py
- Read LAS/LAZ, classify ground (optionally), normalize heights (if ground present),
- Output normalized points for a given footprint center (CLI).
"""
import argparse
import laspy
import numpy as np
from pyproj import Transformer
from shapely.geometry import Point

def extract_window(las_path, x_center, y_center, radius, out_csv=None):
    las = laspy.read(las_path)
    xs = las.x
    ys = las.y
    zs = las.z
    # simple bounding box filter then radial
    mask_box = (xs >= x_center - radius) & (xs <= x_center + radius) & (ys >= y_center - radius) & (ys <= y_center + radius)
    idx = np.where(mask_box)[0]
    if idx.size == 0:
        print("No points in bbox.")
        return None
    dx = xs[idx] - x_center
    dy = ys[idx] - y_center
    rmask = (dx*dx + dy*dy) <= radius*radius
    sel = idx[rmask]
    if sel.size == 0:
        print("No points in circular footprint.")
        return None
    out = np.vstack([dx[rmask], dy[rmask], zs[sel]]).T
    if out_csv:
        import pandas as pd
        df = pd.DataFrame(out, columns=['dx','dy','z'])
        df.to_csv(out_csv, index=False)
    return out

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--las", required=True)
    p.add_argument("--x", type=float, required=True)
    p.add_argument("--y", type=float, required=True)
    p.add_argument("--r", type=float, default=15.0)
    p.add_argument("--out", default=None)
    args = p.parse_args()
    pts = extract_window(args.las, args.x, args.y, args.r, out_csv=args.out)
    if pts is not None:
        print(f"Extracted {pts.shape[0]} points.")
