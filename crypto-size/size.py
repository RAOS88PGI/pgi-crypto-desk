#!/usr/bin/env python3
"""Hitung ukuran posisi + cek risiko (PASS / BLOCK). Hanya library standar.

  python3 size.py --account 1000 --entry 100 --stop 95 --target 112
  python3 size.py --account 5000 --risk-pct 1 --entry 62000 --stop 60500 --side long
Kode keluar: 0 = PASS, 2 = BLOCK.
"""
import argparse
import json
import sys


def calc(account, entry, stop, target=None, side="long", risk_pct=1.0, fee_pct=0.1, leverage=1.0,
         max_risk_pct=2.0, min_rr=1.5, day_loss=0.0, max_daily_loss_pct=3.0):
    fee = fee_pct / 100.0
    blocks, warns = [], []
    if side not in ("long", "short"):
        raise ValueError("side harus long atau short")
    wrong = (stop >= entry) if side == "long" else (stop <= entry)
    if wrong:
        blocks.append("Stop berada di sisi yang salah untuk posisi %s." % side)
        return {"verdict": "BLOCK", "blocks": blocks, "warnings": warns}
    risk_amt = account * risk_pct / 100.0
    unit_risk = abs(entry - stop) + fee * entry + fee * stop  # selisih harga + biaya masuk & keluar di stop
    qty = risk_amt / unit_risk
    notional = qty * entry
    capped = False
    if notional > account * leverage:
        qty = account * leverage / entry
        notional = qty * entry
        capped = True
    max_loss = qty * unit_risk
    actual_risk_pct = max_loss / account * 100
    out = {"side": side, "qty": qty, "notional": notional, "max_loss": max_loss,
           "risk_pct_actual": actual_risk_pct, "capped_by_leverage": capped,
           "stop_distance_pct": abs(entry - stop) / entry * 100}
    if capped:
        warns.append("Ukuran posisi dipotong karena melebihi modal x leverage (%.1fx)." % leverage)
    if out["stop_distance_pct"] < 0.3:
        warns.append("Stop sangat dekat (%.2f%%), mudah kena noise & biaya." % out["stop_distance_pct"])
    if actual_risk_pct > max_risk_pct:
        blocks.append("Risiko %.2f%% melebihi batas %.2f%% per trade." % (actual_risk_pct, max_risk_pct))
    if (day_loss + max_loss) / account * 100 > max_daily_loss_pct:
        blocks.append("Rugi hari ini + risiko trade ini melewati batas harian %.1f%%." % max_daily_loss_pct)
    if target is not None:
        good = (target > entry) if side == "long" else (target < entry)
        if not good:
            blocks.append("Target berada di sisi yang salah.")
        else:
            reward = abs(target - entry) - fee * entry - fee * target
            out["net_rr"] = reward / unit_risk
            out["target_gain"] = qty * reward
            if out["net_rr"] < min_rr:
                blocks.append("R:R bersih %.2f di bawah minimum %.2f." % (out["net_rr"], min_rr))
    else:
        warns.append("Tidak ada target, R:R tidak diperiksa.")
    out.update(verdict="BLOCK" if blocks else "PASS", blocks=blocks, warnings=warns)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Ukuran posisi & cek risiko")
    ap.add_argument("--account", type=float, required=True, help="modal (USDT)")
    ap.add_argument("--entry", type=float, required=True)
    ap.add_argument("--stop", type=float, required=True)
    ap.add_argument("--target", type=float)
    ap.add_argument("--side", default="long", choices=["long", "short"])
    ap.add_argument("--risk-pct", type=float, default=1.0, help="risiko per trade, %% modal (default 1)")
    ap.add_argument("--fee-pct", type=float, default=0.1, help="biaya per sisi, %% (Binance spot 0.1)")
    ap.add_argument("--leverage", type=float, default=1.0, help="leverage maksimum (spot = 1)")
    ap.add_argument("--max-risk-pct", type=float, default=2.0)
    ap.add_argument("--min-rr", type=float, default=1.5)
    ap.add_argument("--day-loss", type=float, default=0.0, help="rugi hari ini sejauh ini (USDT)")
    ap.add_argument("--max-daily-loss-pct", type=float, default=3.0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = calc(a.account, a.entry, a.stop, a.target, a.side, a.risk_pct, a.fee_pct, a.leverage,
             a.max_risk_pct, a.min_rr, a.day_loss, a.max_daily_loss_pct)
    if a.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print("HASIL: %s" % r["verdict"])
        if "qty" in r:
            print("Jumlah koin : %.6g" % r["qty"])
            print("Nilai posisi: %.2f USDT" % r["notional"])
            print("Rugi maks   : %.2f USDT (%.2f%% modal) jika stop kena" % (r["max_loss"], r["risk_pct_actual"]))
            if "net_rr" in r:
                print("R:R bersih  : %.2f   Potensi untung: %.2f USDT" % (r["net_rr"], r["target_gain"]))
        for b in r["blocks"]:
            print("BLOCK: " + b)
        for w in r["warnings"]:
            print("Catatan: " + w)
    return 0 if r["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
