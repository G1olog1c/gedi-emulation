#!/usr/bin/env python3
"""
03_simulate_wf.py
- From z,profile simulate full waveform: attenuation + convolution with pulse + add noise
"""
import argparse
import numpy as np
from scripts.utils import apply_attenuation, convolve_with_pulse

def add_noise(wf, snr_db=30):
    # SNR in dB: signal power / noise power
    sig_power = np.mean(wf**2)
    snr_linear = 10**(snr_db/10.0)
    noise_power = sig_power / snr_linear if sig_power>0 else 1e-9
    noise = np.random.normal(scale=np.sqrt(noise_power), size=wf.shape)
    return wf + noise

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--profile_npz", required=True)
    p.add_argument("--k", type=float, default=0.028)
    p.add_argument("--pulse_sigma", type=float, default=0.6)
    p.add_argument("--dz", type=float, default=0.15)
    p.add_argument("--snr", type=float, default=30.0)
    p.add_argument("--out_npz", default="wf_sim.npz")
    args = p.parse_args()
    data = np.load(args.profile_npz)
    z = data['z']
    profile = data['profile']
    atten = apply_attenuation(profile, z, k=args.k)
    wf = convolve_with_pulse(atten, z, pulse_sigma=args.pulse_sigma, dz=args.dz)
    wf_n = add_noise(wf, snr_db=args.snr)
    np.savez(args.out_npz, z=z, wf=wf_n, wf_clean=wf, attenuated=atten)
    print("Saved simulated waveform to", args.out_npz)
