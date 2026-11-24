#!/usr/bin/env python3
"""Jurnal trading sederhana (catatan saja, tidak menyentuh akun mana pun). Library standar.

  python3 journal.py add --symbol BTCUSDT --side long --entry 62000 --stop 60500 --qty 0.02 --note "breakout 4h"
  python3 journal.py close --id 1 --exit 64000 --note "kena target"
  python3 journal.py list
  python3 journal.py stats
Data disimpan di crypto/journal.json
"""
import argparse
import datetime
import json
import os
import sys

PATH = "crypto/journal.json"


def load(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"trades": []}


def save(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def r_multiple(t):
    risk = abs(t["entry"] - t["stop"])
    if risk == 0 or t.get("exit") is None:
        return None
    sgn = 1 if t["side"] == "long" else -1
    return sgn * (t["exit"] - t["entry"]) / risk


def stats(trades):
    closed = [t for t in trades if t.get("exit") is not None]
    if not closed:
        return {"closed": 0, "open": len(trades)}
    rs = [r_multiple(t) for t in closed]
    pnl = [(t["exit"] - t["entry"]) * t["qty"] * (1 if t["side"] == "long" else -1) for t in closed]
    wins = [r for r in rs if r > 0]
    return {"closed": len(closed), "open": len(trades) - len(closed), "win_rate": len(wins) / len(closed) * 100,
            "avg_r": sum(rs) / len(rs), "total_r": sum(rs), "pnl_usdt_before_fees": sum(pnl)}


def main(argv=None, path=None):
    path = path or PATH
    ap = argparse.ArgumentParser(description="Jurnal trading")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a_ = sub.add_parser("add")
    a_.add_argument("--symbol", required=True)
    a_.add_argument("--side", default="long", choices=["long", "short"])
    a_.add_argument("--entry", type=float, required=True)
    a_.add_argument("--stop", type=float, required=True)
    a_.add_argument("--qty", type=float, required=True)
    a_.add_argument("--target", type=float)
    a_.add_argument("--note", default="")
    c_ = sub.add_parser("close")
    c_.add_argument("--id", type=int, required=True)
    c_.add_argument("--exit", type=float, required=True)
    c_.add_argument("--note", default="")
    sub.add_parser("list")
    sub.add_parser("stats")
    a = ap.parse_args(argv)
    data = load(path)
    if a.cmd == "add":
        t = {"id": len(data["trades"]) + 1, "opened": datetime.datetime.now().isoformat(timespec="minutes"),
             "symbol": a.symbol.upper(), "side": a.side, "entry": a.entry, "stop": a.stop, "qty": a.qty,
             "target": a.target, "note": a.note, "exit": None}
        data["trades"].append(t)
        save(path, data)
        print("Tercatat trade #%d %s %s" % (t["id"], t["side"], t["symbol"]))
    elif a.cmd == "close":
        t = next((x for x in data["trades"] if x["id"] == a.id), None)
        if t is None or t.get("exit") is not None:
            sys.exit("Trade tidak ditemukan atau sudah ditutup.")
        t["exit"], t["closed"] = a.exit, datetime.datetime.now().isoformat(timespec="minutes")
        t["note"] = (t["note"] + " | " + a.note).strip(" |")
        save(path, data)
        print("Trade #%d ditutup: %+.2fR" % (t["id"], r_multiple(t)))
    elif a.cmd == "list":
        for t in data["trades"]:
            r = r_multiple(t)
            print("#%d %-9s %-5s masuk %s stop %s %s %s" % (
                t["id"], t["symbol"], t["side"], t["entry"], t["stop"],
                "KELUAR %s (%+.2fR)" % (t["exit"], r) if r is not None else "(terbuka)", t["note"]))
    else:
        print(json.dumps(stats(data["trades"]), indent=2))
    return data


if __name__ == "__main__":
    main()
