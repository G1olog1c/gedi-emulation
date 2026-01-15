import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import csv
import numpy as np
import importlib.util

spec = importlib.util.spec_from_file_location("genmod", str(Path(__file__).resolve().parents[1] / "scripts" / "generate_footprints_from_las.py"))
genmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(genmod)

class FakeChunk:
    def __init__(self, xs, ys):
        class Pts:
            pass
        pts = Pts()
        pts.x = xs
        pts.y = ys
        self._pts = pts
    def __getattr__(self, name):
        return getattr(self._pts, name)

class TestGenerateFootprints(unittest.TestCase):
    @patch("laspy.open")
    def test_generate_small_streaming(self, mock_lasopen):
        rng = np.random.RandomState(0)
        pts1_x = rng.uniform(0, 100, size=150)
        pts1_y = rng.uniform(0, 100, size=150)
        pts2_x = rng.uniform(200, 300, size=120)
        pts2_y = rng.uniform(200, 300, size=120)

        fake_fh = MagicMock()
        fake_fh.__enter__.return_value = fake_fh
        def chunk_iter(size):
            yield FakeChunk(pts1_x, pts1_y)
            yield FakeChunk(pts2_x, pts2_y)
        fake_fh.chunk_iterator = lambda s: chunk_iter(s)
        hdr = MagicMock()
        hdr.min = (0.0, 0.0)
        hdr.max = (300.0, 300.0)
        fake_fh.header = hdr
        mock_lasopen.return_value = fake_fh

        tmpdir = tempfile.TemporaryDirectory()
        out = Path(tmpdir.name) / "footprints.csv"
        n = genmod.generate_footprints_stream("dummy.laz", out, spacing=50.0, radius=20.0, min_count=10, max_centers=100, chunk_size=50)
        self.assertTrue(out.exists())
        with out.open() as f:
            rdr = csv.DictReader(f)
            rows = list(rdr)
        self.assertGreaterEqual(len(rows), 1)
        tmpdir.cleanup()

if __name__ == "__main__":
    unittest.main()
