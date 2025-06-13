import os
import pandas as pd
import re

def save_html(html_tables, html_blocks, results_dir, timestamp):
    """Speichert die Simulationsergebnisse als HTML-Datei mit korrekter Formatierung."""
    html_output_path = os.path.join(results_dir, f"simulation_runs_{timestamp}.html")

    with open(html_output_path, "w", encoding="utf-8") as html_file:
        html_file.write("<html><head><meta charset='utf-8'><title>Simulation Runs</title>")
        html_file.write("<style> body { font-size: 1.18em; font-family: Arial, sans-serif; background: #f7f7fa; } h2 { font-size: 1.7em; color: #222; margin-top: 1.2em; } </style></head><body>\n")
        html_file.write("<h2>Übersicht der Simulationsergebnisse</h2>\n")

        for block, (idx, table_html) in zip(html_blocks, html_tables):
            table_html = re.sub(r"\n", "<br>\n", table_html)  # Setzt korrekte Zeilenumbrüche
            html_file.write(block + "<br>\n" + table_html + "<br>\n")

        html_file.write("</body></html>\n")

    print(f"\n✅ HTML-Datei erfolgreich erstellt: {html_output_path}")


def print_console(html_tables):
    """Zeigt die Simulationsergebnisse in der Konsole an."""
    for idx, table_html in html_tables:
        clean_text = re.sub(r"<.*?>", "", table_html)  # Entfernt HTML-Tags
        print(f"\n🔹 Simulation Run {idx} Ergebnisse:")
        print(clean_text)

    print("\n✅ Simulationsergebnisse erfolgreich angezeigt.")

def save_csv(csv_data, results_dir, timestamp):
    """Speichert die Simulationsergebnisse als CSV-Datei."""
    csv_output_path = os.path.join(results_dir, f"simulation_runs_{timestamp}.csv")

    # Entferne doppelte Einträge
    unique_csv_data = []
    seen_strategies = set()
    
    for entry in csv_data:
        strategy_key = (entry["Run Index"], entry["Strategy"])
        if strategy_key not in seen_strategies:
            seen_strategies.add(strategy_key)
            unique_csv_data.append(entry)

    # Schreibe CSV mit richtiger Spaltenreihenfolge
    df = pd.DataFrame(unique_csv_data)
    df.to_csv(csv_output_path, index=False, sep=";", encoding="utf-8-sig")

    print(f"\n✅ CSV-Datei erfolgreich erstellt: {csv_output_path}")

