import numpy as np
from scripts.utils import compute_rh_metrics

def test_rh_monotonicity():
    z = np.linspace(0, 30, 301)
    profile = np.exp(-0.5*((z-15)/3)**2)
    rh = compute_rh_metrics(z, profile, percentiles=(25,50,75,90))
    assert rh["RH25"] < rh["RH50"] < rh["RH75"] < rh["RH90"]
