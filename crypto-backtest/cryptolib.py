#!/usr/bin/env python3
"""Fungsi bersama: ambil data Binance (publik, tanpa API key) dan hitung indikator.
Hanya library standar Python. File ini sama persis di tiap folder skill supaya
tiap skill bisa dipakai sendiri-sendiri."""
import json
import os
import time
import urllib.parse
import urllib.request

HOSTS = ("https://data-api.binance.vision", "https://api.binance.com")
UA = "crypto-trader-skill/1.0"
STABLES = {"USDC", "FDUSD", "TUSD", "BUSD", "USDP", "DAI", "USDE", "AEUR", "EUR", "EURI", "XUSD", "USD1", "PAXG"}


def http_json(path, params=None, timeout=20):
    q = urllib.parse.urlencode(params or {})
    last = None
    for host in HOSTS:
        url = host + path + ("?" + q if q else "")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # coba host berikutnya
            last = e
    raise RuntimeError("Gagal mengambil data Binance: %s" % last)


def parse_klines(rows):
    return [{"t": int(r[0]), "o": float(r[1]), "h": float(r[2]), "l": float(r[3]),
             "c": float(r[4]), "v": float(r[5]), "ct": int(r[6]), "qv": float(r[7])} for r in rows]


def fetch_klines(symbol, interval="1d", limit=500, offline=None, closed_only=True):
    """Ambil candle. offline=folder berisi file SIMBOL-interval.json (untuk tes)."""
    symbol = symbol.upper()
    if offline:
        with open(os.path.join(offline, "%s-%s.json" % (symbol, interval)), encoding="utf-8") as f:
            k = parse_klines(json.load(f))
        return k[-limit:] if limit else k
    rows, end, remaining = [], None, limit
    while remaining > 0:
        n = min(1000, remaining)
        params = {"symbol": symbol, "interval": interval, "limit": n}
        if end is not None:
            params["endTime"] = end
        batch = http_json("/api/v3/klines", params)
        if not batch:
            break
        rows = batch + rows
        remaining -= len(batch)
        end = int(batch[0][0]) - 1
        if len(batch) < n:
            break
    k = parse_klines(rows)
    if closed_only and k and k[-1]["ct"] > time.time() * 1000:
        k = k[:-1]  # buang candle yang belum selesai
    return k


# ---------- indikator ----------
def sma(values, n):
    out = [None] * len(values)
    for i in range(n - 1, len(values)):
        w = values[i - n + 1:i + 1]
        if None not in w:
            out[i] = sum(w) / n
    return out


def ema(values, n):
    out = [None] * len(values)
    s = next((i for i, v in enumerate(values) if v is not None), None)
    if s is None or len(values) - s < n:
        return out
    prev = sum(values[s:s + n]) / n
    out[s + n - 1] = prev
    k = 2.0 / (n + 1)
    for i in range(s + n, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(closes, n=14):
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    gains = [max(closes[i] - closes[i - 1], 0) for i in range(1, len(closes))]
    losses = [max(closes[i - 1] - closes[i], 0) for i in range(1, len(closes))]
    ag, al = sum(gains[:n]) / n, sum(losses[:n]) / n

    def val(g, l):
        return 100.0 if l == 0 else 100.0 - 100.0 / (1 + g / l)
    out[n] = val(ag, al)
    for i in range(n, len(gains)):
        ag = (ag * (n - 1) + gains[i]) / n
        al = (al * (n - 1) + losses[i]) / n
        out[i + 1] = val(ag, al)
    return out


def macd(closes, fast=12, slow=26, sig=9):
    ef, es = ema(closes, fast), ema(closes, slow)
    line = [a - b if a is not None and b is not None else None for a, b in zip(ef, es)]
    signal = ema(line, sig)
    hist = [a - b if a is not None and b is not None else None for a, b in zip(line, signal)]
    return line, signal, hist


def atr(klines, n=14):
    out = [None] * len(klines)
    if len(klines) <= n:
        return out
    tr = [klines[0]["h"] - klines[0]["l"]]
    for i in range(1, len(klines)):
        k, pc = klines[i], klines[i - 1]["c"]
        tr.append(max(k["h"] - k["l"], abs(k["h"] - pc), abs(k["l"] - pc)))
    prev = sum(tr[1:n + 1]) / n
    out[n] = prev
    for i in range(n + 1, len(klines)):
        prev = (prev * (n - 1) + tr[i]) / n
        out[i] = prev
    return out


def fmt_price(x):
    return "%.8g" % x
