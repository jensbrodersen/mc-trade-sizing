import os
import pandas as pd
import re
import openpyxl  # (.xlsx)
import json
import sqlite3

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

def print_console(html_tables):
    """Zeigt die Simulationsergebnisse in der Konsole an."""
    for idx, table_html in html_tables:
        clean_text = re.sub(r"<.*?>", "", table_html)  # Entfernt HTML-Tags
        print(f"\n🔹 Simulation Run {idx} Ergebnisse:")
        print(clean_text)

def save_csv(csv_data, results_dir, timestamp):
    """Speichert die Simulationsergebnisse als CSV-Datei."""
    csv_output_path = os.path.join(results_dir, f"simulation_runs_{timestamp}.csv")

    # Remove doubled entries
    unique_csv_data = []
    seen_strategies = set()

    for entry in csv_data:
        strategy_key = (entry["Run Index"], entry["Strategy"])
        if strategy_key not in seen_strategies:
            seen_strategies.add(strategy_key)
            unique_csv_data.append(entry)

    # Write to CSV in correct order
    df = pd.DataFrame(unique_csv_data)
    df.to_csv(csv_output_path, index=False, sep=";", encoding="utf-8-sig")

def save_excel(csv_data, results_dir, timestamp):
    """Speichert die Simulationsergebnisse als Excel-Datei."""
    excel_output_path = os.path.join(results_dir, f"simulation_runs_{timestamp}.xlsx")

    # Remove doubled entries
    unique_csv_data = []
    seen_strategies = set()

    for entry in csv_data:
        strategy_key = (entry["Run Index"], entry["Strategy"])
        if strategy_key not in seen_strategies:
            seen_strategies.add(strategy_key)
            unique_csv_data.append(entry)

    # Write to Excel-file in correct order
    df = pd.DataFrame(unique_csv_data)
    df.to_excel(excel_output_path, index=False, engine="openpyxl")

def save_json(csv_data, results_dir, timestamp):
    """Speichert die Simulationsergebnisse als JSON-Datei."""
    json_output_path = os.path.join(results_dir, f"simulation_runs_{timestamp}.json")

    # Entferne doppelte Einträge
    unique_json_data = []
    seen_strategies = set()

    for entry in csv_data:
        strategy_key = (entry["Run Index"], entry["Strategy"])
        if strategy_key not in seen_strategies:
            seen_strategies.add(strategy_key)
            unique_json_data.append(entry)

    # Schreibe JSON-Datei
    with open(json_output_path, "w", encoding="utf-8") as json_file:
        json.dump(unique_json_data, json_file, indent=4, ensure_ascii=False)

def save_parquet(data, results_dir, timestamp):
    """Save simulation results in Parquet format."""
    parquet_output_path = os.path.join(results_dir, f"simulation_runs_{timestamp}.parquet")
    
    df = pd.DataFrame(data)
    
    try:
        df.to_parquet(parquet_output_path, engine="pyarrow", index=False)
    except Exception as e:
        print(f"❌ Error saving Parquet file: {e}")
    #for debugging only: print(df.head())  # Show first few lines of decoded parquet data
    #for debugging only: print(df)

def save_sql(data, results_dir, timestamp):
    """Speichert die Simulationsergebnisse in SQLite-Datenbank im gleichen Ordner wie Parquet."""
    db_path = os.path.join(results_dir, f"simulation_results_{timestamp}.db")  # SQL-Datei im gleichen Ordner
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tabelle erstellen, falls sie nicht existiert
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trade_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_index INTEGER,
        hit_rate FLOAT,
        strategy TEXT,
        avg_win FLOAT,
        avg_loss FLOAT,
        num_simulations INTEGER,
        num_trades INTEGER,
        num_shuffles INTEGER,
        avg_drawdown FLOAT,
        profit_maxdd FLOAT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Daten einfügen
    for entry in data:
        cursor.execute("""
        INSERT INTO trade_results (run_index, hit_rate, strategy, avg_win, avg_loss, num_simulations, num_trades, num_shuffles, avg_drawdown, profit_maxdd)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["Run Index"], entry["Hit Rate (%)"], entry["Mode"],
            entry["Avg Win (€)"], entry["Avg Loss (€)"], entry["Num Simulations"],
            entry["Num Trades"], entry["Num Shuffles"], entry["Avg Drawdown (€)"], entry["Profit/MaxDD"]
        ))

    conn.commit()
    conn.close()

