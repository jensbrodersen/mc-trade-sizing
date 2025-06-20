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
#
# License:
# Provided free of charge for personal, educational, and non-commercial use only.
# Commercial use requires a separate paid license.
# See LICENSE file or contact: https://github.com/jensbrodersen
# No financial advice.
# ------------------------------------------------------------------------------------------

import subprocess
import json
import os
import sys
import concurrent.futures
import threading
from datetime import datetime
import pandas as pd
import re
import queue
from src.output_handler import save_json
from src.influx_handler import write_to_influxdb  # ✅ Richtig
from influxdb_client import Point  # ✅ Importiere Point direkt aus influxdb_client
from src.influx_handler import load_config, write_to_influxdb, is_influxdb_reachable
from src.api_handler import start_api
from src.output_handler import save_parquet
from src.output_handler import save_sql

def timed_input(prompt, timeout=8, default="n"):
    print(prompt, end="", flush=True)
    result = queue.Queue()

    def ask():
        try:
            result.put(sys.stdin.readline().strip())
        except Exception:
            result.put(default)

    t = threading.Thread(target=ask)
    t.daemon = True
    t.start()
    t.join(timeout)

    if t.is_alive():
        print(f"\n⏱ No input after {timeout} seconds, defaulting to '{default}'")
        return default.lower()
    return result.get().lower()

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

import re

def extract_simulation_settings(table_text):
    """Extracts simulation parameters from HTML text and returns them as a dictionary."""
    hit_rate_match = re.search(r"Hit rate: ([\d.]+)%", table_text)
    mode_match = re.search(r"Mode: (.*?)\n", table_text)
    avg_win_match = re.search(r"Average win per trade: €([\d.]+)", table_text)
    avg_loss_match = re.search(r"Average loss per trade: €([\d.]+)", table_text)
    num_simulations_match = re.search(r"Number of simulations: (\d+)", table_text)
    num_trades_match = re.search(r"Number of trades per simulation: (\d+)", table_text)
    num_shuffles_match = re.search(r"Number of shuffles per simulation: (\d+)", table_text)
    break_even_match = re.search(r"Break-even hit rate: ([\d.]+)%", table_text)

    return {
        "Hit Rate (%)": hit_rate_match.group(1) if hit_rate_match else None,
        "Mode": mode_match.group(1).strip() if mode_match else None,
        "Avg Win (€)": float(avg_win_match.group(1)) if avg_win_match else None,
        "Avg Loss (€)": float(avg_loss_match.group(1)) if avg_loss_match else None,
        "Num Simulations": int(num_simulations_match.group(1)) if num_simulations_match else None,
        "Num Trades": int(num_trades_match.group(1)) if num_trades_match else None,
        "Num Shuffles": int(num_shuffles_match.group(1)) if num_shuffles_match else None,
        "Break-even Hit Rate (%)": break_even_match.group(1) if break_even_match else None
    }

def main():
    # Load configuration file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "input.json")
    try:
        with open(config_path, "r", encoding="utf-8") as file:  # Ensure proper encoding
            args = json.load(file)
    except FileNotFoundError:
        print(f"Error: '{config_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        sys.exit(1)

    # Extract required parameters
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

    # Load InfluxDB configuration from JSON file
    influx_config = load_config()
    
    simulation_cmds = []
    html_blocks = []
    total_runs = 12
    run_counter = 1

    for i, hit_rate in enumerate(hit_rates, start=1):
        # 1. Without Markov
        html_blocks.append(html_run_header(run_counter, total_runs, hit_rate, "without Markov"))
        cmd = [
            sys.executable,
            os.path.join(script_dir, "src", "trading_models.py"),
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

    # Extract simulation settings from HTML content before processing individual strategies
    # Iterate through all simulations
    for idx, table_html in html_tables:
        table_text = re.sub(r"<.*?>", "", table_html)  # Remove HTML tags for clean processing

        # Extract simulation settings using the cleaned text
        simulation_settings = extract_simulation_settings(table_text)

    # Print all simulation results to console with cleaned HTML
    for idx, table_html in html_tables:
        clean_text = re.sub(r"<.*?>", "", table_html)  # Remove HTML tags for better readability in console output
        print(f"\n🔹 Simulation Run {idx} Results:")
        print(clean_text)

    print("\n✅ Simulation results successfully displayed in the console.")
    print(f"\n✅ HTML overview successfully created: {html_output_path}")

    # Generate timestamp for the filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_output_path = os.path.join(results_dir, f"simulation_runs_{timestamp}.csv")
    excel_output_path = os.path.join(results_dir, f"simulation_runs_{timestamp}.xlsx")

    csv_data = []

    # Iterate through all simulations
    for idx, table_html in html_tables:
        table_text = re.sub(r"<.*?>", "", table_html)  # Remove HTML tags for clean processing

        # Extract simulation settings before processing strategies
        simulation_settings = extract_simulation_settings(table_text)  

        # ✅ Define `filtered_lines` BEFORE using it
        filtered_lines = [
            line for line in table_text.split("\n")
            if len(line.split()) >= 10 and "Top 4 strategies compared to" not in line
        ]

        # Process each strategy line
        for line in filtered_lines:
            match = re.match(r"(.+?)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)", line)

            if match:
                strategy_data = {
                    "Run Index": idx,
                    **simulation_settings,  # Ensures settings apply correctly per run
                    "Strategy": match.group(1).strip(),
                    "Avg Profit (€)": float(match.group(2)),
                    "Avg Drawdown (€)": float(match.group(3)),
                    "Ratio": float(match.group(4)),
                    "Min (€)": float(match.group(5)),
                    "Max (€)": float(match.group(6)),
                    "Min DD (€)": float(match.group(7)),
                    "Max DD (€)": float(match.group(8)),
                    "Avg/Trade": float(match.group(9)),
                    "Profit/MaxDD": float(match.group(10)),
                }
                csv_data.append(strategy_data)

    # Remove duplicate strategy entries
    unique_csv_data = []
    seen_strategies = set()

    for entry in csv_data:
        strategy_key = (entry["Run Index"], entry["Strategy"])
        if strategy_key not in seen_strategies:
            seen_strategies.add(strategy_key)
            unique_csv_data.append(entry)

    # Create DataFrame and write to CSV
    df = pd.DataFrame(unique_csv_data)
    df.to_csv(csv_output_path, index=False, sep=";", encoding="utf-8-sig")
    print(f"\n✅ CSV file successfully created: {csv_output_path}")

    # Create DataFrame and write to XLSX
    df.to_excel(excel_output_path, index=False, engine="openpyxl")
    print(f"\n✅ Excel file successfully created: {excel_output_path}")

    # Save results in JSON format
    json_output_path = os.path.join(results_dir, f"simulation_runs_{timestamp}.json")
    save_json(unique_csv_data, results_dir, timestamp)
    print(f"\n✅ JSON file successfully created: {json_output_path}")

    # Save results in Parquet format
    save_parquet(unique_csv_data, results_dir, timestamp)
    print(f"\n✅ Parquet file successfully created: {os.path.join(results_dir, f'simulation_runs_{timestamp}.parquet')}")

    # Write results to InfluxDB (if integrating with InfluxDB)
    # from influx_handler import write_to_influxdb
    # write_to_influxdb(csv_data)
    # Check if InfluxDB usage is enabled
    config = load_config()
    use_influxdb = config.get("use_influxdb", False)


    if use_influxdb and is_influxdb_reachable(config["influxdb_url"]):
        try:
            write_to_influxdb(unique_csv_data)
            print("\n✅ Data successfully written to InfluxDB!")
        except Exception as e:
            print(f"\n⚠ Error writing to InfluxDB: {e}")
    elif use_influxdb:
        print("\n⚠ InfluxDB is enabled, but the server is unreachable. Skipping write.")
    else:
        print("\nℹ️ InfluxDB usage is disabled in configuration.")

    #sqlite3 output
    db_path = os.path.join(results_dir, f"simulation_results_{timestamp}.db")
    save_sql(unique_csv_data, results_dir, timestamp)
    print(f"\n✅ SQLite database file successfully created: {db_path}")


    # Ask user if the REST API should be started
    timeout_setting = config.get("api_timeout", 60)
    answer = timed_input("Do you want to continue? [y/N]: ", timeout=timeout_setting)
    run_api = timed_input("\n❓ Should the REST API be started? (y/n): ")
    if run_api == "y":
        # Extract API timeout dynamically
        api_timeout = config.get("api_timeout", 60) # Default to 60 if missing
        print(f"\n⏳ API timeout loaded from JSON: {api_timeout} seconds")
        print("\n🚀 Starting the REST API with a timeout of", api_timeout, "seconds...")
        start_api(unique_csv_data, api_timeout)  # Pass the timeout dynamically
    else:
        print("\n⏹ REST API was not started.")

    print("\n✅ All data has been successfully saved!")

if __name__ == "__main__":
    main()  # Calls main() to execute the script

