# How to run: D:\documents\MyTrading\Tools_alles\python> python mc_tradingsimulation.py --hit_rate 0.81 --avg_win 307 --avg_loss 506

# mc_tradingsimulation.py

import numpy as np
import argparse

def simulate_trades(hit_rate, avg_win, avg_loss, num_trades):
    return np.random.choice([avg_win, -avg_loss], size=num_trades, p=[hit_rate, 1 - hit_rate])

def calculate_drawdown(equity_curve):
    peak = np.maximum.accumulate(equity_curve)
    drawdowns = equity_curve - peak
    return np.min(drawdowns)

def strategy_static(results):
    equity = np.cumsum(results)
    total_profit = np.sum(results)
    drawdown = calculate_drawdown(equity)
    return total_profit, drawdown

def strategy_dynamic(results, condition_func):
    equity = []
    position_size = 1
    state = {'win_streak': 0, 'loss_streak': 0, 'mode': 'trading'}

    for i in range(len(results)):
        trade_result = results[i] * position_size
        if state['mode'] == 'trading':
            equity.append(trade_result)
        else:
            equity.append(0)

        if results[i] > 0:
            state['win_streak'] += 1
            state['loss_streak'] = 0
        else:
            state['loss_streak'] += 1
            state['win_streak'] = 0

        position_size, state = condition_func(results[i], position_size, state)

    cumulative_equity = np.cumsum(equity)
    return np.sum(equity), calculate_drawdown(cumulative_equity)

def make_condition_func(strategy_id):
    def func(result, size, state):
        if strategy_id == 2:
            if result > 0:
                size = 2
            else:
                size = 1

        elif strategy_id in [3, 4, 5]:
            limit = strategy_id - 2
            if result > 0:
                if size == 1:
                    size = 2
                state['win_streak'] += 1
                if state['win_streak'] >= limit:
                    size = 1
                    state['win_streak'] = 0
            else:
                size = 1
                state['win_streak'] = 0

        elif strategy_id in [6, 7, 8]:
            limit = strategy_id - 5
            if result < 0:
                state['loss_streak'] += 1
                if state['loss_streak'] >= limit:
                    size = 2
            else:
                size = 1
                state['loss_streak'] = 0

        elif strategy_id in [9, 10, 11, 12]:
            limit = strategy_id - 8
            if state['mode'] == 'trading':
                if result > 0:
                    state['win_streak'] += 1
                    if state['win_streak'] >= limit:
                        state['mode'] = 'waiting'
            elif result < 0:
                state['mode'] = 'trading'
                state['win_streak'] = 0

        # Erweiterung: Beispielhafte Implementierung für Strategie 13-20 (Platzhalter, bitte anpassen!)
        elif strategy_id == 13:
            # Nach 2 Gewinnen auf 2 erhöhen, nach 2 Verlusten zurück auf 1
            if result > 0:
                state['win_streak'] += 1
                if state['win_streak'] >= 2:
                    size = 2
            else:
                state['loss_streak'] += 1
                state['win_streak'] = 0
                if state['loss_streak'] >= 2:
                    size = 1
                    state['loss_streak'] = 0

        elif strategy_id == 14:
            # Nach 1 Gewinn und 1 Verlust auf 2 erhöhen, sonst auf 1
            if result > 0:
                state['win_streak'] += 1
            else:
                state['loss_streak'] += 1
            if state['win_streak'] >= 1 and state['loss_streak'] >= 1:
                size = 2
                state['win_streak'] = 0
                state['loss_streak'] = 0
            else:
                size = 1

        elif strategy_id == 15:
            # Nach 2 Gewinnen in Folge pausieren bis 1 Verlust, dann auf 2 erhöhen
            if state.get('paused', False):
                if result < 0:
                    size = 2
                    state['paused'] = False
                else:
                    size = 0
            else:
                if result > 0:
                    state['win_streak'] += 1
                    if state['win_streak'] >= 2:
                        state['paused'] = True
                        state['win_streak'] = 0
                        size = 0
                else:
                    state['win_streak'] = 0
                    size = 1

        elif strategy_id == 16:
            # Nach 2 Verlusten auf 2 erhöhen, nach 1 Gewinn pausieren bis zum nächsten Verlust
            if state.get('paused', False):
                if result < 0:
                    state['paused'] = False
                    size = 2
                else:
                    size = 0
            else:
                if result < 0:
                    state['loss_streak'] += 1
                    if state['loss_streak'] >= 2:
                        size = 2
                        state['loss_streak'] = 0
                else:
                    state['loss_streak'] = 0
                    state['paused'] = True
                    size = 0

        elif strategy_id == 17:
            # Nach 1 Gewinn auf 2 erhöhen, aber nur wenn davor 1 Verlust war, sonst auf 1
            if result > 0 and state.get('last_result', 0) < 0:
                size = 2
            else:
                size = 1
            state['last_result'] = result

        elif strategy_id == 18:
            # Nach 3 Gewinnen auf 3 erhöhen, nach 1 Verlust zurück auf 1
            if result > 0:
                state['win_streak'] += 1
                if state['win_streak'] >= 3:
                    size = 3
            else:
                size = 1
                state['win_streak'] = 0

        elif strategy_id == 19:
            # Nach 2 Gewinnen auf 2 erhöhen, nach 2 Verlusten auf 3 erhöhen, sonst auf 1
            if result > 0:
                state['win_streak'] += 1
                state['loss_streak'] = 0
                if state['win_streak'] >= 2:
                    size = 2
                else:
                    size = 1
            else:
                state['loss_streak'] += 1
                state['win_streak'] = 0
                if state['loss_streak'] >= 2:
                    size = 3
                else:
                    size = 1

        elif strategy_id == 20:
            # Nach 1 Gewinn auf 2 erhöhen, nach 2 Verlusten auf 3 erhöhen, nach Gewinn zurück auf 1
            if result > 0:
                if state.get('last_size', 1) == 3:
                    size = 1
                else:
                    size = 2
                state['loss_streak'] = 0
            else:
                state['loss_streak'] += 1
                if state['loss_streak'] >= 2:
                    size = 3
                else:
                    size = 1
            state['last_size'] = size

        return size, state

    return func

def find_break_even_hit_rate(avg_win, avg_loss):
    return avg_loss / (avg_win + avg_loss)

def run_all_strategies(hit_rate, avg_win, avg_loss, num_trades, num_simulations, num_mc_shuffles):
    base_results = simulate_trades(hit_rate, avg_win, avg_loss, num_trades)

    descriptions = {
        1: "Konstante Positionsgröße 1",
        2: "Nach Gewinn auf 2 erhöhen, nach Verlust zurück auf 1",
        3: "Nach Gewinn auf 2 erhöhen, nach Verlust oder 2 Gewinnen zurück auf 1",
        4: "Nach Gewinn auf 2 erhöhen, nach Verlust oder 3 Gewinnen zurück auf 1",
        5: "Nach Gewinn auf 2 erhöhen, nach Verlust oder 4 Gewinnen zurück auf 1",
        6: "Nach Verlust auf 2 erhöhen, nach Gewinn zurück auf 1",
        7: "Nach 2 Verlusten auf 2 erhöhen, nach Gewinn zurück auf 1",
        8: "Nach 3 Verlusten auf 2 erhöhen, nach Gewinn zurück auf 1",
        9: "Nach 1 Gewinn pausieren bis zum nächsten Verlust",
        10: "Nach 2 Gewinnen pausieren bis zum nächsten Verlust",
        11: "Nach 3 Gewinnen pausieren bis zum nächsten Verlust",
        12: "Nach 4 Gewinnen pausieren bis zum nächsten Verlust",
        13: "Nach 2 Gewinnen auf 2 erhöhen, nach 2 Verlusten zurück auf 1",
        14: "Nach 1 Gewinn und 1 Verlust auf 2 erhöhen, sonst auf 1",
        15: "Nach 2 Gewinnen in Folge pausieren bis 1 Verlust, dann auf 2 erhöhen",
        16: "Nach 2 Verlusten auf 2 erhöhen, nach 1 Gewinn pausieren bis zum nächsten Verlust",
        17: "Nach 1 Gewinn auf 2 erhöhen, aber nur wenn davor 1 Verlust war, sonst auf 1",
        18: "Nach 3 Gewinnen auf 3 erhöhen, nach 1 Verlust zurück auf 1",
        19: "Nach 2 Gewinnen auf 2 erhöhen, nach 2 Verlusten auf 3 erhöhen, sonst auf 1",
        20: "Nach 1 Gewinn auf 2 erhöhen, nach 2 Verlusten auf 3 erhöhen, nach Gewinn zurück auf 1",
    }

    summary = {i: [] for i in range(1, 21)}

    for _ in range(num_simulations):
        for _ in range(num_mc_shuffles):  # Shuffle multiple times per simulation
            np.random.shuffle(base_results)

            profit, dd = strategy_static(base_results)
            summary[1].append((profit, dd))

            for i in range(2, 21):
                cond_func = make_condition_func(i)
                profit, dd = strategy_dynamic(base_results, cond_func)
                summary[i].append((profit, dd))

    summary_final = []
    for i in range(1, 21):
        profits = [x[0] for x in summary[i]]
        drawdowns = [x[1] for x in summary[i]]
        avg_profit = np.mean(profits)
        avg_drawdown = np.mean(drawdowns)
        min_profit = np.min(profits)
        max_profit = np.max(profits)
        min_dd = np.min(drawdowns)
        max_dd = np.max(drawdowns)
        avg_per_trade = avg_profit / num_trades
        ratio = avg_profit / abs(avg_drawdown) if avg_drawdown != 0 else float('inf')
        ratio_max_dd = avg_profit / abs(max_dd) if max_dd != 0 else float('inf')
        summary_final.append((descriptions[i], avg_profit, avg_drawdown, ratio, min_profit, max_profit, min_dd, max_dd, avg_per_trade, ratio_max_dd))

    # Sortierung: erst alle mit Gewinn/MaxDD >= 0 (absteigend), dann alle mit Gewinn/MaxDD < 0 (aufsteigend)
    positive = [row for row in summary_final if row[9] >= 0]
    negative = [row for row in summary_final if row[9] < 0]
    positive.sort(key=lambda x: x[9], reverse=True)
    negative.sort(key=lambda x: x[9])
    summary_final = positive + negative

    return summary_final

def main():
    parser = argparse.ArgumentParser(description="Simuliere 20 Trading-Strategien")
    parser.add_argument("--hit_rate", type=float, required=True, help="Trefferquote, z.B. 0.7")
    parser.add_argument("--avg_win", type=float, required=True, help="Durchschnittlicher Gewinn pro Trade")
    parser.add_argument("--avg_loss", type=float, required=True, help="Durchschnittlicher Verlust pro Trade")
    parser.add_argument("--num_simulations", type=int, default=200, help="Anzahl der Simulationen (default: 200)")
    parser.add_argument("--num_trades", type=int, default=400, help="Anzahl der Trades pro Simulation (default: 400)")
    parser.add_argument("--num_mc_shuffles", type=int, default=200, help="Anzahl der Shuffles pro Simulation (default: 200)")
    args = parser.parse_args()

    print("\nEingabewerte:")
    print(f"Trefferquote: {args.hit_rate:.2%}")
    print(f"Durchschnittlicher Gewinn pro Trade: {args.avg_win} €")
    print(f"Durchschnittlicher Verlust pro Trade: {args.avg_loss} €")
    print(f"Anzahl der Simulationen: {args.num_simulations}")
    print(f"Anzahl der Trades pro Simulation: {args.num_trades}")
    print(f"Anzahl der Shuffles pro Simulation: {args.num_mc_shuffles}")
    breakeven = find_break_even_hit_rate(args.avg_win, args.avg_loss)
    print(f"Break-even-Trefferquote: {breakeven:.2%}")

    summary = run_all_strategies(args.hit_rate, args.avg_win, args.avg_loss, args.num_trades, args.num_simulations, args.num_mc_shuffles)

    print("\nErgebnisse (Monte Carlo, basierend auf den Eingabewerten):\n")
    # Neue, breitere Formatierung für lange Strategienamen
    header = (
        f"{'Strategie':<90} {'Ø Gewinn (€)':>14} {'Ø Drawdown (€)':>16} {'Verhältnis':>12} "
        f"{'Min (€)':>12} {'Max (€)':>12} {'Min DD (€)':>14} {'Max DD (€)':>14} "
        f"{'Ø/Trade':>12} {'Gewinn/MaxDD':>18}"
    )
    print("\nErgebnisse (Monte Carlo, basierend auf den Eingabewerten):\n")
    # Neue, breitere Formatierung für lange Strategienamen
    header = (
        f"{'Strategie':<90} {'Ø Gewinn (€)':>14} {'Ø Drawdown (€)':>16} {'Verhältnis':>12} "
        f"{'Min (€)':>12} {'Max (€)':>12} {'Min DD (€)':>14} {'Max DD (€)':>14} "
        f"{'Ø/Trade':>12} {'Gewinn/MaxDD':>18}"
    )
    print(header)
    print("=" * len(header))
    for idx, (description, profit, dd, ratio, min_p, max_p, min_d, max_d, avg_per_trade, ratio_max_dd) in enumerate(summary):
        print(
            f"{description:<90} {profit:14.2f} {dd:16.2f} {ratio:12.2f} "
            f"{min_p:12.2f} {max_p:12.2f} {min_d:14.2f} {max_d:14.2f} "
            f"{avg_per_trade:12.2f} {ratio_max_dd:18.2f}"
        )
        if idx == 2:
            print("-" * len(header))

    # Erweiterte Ausgabe: Beste 4 Strategien im Vergleich zu "Konstante Positionsgröße 1"
    # Farbcode: Grün für beste, Rot für konstant
    from colorama import Fore, Style, init
    init(autoreset=True)

    # Finde Index der Konstanten Positionsgröße 1
    konst_idx = next((i for i, row in enumerate(summary) if row[0].startswith("Konstante Positionsgröße 1")), None)

    print("\n\n\nTop 4 Strategien im Vergleich zu 'Konstante Positionsgröße 1':")
    print("--------------------------------------------------------------")
    for idx in range(4):
        if idx >= len(summary):
            break
        # 1. Leerzeile
        print()
        # 2. Beste Strategie in grün
        row = summary[idx]
        print(Fore.GREEN + (
            f"{row[0]:<90} {row[1]:14.2f} {row[2]:16.2f} {row[3]:12.2f} "
            f"{row[4]:12.2f} {row[5]:12.2f} {row[6]:14.2f} {row[7]:14.2f} "
            f"{row[8]:12.2f} {row[9]:18.2f}"
        ) + Style.RESET_ALL)
        # 3. Konstante Positionsgröße 1 in rot
        if konst_idx is not None:
            konst_row = summary[konst_idx]
            print(Fore.RED + (
                f"{konst_row[0]:<90} {konst_row[1]:14.2f} {konst_row[2]:16.2f} {konst_row[3]:12.2f} "
                f"{konst_row[4]:12.2f} {konst_row[5]:12.2f} {konst_row[6]:14.2f} {konst_row[7]:14.2f} "
                f"{konst_row[8]:12.2f} {konst_row[9]:18.2f}"
            ) + Style.RESET_ALL)

if __name__ == "__main__":
    main()