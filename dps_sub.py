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

#origdef find_break_even_hit_rate(avg_win, avg_loss):
#orig    return avg_loss / (avg_win + avg_loss)
#new function start
def find_break_even_hit_rate(avg_win, avg_loss, mode):
    """ Calculates the break-even hit rate with additional safety checks and debugging prints. """

    # Prevent division by zero
    if avg_win is None or avg_loss is None or avg_win <= 0 or avg_loss <= 0:
        print("❌ ERROR: Invalid values for avg_win or avg_loss! Calculation not possible.")
        return None  # Exit early to prevent errors

    # Basic calculation of break-even hit rate
    base_rate = avg_loss / (avg_win + avg_loss)

    # Check for infinite values (overflow protection)
    if base_rate == float('inf'):
        print("❌ ERROR: Calculation resulted in an infinite value!")
        return None
    
    # Adjust the calculation based on the selected mode
    if mode == "1st Order Markov":
        p_adj = 0.7  # Example value, should be dynamically determined
        #print(f"DEBUG: 1st Order Markov active -> Adjustment factor {1 + (p_adj - 0.5) / 5:.4f}")
        base_rate *= (1 + (p_adj - 0.5) / 5)

    elif mode == "2nd Order Markov":
        p_adj = 0.8  # Example value
        #print(f"DEBUG: 2nd Order Markov active -> Adjustment factor {1 + (p_adj - 0.5) / 4:.4f}")
        base_rate *= (1 + (p_adj - 0.5) / 4)

    elif mode == "Regime Switching":
        # Example calculation based on multiple regimes
        avg_regime_hit_rate = 0.6  # Example value, should be loaded from JSON
        #print(f"DEBUG: Regime Switching active -> Average regime hit rate={avg_regime_hit_rate:.4f}")
        base_rate *= (1 + (avg_regime_hit_rate - 0.5) / 3)

    return base_rate
#new function end

def run_all_strategies(
    hit_rate, avg_win, avg_loss, num_trades, num_simulations, num_mc_shuffles,
    use_markov=False, p_win_after_win=0.7, p_win_after_loss=0.5,
    use_markov2=False, p_win_ww=0.8, p_win_wl=0.6, p_win_lw=0.5, p_win_ll=0.3,
    use_regime=False, regimes=None
):
    descriptions = {
        1: "Constant position size 1",
        2: "Increase to 2 after win, reset to 1 after loss",
        3: "Increase to 2 after win, reset to 1 after loss or 2 wins",
        4: "Increase to 2 after win, reset to 1 after loss or 3 wins",
        5: "Increase to 2 after win, reset to 1 after loss or 4 wins",
        6: "Increase to 2 after loss, reset to 1 after win",
        7: "Increase to 2 after 2 losses, reset to 1 after win",
        8: "Increase to 2 after 3 losses, reset to 1 after win",
        9: "Pause after 1 win until next loss",
        10: "Pause after 2 wins until next loss",
        11: "Pause after 3 wins until next loss",
        12: "Pause after 4 wins until next loss",
        13: "Increase to 2 after 2 wins, reset to 1 after 2 losses",
        14: "Increase to 2 after 1 win and 1 loss, else 1",
        15: "Pause after 2 consecutive wins until 1 loss, then increase to 2",
        16: "Increase to 2 after 2 losses, pause after 1 win until next loss",
        17: "Increase to 2 after 1 win only if preceded by 1 loss, else 1",
        18: "Increase to 3 after 3 wins, reset to 1 after 1 loss",
        19: "Increase to 2 after 2 wins, to 3 after 2 losses, else 1",
        20: "Increase to 2 after 1 win, to 3 after 2 losses, reset to 1 after win",
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
                    print(f"Error parsing profit/dd for strategy {i}: {profit}, {dd}")
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
    parser = argparse.ArgumentParser(description="Simulate 20 trading strategies with/without Markov correlations, second-order Markov, and regime switching")
    parser.add_argument("--hit_rate", type=float, required=True, help="Hit rate, e.g. 0.7")
    parser.add_argument("--avg_win", type=float, required=True, help="Average win per trade")
    parser.add_argument("--avg_loss", type=float, required=True, help="Average loss per trade")
    parser.add_argument("--num_simulations", type=int, default=200, help="Number of simulations (default: 200)")
    parser.add_argument("--num_trades", type=int, default=400, help="Number of trades per simulation (default: 400)")
    parser.add_argument("--num_mc_shuffles", type=int, default=200, help="Number of shuffles per simulation (default: 200)")
    parser.add_argument("--use_markov", action="store_true", help="Use Markov chain correlations (1st order)")
    parser.add_argument("--p_win_after_win", type=float, default=0.7, help="P(win|win) for 1st order Markov model")
    parser.add_argument("--p_win_after_loss", type=float, default=0.5, help="P(win|loss) for 1st order Markov model")
    parser.add_argument("--use_markov2", action="store_true", help="Use 2nd order Markov model")
    parser.add_argument("--p_win_ww", type=float, default=0.8, help="P(win|win,win) for 2nd order Markov")
    parser.add_argument("--p_win_wl", type=float, default=0.6, help="P(win|win,loss) for 2nd order Markov")
    parser.add_argument("--p_win_lw", type=float, default=0.5, help="P(win|loss,win) for 2nd order Markov")
    parser.add_argument("--p_win_ll", type=float, default=0.3, help="P(win|loss,loss) for 2nd order Markov")
    parser.add_argument("--use_regime", action="store_true", help="Use regime switching model")
    parser.add_argument("--regimes", type=str, default=None, help="Regime list as JSON string")
    args = parser.parse_args()

    print("\n" + "="*90)
    print("CURRENT SIMULATION SETTING:")
    print(f"Hit rate: {args.hit_rate:.2%}")
    if args.use_regime:
        print("Mode: Regime Switching")
        if args.regimes:
            print(f"Regimes: {args.regimes}")
    elif args.use_markov2:
        print("Mode: 2nd Order Markov")
        print(f"P(win|WW): {args.p_win_ww}, P(win|WL): {args.p_win_wl}, P(win|LW): {args.p_win_lw}, P(win|LL): {args.p_win_ll}")
    elif args.use_markov:
        print("Mode: 1st Order Markov")
        print(f"P(win|win): {args.p_win_after_win}, P(win|loss): {args.p_win_after_loss}")
    else:
        print("Mode: No Markov")
    print("="*90 + "\n")

    print(f"Average win per trade: €{args.avg_win}")
    print(f"Average loss per trade: €{args.avg_loss}")
    print(f"Number of simulations: {args.num_simulations}")
    print(f"Number of trades per simulation: {args.num_trades}")
    print(f"Number of shuffles per simulation: {args.num_mc_shuffles}")

    mode = "No Markov"
    if args.use_regime:
        mode = "Regime Switching"
    elif args.use_markov2:
        mode = "2nd Order Markov"
    elif args.use_markov:
        mode = "1st Order Markov"

    breakeven = find_break_even_hit_rate(args.avg_win, args.avg_loss, mode)
    print(f"Break-even hit rate: {breakeven:.2%}")

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

    print("\nResults (Monte Carlo, based on input parameters):\n")
    header = (
        f"{'Strategy':<90} {'Avg Profit (€)':>14} {'Avg Drawdown (€)':>16} {'Ratio':>12} "
        f"{'Min (€)':>12} {'Max (€)':>12} {'Min DD (€)':>14} {'Max DD (€)':>14} "
        f"{'Avg/Trade':>12} {'Profit/MaxDD':>18}"
    )
    print(header)
    print("=" * len(header))

    print()

    try:
        from colorama import Fore, Style
        if args.use_regime:
            model_label = f"Hit rate: {int(round(args.hit_rate * 100))}%  -  Regime Switching Model"
        elif args.use_markov2:
            model_label = f"Hit rate: {int(round(args.hit_rate * 100))}%  -  2nd Order Markov"
        elif args.use_markov:
            model_label = f"Hit rate: {int(round(args.hit_rate * 100))}%  -  1st Order Markov"
        else:
            model_label = f"Hit rate: {int(round(args.hit_rate * 100))}%  -  No Markov"
        print(Fore.YELLOW + f"*** {model_label} ***" + Style.RESET_ALL)
    except ImportError:
        if args.use_regime:
            model_label = f"Hit rate: {int(round(args.hit_rate * 100))}%  -  Regime Switching Model"
        elif args.use_markov2:
            model_label = f"Hit rate: {int(round(args.hit_rate * 100))}%  -  2nd Order Markov"
        elif args.use_markov:
            model_label = f"Hit rate: {int(round(args.hit_rate * 100))}%  -  1st Order Markov"
        else:
            model_label = f"Hit rate: {int(round(args.hit_rate * 100))}%  -  No Markov"
        print(f"*** {model_label} ***")

    print()

    for idx, (description, profit, dd, ratio, min_p, max_p, min_d, max_d, avg_per_trade, ratio_max_dd) in enumerate(summary):
        print(
            f"{description:<90} {profit:14.2f} {dd:16.2f} {ratio:12.2f} "
            f"{min_p:12.2f} {max_p:12.2f} {min_d:14.2f} {max_d:14.2f} "
            f"{avg_per_trade:12.2f} {ratio_max_dd:18.2f}"
        )
        if idx == 2:
            print("-" * len(header))

    try:
        from colorama import Fore, Style, init
        init(autoreset=True)
        konst_idx = next((i for i, row in enumerate(summary) if row[0].startswith("Constant position size 1")), None)
        print("\n\n\nTop 4 strategies compared to 'Constant position size 1':")
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
