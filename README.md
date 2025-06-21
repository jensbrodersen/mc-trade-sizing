> **Tested with Python 3.10+ | Docker 24+ | Kubernetes 1.28+**

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
- **REST API** for external access to simulation results
- **Parquet & InfluxDB & SQLite3 storage** for efficient result management
- Generates detailed performance reports in **CSV, HTML, JSON, XLSX, Parquet**

---

## Project Structure

```
.
├── Dockerfile               # Image definition for mc-trade-sizing
├── dps.py                   # Main script for trade simulation
├── dps_config.yaml          # Configuration file (YAML format)
├── requirements.txt         # Python dependencies
├── k8s/                     # Kubernetes job and deployment manifests
│   └── dps-job.yaml
├── docs/                    # Usage documentation (Docker & Kubernetes)
│   ├── readme_docker_usage.md
│   └── readme_kubernetes_usage.md
├── src/                     # Supporting modules and API backend
│   ├── api_handler.py
│   ├── influx_handler.py
│   ├── output_handler.py
│   └── trading_models.py
├── results/                 # Output folder (mounted by Docker)
├── LICENSE
└── README.md
```

---

## Installation

**Install dependencies:**
```bash
pip install -r requirements.txt
```

---

## Docker

Alternatively, use the provided Docker image:

```bash
docker run -it -v "$PWD/results":/app/results jensbrodersen/mc-trade-sizing
```

> **Note:**
> See Quick Start step 3 for usage details.

---

## Kubernetes

To run the simulation as a Kubernetes Job:

```bash
kubectl apply -f k8s/dps-job.yaml
kubectl logs -l job-name=mc-trade-simulation
```

To reset the job:

```bash
kubectl delete job mc-trade-simulation
kubectl apply -f k8s/dps-job.yaml
```

To download result files from the container:

```bash
kubectl get pods
kubectl cp <pod-name>:/app/results ./results
```

> For full usage instructions under WSL2 + MicroK8s, see docs/readme_kubernetes_usage.md

---

## Purpose

Improve portfolio management by incorporating realistic trading behavior and
sequence dependencies, going beyond static position sizing methods.

---

## Quick Start

1. Adjust parameters in `dps_config.yaml`:

```yaml
hit_rate: 0.82
avg_win: 186
avg_loss: 219
```

2. Run the simulator locally (Python script):

```bash
python dps.py
```

3. Run the simulator via Docker (with interactive prompt support):

```bash
docker run -it -v "$PWD/results":/app/results jensbrodersen/mc-trade-sizing
```
> **Note:**
> The `-it` flags (`-i` for interactive, `-t` for pseudo-TTY) are required to enable keyboard input inside the container.
> Without `-it`, any prompts (e.g. confirmation for starting the REST API) will be skipped automatically.

4. Run the REST API:

```bash
python api_handler.py
```


5. Access results in results/ folder or via REST API:

```bash
curl http://127.0.0.1:5000/api/simulations
```

6. REST API Usage:

| Endpoint                | Method | Description                    |
|-------------------------|--------|--------------------------------|
| `/api/simulations/`     | GET    | Retrieve all simulation results |
| `/api/simulations/<id>` | GET    | Get details on specific runs    |
| `/shutdown`             | POST   | Stop the REST API server        |


7. REST API Example Request:
```bash
curl http://127.0.0.1:5000/api/simulations
```

8. Output: All performance reports in `results/`

---

## Strategies Simulated

- Constant position sizing
- Martingale / anti-Martingale  
- Streak-based (pause/increase on win/loss)
- Pause-combo strategies
- Regime- and Markov-based variations

Each strategy runs with multiple Monte Carlo shuffles for robustness testing.

---

## Supported Simulation Models

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

```bash
--use_markov --p_win_after_win 0.75 --p_win_after_loss 0.60
```

#### Second-Order:
- Depends on last 2 trades
- Parameters:
  - `--use_markov2`
  - `--p_win_ww`, `--p_win_wl`, `--p_win_lw`, `--p_win_ll`

```bash
--use_markov2 --p_win_ww 0.85 --p_win_wl 0.65 --p_win_lw 0.55 --p_win_ll 0.30
```

---

### Regime-Switching

Models alternating market conditions:

```bash
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

## Simulation Output Formats
- Terminal Window
- HTML → simulation_runs_YYYY-MM-DD_HH-MM-SS.html
- CSV → simulation_runs_YYYY-MM-DD_HH-MM-SS.csv
- Excel → simulation_runs_YYYY-MM-DD_HH-MM-SS.xlsx
- JSON → simulation_runs_YYYY-MM-DD_HH-MM-SS.json
- Parquet → simulation_runs_YYYY-MM-DD_HH-MM-SS.parquet
- SQLite3 → simulation_results.db
- InfluxDB → Time-series storage for efficient analysis and visualization

---

## Troubleshooting:

REST API does not respond? Ensure Flask is running on 127.0.0.1:5000:

```bash
python api_handler.py
```

Verify firewall & port settings:
```Powershell
netstat -ano | findstr :5000
```

Test API manually:
```bash
curl http://127.0.0.1:5000/api/simulations
```

Database file not found? Check SQLite3 or Parquet storage in results/

---

## Example

```bash
python dps.py
```

→ Runs 20 strategies × 1000 Monte Carlo simulations = 20,000 runs.
→ Results saved in `results/*.*`

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

This project is licensed under a custom non-commercial license.
Personal, educational, and non-commercial use is permitted free of charge.

**Commercial use requires a separate paid license.**
See the [LICENSE](./LICENSE) file for details and contact information.

---

## Contributing

Feel free to open issues, pull requests, or contribute new strategy modules.

---

## Sponsoring

If this tool adds value to your trading or research work, please consider
sponsoring further development 🙏

👉 GitHub Sponsors button will appear once the profile is approved.

---

