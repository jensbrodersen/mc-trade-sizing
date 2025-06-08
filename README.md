# mc-trade-sizing

Monte Carlo simulations for dynamic position sizing based on trade sequences
and risk analysis.

This project analyzes trade sequences to optimize position sizing dynamically
using Monte Carlo simulations. It evaluates the impact of varying position
sizes based on trading streak behaviors and simulates performance under
different market scenarios.

---

## Features

- Monte Carlo simulation framework for trade outcome modeling  
- Dynamic position sizing strategies based on trade series analysis  
- Markov and regime-switching models for realistic simulations  
- Comparison of risk and return metrics under various assumptions  
- Generates detailed performance reports in HTML  

---

## Purpose

Improve portfolio management by incorporating realistic trading behavior and
sequence dependencies, going beyond static position sizing methods.

---

## Quick Start

1. Adjust parameters in `input.json`:

```json
"hit_rate": 0.82,
"avg_win": 186,
"avg_loss": 219
```

2. Run the simulator:

```bash
python dps.py
```

3. Output: HTML performance reports in `/results/`

---

## Strategies Simulated

- Constant position sizing  
- Martingale / anti-Martingale  
- Streak-based (pause/increase on win/loss)  
- Pause-combo strategies  
- Regime- and Markov-based variations  

Each strategy runs with multiple Monte Carlo shuffles for robustness testing.

---

## Simulation Models

### Random Trade Order (Baseline)

Each trade is shuffled randomly. Simulates 1000 runs per strategy × 20
strategies = 20,000 simulations.

---

### Markov Models

#### First-Order:
- Probabilities depend on the previous trade
- Parameters:
  - `--use_markov`
  - `--p_win_after_win`
  - `--p_win_after_loss`

#### Second-Order:
- Depends on last 2 trades  
- Parameters:
  - `--use_markov2`
  - `--p_win_ww`, `--p_win_wl`, `--p_win_lw`, `--p_win_ll`

---

### Regime-Switching

Models alternating market conditions:

```json
--use_regime
--regimes '[{"length":300,"hit_rate":0.9,"avg_win":200,"avg_loss":100},
            {"length":200,"hit_rate":0.5,"avg_win":100,"avg_loss":100},
            {"length":500,"hit_rate":0.2,"avg_win":100,"avg_loss":200}]'
```

---

## Metrics Reported (per Strategy)

- Avg. profit  
- Avg. drawdown  
- Profit-to-drawdown ratio  
- Min/max profit and drawdown  
- Profit per trade  
- Profit / max drawdown  

---

## Example

```bash
python dps.py
```

→ Runs 20 strategies × 1000 Monte Carlo simulations = 20,000 runs.  
→ Results saved in `/results/*.html`

---

## Notes

- Three degradation scenarios simulated:
  - Backtest model
  - 5% worse
  - 10% worse
- No transaction costs or slippage included  
- Fully extendable architecture  

---

## License

This project is licensed under the [MIT License](./LICENSE).

---

## Contributing

Feel free to open issues, pull requests, or contribute new strategy modules.

---

## Sponsoring

If this tool adds value to your trading or research work, please consider
sponsoring further development 🙏

👉 GitHub Sponsors button will appear once the profile is approved.

---


