#!/usr/bin/env python3
"""
read_gedi_h5.py
Flexible reader for GEDI HDF5 files (GEDI02 or simplified test files).
Extracts available RH percentiles and metadata into a CSV table.
Usage:
    python scripts/read_gedi_h5.py --h5 path/to/GEDI.h5 --out data/gedi_table.csv
"""
import argparse
import h5py
import csv

COMMON_RH_NAMES = ["rh_1", "rh_5", "rh_10", "rh_25", "rh_50", "rh_75", "rh_90", "rh_98",
                   "rh_100", "rh_95", "rh_10", "rh_20"]  # broad set

def find_dataset_name(h5, candidates):
    for name in candidates:
        if name in h5:
            return name
    # try searching for any dataset containing 'rh_' in name
    for name in h5:
        if "rh" in name.lower():
            return name
    return None

def extract(h5_path, out_csv):
    with h5py.File(h5_path, "r") as f:
        # flatten top-level names
        keys = list(f.keys())
        # simple heuristics for rh datasets
        # Try common direct names
        rh_fields = {}
        for candidate in ["rh_25", "rh_50", "rh_75", "rh_98", "rh_10", "rh_90"]:
            if candidate in f:
                rh_fields[candidate] = f[candidate][:]
        # fallback: find any dataset name starting with 'rh'
        for name in keys:
            if name.lower().startswith("rh_") and name not in rh_fields:
                try:
                    rh_fields[name] = f[name][:]
                except Exception:
                    pass
        # also read lat/lon if present
        lat = f.get("lat") or f.get("latitude") or f.get("geolocation/latitude")
        lon = f.get("lon") or f.get("longitude") or f.get("geolocation/longitude")
        sens = f.get("sensitivity")
        slope = f.get("slope")
        degrade = f.get("degrade_flag")
        # build rows
        n = None
        # determine n from any rh field or lat
        if rh_fields:
            for arr in rh_fields.values():
                n = len(arr)
                break
        if n is None and lat is not None:
            n = len(lat[:])
        if n is None:
            raise RuntimeError("No recognizable array datasets found in HDF5.")
        rows = []
        for i in range(n):
            row = {}
            if lat is not None:
                try: row["lat"] = float(lat[i])
                except Exception: row["lat"] = ""
            if lon is not None:
                try: row["lon"] = float(lon[i])
                except Exception: row["lon"] = ""
            for k, arr in rh_fields.items():
                try:
                    row[k] = float(arr[i])
                except Exception:
                    row[k] = ""
            if sens is not None:
                try: row["sensitivity"] = float(sens[i])
                except Exception: row["sensitivity"] = ""
            if slope is not None:
                try: row["slope"] = float(slope[i])
                except Exception: row["slope"] = ""
            if degrade is not None:
                try: row["degrade_flag"] = int(degrade[i])
                except Exception: row["degrade_flag"] = ""
            rows.append(row)
    # write CSV
    # determine header order
    header = []
    if "lat" in rows[0]: header.append("lat")
    if "lon" in rows[0]: header.append("lon")
    # append rh keys in sorted order
    rh_keys = sorted([k for k in rows[0].keys() if k.startswith("rh_")])
    header.extend(rh_keys)
    for extra in ["sensitivity", "slope", "degrade_flag"]:
        if extra in rows[0]:
            header.append(extra)
    with open(out_csv, "w", newline="") as csvf:
        writer = csv.DictWriter(csvf, fieldnames=header)
        writer.writeheader()
        for r in rows:
            # ensure keys present
            out = {k: r.get(k, "") for k in header}
            writer.writerow(out)
    print(f"Wrote {len(rows)} rows to {out_csv}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--h5", required=True, help="Path to GEDI HDF5 file")
    p.add_argument("--out", required=True, help="Output CSV path")
    args = p.parse_args()
    extract(args.h5, args.out)
