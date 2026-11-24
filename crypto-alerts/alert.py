#!/usr/bin/env python3
"""Peringatan otomatis lewat email: golden cross MACD bulanan & pemindaian harian.
Hanya library standar. Dipakai oleh GitHub Actions, bisa juga dijalankan manual.

  python3 alert.py monthly            # tampilkan saja (tanpa kirim) bila kunci email belum diisi
  python3 alert.py daily --send       # kirim email
Kunci email dibaca dari variabel lingkungan GMAIL_USER, GMAIL_APP_PASSWORD (jangan ditulis di file/chat).
Penerima: MAIL_TO (default prastyaglobalindonesia@gmail.com).
"""
import argparse
import datetime
import os
import smtplib
import ssl
import sys
import time
from email.message import EmailMessage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "crypto-scanner"))
import cryptolib as C  # noqa: E402
import scan  # noqa: E402

DEFAULT_TO = "prastyaglobalindonesia@gmail.com"
LABEL = {"breakout": "breakout", "oversold": "oversold", "bounce": "pantulan RSI",
         "volume": "lonjakan volume", "macd_cross": "golden cross MACD"}


def collect(tf, top, only=None, offline=None):
    symbols = scan.universe(20_000_000, top, offline)
    limit = 60 if tf == "1M" else 150
    hits, scanned, errors = [], 0, 0
    for s in symbols:
        try:
            k = C.fetch_klines(s, tf, limit, offline, closed_only=True)
        except Exception:
            errors += 1
            continue
        r = scan.analyze(k)
        if r is None:
            continue
        scanned += 1
        if only:
            r["setups"] = [x for x in r["setups"] if x in only]
        if r["setups"]:
            hits.append(dict(symbol=s, **r))
        if not offline:
            time.sleep(0.08)
    hits.sort(key=lambda h: (-len(h["setups"]), h["symbol"]))
    return hits, scanned, errors, len(symbols)


def build(mode, offline=None, today=None):
    """Return (subject, body, ok). ok=False jika data tidak bisa diambil sama sekali."""
    today = today or datetime.date.today()
    if mode == "monthly":
        hits, scanned, errors, total = collect("1M", 100, ["macd_cross"], offline)
        # candle bulanan terakhir yang selesai = bulan sebelumnya
        first = today.replace(day=1)
        prev = first - datetime.timedelta(days=1)
        title = "Golden cross MACD bulanan (candle %s)" % prev.strftime("%b %Y")
    else:
        hits, scanned, errors, total = collect("1d", 60, None, offline)
        hits = hits[:15]
        title = "Pindai harian %s" % today.isoformat()
    subject = "[PGI Crypto Desk] " + title
    if total == 0 or scanned == 0:
        body = ("GAGAL mengambil data Binance (%d koin dicoba, %d error).\n"
                "Kemungkinan Binance memblokir server ini. Tidak ada hasil yang bisa dilaporkan." % (total, errors))
        return "[PGI Crypto Desk] GAGAL - " + title, body, False
    lines = ["%s" % title, "Dipindai %d koin, %d cocok." % (scanned, len(hits)), ""]
    for h in hits:
        extra = " | MACD masih di bawah 0" if (mode == "monthly" and h["macd_below_zero"]) else ""
        lines.append("%-10s harga %-10s RSI %-5s %s%s" % (h["symbol"].replace("USDT", ""), C.fmt_price(h["price"]),
                     h["rsi"], ", ".join(LABEL[x] for x in h["setups"]), extra))
    if not hits:
        lines.append("Tidak ada koin yang cocok kali ini.")
    if errors:
        lines.append("\n(%d koin gagal diambil.)" % errors)
    lines += ["", "Ini daftar chart yang cocok aturan, bukan rekomendasi beli. Cek stop & ukuran posisi dulu."]
    return subject, "\n".join(lines), True


def send(subject, body, user, password, to):
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, user, to
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=30) as s:
        s.login(user, password)
        s.send_message(msg)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Peringatan email PGI Crypto Desk")
    ap.add_argument("mode", choices=["monthly", "daily"])
    ap.add_argument("--send", action="store_true", help="kirim email (default: kirim hanya jika kunci tersedia di GitHub Actions)")
    ap.add_argument("--offline")
    a = ap.parse_args(argv)
    subject, body, ok = build(a.mode, a.offline)
    print(subject + "\n\n" + body)
    user, pw = os.environ.get("GMAIL_USER"), os.environ.get("GMAIL_APP_PASSWORD")
    if a.send or (os.environ.get("GITHUB_ACTIONS") and user and pw):
        if not (user and pw):
            sys.exit("GMAIL_USER / GMAIL_APP_PASSWORD belum diisi.")
        send(subject, body, user, pw, os.environ.get("MAIL_TO") or DEFAULT_TO)
        print("\nEmail terkirim.")
    else:
        print("\n(Mode tampil saja: email tidak dikirim.)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
