#!/usr/bin/env python3
"""Pemindai koin: cari setup di puluhan koin USDT Binance. Hanya library standar.

  python3 scan.py                       # 1D, 60 koin paling ramai
  python3 scan.py --tf 1M               # bulanan (golden cross MACD bulanan)
  python3 scan.py --tf 4h --top 100
  python3 scan.py --symbols BTCUSDT,ETHUSDT,SOLUSDT
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cryptolib as C  # noqa: E402

SETUP_NAMES = {
    "breakout": "Breakout (tutup di atas high 20 candle)",
    "oversold": "Oversold (RSI<30)",
    "bounce": "Pantulan dari oversold (RSI naik lewat 30)",
    "volume": "Lonjakan volume (>2x rata-rata) + candle hijau",
    "macd_cross": "MACD golden cross (garis MACD potong naik sinyal)",
}


def universe(min_vol, top, offline=None):
    if offline:
        with open(os.path.join(offline, "universe.json"), encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = C.http_json("/api/v3/ticker/24hr")
    rows = []
    for d in data:
        s = d["symbol"]
        if not s.endswith("USDT") or s[:-4] in C.STABLES:
            continue
        qv = float(d["quoteVolume"])
        if qv >= min_vol:
            rows.append((s, qv))
    rows.sort(key=lambda x: -x[1])
    return [s for s, _ in rows[:top]]


def analyze(k):
    """Cek setup pada candle terakhir yang sudah selesai. None jika data kurang."""
    if len(k) < 40:
        return None
    c = [x["c"] for x in k]
    r = C.rsi(c, 14)
    line, sig, _ = C.macd(c)
    found = []
    if c[-1] > max(x["h"] for x in k[-21:-1]):
        found.append("breakout")
    if r[-1] is not None and r[-1] < 30:
        found.append("oversold")
    recent = [v for v in r[-4:-1] if v is not None]
    if recent and min(recent) < 30 <= r[-1]:
        found.append("bounce")
    avg_v = sum(x["v"] for x in k[-21:-1]) / 20
    if avg_v > 0 and k[-1]["v"] > 2 * avg_v and k[-1]["c"] > k[-1]["o"]:
        found.append("volume")
    if None not in (line[-1], line[-2], sig[-1], sig[-2]) and line[-2] <= sig[-2] and line[-1] > sig[-1]:
        found.append("macd_cross")
    chg = (c[-1] / c[-2] - 1) * 100 if c[-2] else 0.0
    return {"price": c[-1], "change_pct": round(chg, 2), "rsi": round(r[-1], 1) if r[-1] is not None else None,
            "macd_below_zero": bool(line[-1] is not None and line[-1] < 0), "setups": found}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pemindai setup kripto (Binance)")
    ap.add_argument("--tf", default="1d", help="1h, 4h, 1d, 1w, 1M (default 1d)")
    ap.add_argument("--top", type=int, default=60, help="jumlah koin teramai yang dipindai")
    ap.add_argument("--min-volume", type=float, default=20_000_000, help="volume 24 jam minimum (USDT)")
    ap.add_argument("--symbols", help="daftar manual, pisah koma, mis. BTCUSDT,ETHUSDT")
    ap.add_argument("--include-open", action="store_true", help="ikutkan candle yang belum selesai")
    ap.add_argument("--only", help="tampilkan hanya setup ini: " + ",".join(SETUP_NAMES))
    ap.add_argument("--out", default="crypto/watchlist.json")
    ap.add_argument("--offline", help="folder data uji (untuk tes)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    symbols = [s.strip().upper() for s in a.symbols.split(",")] if a.symbols else universe(a.min_volume, a.top, a.offline)
    limit = 60 if a.tf == "1M" else 150
    hits, errors, scanned = [], 0, 0
    for s in symbols:
        try:
            k = C.fetch_klines(s, a.tf, limit, a.offline, closed_only=not a.include_open)
        except Exception:
            errors += 1
            continue
        res = analyze(k)
        if res is None:
            continue
        scanned += 1
        if a.only:
            res["setups"] = [x for x in res["setups"] if x == a.only]
        if res["setups"]:
            hits.append(dict(symbol=s, **res))
        if not a.offline:
            time.sleep(0.08)
    hits.sort(key=lambda h: -len(h["setups"]))
    payload = {"tf": a.tf, "scanned": scanned, "errors": errors, "hits": hits}
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    if a.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return payload
    print("Dipindai %d koin (timeframe %s), %d punya setup, %d gagal diambil.\n" % (scanned, a.tf, len(hits), errors))
    for h in hits:
        print("%-12s harga %-12s 24c %+6.2f%%  RSI %-5s  %s" % (
            h["symbol"], C.fmt_price(h["price"]), h["change_pct"], h["rsi"], ", ".join(h["setups"])))
    print("\nIngat: ini daftar chart yang cocok dengan aturan, BUKAN daftar beli. Hasil tersimpan di %s" % a.out)
    return payload


if __name__ == "__main__":
    main()
