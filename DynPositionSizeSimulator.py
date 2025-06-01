import subprocess
import json
import os
import sys
import concurrent.futures

def run_simulation(cmd):
    result = subprocess.run(cmd)
    return result.returncode

def main():
    # Konfigurationsdatei einlesen
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "input.json")
    try:
        with open(config_path, "r") as file:
            args = json.load(file)
    except FileNotFoundError:
        print(f"Fehler: '{config_path}' wurde nicht gefunden.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Fehler beim Parsen der JSON-Datei: {e}")
        sys.exit(1)

    # Drei unterschiedliche Trefferquoten berechnen
    base_hit = args.get("hit_rate")
    if base_hit is None:
        print("Fehler: 'hit_rate' fehlt in der JSON-Datei.")
        sys.exit(1)

    hit_rates = [
        base_hit - 0.1,
        base_hit - 0.05,
        base_hit
    ]

    for key in ("avg_win", "avg_loss", "num_simulations", "num_trades", "num_mc_shuffles"):
        if key not in args:
            print(f"Fehler: '{key}' fehlt in der JSON-Datei.")
            sys.exit(1)

    # Markov-Parameter aus JSON einlesen (mit Defaultwerten)
    p_win_after_win = args.get("p_win_after_win", 0.7)
    p_win_after_loss = args.get("p_win_after_loss", 0.5)

    simulation_cmds = []
    for i, hit_rate in enumerate(hit_rates, start=1):
        print(f"\n--- Run {2*i-1}/6: hit_rate = {hit_rate:.2f} (ohne Markov) ---\n")
        cmd = [
            sys.executable,
            os.path.join(script_dir, "MyTradingSimulator_sub.py"),
            "--hit_rate", str(hit_rate),
            "--avg_win", str(args["avg_win"]),
            "--avg_loss", str(args["avg_loss"]),
            "--num_simulations", str(args["num_simulations"]),
            "--num_trades", str(args["num_trades"]),
            "--num_mc_shuffles", str(args["num_mc_shuffles"])
        ]
        simulation_cmds.append((2*i-1, cmd, f"ohne Markov"))

        print(f"\n--- Run {2*i}/6: hit_rate = {hit_rate:.2f} (mit Markov) ---\n")
        cmd_markov = cmd + [
            "--use_markov",
            "--p_win_after_win", str(p_win_after_win),
            "--p_win_after_loss", str(p_win_after_loss)
        ]
        simulation_cmds.append((2*i, cmd_markov, f"mit Markov"))

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_run = {executor.submit(run_simulation, cmd): (idx, label) for idx, cmd, label in simulation_cmds}
        for future in concurrent.futures.as_completed(future_to_run):
            idx, label = future_to_run[future]
            try:
                returncode = future.result()
                if returncode != 0:
                    print(f"Run {idx} ({label}) ist mit Fehlercode {returncode} abgebrochen.")
                    sys.exit(returncode)
            except Exception as exc:
                print(f"Run {idx} ({label}) erzeugte eine Ausnahme: {exc}")
                sys.exit(1)

if __name__ == "__main__":
    main()
    