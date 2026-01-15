#!/usr/bin/env python3
"""
Memory-efficient footprint generator (robust for tests and prod).

Tries to open via laspy.open first (allows tests to mock laspy.open).
If open fails and file doesn't exist -> FileNotFoundError.
Otherwise proceeds with streaming/chunked reading.
"""
import argparse
from pathlib import Path
import numpy as np
import csv

def _has_chunk_iterator(fh):
    return hasattr(fh, "chunk_iterator")

def generate_footprints_stream(las_path, out_csv, spacing=30.0, radius=15.0, min_count=5, max_centers=None, chunk_size=200_000):
    import laspy
    from scipy.spatial import cKDTree

    las_path = Path(las_path)

    # Try opening via laspy.open (this allows mocking in tests)
    try:
        fh_test = laspy.open(str(las_path))
        # close test handle if it is a real handle
        try:
            fh_test.close()
        except Exception:
            pass
    except Exception as e:
        # if file does not exist, raise; otherwise re-raise
        if not las_path.exists():
            raise FileNotFoundError(f"{las_path} not found")
        # otherwise proceed (laspy.open might fail for other reasons later)

    # Open again for real processing
    with laspy.open(str(las_path)) as fh:
        hdr = fh.header
        # try to read bbox from header
        try:
            if hasattr(hdr, "min") and hasattr(hdr, "max"):
                xmin = float(hdr.min[0]); ymin = float(hdr.min[1])
                xmax = float(hdr.max[0]); ymax = float(hdr.max[1])
            else:
                xmin = float(hdr.x_min); ymin = float(hdr.y_min)
                xmax = float(hdr.x_max); ymax = float(hdr.y_max)
        except Exception:
            # fallback: read a small chunk to compute bounds
            try:
                data = fh.read(1)
                xs = np.asarray(data.x, dtype=np.float64)
                ys = np.asarray(data.y, dtype=np.float64)
                xmin, xmax = float(xs.min()), float(xs.max())
                ymin, ymax = float(ys.min()), float(ys.max())
            except Exception as ee:
                raise RuntimeError("Could not determine LAS bounds: " + str(ee))

    # Create grid of centers (in same units as LAS)
    x_coords = np.arange(xmin + spacing/2.0, xmax, spacing)
    y_coords = np.arange(ymin + spacing/2.0, ymax, spacing)
    if x_coords.size == 0:
        x_coords = np.array([(xmin + xmax) / 2.0])
    if y_coords.size == 0:
        y_coords = np.array([(ymin + ymax) / 2.0])
    grid_x, grid_y = np.meshgrid(x_coords, y_coords)
    centers = np.column_stack([grid_x.ravel(), grid_y.ravel()]).astype(np.float64)
    n_centers = centers.shape[0]

    if n_centers == 0:
        raise RuntimeError("No centers generated (check spacing vs extent)")

    # Build tree on centers (centers typically << points)
    tree_centers = cKDTree(centers)

    # counts per center
    counts = np.zeros(n_centers, dtype=np.int64)

    # stream points and increment counts
    with laspy.open(str(las_path)) as fh:
        if _has_chunk_iterator(fh):
            for chunk in fh.chunk_iterator(chunk_size):
                xs = np.asarray(chunk.x, dtype=np.float64)
                ys = np.asarray(chunk.y, dtype=np.float64)
                if xs.size == 0:
                    continue
                pts = np.column_stack([xs, ys])
                lists = tree_centers.query_ball_point(pts, r=radius)
                for idxs in lists:
                    if len(idxs) == 0:
                        continue
                    for i in idxs:
                        counts[i] += 1
                flattened = []
                for sub in lists:
                    if sub:
                        flattened.extend(sub)
                if len(flattened) == 0:
                    continue
                arr = np.fromiter(flattened, dtype=np.int64)
                counts += np.bincount(arr, minlength=n_centers)
        else:
            # fallback to full read (memory heavy)
            data = fh.read()
            xs = np.asarray(data.x, dtype=np.float64)
            ys = np.asarray(data.y, dtype=np.float64)
            if xs.size > 0:
                pts = np.column_stack([xs, ys])
                lists = tree_centers.query_ball_point(pts, r=radius)
                flattened = []
                for sub in lists:
                    if sub:
                        flattened.extend(sub)
                if len(flattened) > 0:
                    arr = np.fromiter(flattened, dtype=np.int64)
                    counts += np.bincount(arr, minlength=n_centers)

    # filter centers by min_count
    keep_mask = counts >= min_count
    kept_centers = centers[keep_mask]
    kept_counts = counts[keep_mask]

    if kept_centers.shape[0] == 0:
        out_csv = Path(out_csv)
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        with out_csv.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["footprint_id", "x", "y", "radius"])
        return 0

    # optionally limit max_centers by density
    if max_centers and len(kept_centers) > max_centers:
        idx_sorted = np.argsort(-kept_counts)[:max_centers]
        kept_centers = kept_centers[idx_sorted]
        kept_counts = kept_counts[idx_sorted]

    # write CSV
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["footprint_id", "x", "y", "radius"])
        for i, (cx, cy) in enumerate(kept_centers):
            writer.writerow([f"fp_{i:06d}", f"{cx:.3f}", f"{cy:.3f}", f"{radius:.3f}"])
    return int(kept_centers.shape[0])

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--las", required=True)
    p.add_argument("--out", default="inputs/footprints.csv")
    p.add_argument("--spacing", type=float, default=30.0)
    p.add_argument("--radius", type=float, default=15.0)
    p.add_argument("--min_count", type=int, default=5)
    p.add_argument("--max_centers", type=int, default=None)
    p.add_argument("--chunk_size", type=int, default=200000)
    args = p.parse_args(argv)
    n = generate_footprints_stream(args.las, args.out, spacing=args.spacing, radius=args.radius, min_count=args.min_count, max_centers=args.max_centers, chunk_size=args.chunk_size)
    print(f"Wrote {n} footprints to {args.out}")

if __name__ == "__main__":
    main()
