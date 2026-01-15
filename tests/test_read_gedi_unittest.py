import unittest
import os
import tempfile
import h5py
import csv
from pathlib import Path
import subprocess
import sys

PY = sys.executable
READER = Path(__file__).resolve().parents[1] / "scripts" / "read_gedi_h5.py"

class TestReadGedi(unittest.TestCase):
    def setUp(self):
        # create temporary GEDI-like HDF5
        self.tmpdir = tempfile.TemporaryDirectory()
        self.h5path = Path(self.tmpdir.name) / "test_gedi.h5"
        with h5py.File(self.h5path, "w") as f:
            # create simple arrays
            n = 5
            f.create_dataset("lat", data=[50.0+i*0.01 for i in range(n)])
            f.create_dataset("lon", data=[20.0+i*0.01 for i in range(n)])
            f.create_dataset("rh_25", data=[1,2,3,4,5])
            f.create_dataset("rh_50", data=[2,3,4,5,6])
            f.create_dataset("rh_75", data=[3,4,5,6,7])
            f.create_dataset("rh_98", data=[4,5,6,7,8])
            f.create_dataset("sensitivity", data=[0.98,0.99,0.95,0.96,0.97])
            f.create_dataset("slope", data=[1,2,3,4,5])
        self.outcsv = Path(self.tmpdir.name) / "gedi_out.csv"

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_reader_creates_csv(self):
        cmd = [PY, str(READER), "--h5", str(self.h5path), "--out", str(self.outcsv)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        self.assertTrue(self.outcsv.exists())
        # check CSV header and row count
        with open(self.outcsv, newline='') as f:
            rdr = csv.DictReader(f)
            rows = list(rdr)
        self.assertEqual(len(rows), 5)
        # check one field
        self.assertIn("rh_98", rows[0])

if __name__ == "__main__":
    unittest.main()
