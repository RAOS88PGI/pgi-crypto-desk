---
name: crypto-backtest
description: >-
  Mesin waktu kripto: menguji aturan (breakout, pantulan RSI, golden cross
  MACD) pada data historis Binance dengan biaya, slippage, stop, target, dan
  simulasi acak 2000x dari trade yang ada. Pakai saat pengguna bilang "backtest", "uji
  strategi", "apakah aturan ini profit", "replay", "winrate strategi ini",
  atau sebelum memakai aturan baru dengan uang sungguhan.
argument-hint: "--symbol BTCUSDT --tf 1d --rule breakout|bounce|macd_cross"
---

# crypto-backtest

```bash
python3 "${CLAUDE_SKILL_DIR}/backtest.py" --symbol BTCUSDT --tf 1d --rule breakout --bars 1000
python3 "${CLAUDE_SKILL_DIR}/backtest.py" --symbol ETHUSDT --tf 4h --rule macd_cross --stop-atr 2 --rr 2 --json
```

Cara kerja: sinyal muncul saat candle tutup, masuk di open candle berikutnya, stop = ATR x pengali, target = RR x jarak stop.
Jika stop dan target kena di candle yang sama, stop dianggap kena duluan. Satu posisi pada satu waktu, hanya long.
Biaya 0.1% dan slippage 0.05% per sisi sudah dihitung.

Cara menjawab: sebut **jumlah trade dulu**, lalu rata-rata R, win rate, return vs max drawdown, dan pembanding beli-dan-tahan.
Di bawah 30 trade, katakan hasilnya belum membuktikan apa pun. Jika rata-rata R <= 0, katakan aturannya tidak punya
keunggulan pada data itu. Jangan menjanjikan hasil masa depan; sarankan uji di koin dan periode lain.
