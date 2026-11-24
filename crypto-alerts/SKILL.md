---
name: crypto-alerts
description: >-
  Peringatan otomatis kripto lewat email: golden cross MACD bulanan dan
  pemindaian harian, berjalan terjadwal di GitHub Actions. Pakai saat pengguna
  bilang "alert golden cross", "kirim sinyal ke email", "jadwalkan scan",
  "laporan otomatis", "cek workflow", atau menanyakan hasil peringatan.
argument-hint: "monthly|daily [--send]"
---

# crypto-alerts

```bash
python3 "${CLAUDE_SKILL_DIR}/alert.py" monthly     # tampil saja
python3 "${CLAUDE_SKILL_DIR}/alert.py" daily --send  # kirim email (butuh GMAIL_USER & GMAIL_APP_PASSWORD)
```

Jadwal otomatis ada di `.github/workflows/crypto-alerts.yml` (bulanan tanggal 1 dan harian, 08:05 WIB).
Kunci email disimpan di GitHub: Settings, Secrets and variables, Actions (`GMAIL_USER`, `GMAIL_APP_PASSWORD`, opsional `MAIL_TO`).
**Jangan pernah minta atau menerima kunci/sandi di chat**; arahkan pengguna memasukkannya sendiri di pengaturan GitHub.
Jika email berjudul "GAGAL", artinya Binance tidak bisa dijangkau dari server GitHub; katakan terus terang dan tawarkan sumber data cadangan.
