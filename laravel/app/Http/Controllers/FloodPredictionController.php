<?php

namespace App\Http\Controllers;

use App\Models\FloodPrediction;
use App\Services\FloodPredictionService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;
use Throwable;

class FloodPredictionController extends Controller
{
    public function __construct(private FloodPredictionService $service)
    {
    }

    public function index(): View
    {
        return view('flood.index', [
            'riwayat' => FloodPrediction::latest()->limit(10)->get(),
        ]);
    }

    public function store(Request $request): RedirectResponse
    {
        // Rentang disamakan dengan validasi di API Python (ml/common.py)
        $data = $request->validate([
            'curah_hujan_mm'           => ['required', 'numeric', 'between:0,500'],
            'hujan_3hari_mm'           => ['required', 'numeric', 'between:0,1000'],
            'hujan_7hari_mm'           => ['required', 'numeric', 'between:0,2000'],
            'prakiraan_hujan_besok_mm' => ['required', 'numeric', 'between:0,500'],
            'tinggi_muka_air_cm'       => ['required', 'numeric', 'between:0,1500'],
            'kelembapan_tanah_persen'  => ['required', 'numeric', 'between:0,100'],
            'elevasi_m'                => ['required', 'numeric', 'between:-5,3000'],
            'jarak_sungai_m'           => ['required', 'numeric', 'between:0,20000'],
            'drainase_skor'            => ['required', 'integer', 'between:1,5'],
            'bulan'                    => ['required', 'integer', 'between:1,12'],
        ]);

        try {
            $hasil = $this->service->predict($data);
        } catch (Throwable $e) {
            return back()->withInput()->withErrors(['api' => $e->getMessage()]);
        }

        FloodPrediction::create([
            'input'       => $data,
            'probabilitas' => $hasil['probabilitas'],
            'level'       => $hasil['level'],
        ]);

        return back()->withInput()->with('hasil', $hasil);
    }
}
