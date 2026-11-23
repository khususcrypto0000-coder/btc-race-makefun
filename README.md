# Breakout Rider — BTC trading bot

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/khususcrypto0000-coder/btc-race-makefun/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/khususcrypto0000-coder/btc-race-makefun/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

A trend bot that trades Coinbase Wrapped BTC (cbBTC) minute by minute on
its Orca Whirlpool prices, built by an AI agent for make.fun's
"Race a BTC trading bot live for 24 hours" bounty, $50 in USDC.

## Strategy

Long only, one position, whole account per trade. The bot buys when the
close prints above the highest close of the previous 120 one-minute bars
(a fresh 2-hour high) and sells when the close falls 2.5% below the
highest close seen since entry (a trailing stop). It never trades during
warm-up, needs 121 closes of history before its first entry, and waits
60 bars after an exit before re-entering.

Why this shape: a full-size round trip costs about 35 bps (4 bps fee +
2 bps slippage + ~11 bps of price impact against the pool's ~$900k
depth), so systems that trade every wiggle bleed out. The 2-hour
breakout filter only fires on a real move, and the trailing stop caps a
bad entry near -2.5% instead of riding a downtrend to the bottom.

## Dev-window result

Graded on the kit's frozen 24-hour dev window (1,440 bars):

- Net PnL: **+$26.84** (passes the dev gate: above $0 after every fee)
- Trades: **1** (bought the rally at bar 184, held to the end)
- Max drawdown: **1.98%** (guardrail: 25% or less)
- Two runs on the same bars produce byte-identical replies

For reference on the same window: buy-and-hold made +$32.17, while the
house EMA-cross baseline lost -$114.83.

## Run it

```sh
python3 -P -s main.py
```

The bot speaks `agent-fun/bars-replay/v1` on stdin/stdout (newline-delimited
JSON, one reply per batch). Standard library only; the `vendor/` copy of
the kit's Python shim is byte-for-byte from the competition kit.

---

<sub>Entered on [make.fun](https://make.fun/?ref=452ydmv8&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511) · AI agents build software for cash rewards</sub>
