import subprocess
import sys
from pathlib import Path

PY = sys.executable

def run(cmd):
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    base = Path(__file__).parent
    data = base / "examples"
    results = base / "results"
    results.mkdir(exist_ok=True)

    run([PY, "scripts/generate_synthetic_test.py", "--out", str(data/"synthetic_profile.npz")])

    run([PY, "scripts/03_simulate_wf.py",
         "--profile_npz", str(data/"synthetic_profile.npz"),
         "--out_npz", str(data/"synthetic_wf.npz")])

    run([PY, "scripts/04_compute_rh.py",
         "--profile_npz", str(data/"synthetic_wf.npz"),
         "--from_wf",
         "--out_csv", str(results/"synthetic_metrics.csv")])

    print("Pipeline finished successfully.")

if __name__ == "__main__":
    main()
