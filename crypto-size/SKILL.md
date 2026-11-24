---
name: crypto-size
description: >-
  Ukuran posisi dan cek risiko kripto. Menghitung berapa koin yang boleh dibeli
  dari modal, risiko per trade, stop dan target, lengkap dengan biaya Binance,
  lalu memberi PASS atau BLOCK. Pakai saat pengguna bilang "berapa lot",
  "ukuran posisi", "hitung risiko", "position size", "boleh entry nggak",
  "cek risk", atau sebelum entry apa pun.
argument-hint: "--account 1000 --entry 100 --stop 95 [--target 112]"
---

# crypto-size

```bash
python3 "${CLAUDE_SKILL_DIR}/size.py" --account 1000 --entry 100 --stop 95 --target 112
python3 "${CLAUDE_SKILL_DIR}/size.py" --account 5000 --risk-pct 1 --entry 62000 --stop 60500 --day-loss 40
```

Aturan bawaan (bisa diubah lewat opsi): risiko 1% modal per trade, maksimum 2%, R:R bersih minimal 1.5,
batas rugi harian 3%, leverage 1x (spot), biaya 0.1% per sisi. Hasil **BLOCK** jika stop di sisi yang salah,
risiko melebihi batas, R:R terlalu kecil, atau batas rugi harian terlewati. Kode keluar 2 saat BLOCK.

Cara menjawab: tampilkan PASS/BLOCK dulu, lalu jumlah koin, nilai posisi, dan rugi maksimum dalam USDT.
Jika BLOCK, jelaskan alasannya dan jangan membantu mengakali batasnya. Pengguna yang meminta menaikkan
batas risiko perlu diingatkan konsekuensinya. Alat ini hanya menghitung; tidak mengirim order ke mana pun.
