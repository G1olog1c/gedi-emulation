import numpy as np
from scripts.utils import convolve_with_pulse

def test_waveform_length_preserved():
    z = np.linspace(0, 20, 100)
    profile = np.exp(-0.5*((z-10)/2)**2)
    wf = convolve_with_pulse(profile, z, pulse_sigma=0.6, dz=z[1]-z[0])
    assert len(wf) == len(profile)
