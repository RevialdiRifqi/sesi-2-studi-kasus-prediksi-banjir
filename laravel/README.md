# Bagian Laravel (antarmuka web)

> **Status:** kode Laravel di folder ini **belum diuji jalan** oleh pembuatnya (lingkungan pembuatan
> tidak memiliki PHP). Bagian Python/API sudah diuji (`python run_all.py`). Jalankan langkah di bawah dan
> perbaiki bila ada penyesuaian versi Laravel.

Folder ini bukan proyek Laravel utuh, melainkan file yang disalin ke proyek Laravel 11/12 baru.

## Langkah
1. Buat proyek baru: `composer create-project laravel/laravel banjir-web`
2. Salin ke proyek tersebut (struktur folder sama):
   - `app/Services/FloodPredictionService.php`
   - `app/Http/Controllers/FloodPredictionController.php`
   - `app/Models/FloodPrediction.php`
   - `database/migrations/2026_10_20_000000_create_flood_predictions_table.php`
   - `resources/views/flood/index.blade.php`
3. Tambahkan isi `snippets/routes_web.php.txt` ke `routes/web.php` dan `snippets/config_services.php.txt` ke `config/services.php`.
4. Di `.env` proyek Laravel tambahkan: `FLOOD_API_URL=http://127.0.0.1:5000`
5. `php artisan migrate`
6. Jalankan API Python di terminal lain (dari root repo): `python ml/app.py`
7. `php artisan serve`, lalu buka `http://127.0.0.1:8000/banjir`

## Alur
Browser → Laravel (validasi + simpan riwayat) → HTTP POST `/predict` → Flask + model scikit-learn → hasil JSON → ditampilkan.
