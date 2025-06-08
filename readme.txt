## License

This project is licensed under the [MIT License](./LICENSE).



dps.py (Dynamic Position Sizing Simulator) - Overview
======================================================

This script simulates and compares 20 different position sizing strategies for a
series of trading trades with fixed profit and loss amounts and a given hit rate.
The goal is to evaluate the robustness and risk-return profile of various
approaches.

Process
-------

1. Configure the following parameters in `input.json`, which are derived from
   backtesting the trading systems:

  "hit_rate": 0.82,    # Corresponds to a win rate of 82%  
  "avg_win": 186,      # Corresponds to an average profit of 186 USD  
  "avg_loss": 219,     # Corresponds to an average loss of 219 USD  

  (Adjust the parameters for each system accordingly.)

2. Run the script with:  
   `python dps.py`

3. The script performs multiple Monte Carlo simulations and shuffles for each
   strategy to test robustness.

4. Key metrics are calculated and clearly output for each strategy.

Strategies
----------

- Constant position sizing  
- Martingale and anti-Martingale approaches  
- Streak strategies (increase or pause after wins/losses)  
- Pause and combination strategies  

Results
-------

The output includes for each strategy:  
- Average profit (€)  
- Average drawdown (€)  
- Profit to drawdown ratio  
- Min/max profit and drawdown  
- Average profit per trade  
- Profit / maximum drawdown  

Results are saved as an HTML report in the `/results` subfolder.

Notes
-----

- Hit rate, profit, and loss are constant (no market phases).  
- Since in practice every trading system performs worse than backtesting,  
  three scenarios are always simulated:  
  1. The system performs 10% worse consistently (for higher win rates)  
  2. The system performs 5% worse consistently (for lower win rates)  
  3. The theoretical backtest system without performance degradation.  
- No transaction costs or slippage are considered.  
- Strategies are flexible and can easily be extended.  
- The simulation is particularly suitable for comparing position sizing  
  strategies under identical conditions.

Monte Carlo Simulation
----------------------

Multiple Monte Carlo simulations are performed for each strategy.  
The order of trades is shuffled several times randomly to test the robustness
of the strategy against different trade sequences. This realistically models
rare losing streaks and winning runs.

Example:  
If you have 100 trades and set 1000 Monte Carlo simulations,  
then 1000 different randomly shuffled trade sequences per strategy are
simulated.  
With 20 strategies, that results in 20,000 simulation runs in total.  
Results are statistically evaluated and reported as averages and extreme
values (minimum/maximum) per strategy.

Example usage
-------------

`python dps.py`

By default, each strategy is tested with 1000 Monte Carlo simulations,  
meaning the trade order is shuffled 1000 times per strategy.  
A total of 20,000 simulation runs (20 strategies × 1000 shuffles) are
performed and analyzed.

Incorporating Win and Loss Streaks
----------------------------------

To make the simulation even more realistic, win and loss streaks can be
incorporated.  
Trades are not shuffled completely randomly, but phases with multiple
consecutive wins or losses are generated.  
This models typical market phases such as winning streaks or losing runs.

One way is to temporarily increase or decrease the hit rate for certain
sections of the trading series or to specifically create blocks of wins and
losses.  
This tests the robustness of strategies against longer winning or losing
phases.

Example:  
Instead of randomly shuffling 100 single trades,  
10 winning streaks of 5 wins each and 10 losing streaks of 5 losses each can
be generated,  
and then the order of these blocks is shuffled.  
Alternatively, the hit rate for certain periods can be set to, for example,
90% (winning phase) or 30% (losing phase).

This allows analyzing how different position sizing strategies react to longer
win or loss streaks and how robust they are during difficult market phases.

Advanced Models for More Realistic Simulations
==============================================

Markov Models (1st and 2nd Order)
---------------------------------

What is a Markov model?  
A Markov model describes that the outcome of a trade is not completely
independent of the previous one, but influenced by history.  
In practice, this means that after a win, the probability of another win (or
loss) is often different than after a loss.  
This model can more realistically represent win and loss streaks.

Markov 1st Order:  
The win probability of a trade depends only on the result of the immediately
preceding trade.  
- Example: After a win, the win probability might be 80%, after a loss only 40%.  
- Parameters:  
  --use_markov  
  --p_win_after_win (e.g. 0.8)  
  --p_win_after_loss (e.g. 0.4)  

Markov 2nd Order:  
The win probability depends on the last TWO trade results.  
- Example: After two wins in a row, the probability of another win might be 85%,
  after win+loss 60%, etc.  
- Parameters:  
  --use_markov2  
  --p_win_ww (after two wins)  
  --p_win_wl (win then loss)  
  --p_win_lw (loss then win)  
  --p_win_ll (after two losses)  

Why is this useful?  
In real markets, phases occur where wins or losses cluster (streaks,
clustering).  
Simple random models underestimate these effects.  
Markov models simulate these phases realistically, which better tests
strategy robustness and risk.

Regime-Switching Model
----------------------

What is a regime-switching model?  
Here the trading series is divided into different market phases ("regimes")  
e.g. bull market, sideways phase, crash. Each phase has its own parameters
for hit rate, profit, and loss.  
The length and order of phases can be freely chosen.

Example:  
1. 300 trades with high hit rate (e.g. 90%) and high profit  
2. 200 trades with neutral parameters  
3. 500 trades with low hit rate (e.g. 20%) and high loss  

Parameters:  
  --use_regime  
  --regimes '[{"length":300,"hit_rate":0.9,"avg_win":200,"avg_loss":100},  
              {"length":200,"hit_rate":0.5,"avg_win":100,"avg_loss":100},  
              {"length":500,"hit_rate":0.2,"avg_win":100,"avg_loss":200}]'  

Why is this useful?  
Financial markets switch between different states (trends, sideways phases,
crises).  
Strategies that work in one regime may fail in another.  
Regime-switching allows testing how robust a strategy is across market phases.  
This makes simulations much more realistic and shows how strategies react to
difficult conditions.

Model Comparison
----------------

- Random model: Each trade is independent, no streaks, no market phases.  
- Markov 1st/2nd order: Dependency on 1 or 2 previous trades, realistic
  win/loss streaks.  
- Regime-switching: Explicit market phases with individual parameters,
  simulates e.g. bull market, crash, sideways phase.

Summary:  
Markov and regime-switching models make simulations much more realistic.  
They help test strategy robustness against real market conditions and identify
weaknesses early.
