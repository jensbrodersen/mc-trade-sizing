# ------------------------------------------------------------------------------------------
# Trading-Strategie-Simulator mit Monte-Carlo-Analyse und adaptiver Positionsgrößensteuerung
#
# Übersicht:
# Dieses Skript simuliert verschiedene Trading-Strategien, bei denen die Positionsgröße
# dynamisch an Gewinn- oder Verlustserien angepasst wird. Es werden 20 Strategien getestet,
# darunter klassische Martingale- und Anti-Martingale-Ansätze sowie Strategien mit
# Pausenphasen nach Gewinnserien.
#
# Funktionsweise:
# - Für gegebene Trefferquote, durchschnittlichen Gewinn und Verlust sowie Trade-Anzahl
#   werden zufällige Trade-Serien erzeugt (Monte-Carlo-Prinzip).
# - Für jede Strategie wird die Entwicklung des Kapitals und der maximale Drawdown
#   simuliert und ausgewertet.
# - Die Positionsgröße wird je nach Strategie nach bestimmten Regeln erhöht, reduziert
#   oder pausiert (z.B. nach x Gewinnen/Verlusten).
#
# Output und Bewertung:
# - Für jede Strategie werden folgende Kennzahlen berechnet:
#   * Ø Gewinn (€): Durchschnittlicher Gesamtgewinn über alle Simulationen.
#   * Ø Drawdown (€): Durchschnittlicher maximaler Kapitalrückgang.
#   * Verhältnis: Verhältnis von Ø Gewinn zu Ø Drawdown (Chance-Risiko).
#   * Min/Max (€): Minimaler und maximaler Gesamtgewinn.
#   * Min DD/Max DD (€): Minimaler und maximaler Drawdown.
#   * Ø/Trade: Durchschnittlicher Gewinn pro Trade.
#   * Gewinn/MaxDD: Verhältnis von Ø Gewinn zu maximalem Drawdown.
# - Die Strategien werden nach Gewinn/MaxDD absteigend sortiert, um die profitabelsten
#   Varianten hervorzuheben.
#
# Bewertung:
# Die Auswertung zeigt, wie sich verschiedene Anpassungen der Positionsgröße auf
# Gewinn, Risiko und Robustheit auswirken. Besonders Strategien mit Pausen oder
# gezielter Erhöhung nach Verlusten können das Chance-Risiko-Profil verbessern,
# bergen aber auch Risiken bei langen Verlustserien.
#
# Nutzung:
# Das Skript wird über die Kommandozeile gestartet. Im gleichen Ordnner muss die Datei
# "input.json" liegen, die die Parameter für die Simulation enthält. Diese Datei sollte
# die folgenden Schlüssel enthalten:
# - hit_rate: Trefferquote (z.B. 0.81 für 81%)
# - avg_win: Durchschnittlicher Gewinn pro Trade (z.B. 307)
# - avg_loss: Durchschnittlicher Verlust pro Trade (z.B. 506)
# - num_simulations: Anzahl der Simulationen (z.B. 1000)
# - num_trades: Anzahl der Trades pro Simulation (z.B. 100)
# - num_mc_shuffles: Anzahl der Monte-Carlo-Shuffles (z.B. 1000)
# ------------------------------------------------------------------------------------------
# Die Ergebnisse werden direkt in der Konsole ausgegeben.
#
# Beispielaufruf:
#   python my_trading_simulator.py
# ------------------------------------------------------------------------------------------

import subprocess
import json
import os
import sys

def main():
    # Pfad zur JSON-Konfigurationsdatei (input.json im selben Ordner)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "input.json")

    # JSON-Datei einlesen
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
        base_hit - 0.1,   # Run 1
        base_hit - 0.05,  # Run 2
        base_hit          # Run 3
    ]

    # Werte-Checker (optional)
    for key in ("avg_win", "avg_loss", "num_simulations", "num_trades", "num_mc_shuffles"):
        if key not in args:
            print(f"Fehler: '{key}' fehlt in der JSON-Datei.")
            sys.exit(1)

    # Markov-Parameter (optional, Standardwerte wie im Subskript)
    p_win_after_win = args.get("p_win_after_win", 0.7)
    p_win_after_loss = args.get("p_win_after_loss", 0.5)

    # Für jede Trefferquote: einmal ohne und einmal mit Markov-Korrelation aufrufen
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
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"Run {2*i-1} ist mit Fehlercode {result.returncode} abgebrochen.")
            sys.exit(result.returncode)

        print(f"\n--- Run {2*i}/6: hit_rate = {hit_rate:.2f} (mit Markov) ---\n")
        cmd_markov = cmd + [
            "--use_markov",
            "--p_win_after_win", str(p_win_after_win),
            "--p_win_after_loss", str(p_win_after_loss)
        ]
        result = subprocess.run(cmd_markov)
        if result.returncode != 0:
            print(f"Run {2*i} ist mit Fehlercode {result.returncode} abgebrochen.")
            sys.exit(result.returncode)

if __name__ == "__main__":
    main()
