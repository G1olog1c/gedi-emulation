#!/usr/bin/env python3
"""
Produce a simple synthetic vertical structure for quick tests (useful for CI/tests)
"""
import numpy as np
import argparse
from scripts.utils import gaussian_pulse

def synthetic_structure(z):
    # two canopy layers + trunk near ground
    prof = np.exp(-0.5*((z-2.0)/0.8)**2) * 0.8 + np.exp(-0.5*((z-10.0)/2.0)**2)*1.2
    prof = np.maximum(prof, 0.0)
    prof = prof / (prof.sum()* (z[1]-z[0]))
    return prof

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dz", type=float, default=0.5)
    p.add_argument("--out", default="synthetic_profile.npz")
    args = p.parse_args()
    z = np.arange(0, 25+args.dz, args.dz)
    prof = synthetic_structure(z)
    np.savez(args.out, z=z, profile=prof)
    print("Saved synthetic profile to", args.out)
