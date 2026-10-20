"""Konstanta dan path bersama."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
MODELS = ROOT / "models"
for d in (DATA, RESULTS, MODELS):
    d.mkdir(exist_ok=True)

TARGET = "banjir_besok"
FITUR = [
    "curah_hujan_mm", "hujan_3hari_mm", "hujan_7hari_mm", "prakiraan_hujan_besok_mm",
    "tinggi_muka_air_cm", "kelembapan_tanah_persen",
    "elevasi_m", "jarak_sungai_m", "drainase_skor", "bulan",
]
# Rentang valid input (dipakai API untuk validasi)
RENTANG = {
    "curah_hujan_mm": (0, 500), "hujan_3hari_mm": (0, 1000), "hujan_7hari_mm": (0, 2000),
    "prakiraan_hujan_besok_mm": (0, 500), "tinggi_muka_air_cm": (0, 1500),
    "kelembapan_tanah_persen": (0, 100), "elevasi_m": (-5, 3000),
    "jarak_sungai_m": (0, 20000), "drainase_skor": (1, 5), "bulan": (1, 12),
}
