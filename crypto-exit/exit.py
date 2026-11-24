#!/usr/bin/env python3
"""Tentukan stop & target berdasarkan volatilitas (ATR). Hanya library standar.

  python3 exit.py --symbol BTCUSDT --tf 4h                 # entry = harga terakhir
  python3 exit.py --symbol SOLUSDT --tf 1d --entry 150 --atr-mult 2.5
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cryptolib as C  # noqa: E402


def plan(k, entry=None, side="long", atr_mult=2.0, swing_bars=10, rrs=(1, 2, 3)):
    a = C.atr(k, 14)[-1]
    if a is None:
        raise ValueError("Data kurang untuk menghitung ATR (butuh >15 candle).")
    entry = entry if entry is not None else k[-1]["c"]
    sgn = 1 if side == "long" else -1
    stop_atr = entry - sgn * atr_mult * a
    recent = k[-swing_bars:]
    swing = min(x["l"] for x in recent) - 0.1 * a if side == "long" else max(x["h"] for x in recent) + 0.1 * a
    risk = abs(entry - stop_atr)
    targets = [{"r": r, "price": entry + sgn * r * risk, "pct": sgn * r * risk / entry * 100} for r in rrs]
    return {"entry": entry, "side": side, "atr": a, "atr_pct": a / entry * 100,
            "stop_atr": stop_atr, "stop_atr_pct": abs(entry - stop_atr) / entry * 100,
            "stop_swing": swing, "stop_swing_pct": abs(entry - swing) / entry * 100, "targets": targets}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Stop & target berbasis ATR")
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--tf", default="4h")
    ap.add_argument("--entry", type=float)
    ap.add_argument("--side", default="long", choices=["long", "short"])
    ap.add_argument("--atr-mult", type=float, default=2.0, help="stop = entry -/+ mult x ATR (default 2)")
    ap.add_argument("--swing-bars", type=int, default=10)
    ap.add_argument("--offline")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    k = C.fetch_klines(a.symbol, a.tf, 200, a.offline)
    p = plan(k, a.entry, a.side, a.atr_mult, a.swing_bars)
    if a.json:
        print(json.dumps(p, indent=2))
        return p
    f = C.fmt_price
    print("%s %s  entry %s  ATR %s (%.2f%%)" % (a.symbol.upper(), a.tf, f(p["entry"]), f(p["atr"]), p["atr_pct"]))
    print("Stop (ATR x%.1f): %s  (jarak %.2f%%)" % (a.atr_mult, f(p["stop_atr"]), p["stop_atr_pct"]))
    print("Stop (swing)   : %s  (jarak %.2f%%)  <- alternatif, di balik low/high terakhir" % (f(p["stop_swing"]), p["stop_swing_pct"]))
    for t in p["targets"]:
        print("Target %dR      : %s  (%+.2f%%)" % (t["r"], f(t["price"]), t["pct"]))
    print("\nPilih SATU stop, lalu hitung ukuran posisinya dengan crypto-size.")
    return p


if __name__ == "__main__":
    main()
