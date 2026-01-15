#!/usr/bin/env python3
"""
05_compare_with_gedi.py
- Basic comparison pipeline: given table of simulated/ALS RH and GEDI RH, compute bias, RMSE, R2.
"""
import argparse
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score

def compare(df, col_sim, col_gedi):
    mask = (~df[col_sim].isna()) & (~df[col_gedi].isna())
    x = df.loc[mask, col_sim].values
    y = df.loc[mask, col_gedi].values
    if x.size == 0:
        return {}
    bias = np.mean(x - y)
    rmse = np.sqrt(mean_squared_error(y, x))
    r2 = r2_score(y, x)
    return {'n': int(x.size), 'bias': float(bias), 'rmse': float(rmse), 'r2': float(r2)}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--sim_csv", required=True)
    p.add_argument("--gedi_csv", required=True)
    p.add_argument("--on", default="RH98")
    args = p.parse_args()
    sim = pd.read_csv(args.sim_csv)
    gedi = pd.read_csv(args.gedi_csv)
    # assume both have footprint_id column
    df = pd.merge(sim, gedi, on='footprint_id', suffixes=('_sim','_gedi'))
    metrics = compare(df, f"{args.on}_sim", f"{args.on}_gedi")
    print(metrics)
