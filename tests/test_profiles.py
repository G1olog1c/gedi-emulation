import numpy as np
from scripts.generate_synthetic_test import synthetic_structure

def test_synthetic_profile_positive():
    z = np.linspace(0, 25, 51)
    prof = synthetic_structure(z)
    assert np.all(prof >= 0)

def test_synthetic_profile_integral():
    z = np.linspace(0, 25, 51)
    dz = z[1] - z[0]
    prof = synthetic_structure(z)
    assert np.isclose(np.sum(prof)*dz, 1.0, atol=1e-2)
