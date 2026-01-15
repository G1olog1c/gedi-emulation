# utils.py
import numpy as np
from scipy.signal import fftconvolve
from scipy.stats import entropy

def gaussian_pulse(z, sigma=0.6, dz=0.15):
    """Return Gaussian pulse sampled at z positions (centered at 0)."""
    mu = 0.0
    g = np.exp(-0.5 * ((z - mu) / sigma) ** 2)
    return g / (g.sum() * dz)

def footprint_weight(xs, ys, sigma_fp=5.5):
    """Compute Gaussian footprint weights for arrays xs, ys (offsets from centre)."""
    r2 = xs**2 + ys**2
    w = np.exp(-0.5 * r2 / (sigma_fp**2))
    return w / w.sum()

def apply_attenuation(profile, z, k=0.028):
    """
    Apply Beer-Lambert like attenuation to profile.
    profile: 1D array of raw scatter (per-bin)
    z: corresponding heights (same length)
    k: attenuation coefficient
    """
    # cumulative integral (approx)
    dz = np.mean(np.diff(z))
    cum = np.cumsum(profile) * dz
    atten = profile * np.exp(-k * cum)
    return atten

def convolve_with_pulse(profile, z, pulse_sigma=0.6, dz=0.15):
    z_pulse = np.arange(-5, 5 + dz, dz)
    pulse = gaussian_pulse(z_pulse, sigma=pulse_sigma, dz=dz)
    wf = fftconvolve(profile, pulse, mode='same') * dz
    return wf

def compute_rh_metrics(z, profile, percentiles=(25,50,75,90,98)):
    """
    Compute RH percentiles from a vertical profile.
    profile should represent energy per z-bin (non-negative).
    """
    dz = np.mean(np.diff(z))
    total = profile.sum() * dz
    if total <= 0:
        return {f"RH{p}": np.nan for p in percentiles}
    cumsum = np.cumsum(profile) * dz
    results = {}
    for p in percentiles:
        target = p/100.0 * total
        idx = np.searchsorted(cumsum, target)
        results[f"RH{p}"] = float(z[idx]) if idx < len(z) else float(z[-1])
    return results

def foliage_height_diversity(profile, base=np.e):
    """
    Shannon entropy-like FHD: compute normalized entropy across profile.
    """
    p = profile.copy()
    s = p.sum()
    if s <= 0:
        return np.nan
    p = p / s
    # use scipy.stats.entropy for stable calculation
    return float(entropy(p, base=base))
