#!/usr/bin/env python3
"""Mesin waktu: uji aturan pada data historis, lengkap dengan biaya & slippage.
Hanya library standar Python.

  python3 backtest.py --symbol BTCUSDT --tf 1d --rule breakout --bars 1000
  python3 backtest.py --symbol ETHUSDT --tf 4h --rule macd_cross --stop-atr 2 --rr 2
Aturan: breakout | bounce | macd_cross.  Hanya posisi LONG, satu posisi pada satu waktu.
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cryptolib as C  # noqa: E402


def signals(k, rule):
    """Daftar indeks candle yang memberi sinyal (berdasarkan harga tutup candle itu)."""
    c = [x["c"] for x in k]
    out = []
    if rule == "breakout":
        for i in range(20, len(k)):
            if c[i] > max(x["h"] for x in k[i - 20:i]):
                out.append(i)
    elif rule == "bounce":
        r = C.rsi(c, 14)
        for i in range(18, len(k)):
            prev = [v for v in r[i - 3:i] if v is not None]
            if prev and r[i] is not None and min(prev) < 30 <= r[i]:
                out.append(i)
    elif rule == "macd_cross":
        line, sig, _ = C.macd(c)
        for i in range(1, len(k)):
            if None not in (line[i], line[i - 1], sig[i], sig[i - 1]) and line[i - 1] <= sig[i - 1] and line[i] > sig[i]:
                out.append(i)
    else:
        raise ValueError("aturan tidak dikenal: %s" % rule)
    return out


def simulate_trade(k, start, stop, target, max_hold):
    """Mulai dari candle `start` (candle masuk). Jika stop & target kena di candle yang sama, stop dianggap
    kena duluan (konservatif). Gap di bawah stop keluar di harga open. Return (exit_price, alasan, indeks)."""
    last = min(start + max_hold, len(k) - 1)
    for j in range(start, last + 1):
        b = k[j]
        if b["o"] <= stop:
            return b["o"], "stop (gap)", j
        if b["l"] <= stop:
            return stop, "stop", j
        if b["h"] >= target:
            return target, "target", j
    return k[last]["c"], "waktu", last


def run(k, rule="breakout", stop_atr=2.0, rr=2.0, max_hold=30, fee_pct=0.1, slip_pct=0.05, risk_pct=1.0):
    fee, slip = fee_pct / 100, slip_pct / 100
    atr = C.atr(k, 14)
    sig = signals(k, rule)
    trades, i_sig, idx = [], 0, 0
    next_free = 0
    for i in sig:
        if i < next_free or i + 1 >= len(k) or atr[i] is None:
            continue
        entry = k[i + 1]["o"] * (1 + slip)
        stop = entry - stop_atr * atr[i]
        if stop <= 0:
            continue
        target = entry + rr * (entry - stop)
        px, why, j = simulate_trade(k, i + 1, stop, target, max_hold)
        px_eff = px * (1 - slip)
        ret = px_eff * (1 - fee) / (entry * (1 + fee)) - 1
        risk_frac = (entry - stop) / entry + 2 * fee + slip
        trades.append({"entry_t": k[i + 1]["t"], "entry": entry, "exit": px_eff, "why": why,
                       "bars": j - i, "ret_pct": ret * 100, "r": ret / risk_frac})
        next_free = j + 1
    return trades


def stats(trades, risk_pct=1.0):
    n = len(trades)
    if n == 0:
        return {"n": 0}
    rs = [t["r"] for t in trades]
    wins = [r for r in rs if r > 0]
    eq, peak, mdd = 1.0, 1.0, 0.0
    for r in rs:
        eq *= 1 + risk_pct / 100 * r
        peak = max(peak, eq)
        mdd = max(mdd, (peak - eq) / peak)
    return {"n": n, "win_rate": len(wins) / n * 100, "avg_r": sum(rs) / n,
            "avg_win_r": sum(wins) / len(wins) if wins else 0.0,
            "avg_loss_r": sum(r for r in rs if r <= 0) / max(1, n - len(wins)),
            "total_return_pct": (eq - 1) * 100, "max_dd_pct": mdd * 100}


def monte_carlo(trades, risk_pct=1.0, runs=2000, seed=7):
    rs = [t["r"] for t in trades]
    rng = random.Random(seed)
    finals, dds = [], []
    for _ in range(runs):
        seq = [rng.choice(rs) for _ in rs]  # ambil ulang trade secara acak (bootstrap)
        eq, peak, mdd = 1.0, 1.0, 0.0
        for r in seq:
            eq *= 1 + risk_pct / 100 * r
            peak = max(peak, eq)
            mdd = max(mdd, (peak - eq) / peak)
        finals.append((eq - 1) * 100)
        dds.append(mdd * 100)
    finals.sort()
    dds.sort()
    q = lambda arr, p: arr[int(p * (len(arr) - 1))]
    return {"ret_p5": q(finals, .05), "ret_p50": q(finals, .5), "dd_p50": q(dds, .5), "dd_p95": q(dds, .95)}


def verdict_notes(s, mc_ok):
    notes = []
    if s["n"] < 30:
        notes.append("Hanya %d trade: terlalu sedikit untuk membuktikan apa pun." % s["n"])
    if s["n"] and s["avg_r"] <= 0:
        notes.append("Rata-rata R <= 0 setelah biaya: aturan ini tidak punya keunggulan pada data ini.")
    if s["n"] >= 5 and s["win_rate"] == 100:
        notes.append("Tidak ada trade rugi: curigai data/sampel kecil, bukan keajaiban.")
    notes.append("Hasil masa lalu tidak menjamin masa depan; uji juga di koin & periode lain.")
    return notes


def main(argv=None):
    ap = argparse.ArgumentParser(description="Backtest aturan sederhana (long only)")
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--tf", default="1d")
    ap.add_argument("--rule", default="breakout", choices=["breakout", "bounce", "macd_cross"])
    ap.add_argument("--bars", type=int, default=1000, help="jumlah candle historis")
    ap.add_argument("--stop-atr", type=float, default=2.0)
    ap.add_argument("--rr", type=float, default=2.0, help="target = rr x jarak stop")
    ap.add_argument("--max-hold", type=int, default=30, help="keluar paksa setelah N candle")
    ap.add_argument("--fee-pct", type=float, default=0.1)
    ap.add_argument("--slip-pct", type=float, default=0.05)
    ap.add_argument("--risk-pct", type=float, default=1.0, help="risiko per trade untuk kurva modal")
    ap.add_argument("--offline")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    k = C.fetch_klines(a.symbol, a.tf, a.bars, a.offline)
    trades = run(k, a.rule, a.stop_atr, a.rr, a.max_hold, a.fee_pct, a.slip_pct, a.risk_pct)
    s = stats(trades, a.risk_pct)
    bh = (k[-1]["c"] / k[0]["o"] - 1) * 100
    mc = monte_carlo(trades, a.risk_pct) if s["n"] >= 10 else None
    res = {"symbol": a.symbol.upper(), "tf": a.tf, "rule": a.rule, "bars": len(k), "buy_hold_pct": bh,
           "stats": s, "monte_carlo": mc, "notes": verdict_notes(s, mc is not None) if s["n"] else ["Tidak ada sinyal."]}
    if a.json:
        print(json.dumps(res, indent=2))
        return res
    print("%s %s | aturan: %s | %d candle | biaya %.2f%% + slippage %.2f%% per sisi" % (
        res["symbol"], a.tf, a.rule, len(k), a.fee_pct, a.slip_pct))
    if s["n"]:
        print("Jumlah trade   : %d" % s["n"])
        print("Menang         : %.0f%%   Rata-rata R: %+.2f (menang %+.2f / kalah %+.2f)" % (
            s["win_rate"], s["avg_r"], s["avg_win_r"], s["avg_loss_r"]))
        print("Return (risiko %.1f%%/trade): %+.1f%%   Max drawdown: %.1f%%" % (a.risk_pct, s["total_return_pct"], s["max_dd_pct"]))
        print("Pembanding beli-dan-tahan: %+.1f%%" % bh)
        if mc:
            print("Simulasi 2000x (trade diambil ulang acak): return median %+.1f%% (5%% terburuk %+.1f%%), drawdown median %.1f%% / terburuk 5%% %.1f%%" % (
                mc["ret_p50"], mc["ret_p5"], mc["dd_p50"], mc["dd_p95"]))
    for n in res["notes"]:
        print("- " + n)
    return res


if __name__ == "__main__":
    main()
