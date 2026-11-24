import importlib.util
import json
import os
import random
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(folder, name):
    sys.path.insert(0, os.path.join(ROOT, folder))
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, folder, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


C = load("crypto-scanner", "cryptolib")
scan = load("crypto-scanner", "scan")
size = load("crypto-size", "size")
ex = load("crypto-exit", "exit")
bt = load("crypto-backtest", "backtest")
jr = load("crypto-journal", "journal")


def bars(closes, spread=1.0, vol=100.0, step=86400000):
    rows, prev = [], closes[0]
    for i, c in enumerate(closes):
        o = prev
        h, l = max(o, c) + spread, min(o, c) - spread
        rows.append([i * step, str(o), str(h), str(l), str(c), str(vol), i * step + step - 1, str(vol * c), 10])
        prev = c
    return rows


def walk(n, seed=1, start=100.0, drift=0.0005, vol=0.02):
    rng = random.Random(seed)
    x, out = start, []
    for _ in range(n):
        x *= 1 + rng.gauss(drift, vol)
        out.append(x)
    return out


class Indicators(unittest.TestCase):
    def test_sma_ema(self):
        self.assertEqual(C.sma([1, 2, 3, 4], 2), [None, 1.5, 2.5, 3.5])
        e = C.ema([5.0] * 30, 10)
        self.assertAlmostEqual(e[-1], 5.0)

    def test_rsi_extremes(self):
        up = [float(i) for i in range(1, 40)]
        self.assertEqual(C.rsi(up)[-1], 100.0)
        down = [float(i) for i in range(40, 1, -1)]
        self.assertAlmostEqual(C.rsi(down)[-1], 0.0, places=6)

    def test_macd_uptrend_positive(self):
        line, sig, hist = C.macd([100 * 1.01 ** i for i in range(80)])
        self.assertGreater(line[-1], 0)
        self.assertIsNotNone(sig[-1])

    def test_atr_constant_range(self):
        k = C.parse_klines(bars([100.0] * 40, spread=1.0))
        self.assertAlmostEqual(C.atr(k)[-1], 2.0)


class Size(unittest.TestCase):
    def test_basic(self):
        r = size.calc(1000, 100, 95, 112, risk_pct=1, fee_pct=0.1)
        self.assertEqual(r["verdict"], "PASS")
        self.assertAlmostEqual(r["max_loss"], 10.0, places=6)
        self.assertAlmostEqual(r["qty"], 10 / 5.195, places=6)

    def test_wrong_side_blocks(self):
        self.assertEqual(size.calc(1000, 100, 105)["verdict"], "BLOCK")

    def test_leverage_cap(self):
        r = size.calc(1000, 100, 99.9, leverage=1.0)
        self.assertTrue(r["capped_by_leverage"])
        self.assertLessEqual(r["notional"], 1000.0001)

    def test_daily_loss_and_rr_block(self):
        self.assertEqual(size.calc(1000, 100, 95, 112, day_loss=25)["verdict"], "BLOCK")
        self.assertEqual(size.calc(1000, 100, 95, 103)["verdict"], "BLOCK")

    def test_short(self):
        r = size.calc(1000, 100, 105, 88, side="short")
        self.assertEqual(r["verdict"], "PASS")

    def test_exit_codes(self):
        self.assertEqual(size.main(["--account", "1000", "--entry", "100", "--stop", "95", "--target", "112"]), 0)
        self.assertEqual(size.main(["--account", "1000", "--entry", "100", "--stop", "105"]), 2)


class Backtest(unittest.TestCase):
    def mk(self, rows):
        return C.parse_klines([[i * 86400000, str(o), str(h), str(l), str(c), "1", i * 86400000 + 1, "1", 1]
                               for i, (o, h, l, c) in enumerate(rows)])

    def test_stop_first_when_both_hit(self):
        k = self.mk([(100, 101, 99, 100), (100, 120, 90, 100)])
        px, why, _ = bt.simulate_trade(k, 1, stop=95, target=110, max_hold=5)
        self.assertEqual((px, why), (95, "stop"))

    def test_gap_down_exits_at_open(self):
        k = self.mk([(100, 101, 99, 100), (90, 91, 88, 89)])
        px, why, _ = bt.simulate_trade(k, 1, stop=95, target=110, max_hold=5)
        self.assertEqual((px, why), (90, "stop (gap)"))

    def test_target_and_time(self):
        k = self.mk([(100, 101, 99, 100), (100, 112, 99, 111)])
        self.assertEqual(bt.simulate_trade(k, 1, 95, 110, 5)[1], "target")
        k = self.mk([(100, 101, 99, 100), (100, 102, 99, 101), (101, 102, 99, 100)])
        self.assertEqual(bt.simulate_trade(k, 1, 90, 130, 1)[1], "waktu")

    def test_run_no_overlap_and_costs(self):
        k = C.parse_klines(bars(walk(600, seed=3, drift=0.002)))
        trades = bt.run(k, "breakout")
        self.assertGreater(len(trades), 5)
        ts = [t["entry_t"] for t in trades]
        self.assertEqual(ts, sorted(set(ts)))
        s = bt.stats(trades)
        self.assertEqual(s["n"], len(trades))
        zero = bt.run(k, "breakout", fee_pct=0, slip_pct=0)
        self.assertGreaterEqual(sum(t["r"] for t in zero), sum(t["r"] for t in trades) - 1e-9)

    def test_monte_carlo_and_rules(self):
        k = C.parse_klines(bars(walk(900, seed=5)))
        for rule in ("breakout", "bounce", "macd_cross"):
            tr = bt.run(k, rule)
            self.assertIsInstance(tr, list)
        tr = bt.run(k, "macd_cross")
        if len(tr) >= 10:
            mc = bt.monte_carlo(tr)
            self.assertLessEqual(mc["ret_p5"], mc["ret_p50"])


class ScannerAndExit(unittest.TestCase):
    def test_breakout_and_volume_detected(self):
        closes = [100 + (i % 3) for i in range(60)] + [130]
        rows = bars(closes, spread=0.5, vol=100)
        rows[-1][5] = "500"
        d = tempfile.mkdtemp()
        json.dump(rows, open(os.path.join(d, "AAAUSDT-1d.json"), "w"))
        json.dump([{"symbol": "AAAUSDT", "quoteVolume": "50000000"},
                   {"symbol": "USDCUSDT", "quoteVolume": "90000000"},
                   {"symbol": "SMALLUSDT", "quoteVolume": "1000"},
                   {"symbol": "AAABTC", "quoteVolume": "90000000"}], open(os.path.join(d, "universe.json"), "w"))
        self.assertEqual(scan.universe(20e6, 10, d), ["AAAUSDT"])
        out = os.path.join(d, "w.json")
        p = scan.main(["--offline", d, "--out", out])
        self.assertEqual(p["hits"][0]["symbol"], "AAAUSDT")
        self.assertIn("breakout", p["hits"][0]["setups"])
        self.assertIn("volume", p["hits"][0]["setups"])
        self.assertTrue(os.path.exists(out))

    def test_macd_cross_detected(self):
        import math
        closes = [100 + 10 * math.sin(i / 6.0) for i in range(160)]
        hits = 0
        for n in range(45, len(closes) + 1):
            r = scan.analyze(C.parse_klines(bars(closes[:n])))
            if r and "macd_cross" in r["setups"]:
                hits += 1
                _, _, h = C.macd(closes[:n])
                self.assertLessEqual(h[-2], 0)
                self.assertGreater(h[-1], 0)
        self.assertGreaterEqual(hits, 2)

    def test_too_little_data(self):
        self.assertIsNone(scan.analyze(C.parse_klines(bars([100.0] * 10))))

    def test_exit_plan(self):
        k = C.parse_klines(bars([100.0] * 40, spread=1.0))
        p = ex.plan(k, entry=100, atr_mult=2)
        self.assertAlmostEqual(p["stop_atr"], 96.0)
        self.assertAlmostEqual(p["targets"][1]["price"], 108.0)
        ps = ex.plan(k, entry=100, side="short")
        self.assertAlmostEqual(ps["stop_atr"], 104.0)


class Journal(unittest.TestCase):
    def test_flow(self):
        p = os.path.join(tempfile.mkdtemp(), "j.json")
        jr.main(["add", "--symbol", "btcusdt", "--entry", "100", "--stop", "95", "--qty", "1"], p)
        jr.main(["close", "--id", "1", "--exit", "110"], p)
        t = jr.load(p)["trades"][0]
        self.assertAlmostEqual(jr.r_multiple(t), 2.0)
        s = jr.stats(jr.load(p)["trades"])
        self.assertEqual(s["win_rate"], 100.0)


class Repo(unittest.TestCase):
    def test_cryptolib_copies_identical(self):
        base = open(os.path.join(ROOT, "crypto-scanner", "cryptolib.py"), "rb").read()
        for d in ("crypto-exit", "crypto-backtest"):
            self.assertEqual(base, open(os.path.join(ROOT, d, "cryptolib.py"), "rb").read(), d)

    def test_skill_files(self):
        for d in os.listdir(ROOT):
            if d.startswith("crypto-"):
                t = open(os.path.join(ROOT, d, "SKILL.md"), encoding="utf-8").read()
                self.assertTrue(t.startswith("---\nname: " + d), d)


if __name__ == "__main__":
    unittest.main()
