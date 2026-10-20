"""Demonstrasi konsep HPC skala kecil: paralelisme data/model pada satu mesin multi-core.

Mengukur waktu (a) pelatihan Random Forest, (b) cross-validation, (c) skoring massal
(mis. satu juta sel grid) dengan jumlah worker berbeda. Hasil bergantung pada mesin;
speedup umumnya sublinear (Amdahl's law + overhead).
"""
import os
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from common import DATA, FITUR, RESULTS, TARGET

df = pd.read_csv(DATA / "hidrometeorologi.csv").fillna(0)
X, y = df[FITUR].to_numpy(), df[TARGET].to_numpy()
cpu = os.cpu_count() or 1
workers = sorted({w for w in (1, 2, 4, 8, cpu) if w <= cpu})
print(f"CPU logis tersedia: {cpu} | uji worker: {workers}\n")


def waktu(fn, ulang=2):
    t = []
    for _ in range(ulang):
        a = time.perf_counter(); fn(); t.append(time.perf_counter() - a)
    return min(t)


rows = []
# (a) Pelatihan model
for w in workers:
    rf = RandomForestClassifier(300, min_samples_leaf=3, random_state=0, n_jobs=w)
    rows.append({"eksperimen": "Latih Random Forest (300 pohon)", "worker": w, "detik": waktu(lambda: rf.fit(X, y))})
# (b) Cross-validation 5-fold paralel
for w in workers:
    rf = RandomForestClassifier(100, min_samples_leaf=3, random_state=0, n_jobs=1)
    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    rows.append({"eksperimen": "Cross-validation 5-fold (paralel antar fold)", "worker": w,
                 "detik": waktu(lambda: cross_val_score(rf, X, y, cv=cv, scoring="average_precision", n_jobs=w), 1)})
# (c) Skoring massal 1 juta "sel grid"
rf = RandomForestClassifier(100, min_samples_leaf=3, random_state=0, n_jobs=-1).fit(X, y)
grid = np.tile(X, (int(np.ceil(1_000_000 / len(X))), 1))[:1_000_000]
for w in workers:
    rf.set_params(n_jobs=w)
    rows.append({"eksperimen": "Skoring 1 juta sel grid", "worker": w, "detik": waktu(lambda: rf.predict_proba(grid), 1)})

hasil = pd.DataFrame(rows)
hasil["speedup"] = hasil.groupby("eksperimen")["detik"].transform(lambda s: s.iloc[0] / s)
hasil.round(2).to_csv(RESULTS / "hasil_benchmark_hpc.csv", index=False)
print(hasil.round(2).to_string(index=False))

fig, ax = plt.subplots(figsize=(6.5, 4))
for nama, g in hasil.groupby("eksperimen", sort=False):
    ax.plot(g.worker, g.speedup, marker="o", label=nama)
ax.plot(workers, workers, "k--", lw=1, label="ideal (linear)")
ax.set(xlabel="Jumlah worker (core)", ylabel="Speedup vs 1 worker", title=f"Speedup paralel ({cpu} core)")
ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(RESULTS / "speedup_hpc.png", dpi=150)
