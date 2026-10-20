"""Uji cepat API tanpa menjalankan server."""
from app import app

c = app.test_client()
aman = dict(curah_hujan_mm=0, hujan_3hari_mm=2, hujan_7hari_mm=10, prakiraan_hujan_besok_mm=1,
            tinggi_muka_air_cm=110, kelembapan_tanah_persen=40, elevasi_m=55, jarak_sungai_m=2000, drainase_skor=5, bulan=8)
bahaya = dict(curah_hujan_mm=120, hujan_3hari_mm=260, hujan_7hari_mm=330, prakiraan_hujan_besok_mm=90,
              tinggi_muka_air_cm=480, kelembapan_tanah_persen=98, elevasi_m=3, jarak_sungai_m=60, drainase_skor=1, bulan=1)
for nama, data in [("kondisi aman", aman), ("kondisi ekstrem", bahaya)]:
    r = c.post("/predict", json=data)
    print(f"{nama}: HTTP {r.status_code} -> {r.get_json()['probabilitas']} | {r.get_json()['level']}")
    assert r.status_code == 200
assert c.post("/predict", json={"bulan": 13}).status_code == 422
assert c.post("/predict", data="bukan json").status_code == 400
assert c.get("/health").get_json()["status"] == "ok"
print("Semua uji API lulus.")
