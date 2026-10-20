<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Prediksi Potensi Banjir</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 860px; margin: 2rem auto; padding: 0 1rem; color: #1f2937; }
        form { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: .9rem; }
        label { display: flex; flex-direction: column; font-size: .85rem; gap: .25rem; }
        input { padding: .5rem; border: 1px solid #cbd5e1; border-radius: 6px; }
        button { grid-column: 1 / -1; padding: .7rem; background: #0369a1; color: #fff; border: 0; border-radius: 6px; font-size: 1rem; cursor: pointer; }
        .hasil { margin: 1.2rem 0; padding: 1rem; border-radius: 8px; background: #f1f5f9; border-left: 6px solid #0369a1; }
        .Rendah { border-color: #16a34a; } .Sedang { border-color: #ca8a04; }
        .Tinggi { border-color: #ea580c; } .SangatTinggi { border-color: #dc2626; }
        .galat { color: #b91c1c; } table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: .9rem; }
        td, th { padding: .4rem; border-bottom: 1px solid #e2e8f0; text-align: left; }
        small { color: #64748b; }
    </style>
</head>
<body>
    <h1>Prediksi Potensi Banjir Besok</h1>
    <p><small>Informasi awal berbasis model Machine Learning (data latih sintetis untuk demonstrasi).
    Bukan peringatan dini resmi; selalu rujuk BMKG/BPBD.</small></p>

    @if ($errors->any())
        <div class="galat">
            <ul>@foreach ($errors->all() as $e)<li>{{ $e }}</li>@endforeach</ul>
        </div>
    @endif

    @if (session('hasil'))
        @php($h = session('hasil'))
        <div class="hasil {{ str_replace(' ', '', $h['level']) }}">
            <strong>Risiko: {{ $h['level'] }}</strong> (skor model {{ number_format($h['probabilitas'] * 100, 1) }}%)<br>
            {{ $h['saran'] }}<br><small>{{ $h['catatan'] }}</small>
        </div>
    @endif

    <form method="POST" action="{{ route('flood.store') }}">
        @csrf
        @foreach ([
            'curah_hujan_mm' => 'Curah hujan hari ini (mm)',
            'hujan_3hari_mm' => 'Akumulasi hujan 3 hari (mm)',
            'hujan_7hari_mm' => 'Akumulasi hujan 7 hari (mm)',
            'prakiraan_hujan_besok_mm' => 'Prakiraan hujan besok (mm)',
            'tinggi_muka_air_cm' => 'Tinggi muka air sungai (cm)',
            'kelembapan_tanah_persen' => 'Kelembapan tanah (%)',
            'elevasi_m' => 'Elevasi lokasi (m)',
            'jarak_sungai_m' => 'Jarak ke sungai (m)',
            'drainase_skor' => 'Kualitas drainase (1 buruk - 5 baik)',
            'bulan' => 'Bulan (1-12)',
        ] as $nama => $label)
            <label>{{ $label }}
                <input type="number" step="any" name="{{ $nama }}" value="{{ old($nama) }}" required>
            </label>
        @endforeach
        <button type="submit">Prediksi</button>
    </form>

    <h2>Riwayat prediksi</h2>
    <table>
        <tr><th>Waktu</th><th>Level</th><th>Skor</th></tr>
        @forelse ($riwayat as $r)
            <tr><td>{{ $r->created_at->format('d M Y H:i') }}</td><td>{{ $r->level }}</td><td>{{ number_format($r->probabilitas * 100, 1) }}%</td></tr>
        @empty
            <tr><td colspan="3"><small>Belum ada prediksi.</small></td></tr>
        @endforelse
    </table>
</body>
</html>
