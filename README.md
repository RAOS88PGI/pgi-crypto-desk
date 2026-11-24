# PGI Crypto Desk

Kumpulan 5 skill Claude untuk trading kripto: **pindai → tentukan stop → hitung ukuran posisi → uji → catat**.
Memakai data publik Binance (tanpa API key). Tidak ada satu pun skill yang bisa mengirim order ke akun kamu.

Konsepnya terinspirasi [day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill) (MIT) milik Jake Schincariol,
tetapi seluruh kodenya ditulis ulang untuk kripto.

| Perintah | Fungsi |
|---|---|
| `/crypto-scanner` | Pindai puluhan koin USDT: breakout, oversold, pantulan RSI, lonjakan volume, golden cross MACD (1D/4H/1W/bulanan) |
| `/crypto-exit` | Stop dan target berbasis ATR (1R/2R/3R) |
| `/crypto-size` | Ukuran posisi + cek risiko, hasil PASS atau BLOCK (risiko per trade, R:R, batas rugi harian, leverage) |
| `/crypto-backtest` | Uji aturan di data historis dengan biaya, slippage, dan simulasi acak 2000x dari trade yang ada |
| `/crypto-journal` | Catat trade, hitung R, win rate, total R |

## Cara pakai paling mudah
Di chat Claude: *"Pakai repo pgi-crypto-desk saya. Scan koin untuk setup breakout di 4H, lalu hitung posisinya untuk modal 1000 USDT."*

Atau dari komputer sendiri (Python 3.8+, tanpa instalasi tambahan):
```
python3 crypto-scanner/scan.py --tf 1M
python3 crypto-size/size.py --account 1000 --entry 100 --stop 95 --target 112
python3 crypto-backtest/backtest.py --symbol BTCUSDT --tf 1d --rule breakout
```
Pasang sebagai skill Claude Code: salin folder `crypto-*` ke `~/.claude/skills/`.

Tes: `python3 -m unittest discover -s tests -v` (offline, memakai data sintetis).

## Batasan (baca ini)
- Hasil pindai adalah chart yang cocok aturan, bukan rekomendasi beli. Ini bukan nasihat keuangan.
- Backtest memakai aturan sederhana, long only, dan data masa lalu. Hasil bagus belum tentu berulang.
- Data dari endpoint publik Binance; bisa terlambat atau terkena batas permintaan. Jaringan tertentu memblokir Binance.
- Kamu yang bertanggung jawab atas setiap order. Mulai dengan akun demo atau nominal sangat kecil.

## Otomatis lewat email (GitHub Actions)
`/crypto-alerts` mengirim email ke prastyaglobalindonesia@gmail.com: golden cross MACD bulanan (tanggal 1, 08:05 WIB) dan pindai harian (08:05 WIB).
Setup satu kali:
1. Di akun Gmail pengirim, aktifkan verifikasi 2 langkah, lalu buat **App Password** (Akun Google, Keamanan, Sandi aplikasi).
2. Di repo ini: **Settings, Secrets and variables, Actions, New repository secret**. Isi `GMAIL_USER` (alamat Gmail) dan `GMAIL_APP_PASSWORD` (sandi aplikasi 16 huruf). Opsional `MAIL_TO` jika penerima berbeda.
3. Tab **Actions**, pilih *Crypto alerts*, **Run workflow**, mode `daily`, untuk mencoba sekali.
Jika email berjudul "GAGAL", Binance memblokir server GitHub; beri tahu Claude untuk memakai sumber data cadangan.
