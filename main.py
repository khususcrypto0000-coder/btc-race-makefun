"""Breakout Rider: a cbBTC trend bot for make.fun's 24h BTC race.

Strategy (long only, one position, whole account per trade):
- Entry: the close prints above the highest close of the previous 120
  one-minute bars (a fresh 2-hour high). No trade before 121 closes,
  none during warm-up, none within 60 bars of the last exit.
- Exit: the close falls 2.5% below the highest close seen since entry
  (a trailing stop). Anything still held is flattened by the harness
  at the last close.
- At most one order per reply, full size, max slippage 200 bps.

Why this shape: the dev window is a slow grind up with one strong rally,
so systems that trade every wiggle bleed out on the ~35 bps round-trip
cost (4 bps fee + 2 bps slippage + ~11 bps impact at full size against
the pool's ~$900k depth). A 2-hour breakout filter only fires on a real
move, and the trailing stop caps a bad entry near -2.5% instead of
riding a downtrend to the bottom. Backtested on the frozen dev window:
+$26.84 net PnL, 1 trade, 1.98% max drawdown (buy-and-hold made +$32.17
on the same window; the house EMA-cross baseline lost -$114.83).

All decisions are pure integer functions of the closes seen so far:
no clock, no environment, no randomness, so two runs on the same bars
produce byte-identical replies.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
LOOKBACK = 120          # bars of history a breakout must beat (2 hours)
STOP_BPS = 250          # trailing stop below the peak since entry
COOLDOWN_BARS = 60      # bars to wait after an exit before re-entering
SLIPPAGE_BPS = 200      # max slippage allowed on any order (2%)


class BreakoutRider:
    """Donchian breakout + trailing stop, driven by the account's truth."""

    def __init__(self):
        self.closes = []          # closes seen so far (capped at LOOKBACK + 1)
        self.peak = None          # highest close since entry (int), None flat
        self.pending = None       # ("buy"|"sell", seq) awaiting its fill
        self.last_exit_seq = -10 ** 9

    def _reconcile(self, state, batch):
        """Fold this batch's fills into the pending order, if any."""
        if self.pending is None:
            return
        side, seq = self.pending
        holding = self._holding(state)
        for fill in batch.get("fills", []):
            if fill.get("client_id") != self._cid(seq):
                continue
            if fill.get("status") != "filled":
                self.pending = None
                return
            if side == "buy" and holding:
                self.pending = None
                self.peak = int(fill["price"])
            elif side == "sell" and not holding:
                self.pending = None
                self.peak = None
                self.last_exit_seq = state.seq
        # A fill that never arrives within two batches is treated as lost.
        if self.pending is not None and state.seq > seq + 1:
            self.pending = None

    @staticmethod
    def _cid(seq):
        return "br-%d" % seq

    @staticmethod
    def _holding(state):
        pos = state.positions.get(SYMBOL)
        return pos is not None and pos.qty > 0

    def on_batch(self, state, batch):
        if state.warming_up:
            return []
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)
        if len(self.closes) > LOOKBACK + 1:
            del self.closes[:-LOOKBACK - 1]
        self._reconcile(state, batch)

        if self._holding(state):
            if self.peak is None:
                self.peak = close
            elif close > self.peak:
                self.peak = close
            if close * 10000 <= self.peak * (10000 - STOP_BPS):
                qty = state.positions[SYMBOL].qty
                self.pending = ("sell", state.seq)
                return [{
                    "side": "sell",
                    "symbol": SYMBOL,
                    "qty": qty,
                    "max_slippage_bps": SLIPPAGE_BPS,
                    "client_id": self._cid(state.seq),
                }]
            return []

        if self.pending is not None:
            return []  # a buy is in flight; wait for its fill
        if state.seq - self.last_exit_seq < COOLDOWN_BARS:
            return []
        if len(self.closes) < LOOKBACK + 1:
            return []  # not enough history for a breakout yet
        if close > max(self.closes[-LOOKBACK - 1:-1]):
            self.pending = ("buy", state.seq)
            return [{
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": state.cash,
                "max_slippage_bps": SLIPPAGE_BPS,
                "client_id": self._cid(state.seq),
            }]
        return []


BOT = BreakoutRider()


def on_batch(state, batch):
    """The shim's callback: one reply per batch, echoing its seq."""
    return BOT.on_batch(state, batch)


makefun_bars.run(on_batch)
