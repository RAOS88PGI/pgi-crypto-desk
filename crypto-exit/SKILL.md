---
name: crypto-exit
description: >-
  Stop dan target kripto berbasis volatilitas (ATR). Menentukan stop sebelum
  masuk, plus target 1R/2R/3R. Pakai saat pengguna bilang "stop loss di mana",
  "target berapa", "tentukan stop", "ATR", "exit plan", "take profit",
  atau setelah crypto-scanner menemukan koin.
argument-hint: "--symbol BTCUSDT [--tf 4h] [--entry 62000] [--atr-mult 2]"
---

# crypto-exit

```bash
python3 "${CLAUDE_SKILL_DIR}/exit.py" --symbol BTCUSDT --tf 4h
python3 "${CLAUDE_SKILL_DIR}/exit.py" --symbol SOLUSDT --tf 1d --entry 150 --atr-mult 2.5 --side long
```

Keluaran: ATR, stop berbasis ATR (default 2x), stop alternatif di balik swing low/high terakhir, dan target 1R, 2R, 3R.
Pilih **satu** stop sebelum masuk dan jangan digeser menjauh setelah posisi berjalan. Lanjutkan ke `/crypto-size`
untuk menghitung ukuran posisi dari stop yang dipilih.
