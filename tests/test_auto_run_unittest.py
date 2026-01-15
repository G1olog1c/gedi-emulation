import unittest
import tempfile
import os
from pathlib import Path
import csv
from unittest.mock import patch, MagicMock
import importlib.util

# Import auto_run by path
spec = importlib.util.spec_from_file_location("auto_run", str(Path(__file__).resolve().parents[1] / "auto_run.py"))
auto_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auto_run)


class TestAutoRun(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.inputs = self.root / "inputs"
        self.als = self.inputs / "als"
        self.gedi = self.inputs / "gedi"
        self.results = self.root / "results"

        self.inputs.mkdir()
        self.als.mkdir()
        self.gedi.mkdir()
        self.results.mkdir()

        # Create dummy LAS
        (self.als / "area.laz").write_text("DUMMY")

        # Create dummy GEDI
        (self.gedi / "g1.h5").write_text("DUMMYH5")

        # Create footprints
        self.fp = self.inputs / "footprints.csv"
        with self.fp.open("w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["footprint_id", "x", "y"])
            writer.writeheader()
            writer.writerow({"footprint_id": "fp1", "x": "100.0", "y": "200.0"})

        self.old_cwd = Path.cwd()
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.tmp.cleanup()

    def fake_run(self, cmd, capture_output=True, text=True):
        s = " ".join(cmd)

        # Simulate footprint generation
        if "generate_footprints_from_las.py" in s:
            fp = Path("inputs/footprints.csv")
            fp.parent.mkdir(parents=True, exist_ok=True)
            with fp.open("w", newline="") as f:
                f.write("footprint_id,x,y\nfp1,1,2\n")
            return MagicMock(returncode=0, stdout="gen ok", stderr="")

        # Simulate GEDI reader creating tmp CSV
        if "read_gedi_h5.py" in s:
            tmp = Path("inputs/gedi_tmp_0.csv")
            with tmp.open("w", newline="") as f:
                f.write("rh_98\n10\n")
            return MagicMock(returncode=0, stdout="gedi ok", stderr="")

        # Simulate pipeline success
        if "pipeline_batch.py" in s:
            return MagicMock(returncode=0, stdout="pipeline ok", stderr="")

        return MagicMock(returncode=0, stdout="ok", stderr="")

    @patch("subprocess.run")
    def test_happy_path_invokes_pipeline(self, mock_run):
        mock_run.side_effect = self.fake_run
        auto_run.main([])
        self.assertTrue(mock_run.called)

    @patch("subprocess.run")
    def test_missing_footprints_generates(self, mock_run):
        self.fp.unlink()  # remove footprints
        mock_run.side_effect = self.fake_run
        auto_run.main([])
        self.assertTrue((self.inputs / "footprints.csv").exists())

    @patch("subprocess.run")
    def test_gedi_read_failure_continues(self, mock_run):
        def side_effect(cmd, capture_output=True, text=True):
            s = " ".join(cmd)
            if "read_gedi_h5.py" in s:
                return MagicMock(returncode=1, stdout="", stderr="fail")
            if "pipeline_batch.py" in s:
                return MagicMock(returncode=0, stdout="pipeline ok", stderr="")
            return MagicMock(returncode=0, stdout="ok", stderr="")

        mock_run.side_effect = side_effect
        auto_run.main([])  # should not raise

    @patch("subprocess.run")
    def test_pipeline_failure_raises(self, mock_run):
        def side_effect(cmd, capture_output=True, text=True):
            s = " ".join(cmd)
            if "pipeline_batch.py" in s:
                return MagicMock(returncode=2, stdout="", stderr="pipeline error")
            if "read_gedi_h5.py" in s:
                tmp = Path("inputs/gedi_tmp_0.csv")
                with tmp.open("w", newline="") as f:
                    f.write("rh_98\n10\n")
                return MagicMock(returncode=0, stdout="ok", stderr="")
            return MagicMock(returncode=0, stdout="ok", stderr="")

        mock_run.side_effect = side_effect
        with self.assertRaises(RuntimeError):
            auto_run.main([])

    def test_no_las_raises(self):
        for f in self.als.glob("*"):
            f.unlink()
        with self.assertRaises(FileNotFoundError):
            auto_run.find_first_las(self.als)


if __name__ == "__main__":
    unittest.main()
