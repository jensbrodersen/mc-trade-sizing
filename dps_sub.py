# ------------------------------------------------------------------------------------------
# Trading-Strategie-Simulator mit Monte-Carlo-Analyse und adaptiver Positionsgrößensteuerung
#
# Übersicht:
# Dieses Skript simuliert 20 verschiedene Trading-Strategien, bei denen die Positionsgröße
# dynamisch an Gewinn- oder Verlustserien angepasst wird. Es werden klassische Martingale-,
# Anti-Martingale-Ansätze sowie Strategien mit Pausenphasen nach Gewinnserien getestet.
#
# Funktionsweise:
# - Für gegebene Trefferquote, durchschnittlichen Gewinn und Verlust sowie Trade-Anzahl
#   werden zufällige Trade-Serien erzeugt (Monte-Carlo-Prinzip).
# - Optional kann ein Markov-Modell (1. oder 2. Ordnung) oder ein Regime-Switching-Modell aktiviert werden.
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
# Das Skript wird über die Kommandozeile gestartet. Beispielaufruf:
#   python dps_sub.py --hit_rate 0.81 --avg_win 307 --avg_loss 506
#   python dps_sub.py --hit_rate 0.81 --avg_win 307 --avg_loss 506 --use_markov --p_win_after_win 0.8 --p_win_after_loss 0.4
#   python dps_sub.py --hit_rate 0.81 --avg_win 307 --avg_loss 506 --use_markov2 --p_win_ww 0.8 --p_win_wl 0.6 --p_win_lw 0.5 --p_win_ll 0.3
#   python dps_sub.py --hit_rate 0.81 --avg_win 307 --avg_loss 506 --use_regime --regimes '[{"length":300,"hit_rate":0.9,"avg_win":200,"avg_loss":100},{"length":200,"hit_rate":0.5,"avg_win":100,"avg_loss":100},{"length":500,"hit_rate":0.2,"avg_win":100,"avg_loss":200}]'
# ------------------------------------------------------------------------------------------

import numpy as np
import argparse
import json as pyjson

def simulate_trades_dynamic(num_trades, hit_rate, avg_win, avg_loss):
    phases = [
        {'length': int(num_trades * 0.2), 'hit_rate': min(hit_rate + 0.2, 1.0), 'avg_win': avg_win * 1.1, 'avg_loss': avg_loss * 0.9},
        {'length': int(num_trades * 0.2), 'hit_rate': max(hit_rate - 0.3, 0.05), 'avg_win': avg_win * 0.9, 'avg_loss': avg_loss * 1.1},
        {'length': num_trades - int(num_trades * 0.4), 'hit_rate': hit_rate, 'avg_win': avg_win, 'avg_loss': avg_loss}
    ]
    results = []
    trades_left = num_trades
    for phase in phases:
        l = min(phase['length'], trades_left)
        if l <= 0:
            continue
        phase_results = np.random.choice(
            [phase['avg_win'], -phase['avg_loss']],
            size=l,
            p=[phase['hit_rate'], 1 - phase['hit_rate']]
        )
        results.extend(phase_results)
        trades_left -= l
        if trades_left <= 0:
            break
    if trades_left > 0:
        results.extend(np.random.choice([avg_win, -avg_loss], size=trades_left, p=[hit_rate, 1 - hit_rate]))
    return np.array(results)

def simulate_trades_markov(num_trades, hit_rate, avg_win, avg_loss, p_win_after_win=0.7, p_win_after_loss=0.5):
    results = []
    last_win = np.random.rand() < hit_rate
    if last_win:
        results.append(avg_win)
    else:
        results.append(-avg_loss)
    for _ in range(1, num_trades):
        if last_win:
            win = np.random.rand() < p_win_after_win
        else:
            win = np.random.rand() < p_win_after_loss
        if win:
            results.append(avg_win)
        else:
            results.append(-avg_loss)
        last_win = win
    return np.array(results)

def simulate_trades_markov2(num_trades, hit_rate, avg_win, avg_loss, p_win_ww=0.8, p_win_wl=0.6, p_win_lw=0.5, p_win_ll=0.3):
    results = []
    last = [np.random.rand() < hit_rate, np.random.rand() < hit_rate]
    for win in last:
        results.append(avg_win if win else -avg_loss)
    for _ in range(2, num_trades):
        if last[-2] and last[-1]:
            p = p_win_ww
        elif last[-2] and not last[-1]:
            p = p_win_wl
        elif not last[-2] and last[-1]:
            p = p_win_lw
        else:
            p = p_win_ll
        win = np.random.rand() < p
        results.append(avg_win if win else -avg_loss)
        last = [last[-1], win]
    return np.array(results)

def simulate_trades_regime_switch(num_trades, regimes=None):
    if regimes is None:
        regimes = [
            {'length': int(num_trades * 0.3), 'hit_rate': 0.9, 'avg_win': 200, 'avg_loss': 100},
            {'length': int(num_trades * 0.2), 'hit_rate': 0.5, 'avg_win': 100, 'avg_loss': 100},
            {'length': num_trades - int(num_trades * 0.5), 'hit_rate': 0.2, 'avg_win': 100, 'avg_loss': 200},
        ]
    results = []
    trades_left = num_trades
    for regime in regimes:
        l = min(regime['length'], trades_left)
        if l <= 0:
            continue
        phase_results = np.random.choice(
            [regime['avg_win'], -regime['avg_loss']],
            size=l,
            p=[regime['hit_rate'], 1 - regime['hit_rate']]
        )
        results.extend(phase_results)
        trades_left -= l
        if trades_left <= 0:
            break
    return np.array(results)

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
    state = {'win_streak': 0, 'loss_streak': 0, 'mode': 'trading', 'last_result': 0, 'last2_result': 0}

    for i in range(len(results)):
        trade_result = results[i] * position_size
        if state.get('mode', 'trading') == 'trading':
            equity.append(trade_result)
        else:
            equity.append(0)

        # Update streaks
        if results[i] > 0:
            state['win_streak'] += 1
            state['loss_streak'] = 0
        else:
            state['loss_streak'] += 1
            state['win_streak'] = 0

        # Für Strategien, die auf die letzten Trades schauen
        state['last2_result'] = state.get('last_result', 0)
        state['last_result'] = results[i]

        position_size, state = condition_func(results[i], position_size, state)

    cumulative_equity = np.cumsum(equity)
    return np.sum(equity), calculate_drawdown(cumulative_equity)

def make_condition_func(strategy_id):
    def func(result, size, state):
        # 1: Konstante Positionsgröße
        if strategy_id == 1:
            size = 1

        # 2: Nach Gewinn auf 2 erhöhen, nach Verlust zurück auf 1
        elif strategy_id == 2:
            size = 2 if result > 0 else 1

        # 3: Nach Gewinn auf 2 erhöhen, nach Verlust oder 2 Gewinnen zurück auf 1
        elif strategy_id == 3:
            if result > 0:
                state['win_streak'] += 1
                if state['win_streak'] >= 2:
                    size = 1
                else:
                    size = 2
            else:
                size = 1
                state['win_streak'] = 0

        # 4: Nach Gewinn auf 2 erhöhen, nach Verlust oder 3 Gewinnen zurück auf 1
        elif strategy_id == 4:
            if result > 0:
                state['win_streak'] += 1
                if state['win_streak'] >= 3:
                    size = 1
                else:
                    size = 2
            else:
                size = 1
                state['win_streak'] = 0

        # 5: Nach Gewinn auf 2 erhöhen, nach Verlust oder 4 Gewinnen zurück auf 1
        elif strategy_id == 5:
            if result > 0:
                state['win_streak'] += 1
                if state['win_streak'] >= 4:
                    size = 1
                else:
                    size = 2
            else:
                size = 1
                state['win_streak'] = 0

        # 6: Nach Verlust auf 2 erhöhen, nach Gewinn zurück auf 1
        elif strategy_id == 6:
            size = 2 if result <= 0 else 1

        # 7: Nach 2 Verlusten auf 2 erhöhen, nach Gewinn zurück auf 1
        elif strategy_id == 7:
            if result > 0:
                size = 1
                state['loss_streak'] = 0
            else:
                state['loss_streak'] += 1
                size = 2 if state['loss_streak'] >= 2 else 1

        # 8: Nach 3 Verlusten auf 2 erhöhen, nach Gewinn zurück auf 1
        elif strategy_id == 8:
            if result > 0:
                size = 1
                state['loss_streak'] = 0
            else:
                state['loss_streak'] += 1
                size = 2 if state['loss_streak'] >= 3 else 1

        # 9: Nach 1 Gewinn pausieren bis zum nächsten Verlust
        elif strategy_id == 9:
            if state.get('mode', 'trading') == 'trading':
                if result > 0:
                    state['mode'] = 'pause'
                size = 1
            elif state.get('mode') == 'pause':
                if result <= 0:
                    state['mode'] = 'trading'
                    size = 1
                else:
                    size = 0  # Pause: keine Position

        # 10: Nach 2 Gewinnen pausieren bis zum nächsten Verlust
        elif strategy_id == 10:
            if state.get('mode', 'trading') == 'trading':
                if result > 0:
                    state['win_streak'] += 1
                    if state['win_streak'] >= 2:
                        state['mode'] = 'pause'
                else:
                    state['win_streak'] = 0
                size = 1
            elif state.get('mode') == 'pause':
                if result <= 0:
                    state['mode'] = 'trading'
                    state['win_streak'] = 0
                    size = 1
                else:
                    size = 0  # Pause: keine Position

        # 11: Nach 3 Gewinnen pausieren bis zum nächsten Verlust
        elif strategy_id == 11:
            if state.get('mode', 'trading') == 'trading':
                if result > 0:
                    state['win_streak'] += 1
                    if state['win_streak'] >= 3:
                        state['mode'] = 'pause'
                else:
                    state['win_streak'] = 0
                size = 1
            elif state.get('mode') == 'pause':
                if result <= 0:
                    state['mode'] = 'trading'
                    state['win_streak'] = 0
                    size = 1
                else:
                    size = 0  # Pause: keine Position

        # 12: Nach 4 Gewinnen pausieren bis zum nächsten Verlust
        elif strategy_id == 12:
            if state.get('mode', 'trading') == 'trading':
                if result > 0:
                    state['win_streak'] += 1
                    if state['win_streak'] >= 4:
                        state['mode'] = 'pause'
                else:
                    state['win_streak'] = 0
                size = 1
            elif state.get('mode') == 'pause':
                if result <= 0:
                    state['mode'] = 'trading'
                    state['win_streak'] = 0
                    size = 1
                else:
                    size = 0  # Pause: keine Position

        # 13: Nach 2 Gewinnen auf 2 erhöhen, nach 2 Verlusten zurück auf 1
        elif strategy_id == 13:
            if result > 0:
                state['win_streak'] += 1
                if state['win_streak'] >= 2:
                    size = 2
            else:
                state['loss_streak'] += 1
                if state['loss_streak'] >= 2:
                    size = 1

        # 14: Nach 1 Gewinn und 1 Verlust auf 2 erhöhen, sonst auf 1
        elif strategy_id == 14:
            if result > 0 and state.get('last2_result', 0) <= 0:
                size = 2
            else:
                size = 1

        # 15: Nach 2 Gewinnen in Folge pausieren bis 1 Verlust, dann auf 2 erhöhen
        elif strategy_id == 15:
            if state.get('mode', 'trading') == 'trading':
                if result > 0:
                    state['win_streak'] += 1
                    if state['win_streak'] >= 2:
                        state['mode'] = 'pause'
                        size = 2
                    else:
                        size = 1
                else:
                    state['win_streak'] = 0
                    size = 1
            elif state.get('mode') == 'pause':
                if result <= 0:
                    state['mode'] = 'trading'
                    state['win_streak'] = 0
                    size = 1
                else:
                    size = 0  # Pause: keine Position

        # 16: Nach 2 Verlusten auf 2 erhöhen, nach 1 Gewinn pausieren bis zum nächsten Verlust
        elif strategy_id == 16:
            if state.get('mode', 'trading') == 'trading':
                if result > 0:
                    state['mode'] = 'pause'
                    size = 1
                else:
                    state['loss_streak'] += 1
                    if state['loss_streak'] >= 2:
                        size = 2
                    else:
                        size = 1
            elif state.get('mode') == 'pause':
                if result <= 0:
                    state['mode'] = 'trading'
                    size = 1
                else:
                    size = 0  # Pause: keine Position

        # 17: Nach 1 Gewinn auf 2 erhöhen, aber nur wenn davor 1 Verlust war, sonst auf 1
        elif strategy_id == 17:
            if result > 0 and state.get('last2_result', 0) <= 0:
                size = 2
            else:
                size = 1

        # 18: Nach 3 Gewinnen auf 3 erhöhen, nach 1 Verlust zurück auf 1
        elif strategy_id == 18:
            if result > 0:
                state['win_streak'] += 1
                if state['win_streak'] >= 3:
                    size = 3
            else:
                size = 1
                state['win_streak'] = 0

        # 19: Nach 2 Gewinnen auf 2 erhöhen, nach 2 Verlusten auf 3 erhöhen, sonst auf 1
        elif strategy_id == 19:
            if state['win_streak'] >= 2:
                size = 2
            elif state['loss_streak'] >= 2:
                size = 3
            else:
                size = 1

        # 20: Nach 1 Gewinn auf 2 erhöhen, nach 2 Verlusten auf 3 erhöhen, nach Gewinn zurück auf 1
        elif strategy_id == 20:
            if result > 0:
                size = 1
            elif state['loss_streak'] >= 2:
                size = 3
            elif result > 0:
                size = 2
            else:
                size = 1

        else:
            size = 1

        return size, state
    return func

def find_break_even_hit_rate(avg_win, avg_loss):
    return avg_loss / (avg_win + avg_loss)

def run_all_strategies(
    hit_rate, avg_win, avg_loss, num_trades, num_simulations, num_mc_shuffles,
    use_markov=False, p_win_after_win=0.7, p_win_after_loss=0.5,
    use_markov2=False, p_win_ww=0.8, p_win_wl=0.6, p_win_lw=0.5, p_win_ll=0.3,
    use_regime=False, regimes=None
):
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
        if use_regime:
            base_results = simulate_trades_regime_switch(num_trades, regimes)
        elif use_markov2:
            base_results = simulate_trades_markov2(
                num_trades, hit_rate, avg_win, avg_loss,
                p_win_ww, p_win_wl, p_win_lw, p_win_ll
            )
        elif use_markov:
            base_results = simulate_trades_markov(
                num_trades, hit_rate, avg_win, avg_loss,
                p_win_after_win, p_win_after_loss
            )
        else:
            base_results = simulate_trades_dynamic(num_trades, hit_rate, avg_win, avg_loss)
        for _ in range(num_mc_shuffles):
            np.random.shuffle(base_results)
            for i in range(1, 21):
                if i == 1:
                    profit, dd = strategy_static(base_results)
                else:
                    cond_func = make_condition_func(i)
                    profit, dd = strategy_dynamic(base_results, cond_func)

                try:
                    profit = float(profit)
                    dd = float(dd)
                except Exception as e:
                    print(f"Fehler beim Parsen von profit/dd für Strategie {i}: {profit}, {dd}")
                    raise

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

    positive = [row for row in summary_final if row[9] >= 0]
    negative = [row for row in summary_final if row[9] < 0]
    positive.sort(key=lambda x: x[9], reverse=True)
    negative.sort(key=lambda x: x[9], reverse=True)
    summary_final = positive + negative

    return summary_final

def main():
    parser = argparse.ArgumentParser(description="Simuliere 20 Trading-Strategien mit/ohne Markov-Korrelationen, Markov 2. Ordnung und Regime-Switching")
    parser.add_argument("--hit_rate", type=float, required=True, help="Trefferquote, z.B. 0.7")
    parser.add_argument("--avg_win", type=float, required=True, help="Durchschnittlicher Gewinn pro Trade")
    parser.add_argument("--avg_loss", type=float, required=True, help="Durchschnittlicher Verlust pro Trade")
    parser.add_argument("--num_simulations", type=int, default=200, help="Anzahl der Simulationen (default: 200)")
    parser.add_argument("--num_trades", type=int, default=400, help="Anzahl der Trades pro Simulation (default: 400)")
    parser.add_argument("--num_mc_shuffles", type=int, default=200, help="Anzahl der Shuffles pro Simulation (default: 200)")
    parser.add_argument("--use_markov", action="store_true", help="Korrelationen zwischen Trades (Markov-Kette, 1. Ordnung) verwenden")
    parser.add_argument("--p_win_after_win", type=float, default=0.7, help="P(Gewinn|Gewinn) für Markov-Modell 1. Ordnung")
    parser.add_argument("--p_win_after_loss", type=float, default=0.5, help="P(Gewinn|Verlust) für Markov-Modell 1. Ordnung")
    parser.add_argument("--use_markov2", action="store_true", help="Markov-Modell 2. Ordnung verwenden")
    parser.add_argument("--p_win_ww", type=float, default=0.8, help="P(Gewinn|Gewinn, Gewinn) für Markov 2. Ordnung")
    parser.add_argument("--p_win_wl", type=float, default=0.6, help="P(Gewinn|Gewinn, Verlust) für Markov 2. Ordnung")
    parser.add_argument("--p_win_lw", type=float, default=0.5, help="P(Gewinn|Verlust, Gewinn) für Markov 2. Ordnung")
    parser.add_argument("--p_win_ll", type=float, default=0.3, help="P(Gewinn|Verlust, Verlust) für Markov 2. Ordnung")
    parser.add_argument("--use_regime", action="store_true", help="Regime-Switching-Modell verwenden")
    parser.add_argument("--regimes", type=str, default=None, help="Regime-Liste als JSON-String")
    args = parser.parse_args()

    # --- Auffälliger Block für den aktuellen Fall ---
    print("\n" + "="*90)
    print("AKTUELLER SIMULATIONSFALL:")
    print(f"Trefferquote: {args.hit_rate:.2%}")
    if args.use_regime:
        print("Modus: Regime-Switching")
        if args.regimes:
            print(f"Regimes: {args.regimes}")
    elif args.use_markov2:
        print("Modus: Markov 2. Ordnung")
        print(f"P(Gewinn|GG): {args.p_win_ww}, P(Gewinn|GV): {args.p_win_wl}, P(Gewinn|VG): {args.p_win_lw}, P(Gewinn|VV): {args.p_win_ll}")
    elif args.use_markov:
        print("Modus: Markov 1. Ordnung")
        print(f"P(Gewinn|Gewinn): {args.p_win_after_win}, P(Gewinn|Verlust): {args.p_win_after_loss}")
    else:
        print("Modus: Ohne Markov")
    print("="*90 + "\n")

    print(f"Durchschnittlicher Gewinn pro Trade: {args.avg_win} €")
    print(f"Durchschnittlicher Verlust pro Trade: {args.avg_loss} €")
    print(f"Anzahl der Simulationen: {args.num_simulations}")
    print(f"Anzahl der Trades pro Simulation: {args.num_trades}")
    print(f"Anzahl der Shuffles pro Simulation: {args.num_mc_shuffles}")
    breakeven = find_break_even_hit_rate(args.avg_win, args.avg_loss)
    print(f"Break-even-Trefferquote: {breakeven:.2%}")

    # Regimes ggf. als JSON laden
    regimes = pyjson.loads(args.regimes) if args.use_regime and args.regimes else None

    summary = run_all_strategies(
        args.hit_rate, args.avg_win, args.avg_loss, args.num_trades,
        args.num_simulations, args.num_mc_shuffles,
        use_markov=args.use_markov,
        p_win_after_win=args.p_win_after_win,
        p_win_after_loss=args.p_win_after_loss,
        use_markov2=args.use_markov2,
        p_win_ww=args.p_win_ww,
        p_win_wl=args.p_win_wl,
        p_win_lw=args.p_win_lw,
        p_win_ll=args.p_win_ll,
        use_regime=args.use_regime,
        regimes=regimes
    )

    print("\nErgebnisse (Monte Carlo, basierend auf den Eingabewerten):\n")
    header = (
        f"{'Strategie':<90} {'Ø Gewinn (€)':>14} {'Ø Drawdown (€)':>16} {'Verhältnis':>12} "
        f"{'Min (€)':>12} {'Max (€)':>12} {'Min DD (€)':>14} {'Max DD (€)':>14} "
        f"{'Ø/Trade':>12} {'Gewinn/MaxDD':>18}"
    )
    print(header)
    print("=" * len(header))

    # a) Leerzeile
    print()

    # b) Modelltyp in gelber Schrift + Trefferquote (neues Format)
    try:
        from colorama import Fore, Style
        if args.use_regime:
            model_label = f"Trefferquote: {int(round(args.hit_rate * 100))} %  -  Regime-Switching-Modell"
        elif args.use_markov2:
            model_label = f"Trefferquote: {int(round(args.hit_rate * 100))} %  -  Markov 2. Ordnung"
        elif args.use_markov:
            model_label = f"Trefferquote: {int(round(args.hit_rate * 100))} %  -  Markov 1. Ordnung"
        else:
            model_label = f"Trefferquote: {int(round(args.hit_rate * 100))} %  -  Kein Markov"
        print(Fore.YELLOW + f"*** {model_label} ***" + Style.RESET_ALL)
    except ImportError:
        if args.use_regime:
            model_label = f"Trefferquote: {int(round(args.hit_rate * 100))} %  -  Regime-Switching-Modell"
        elif args.use_markov2:
            model_label = f"Trefferquote: {int(round(args.hit_rate * 100))} %  -  Markov 2. Ordnung"
        elif args.use_markov:
            model_label = f"Trefferquote: {int(round(args.hit_rate * 100))} %  -  Markov 1. Ordnung"
        else:
            model_label = f"Trefferquote: {int(round(args.hit_rate * 100))} %  -  Kein Markov"
        print(f"*** {model_label} ***")

    # c) Leerzeile
    print()

    # d) Originale Ergebnistabelle
    for idx, (description, profit, dd, ratio, min_p, max_p, min_d, max_d, avg_per_trade, ratio_max_dd) in enumerate(summary):
        print(
            f"{description:<90} {profit:14.2f} {dd:16.2f} {ratio:12.2f} "
            f"{min_p:12.2f} {max_p:12.2f} {min_d:14.2f} {max_d:14.2f} "
            f"{avg_per_trade:12.2f} {ratio_max_dd:18.2f}"
        )
        if idx == 2:
            print("-" * len(header))

    # Erweiterte Ausgabe: Beste 4 Strategien im Vergleich zu "Konstante Positionsgröße 1"
    try:
        from colorama import Fore, Style, init
        init(autoreset=True)
        konst_idx = next((i for i, row in enumerate(summary) if row[0].startswith("Konstante Positionsgröße 1")), None)
        print("\n\n\nTop 4 Strategien im Vergleich zu 'Konstante Positionsgröße 1':")
        print("--------------------------------------------------------------")
        for idx in range(4):
            if idx >= len(summary):
                break
            print()
            row = summary[idx]
            print(Fore.GREEN + (
                f"{row[0]:<90} {row[1]:14.2f} {row[2]:16.2f} {row[3]:12.2f} "
                f"{row[4]:12.2f} {row[5]:12.2f} {row[6]:14.2f} {row[7]:14.2f} "
                f"{row[8]:12.2f} {row[9]:18.2f}"
            ) + Style.RESET_ALL)
            if konst_idx is not None:
                konst_row = summary[konst_idx]
                print(Fore.RED + (
                    f"{konst_row[0]:<90} {konst_row[1]:14.2f} {konst_row[2]:16.2f} {konst_row[3]:12.2f} "
                    f"{konst_row[4]:12.2f} {konst_row[5]:12.2f} {konst_row[6]:14.2f} {konst_row[7]:14.2f} "
                    f"{konst_row[8]:12.2f} {konst_row[9]:18.2f}"
                ) + Style.RESET_ALL)
    except ImportError:
        pass

if __name__ == "__main__":
    main()