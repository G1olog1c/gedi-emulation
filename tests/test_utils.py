import numpy as np
from scripts.utils import gaussian_pulse, footprint_weight, apply_attenuation

def test_gaussian_pulse_normalization():
    z = np.linspace(-5, 5, 101)
    g = gaussian_pulse(z, sigma=0.6, dz=z[1]-z[0])
    assert np.isclose(np.sum(g)*(z[1]-z[0]), 1.0, atol=1e-3)

def test_footprint_weights_sum_to_one():
    x = np.array([0,1,2])
    y = np.array([0,1,2])
    w = footprint_weight(x, y, sigma_fp=5.5)
    assert np.isclose(w.sum(), 1.0)

def test_attenuation_reduces_energy():
    z = np.linspace(0, 20, 100)
    profile = np.ones_like(z)
    atten = apply_attenuation(profile, z, k=0.03)
    assert atten.sum() < profile.sum()
