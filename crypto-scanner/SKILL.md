---
name: crypto-scanner
description: >-
  Pemindai koin kripto. Memindai puluhan koin USDT di Binance untuk mencari
  setup: breakout, oversold, pantulan RSI, lonjakan volume, dan golden cross
  MACD (termasuk bulanan). Pakai saat pengguna bilang "scan koin", "cari
  setup", "koin apa yang breakout", "golden cross MACD bulanan", "oversold",
  "scan crypto", "what is breaking out", atau di awal sesi analisa harian.
argument-hint: "[--tf 1d|4h|1w|1M] [--top N] [--symbols BTCUSDT,ETHUSDT]"
---

# crypto-scanner

Membaca data publik Binance (tanpa API key) dan menandai koin yang cocok dengan aturan. Itu saja:
daftar chart yang cocok aturan, **bukan daftar beli**.

```bash
python3 "${CLAUDE_SKILL_DIR}/scan.py"                      # 1D, 60 koin teramai
python3 "${CLAUDE_SKILL_DIR}/scan.py" --tf 1M              # golden cross MACD bulanan
python3 "${CLAUDE_SKILL_DIR}/scan.py" --tf 4h --top 100 --only breakout
python3 "${CLAUDE_SKILL_DIR}/scan.py" --symbols BTCUSDT,SOLUSDT --json
```

Setup: `breakout`, `oversold`, `bounce`, `volume`, `macd_cross`. Hasil disimpan di `crypto/watchlist.json`.
Hanya candle yang sudah selesai dipakai (kecuali `--include-open`).

Cara menjawab pengguna: tampilkan tabel singkat (koin, harga, RSI, setup), sebut jumlah koin yang dipindai,
dan ingatkan bahwa langkah berikut adalah `/crypto-exit` (stop & target) lalu `/crypto-size` (ukuran posisi).
Jika ada koin gagal diambil (`errors`), sebutkan. Jika semua gagal, kemungkinan jaringan memblokir Binance:
katakan terus terang dan jangan mengarang hasil.
