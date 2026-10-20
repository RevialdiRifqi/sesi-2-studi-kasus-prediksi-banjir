"""API Flask untuk prediksi banjir (dikonsumsi oleh aplikasi Laravel).

Jalankan:  python ml/app.py    ->  http://127.0.0.1:5000
"""
from flask import Flask, jsonify, request
from predictor import prediksi, validasi

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Body harus berupa JSON object"), 400
    galat = validasi(payload)
    if galat:
        return jsonify(error="Input tidak valid", detail=galat), 422
    return jsonify(prediksi(payload))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
