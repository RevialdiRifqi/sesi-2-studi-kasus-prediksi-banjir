"""Logika prediksi yang dipakai oleh API."""
import joblib
from functools import lru_cache
from common import FITUR, MODELS, RENTANG


@lru_cache(maxsize=1)
def _muat():
    return joblib.load(MODELS / "flood_model.joblib")


def validasi(payload: dict) -> list[str]:
    galat = []
    for k in FITUR:
        if k not in payload:
            galat.append(f"{k}: wajib diisi"); continue
        try:
            v = float(payload[k])
        except (TypeError, ValueError):
            galat.append(f"{k}: harus berupa angka"); continue
        lo, hi = RENTANG[k]
        if not lo <= v <= hi:
            galat.append(f"{k}: di luar rentang {lo}-{hi}")
    return galat


def level_risiko(p: float, ambang: float) -> tuple[str, str]:
    if p < 0.5 * ambang:
        return "Rendah", "Kondisi relatif aman. Tetap pantau informasi cuaca."
    if p < ambang:
        return "Sedang", "Mulai waspada dan pantau tinggi muka air serta prakiraan hujan."
    if p < (ambang + 1) / 2:
        return "Tinggi", "Siapkan langkah antisipasi dan ikuti informasi resmi BMKG/BPBD."
    return "Sangat Tinggi", "Segera ikuti arahan BPBD/pemerintah setempat dan siapkan evakuasi bila diperlukan."


def prediksi(payload: dict) -> dict:
    paket = _muat()
    baris = [[float(payload[k]) for k in paket["fitur"]]]
    import pandas as pd
    p = float(paket["model"].predict_proba(pd.DataFrame(baris, columns=paket["fitur"]))[0, 1])
    level, saran = level_risiko(p, paket["ambang"])
    return {"probabilitas": round(p, 4), "level": level, "saran": saran, "model": paket["nama"],
            "catatan": "Informasi awal berbasis model, bukan peringatan dini resmi. Rujuk BMKG/BPBD."}
