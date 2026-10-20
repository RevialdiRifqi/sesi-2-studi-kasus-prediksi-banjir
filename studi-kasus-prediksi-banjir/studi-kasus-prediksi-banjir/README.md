# Studi Kasus: Sistem Prediksi Potensi Banjir Berbasis Web dengan Machine Learning
### Terinspirasi materi High Performance Computing (HPC), Sesi 2 DEEPL

**Penulis:** Nama Anda | **NPM:** NPM Anda | **Mata Kuliah:** DEEPL

Materi Sesi 2 membahas HPC: komputasi berkinerja tinggi untuk mengolah data besar dan menyelesaikan perhitungan
kompleks, dengan contoh permasalahan nyata seperti prediksi banjir. Studi kasus ini membangun **prototipe sistem
prediksi potensi banjir** yang menggabungkan Machine Learning (Python) dan aplikasi web (Laravel), serta
mendemonstrasikan **konsep paralelisme HPC dalam skala kecil** pada satu mesin multi-core.

> **Penting:** seluruh data adalah **data sintetis** yang dibangkitkan kode di repo ini (pola musim hujan
> Nov-Apr). Ini bukan data BMKG/BPBD, sehingga hasilnya hanya untuk demonstrasi alur, **bukan** untuk
> peringatan banjir nyata. Sistem nyata membutuhkan data resmi dan validasi ahli.

## 1. Skenario
Masyarakat membutuhkan informasi awal: *apakah besok ada potensi banjir di zona saya?* Sistem menerima kondisi
hari ini (curah hujan, akumulasi 3 dan 7 hari, tinggi muka air, kelembapan tanah, prakiraan hujan besok) dan
karakter lokasi (elevasi, jarak ke sungai, kualitas drainase), lalu mengembalikan **tingkat risiko** dengan saran.

## 2. Arsitektur
```
Browser --> Laravel (form, validasi, riwayat) --HTTP JSON--> Flask API (ml/app.py) --> model scikit-learn
```
Laravel mengurus antarmuka dan penyimpanan; model dilatih dan dilayani oleh Python lewat endpoint `POST /predict`.

## 3. Pemetaan ke Materi
| Gagasan dari materi | Di mana didemonstrasikan |
|---|---|
| HPC mempercepat pengolahan data besar | `ml/03_hpc_benchmark.py`: pelatihan, cross-validation, dan skoring 1 juta sel grid dengan jumlah worker berbeda |
| Keberhasilan bergantung pada kualitas data | `01_generate_data.py` (nilai hilang), imputasi di pipeline, validasi rentang input di API dan Laravel |
| Infrastruktur komputasi memadai | Benchmark speedup vs jumlah core |
| Kerja sama lintas bidang | Pipeline ML (Python) + aplikasi web (Laravel) |
| Hasil untuk pengambilan keputusan | Level risiko + saran + catatan rujukan ke BMKG/BPBD |

## 4. Cara Menjalankan
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_all.py        # generate data, latih model, benchmark HPC, uji API
python ml/app.py         # jalankan API di http://127.0.0.1:5000
```
Contoh pemanggilan API:
```bash
curl -X POST http://127.0.0.1:5000/predict -H "Content-Type: application/json" -d '{"curah_hujan_mm":120,"hujan_3hari_mm":260,"hujan_7hari_mm":330,"prakiraan_hujan_besok_mm":90,"tinggi_muka_air_cm":480,"kelembapan_tanah_persen":98,"elevasi_m":3,"jarak_sungai_m":60,"drainase_skor":1,"bulan":1}'
```
Antarmuka web Laravel: lihat `laravel/README.md`. File model (`models/*.joblib`) tidak disimpan di Git karena
bergantung versi library; buat dengan `python run_all.py`.

## 5. Data dan Desain Eksperimen
21.912 baris harian, 12 zona, 2020-2024. Label: **banjir besok** (ya/tidak). Prevalensi keseluruhan 5,0%, tetapi
berbeda tiap tahun (2020: 7,3%; 2021: 6,0%; 2022: 4,0%; 2023: 5,1%; 2024: 2,6%).

- **Split berdasarkan waktu:** latih 2020-2022, validasi 2023, uji 2024 (meniru penggunaan nyata: memprediksi masa depan).
- Fitur `prakiraan_hujan_besok_mm` mensimulasikan prakiraan cuaca dengan galat. Ia tersedia pada hari prediksi,
  jadi bukan kebocoran data; tanpa fitur ini model hanya bisa menebak dari kondisi yang sudah terjadi.
- Model dipilih berdasarkan PR-AUC **validasi**, bukan data uji.

## 6. Hasil (data uji 2024, prevalensi banjir 2,6%)

| Model | Ambang | Accuracy | Precision | Recall | F1 | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|---|---|
| Baseline (selalu "tidak banjir") | - | 0,974 | 0,000 | 0,000 | 0,000 | 0,026 | 0,500 |
| Logistic Regression | 0,50 | 0,945 | 0,298 | 0,841 | 0,440 | 0,574 | 0,975 |
| Logistic Regression | 0,87 (dari validasi) | 0,976 | 0,531 | 0,611 | 0,568 | 0,574 | 0,975 |
| Random Forest | 0,50 | 0,973 | 0,484 | 0,655 | 0,556 | 0,530 | 0,971 |
| Random Forest | 0,53 (dari validasi) | 0,974 | 0,497 | 0,628 | 0,555 | 0,530 | 0,971 |
| **HistGradientBoosting** (terpilih) | 0,50 | 0,949 | 0,320 | 0,867 | 0,468 | 0,591 | 0,978 |
| **HistGradientBoosting** (terpilih) | 0,84 (dari validasi) | 0,974 | 0,496 | 0,593 | 0,540 | 0,591 | 0,978 |

Fitur paling berpengaruh (permutation importance): prakiraan hujan besok (0,447), akumulasi hujan 3 hari (0,094),
akumulasi 7 hari (0,076), kelembapan tanah (0,066), elevasi (0,054).

### Pembelajaran
1. **Akurasi menyesatkan lagi.** Model yang selalu menjawab "tidak banjir" mencapai akurasi 97,4% tetapi tidak
   pernah mendeteksi banjir. Untuk peringatan dini, recall dan precision jauh lebih bermakna.
2. **Ambang keputusan bukan angka sakral, dan tidak otomatis berpindah antar waktu.** Ambang dipilih agar recall
   validasi (2023) mencapai 0,80, tetapi pada 2024 recall turun menjadi 0,59-0,63 karena proporsi banjir
   berubah (5,1% menjadi 2,6%). Ambang 0,50 justru memberi recall 0,87 untuk model terpilih, dengan harga
   precision lebih rendah (0,32). Sistem nyata perlu memantau dan mengkalibrasi ulang secara berkala, dan
   memilih trade-off berdasarkan biaya salah-alarm vs banjir yang terlewat.
3. **Split acak terlalu optimistis, tetapi di sini selisihnya kecil.** Random Forest: ROC-AUC 0,985 (split acak)
   vs 0,971 (split waktu). Selisih PR-AUC yang besar (0,783 vs 0,530) sebagian besar disebabkan perbedaan
   prevalensi, jadi ROC-AUC lebih adil untuk membandingkan keduanya.
4. **Model sederhana kompetitif.** Logistic Regression hampir setara model berbasis pohon (ROC-AUC 0,975 vs
   0,978), sejalan dengan pesan "metode kompleks belum tentu terbaik".

## 7. Eksperimen HPC (paralelisme pada satu mesin)
`ml/03_hpc_benchmark.py` mengukur waktu dengan 1, 2, 4, ... worker (sesuai jumlah core) untuk: (a) pelatihan Random
Forest 300 pohon, (b) cross-validation 5-fold yang diparalelkan antar fold, (c) skoring 1 juta sel grid.
Hasil tersimpan di `results/hasil_benchmark_hpc.csv` dan grafik `results/speedup_hpc.png`.

**Catatan jujur:** lingkungan tempat kode ini dibuat hanya memiliki **1 core**, sehingga speedup tidak dapat
diukur di sana (waktu 1 worker: pelatihan 5,5 detik, cross-validation 8,0 detik, skoring 1 juta baris 3,5 detik).
Jalankan di mesin multi-core Anda (misalnya Codespaces 2 core) dan isi tabel berikut dari hasil Anda:

| Eksperimen | 1 worker (detik) | N worker (detik) | Speedup |
|---|---|---|---|
| Latih Random Forest | ... | ... | ... |
| Cross-validation 5-fold | ... | ... | ... |
| Skoring 1 juta sel grid | ... | ... | ... |

Yang umumnya terlihat: speedup **kurang dari linear** karena bagian kode yang tidak paralel (hukum Amdahl),
overhead pembagian kerja, dan persaingan memori. HPC sungguhan (klaster, GPU, MPI) memperluas gagasan yang
sama ke ratusan atau ribuan core; eksperimen ini hanya ilustrasi skala kecil.

## 8. Keterbatasan
- Data sintetis; pola banjir sederhana dan tidak mencakup hidrologi sungguhan (aliran sungai, pasang surut, topografi detail).
- Prakiraan hujan disimulasikan, bukan dari model cuaca nyata.
- Evaluasi hanya satu tahun uji (2024) dengan hanya 12 zona; hasilnya bervariasi antar tahun.
- Bagian Laravel belum diuji jalan oleh pembuat (lihat `laravel/README.md`).
- Bukan sistem peringatan dini resmi.

## 9. Pengembangan Lanjutan
- Ganti data sintetis dengan data nyata: curah hujan dan prakiraan (BMKG, CHIRPS, NASA POWER), kejadian banjir (BNPB DIBI/BPBD), elevasi (DEMNAS/SRTM).
- Tambah pemantauan drift dan kalibrasi probabilitas; antrean (queue) Laravel untuk prediksi batch.
- Peta risiko per zona; skoring grid besar dengan paralelisme proses, Dask, atau GPU.

## Struktur Repo
```
├── README.md
├── requirements.txt
├── run_all.py
├── ml/
│   ├── common.py              # path, daftar fitur, rentang validasi
│   ├── 01_generate_data.py    # data hidrometeorologi sintetis
│   ├── 02_train_evaluate.py   # split waktu, model, ambang, importance
│   ├── 03_hpc_benchmark.py    # speedup paralel
│   ├── 04_smoke_test_api.py   # uji API
│   ├── predictor.py           # validasi, prediksi, level risiko
│   └── app.py                 # API Flask
├── laravel/                   # file untuk proyek Laravel (belum diuji jalan)
├── data/                      # hidrometeorologi.csv (hasil generate)
├── results/                   # tabel metrik, grafik
└── models/                    # model terlatih (dibuat saat run_all, tidak di Git)
```

## Lisensi & Sumber
Kode: MIT. Gagasan: ringkasan Sesi 2 (High Performance Computing), Informatics Practitioner Lecture Series.
