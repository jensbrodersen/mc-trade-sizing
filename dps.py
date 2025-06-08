import subprocess
import json
import os
import sys
import concurrent.futures
import threading
from datetime import datetime

def run_simulation(cmd):
    # Fange die Ausgabe ab (stdout)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout

def html_run_header(run_idx, total_runs, hit_rate, mode):
    color = {
        "ohne Markov": "#2196F3",
        "mit Markov 1.Ord": "#4CAF50",
        "mit Markov 2.Ord": "#FF9800",
        "mit Regime-Switching-Modell": "#9C27B0"
    }.get(mode, "#333")
    html = (
        f'<div style="background:{color};color:#fff;padding:8px 0 8px 10px;'
        f'margin:18px 0 8px 0;font-weight:bold;font-size:1.1em;">'
        f'--- Run {run_idx}/{total_runs}: hit_rate = {hit_rate:.2f} ({mode}) ---'
        f'</div>'
    )
    return html

def ansi_to_html(text):
    # Einfache ANSI zu HTML-Konvertierung für Farben (grün/rot/gelb)
    import re
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Grün
    text = re.sub(r'\x1b\[32m', '<span style="color:#0a0;">', text)
    # Rot
    text = re.sub(r'\x1b\[31m', '<span style="color:#c00;">', text)
    # Gelb
    text = re.sub(r'\x1b\[33m', '<span style="color:#e6b800;">', text)
    # Reset
    text = re.sub(r'\x1b\[0m', '</span>', text)
    # Fett
    text = re.sub(r'\x1b\[1m', '<b>', text)
    text = re.sub(r'\x1b\[22m', '</b>', text)
    # Zeilenumbrüche
    text = text.replace('\n', '<br>\n')
    # Monospace für Tabellen
    return f'<div style="font-family:monospace;font-size:1.13em;white-space:pre;">{text}</div>'

def highlight_top4_section(html):
    """
    Hebt den Abschnitt 'Top 4 Strategien im Vergleich zu ...' im HTML besonders hervor,
    gibt ihn exakt im gewünschten Konsolen-Tabellenformat aus,
    aber mit kleinerer Schrift, damit alles in den gelben Kasten passt.
    Schriftart ist überall identisch: monospace.
    """
    import re
    header = (
        "Strategie".ljust(90) +
        "Ø Gewinn (€)".rjust(14) +
        "Ø Drawdown (€)".rjust(16) +
        "Verhältnis".rjust(12) +
        "Min (€)".rjust(12) +
        "Max (€)".rjust(12) +
        "Min DD (€)".rjust(14) +
        "Max DD (€)".rjust(14) +
        "Ø/Trade".rjust(12) +
        "Gewinn/MaxDD".rjust(18)
    )
    trennlinie = "=" * len(header)
    pattern = r'(Top 4 Strategien im Vergleich zu .+?:<br>)([\s\S]+?)(?=<br><br>|</div>|$)'
    def repl(match):
        values = match.group(2).strip('<br>\n').replace('<br>', '\n')
        values = re.sub(r'-{10,}\n', '', values)
        return (
            '<div style="background:#fffbe6;border:2px solid #fbc02d;'
            'padding:12px 8px 12px 8px;margin:18px 0 18px 0;'
            'font-size:0.93em;color:#333;box-shadow:0 2px 8px #fbc02d55;">'
            '<div style="font-family:monospace;white-space:pre;font-size:0.93em;">'
            + header + '\n\n' + trennlinie + '\n\n' + values +
            '</div></div>'
        )
    return re.sub(pattern, repl, html, flags=re.IGNORECASE)

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
        # 1. Ohne Markov
        html_blocks.append(html_run_header(run_counter, total_runs, hit_rate, "ohne Markov"))
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
        simulation_cmds.append((run_counter, cmd, "ohne Markov", hit_rate))
        run_counter += 1

        # 2. Markov 1. Ordnung
        html_blocks.append(html_run_header(run_counter, total_runs, hit_rate, "mit Markov 1.Ord"))
        cmd_markov1 = cmd + [
            "--use_markov",
            "--p_win_after_win", str(p_win_after_win),
            "--p_win_after_loss", str(p_win_after_loss)
        ]
        simulation_cmds.append((run_counter, cmd_markov1, "mit Markov 1.Ord", hit_rate))
        run_counter += 1

        # 3. Markov 2. Ordnung
        html_blocks.append(html_run_header(run_counter, total_runs, hit_rate, "mit Markov 2.Ord"))
        cmd_markov2 = cmd + [
            "--use_markov2",
            "--p_win_ww", str(p_win_ww),
            "--p_win_wl", str(p_win_wl),
            "--p_win_lw", str(p_win_lw),
            "--p_win_ll", str(p_win_ll)
        ]
        simulation_cmds.append((run_counter, cmd_markov2, "mit Markov 2.Ord", hit_rate))
        run_counter += 1

        # 4. Regime-Switching
        html_blocks.append(html_run_header(run_counter, total_runs, hit_rate, "mit Regime-Switching-Modell"))
        cmd_regime = cmd + ["--use_regime"]
        if regimes:
            import json as pyjson
            cmd_regime += ["--regimes", pyjson.dumps(regimes)]
        simulation_cmds.append((run_counter, cmd_regime, "mit Regime-Switching-Modell", hit_rate))
        run_counter += 1

    # Simulationen ausführen und Ergebnisse sammeln
    html_tables = []
    finished = 0
    total = len(simulation_cmds)
    lock = threading.Lock()

    print(f"Starte {total} Simulationen ...", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_run = {executor.submit(run_simulation, cmd): (idx, label) for idx, cmd, label, _ in simulation_cmds}
        for future in concurrent.futures.as_completed(future_to_run):
            idx, label = future_to_run[future]
            try:
                returncode, output = future.result()
                if returncode != 0:
                    print(f"\nRun {idx} ({label}) ist mit Fehlercode {returncode} abgebrochen.")
                    sys.exit(returncode)
                html_tables.append((idx, ansi_to_html(output)))
            except Exception as exc:
                print(f"\nRun {idx} ({label}) erzeugte eine Ausnahme: {exc}")
                sys.exit(1)
            with lock:
                finished += 1
                print(f"\rFortschritt: {finished}/{total} abgeschlossen", end="", flush=True)
    print("\nAlle Simulationen abgeschlossen.")

    # Nach Run-Nummer sortieren
    html_tables.sort(key=lambda x: x[0])

    # Ordner "results" erstellen, falls nicht vorhanden
    results_dir = os.path.join(script_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # Erzeuge Zeitstempel für Dateinamen
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # HTML-Datei im Unterordner results speichern
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
        html_file.write("<h2>Simulation Runs Übersicht</h2>\n")
        for block, (idx, table_html) in zip(html_blocks, html_tables):
            if "Top 4 Strategien im Vergleich zu" in table_html:
                table_html = highlight_top4_section(table_html)
            html_file.write(block + "\n")
            html_file.write(table_html + "\n")
        html_file.write("</body></html>\n")

    print(f"\nHTML-Übersicht der Runs wurde erzeugt: {html_output_path}")


if __name__ == "__main__":
    main()