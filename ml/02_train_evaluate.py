"""Latih & evaluasi model prediksi banjir besok.

Poin penting:
 - Split BERDASARKAN WAKTU (train 2020-22, validasi 2023, uji 2024), bukan acak.
 - Kelas tidak seimbang -> bandingkan model, class_weight, dan ambang keputusan.
 - Hasil = informasi awal; keputusan akhir tetap mengacu BMKG/BPBD.
"""
import json
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, f1_score, precision_recall_curve,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from common import DATA, FITUR, MODELS, RESULTS, TARGET

df = pd.read_csv(DATA / "hidrometeorologi.csv", parse_dates=["tanggal"])
tahun = df.tanggal.dt.year
tr, va, te = df[tahun <= 2022], df[tahun == 2023], df[tahun == 2024]
print(f"train={len(tr)} | validasi={len(va)} | uji={len(te)} | banjir uji = {te[TARGET].mean():.1%}\n")

modelos = {
    "Baseline (selalu tidak banjir)": make_pipeline(SimpleImputer(strategy="median"), DummyClassifier(strategy="most_frequent")),
    "Logistic Regression (balanced)": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced")),
    "Random Forest (balanced)": make_pipeline(SimpleImputer(strategy="median"), RandomForestClassifier(300, min_samples_leaf=5, class_weight="balanced_subsample", random_state=0, n_jobs=-1)),
    "HistGradientBoosting (balanced)": make_pipeline(SimpleImputer(strategy="median"), HistGradientBoostingClassifier(class_weight="balanced", max_depth=4, learning_rate=0.05, max_iter=300, random_state=0)),
}


def metrik(y, proba, thr):
    pred = (proba >= thr).astype(int)
    return {"accuracy": accuracy_score(y, pred), "precision": precision_score(y, pred, zero_division=0),
            "recall": recall_score(y, pred, zero_division=0), "f1": f1_score(y, pred, zero_division=0),
            "pr_auc": average_precision_score(y, proba), "roc_auc": roc_auc_score(y, proba)}


def ambang_recall(y, proba, target=0.80):
    """Ambang tertinggi yang masih memberi recall >= target pada data validasi."""
    p, r, t = precision_recall_curve(y, proba)
    ok = np.where(r[:-1] >= target)[0]
    return float(t[ok.max()]) if len(ok) else 0.5


baris, terlatih = [], {}
for nama, m in modelos.items():
    m.fit(tr[FITUR], tr[TARGET])
    pv, pt = m.predict_proba(va[FITUR])[:, 1], m.predict_proba(te[FITUR])[:, 1]
    thr = ambang_recall(va[TARGET], pv) if "Baseline" not in nama else 0.5
    terlatih[nama] = (m, thr, pv, pt)
    baris.append({"model": nama, "ambang": "0.50", **metrik(te[TARGET], pt, 0.5)})
    baris.append({"model": nama, "ambang": f"{thr:.2f} (recall>=0.8 di validasi)", **metrik(te[TARGET], pt, thr)})
hasil = pd.DataFrame(baris).round(3)
hasil.to_csv(RESULTS / "hasil_model.csv", index=False)
print(hasil.to_string(index=False))

# ---- Pilih model terbaik berdasarkan PR-AUC pada VALIDASI (bukan uji) ----
kandidat = {n: average_precision_score(va[TARGET], v[2]) for n, v in terlatih.items() if "Baseline" not in n}
terbaik = max(kandidat, key=kandidat.get)
model, thr, _, pt = terlatih[terbaik]
print(f"\nModel terpilih (PR-AUC validasi tertinggi): {terbaik} | ambang = {thr:.3f}")

# ---- Mengapa split waktu penting: bandingkan dengan split acak ----
Xa, Xb, ya, yb = train_test_split(df[FITUR], df[TARGET], test_size=0.25, stratify=df[TARGET], random_state=1)
rf = modelos["Random Forest (balanced)"]
rf_acak = make_pipeline(SimpleImputer(strategy="median"), RandomForestClassifier(300, min_samples_leaf=5, class_weight="balanced_subsample", random_state=0, n_jobs=-1)).fit(Xa, ya)
pa = rf_acak.predict_proba(Xb)[:, 1]
pw = terlatih["Random Forest (balanced)"][3]
print(f"Prevalensi banjir | split acak = {yb.mean():.1%} | uji 2024 = {te[TARGET].mean():.1%}")
print(f"Random Forest | ROC-AUC acak = {roc_auc_score(yb, pa):.3f} vs waktu = {roc_auc_score(te[TARGET], pw):.3f}"
      f" | PR-AUC acak = {average_precision_score(yb, pa):.3f} vs waktu = {average_precision_score(te[TARGET], pw):.3f}")
print("(PR-AUC dipengaruhi prevalensi, sehingga ROC-AUC lebih adil untuk membandingkan dua split)")
prev = df.groupby(tahun)[TARGET].mean().round(3)
print("Proporsi banjir per tahun:", prev.to_dict())

# ---- Pentingnya fitur (permutation importance pada data uji) ----
pi = permutation_importance(model, te[FITUR], te[TARGET], scoring="average_precision", n_repeats=5, random_state=0, n_jobs=-1)
imp = pd.Series(pi.importances_mean, index=FITUR).sort_values()
imp.round(4).sort_values(ascending=False).to_csv(RESULTS / "pentingnya_fitur.csv", header=["penurunan_pr_auc"])
print("\nFitur paling berpengaruh:\n", imp.sort_values(ascending=False).head(5).round(4).to_string())

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for n, (m, _, _, p) in terlatih.items():
    if "Baseline" in n:
        continue
    pr, rc, _ = precision_recall_curve(te[TARGET], p)
    ax[0].plot(rc, pr, label=n.split(" (")[0])
ax[0].axhline(te[TARGET].mean(), ls="--", c="gray", label="acak (prevalensi)")
ax[0].set(xlabel="Recall", ylabel="Precision", title="Kurva Precision-Recall (uji 2024)"); ax[0].legend(fontsize=8)
imp.plot.barh(ax=ax[1]); ax[1].set(title=f"Pentingnya fitur ({terbaik.split(' (')[0]})", xlabel="Penurunan PR-AUC")
fig.tight_layout(); fig.savefig(RESULTS / "evaluasi_model.png", dpi=150)

joblib.dump({"model": model, "ambang": thr, "fitur": FITUR, "nama": terbaik}, MODELS / "flood_model.joblib")
json.dump({"model": terbaik, "ambang": round(thr, 4)}, open(RESULTS / "model_terpilih.json", "w"), indent=2)
print("\nModel disimpan ke models/flood_model.joblib")
