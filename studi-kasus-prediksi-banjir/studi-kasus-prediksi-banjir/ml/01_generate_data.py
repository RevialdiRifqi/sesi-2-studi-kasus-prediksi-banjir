"""Membuat data SINTETIS hidrometeorologi harian untuk 12 zona (2020-2024).

Bukan data BMKG/BPBD. Pola dibuat meniru musim hujan Indonesia (Nov-Apr) agar alur
ML dan sistemnya dapat didemonstrasikan. Label = apakah zona banjir BESOK.
Fitur 'prakiraan_hujan_besok_mm' mensimulasikan prakiraan cuaca (dengan galat), yang
memang tersedia pada hari prediksi sehingga bukan kebocoran data.
"""
import numpy as np
import pandas as pd
from common import DATA

rng = np.random.default_rng(7)
N_ZONA = 12
zona = pd.DataFrame({
    "zona": [f"Z{i:02d}" for i in range(1, N_ZONA + 1)],
    "elevasi_m": rng.uniform(2, 60, N_ZONA).round(1),
    "jarak_sungai_m": rng.uniform(50, 2500, N_ZONA).round(0),
    "drainase_skor": rng.integers(1, 6, N_ZONA),  # 1 buruk ... 5 baik
})

tgl = pd.date_range("2020-01-01", "2024-12-31", freq="D")
T = len(tgl)
bulan = tgl.month.values
basah = np.isin(bulan, [11, 12, 1, 2, 3, 4])

# Hujan regional (bersama untuk semua zona), lalu variasi lokal per zona
ada = rng.random(T) < np.where(basah, 0.60, 0.25)
jumlah = rng.gamma(0.9, np.where(basah, 16, 9))
badai = rng.random(T) < np.where(basah, 0.03, 0.005)
regional = ada * jumlah * np.where(badai, rng.uniform(3, 6, T), 1.0)

frames = []
for _, z in zona.iterrows():
    hujan = np.round(regional * rng.lognormal(0, 0.3, T) * (rng.random(T) < 0.9), 1)
    s = pd.Series(hujan)
    h3 = s.rolling(3, min_periods=1).sum()
    h7 = s.rolling(7, min_periods=1).sum()
    basah_tanah = np.zeros(T)
    for t in range(1, T):
        basah_tanah[t] = 0.9 * basah_tanah[t - 1] + min(hujan[t], 60) * 0.9
    kelembapan = np.clip(20 + 0.8 * basah_tanah + rng.normal(0, 3, T), 10, 100)
    tma = np.clip(80 + 1.1 * h3 + 0.5 * h7 + rng.normal(0, 12, T), 30, 600)
    besok = np.roll(hujan, -1)
    prakiraan = np.round(np.clip(besok * rng.lognormal(0, 0.5, T) + rng.normal(0, 2, T), 0, None), 1)
    frames.append(pd.DataFrame({
        "tanggal": tgl, "zona": z.zona, "curah_hujan_mm": hujan,
        "hujan_3hari_mm": h3.round(1), "hujan_7hari_mm": h7.round(1),
        "prakiraan_hujan_besok_mm": prakiraan,
        "tinggi_muka_air_cm": tma.round(0), "kelembapan_tanah_persen": kelembapan.round(1),
        "elevasi_m": z.elevasi_m, "jarak_sungai_m": z.jarak_sungai_m, "drainase_skor": z.drainase_skor,
        "bulan": bulan,
    }))
df = pd.concat(frames, ignore_index=True)


def zs(x):
    return (x - x.mean()) / x.std()


skor = (1.2 * zs(df.hujan_3hari_mm) + 0.7 * zs(df.curah_hujan_mm) + 0.9 * zs(df.tinggi_muka_air_cm)
        + 0.5 * zs(df.kelembapan_tanah_persen) - 0.9 * zs(df.elevasi_m)
        - 0.5 * zs(np.log(df.jarak_sungai_m)) - 0.5 * zs(df.drainase_skor))
skor = skor + rng.normal(0, 0.6, len(df))
df["banjir_hari_ini"] = (skor > np.quantile(skor, 0.95)).astype(int)
df = df.sort_values(["zona", "tanggal"]).reset_index(drop=True)
df["banjir_besok"] = df.groupby("zona")["banjir_hari_ini"].shift(-1)
df = df.dropna(subset=["banjir_besok"]).drop(columns="banjir_hari_ini")
df["banjir_besok"] = df["banjir_besok"].astype(int)

# Sedikit nilai hilang agar realistis
for kol in ["curah_hujan_mm", "kelembapan_tanah_persen"]:
    df.loc[rng.choice(len(df), int(len(df) * 0.01), replace=False), kol] = np.nan

df.to_csv(DATA / "hidrometeorologi.csv", index=False)
print(f"{len(df)} baris | {N_ZONA} zona | {df.tanggal.min().date()} s.d. {df.tanggal.max().date()} "
      f"| proporsi banjir besok = {df.banjir_besok.mean():.1%}")
