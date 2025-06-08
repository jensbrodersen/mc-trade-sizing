# ------------------------------------------------------------------------------------------
# Trading Strategy Simulator with Monte Carlo Analysis and Adaptive Position Sizing
#
# Overview:
# This script simulates 20 different trading strategies with dynamically adjusted
# position sizing based on win/loss streaks. It evaluates classic Martingale and
# Anti-Martingale approaches, and strategies that pause trading after certain conditions.
#
# Functionality:
# - Generates random trade sequences (Monte Carlo method) based on:
#   hit rate, average win, average loss, and total number of trades.
# - Optional: Enables a 1st or 2nd order Markov model or regime-switching model.
# - Simulates capital progression and max drawdown for each strategy.
# - Position size is adapted after wins/losses or paused depending on strategy rules.
#
# Output & Evaluation:
# - Each strategy outputs:
#   * Avg. Profit (€): Average total return over all simulations.
#   * Avg. Drawdown (€): Average of maximum drawdowns.
#   * Ratio: Avg. profit divided by avg. drawdown (risk/reward).
#   * Min/Max (€): Minimum and maximum profits observed.
#   * Min DD / Max DD (€): Minimum and maximum drawdowns observed.
#   * Avg/Trade (€): Average profit per trade.
#   * Profit/MaxDD: Ratio of average profit to max drawdown.
# - Strategies are sorted by Profit/MaxDD (descending).
#
# Insights:
# - Shows how position sizing rules affect profitability, risk, and robustness.
# - Pausing after winning streaks or adjusting after losses can improve risk/reward.
# - Some strategies perform better under different market regimes or streak types.
##
# License:
# MIT License. Provided for educational purposes. No financial advice.
# ------------------------------------------------------------------------------------------

import subprocess
import json
import os
import sys
import concurrent.futures
import threading
from datetime import datetime

def run_simulation(cmd):
    # Capture output (stdout)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout

def html_run_header(run_idx, total_runs, hit_rate, mode):
    color = {
        "without Markov": "#2196F3",
        "with Markov 1.Ord": "#4CAF50",
        "with Markov 2.Ord": "#FF9800",
        "with Regime-Switching-Modell": "#9C27B0"
    }.get(mode, "#333")
    html = (
        f'<div style="background:{color};color:#fff;padding:8px 0 8px 10px;'
        f'margin:18px 0 8px 0;font-weight:bold;font-size:1.1em;">'
        f'--- Run {run_idx}/{total_runs}: hit_rate = {hit_rate:.2f} ({mode}) ---'
        f'</div>'
    )
    return html

def ansi_to_html(text):
    # Simple ANSI to HTML conversion (colors: green/red/yellow)
    import re
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'\x1b\[32m', '<span style="color:#0a0;">', text)  # Green
    text = re.sub(r'\x1b\[31m', '<span style="color:#c00;">', text)  # Red
    text = re.sub(r'\x1b\[33m', '<span style="color:#e6b800;">', text)  # Yellow
    text = re.sub(r'\x1b\[0m', '</span>', text)  # Reset
    text = re.sub(r'\x1b\[1m', '<b>', text)      # Bold on
    text = re.sub(r'\x1b\[22m', '</b>', text)    # Bold off
    text = text.replace('\n', '<br>\n')          # Line breaks
    return f'<div style="font-family:monospace;font-size:1.13em;white-space:pre;">{text}</div>'

def highlight_top4_section(html):
    """
    Highlights the 'Top 4 strategies compared to ...' section in HTML.
    Preserves the console-style formatting but with smaller text to fit the box.
    Uses monospace font throughout.
    """
    import re
    header = (
        "Strategy".ljust(90) +
        "Ø Profit (€)".rjust(14) +
        "Ø Drawdown (€)".rjust(16) +
        "Ratio".rjust(12) +
        "Min (€)".rjust(12) +
        "Max (€)".rjust(12) +
        "Min DD (€)".rjust(14) +
        "Max DD (€)".rjust(14) +
        "Ø/Trade".rjust(12) +
        "Profit/MaxDD".rjust(18)
    )
    line = "=" * len(header)
    pattern = r'(Top 4 Strategien im Vergleich zu .+?:<br>)([\s\S]+?)(?=<br><br>|</div>|$)'
    def repl(match):
        values = match.group(2).strip('<br>\n').replace('<br>', '\n')
        values = re.sub(r'-{10,}\n', '', values)
        return (
            '<div style="background:#fffbe6;border:2px solid #fbc02d;'
            'padding:12px 8px 12px 8px;margin:18px 0 18px 0;'
            'font-size:0.93em;color:#333;box-shadow:0 2px 8px #fbc02d55;">'
            '<div style="font-family:monospace;white-space:pre;font-size:0.93em;">'
            + header + '\n\n' + line + '\n\n' + values +
            '</div></div>'
        )
    return re.sub(pattern, repl, html, flags=re.IGNORECASE)

def main():
    # Load configuration file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "input.json")
    try:
        with open(config_path, "r") as file:
            args = json.load(file)
    except FileNotFoundError:
        print(f"Error: '{config_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        sys.exit(1)

    base_hit = args.get("hit_rate")
    if base_hit is None:
        print("Error: 'hit_rate' missing in JSON file.")
        sys.exit(1)

    hit_rates = [
        base_hit - 0.1,
        base_hit - 0.05,
        base_hit
    ]

    for key in ("avg_win", "avg_loss", "num_simulations", "num_trades", "num_mc_shuffles"):
        if key not in args:
            print(f"Error: '{key}' missing in JSON file.")
            sys.exit(1)

    p_win_after_win = args.get("p_win_after_win", 0.7)
    p_win_after_loss = args.get("p_win_after_loss", 0.5)
    p_win_ww = args.get("p_win_ww", 0.8)
    p_win_wl = args.get("p_win_wl", 0.6)
    p_win_lw = args.get("p_win_lw", 0.5)
    p_win_ll = args.get("p_win_ll", 0.3)
    regimes = args.get("regimes", None)

    simulation_cmds = []
    html_blocks = []
    total_runs = 12
    run_counter = 1

    for i, hit_rate in enumerate(hit_rates, start=1):
        # 1. Without Markov
        html_blocks.append(html_run_header(run_counter, total_runs, hit_rate, "without Markov"))
        cmd = [
            sys.executable,
            os.path.join(script_dir, "dps_sub.py"),
            "--hit_rate", str(hit_rate),
            "--avg_win", str(args["avg_win"]),
            "--avg_loss", str(args["avg_loss"]),
            "--num_simulations", str(args["num_simulations"]),
            "--num_trades", str(args["num_trades"]),
            "--num_mc_shuffles", str(args["num_mc_shuffles"])
        ]
        simulation_cmds.append((run_counter, cmd, "without Markov", hit_rate))
        run_counter += 1

        # 2. Markov 1st order
        html_blocks.append(html_run_header(run_counter, total_runs, hit_rate, "with Markov 1.Ord"))
        cmd_markov1 = cmd + [
            "--use_markov",
            "--p_win_after_win", str(p_win_after_win),
            "--p_win_after_loss", str(p_win_after_loss)
        ]
        simulation_cmds.append((run_counter, cmd_markov1, "with Markov 1.Ord", hit_rate))
        run_counter += 1

        # 3. Markov 2nd order
        html_blocks.append(html_run_header(run_counter, total_runs, hit_rate, "with Markov 2.Ord"))
        cmd_markov2 = cmd + [
            "--use_markov2",
            "--p_win_ww", str(p_win_ww),
            "--p_win_wl", str(p_win_wl),
            "--p_win_lw", str(p_win_lw),
            "--p_win_ll", str(p_win_ll)
        ]
        simulation_cmds.append((run_counter, cmd_markov2, "with Markov 2.Ord", hit_rate))
        run_counter += 1

        # 4. Regime switching
        html_blocks.append(html_run_header(run_counter, total_runs, hit_rate, "with Regime-Switching-Modell"))
        cmd_regime = cmd + ["--use_regime"]
        if regimes:
            import json as pyjson
            cmd_regime += ["--regimes", pyjson.dumps(regimes)]
        simulation_cmds.append((run_counter, cmd_regime, "with Regime-Switching-Modell", hit_rate))
        run_counter += 1

    # Execute simulations and gather results
    html_tables = []
    finished = 0
    total = len(simulation_cmds)
    lock = threading.Lock()

    print(f"Starting {total} simulations ...", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_run = {executor.submit(run_simulation, cmd): (idx, label) for idx, cmd, label, _ in simulation_cmds}
        for future in concurrent.futures.as_completed(future_to_run):
            idx, label = future_to_run[future]
            try:
                returncode, output = future.result()
                if returncode != 0:
                    print(f"\nRun {idx} ({label}) exited with error code {returncode}.")
                    sys.exit(returncode)
                html_tables.append((idx, ansi_to_html(output)))
            except Exception as exc:
                print(f"\nRun {idx} ({label}) raised an exception: {exc}")
                sys.exit(1)
            with lock:
                finished += 1
                print(f"\rProgress: {finished}/{total} completed", end="", flush=True)
    print("\nAll simulations completed.")

    # Sort by run number
    html_tables.sort(key=lambda x: x[0])

    # Create "results" folder if it doesn't exist
    results_dir = os.path.join(script_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Save HTML to results subfolder
    html_output_path = os.path.join(results_dir, f"simulation_runs_{timestamp}.html")

    with open(html_output_path, "w", encoding="utf-8") as html_file:
        html_file.write(
            "<html><head><meta charset='utf-8'>"
            "<title>Simulation Runs</title>"
            "<style>"
            "body { font-size: 1.18em; font-family: Arial, sans-serif; background: #f7f7fa; }"
            "h2 { font-size: 1.7em; color: #222; margin-top: 1.2em; }"
            "div[style*='font-family:monospace'] { font-size: 1.13em; }"
            "</style></head><body>\n"
        )
        html_file.write("<h2>Simulation Runs Overview</h2>\n")
        for block, (idx, table_html) in zip(html_blocks, html_tables):
            if "Top 4 Strategien im Vergleich zu" in table_html:
                table_html = highlight_top4_section(table_html)
            html_file.write(block + "\n")
            html_file.write(table_html + "\n")
        html_file.write("</body></html>\n")

    print(f"\nHTML overview of the runs has been generated: {html_output_path}")


if __name__ == "__main__":
    main()
