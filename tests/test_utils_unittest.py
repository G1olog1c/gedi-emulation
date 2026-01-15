import unittest
import numpy as np
from scripts.utils import gaussian_pulse, footprint_weight, apply_attenuation, convolve_with_pulse, compute_rh_metrics

class TestUtils(unittest.TestCase):
    def test_gaussian_pulse_normalization(self):
        z = np.linspace(-5, 5, 101)
        dz = z[1]-z[0]
        g = gaussian_pulse(z, sigma=0.6, dz=dz)
        self.assertAlmostEqual(np.sum(g)*dz, 1.0, places=3)

    def test_footprint_weights_sum_to_one(self):
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([0.0, 1.0, 2.0])
        w = footprint_weight(x, y, sigma_fp=5.5)
        self.assertAlmostEqual(float(w.sum()), 1.0, places=6)

    def test_attenuation_reduces_energy(self):
        z = np.linspace(0, 20, 100)
        profile = np.ones_like(z)
        atten = apply_attenuation(profile, z, k=0.03)
        self.assertLess(float(atten.sum()), float(profile.sum()))

    def test_convolve_preserves_length(self):
        z = np.linspace(0, 20, 100)
        profile = np.exp(-0.5*((z-10)/2)**2)
        wf = convolve_with_pulse(profile, z, pulse_sigma=0.6, dz=z[1]-z[0])
        self.assertEqual(len(wf), len(profile))

    def test_rh_percentiles_monotonic(self):
        z = np.linspace(0, 30, 301)
        profile = np.exp(-0.5*((z-15)/3)**2)
        rh = compute_rh_metrics(z, profile, percentiles=(25,50,75,90))
        self.assertLess(rh["RH25"], rh["RH50"])
        self.assertLess(rh["RH50"], rh["RH75"])
        self.assertLess(rh["RH75"], rh["RH90"])

if __name__ == "__main__":
    unittest.main()
