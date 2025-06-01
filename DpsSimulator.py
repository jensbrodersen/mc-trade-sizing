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

    # Markov-Parameter 1. Ordnung
    p_win_after_win = args.get("p_win_after_win", 0.7)
    p_win_after_loss = args.get("p_win_after_loss", 0.5)
    # Markov-Parameter 2. Ordnung
    p_win_ww = args.get("p_win_ww", 0.8)
    p_win_wl = args.get("p_win_wl", 0.6)
    p_win_lw = args.get("p_win_lw", 0.5)
    p_win_ll = args.get("p_win_ll", 0.3)
    # Regime-Switching-Parameter
    regimes = args.get("regimes", None)

    simulation_cmds = []
    for i, hit_rate in enumerate(hit_rates, start=1):
        # 1. Ohne Markov
        print(f"\n--- Run {4*i-3}/12: hit_rate = {hit_rate:.2f} (ohne Markov) ---\n")
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
        simulation_cmds.append((4*i-3, cmd, "ohne Markov"))

        # 2. Markov 1. Ordnung
        print(f"\n--- Run {4*i-2}/12: hit_rate = {hit_rate:.2f} (mit Markov 1.Ord) ---\n")
        cmd_markov1 = cmd + [
            "--use_markov",
            "--p_win_after_win", str(p_win_after_win),
            "--p_win_after_loss", str(p_win_after_loss)
        ]
        simulation_cmds.append((4*i-2, cmd_markov1, "mit Markov 1.Ord"))

        # 3. Markov 2. Ordnung
        print(f"\n--- Run {4*i-1}/12: hit_rate = {hit_rate:.2f} (mit Markov 2.Ord) ---\n")
        cmd_markov2 = cmd + [
            "--use_markov2",
            "--p_win_ww", str(p_win_ww),
            "--p_win_wl", str(p_win_wl),
            "--p_win_lw", str(p_win_lw),
            "--p_win_ll", str(p_win_ll)
        ]
        simulation_cmds.append((4*i-1, cmd_markov2, "mit Markov 2.Ord"))

        # 4. Regime-Switching
        print(f"\n--- Run {4*i}/12: hit_rate = {hit_rate:.2f} (mit Regime-Switching-Modell) ---\n")
        cmd_regime = cmd + ["--use_regime"]
        if regimes:
            import json as pyjson
            cmd_regime += ["--regimes", pyjson.dumps(regimes)]
        simulation_cmds.append((4*i, cmd_regime, "mit Regime-Switching-Modell"))

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