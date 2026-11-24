---
name: crypto-journal
description: >-
  Jurnal trading kripto. Mencatat entry, stop, qty, lalu menutup trade dan
  menghitung R, win rate, serta total R. Hanya catatan, tidak menyentuh akun
  exchange. Pakai saat pengguna bilang "catat trade", "jurnal", "tutup trade",
  "statistik trading saya", "trading journal", atau setelah entry/exit.
argument-hint: "add|close|list|stats"
---

# crypto-journal

```bash
python3 "${CLAUDE_SKILL_DIR}/journal.py" add --symbol BTCUSDT --side long --entry 62000 --stop 60500 --qty 0.02 --note "breakout 4h"
python3 "${CLAUDE_SKILL_DIR}/journal.py" close --id 1 --exit 64000 --note "kena target"
python3 "${CLAUDE_SKILL_DIR}/journal.py" list
python3 "${CLAUDE_SKILL_DIR}/journal.py" stats
```

Data di `crypto/journal.json`. Setelah beberapa trade, bantu pengguna membaca pola (setup mana yang untung, apakah stop dipatuhi),
dengan jujur menyebut jumlah sampelnya. Angka PnL belum termasuk biaya.
