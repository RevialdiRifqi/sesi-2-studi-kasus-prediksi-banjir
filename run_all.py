"""Jalankan seluruh pipeline ML secara berurutan."""
import subprocess, sys
from pathlib import Path

ml = Path(__file__).parent / "ml"
for s in ["01_generate_data.py", "02_train_evaluate.py", "03_hpc_benchmark.py", "04_smoke_test_api.py"]:
    print(f"\n{'=' * 70}\n>>> {s}\n{'=' * 70}")
    subprocess.run([sys.executable, s], cwd=ml, check=True)
