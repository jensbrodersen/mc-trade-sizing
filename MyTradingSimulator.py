# ------------------------------------------------------------------------------------------
# Trading-Strategie-Simulator mit Monte-Carlo-Analyse und adaptiver Positionsgrößensteuerung
#
# Übersicht:
# Dieses Skript simuliert verschiedene Trading-Strategien, bei denen die Positionsgröße
# dynamisch an Gewinn- oder Verlustserien angepasst wird. Es werden 12 Strategien getestet,
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
# - Die Strategien werden nach Ø/Trade absteigend sortiert, um die profitabelsten
#   Varianten hervorzuheben.
#
# Bewertung:
# Die Auswertung zeigt, wie sich verschiedene Anpassungen der Positionsgröße auf
# Gewinn, Risiko und Robustheit auswirken. Besonders Strategien mit Pausen oder
# gezielter Erhöhung nach Verlusten können das Chance-Risiko-Profil verbessern,
# bergen aber auch Risiken bei langen Verlustserien.
#
# Nutzung:
# Das Skript wird über die Kommandozeile mit Parametern für Trefferquote, Gewinn,
# Verlust, Anzahl der Trades und Simulationen gestartet. Die Ergebnisse werden
# direkt in der Konsole ausgegeben.
#
# Beispielaufruf:
#   python mc_tradingsimulation.py --hit_rate 0.81 --avg_win 307 --avg_loss 506
# ------------------------------------------------------------------------------------------
# ...existing code...


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

    # Subskript dreimal aufrufen
    for i, hit_rate in enumerate(hit_rates, start=1):
        print(f"\n--- Run {i}/3: hit_rate = {hit_rate:.2f} ---\n")
        cmd = [
            sys.executable,             # ruft exakt dieselbe Python-Umgebung auf
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
            print(f"Run {i} ist mit Fehlercode {result.returncode} abgebrochen.")
            sys.exit(result.returncode)

if __name__ == "__main__":
    main()
