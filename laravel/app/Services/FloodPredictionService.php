<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use RuntimeException;

class FloodPredictionService
{
    /**
     * Kirim data ke API Python (Flask) dan kembalikan hasil prediksi.
     *
     * @param  array<string, mixed>  $data
     * @return array<string, mixed>
     */
    public function predict(array $data): array
    {
        $baseUrl = rtrim(config('services.flood_api.url'), '/');

        $response = Http::timeout(10)
            ->acceptJson()
            ->post($baseUrl.'/predict', $data);

        if ($response->failed()) {
            $detail = $response->json('detail');
            $pesan = is_array($detail) ? implode('; ', $detail) : ($response->json('error') ?? 'API prediksi tidak merespons.');

            throw new RuntimeException($pesan);
        }

        return $response->json();
    }
}
