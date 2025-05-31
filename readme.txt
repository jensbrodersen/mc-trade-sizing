MyTradingSimulator_sub.py - Übersicht
=====================================

Dieses Skript simuliert und vergleicht 20 verschiedene Positionsgrößen-
Strategien für eine Serie von Trading-Trades mit festen Gewinn- und
Verlustbeträgen und einer vorgegebenen Trefferquote. Ziel ist es, die
Robustheit und das Risiko-Ertrags-Profil verschiedener Ansätze zu bewerten.

Ablauf
------
1. Starte das Skript mit:
   python MyTradingSimulator_sub.py --hit_rate 0.7 --avg_win 100 --avg_loss 150
   (Passe die Parameter nach Bedarf an.)

2. Das Skript führt für jede Strategie mehrere Monte-Carlo-Simulationen
   und Shuffles durch, um die Robustheit zu testen.

3. Die wichtigsten Kennzahlen werden für jede Strategie berechnet und
   übersichtlich ausgegeben.

Strategien
----------
- Konstante Positionsgröße
- Martingale- und Anti-Martingale-Ansätze
- Streak-Strategien (nach Gewinn/Verlust erhöhen oder pausieren)
- Pausen- und Kombinationsstrategien

Ergebnisse
----------
Die Ausgabe enthält für jede Strategie:
- Ø Gewinn (€)
- Ø Drawdown (€)
- Verhältnis Gewinn/Drawdown
- Min/Max Gewinn und Drawdown
- Ø Gewinn pro Trade
- Gewinn/Maximaler Drawdown

Die besten Strategien werden farblich hervorgehoben (grün für beste,
rot für konstante Positionsgröße).

Hinweise
--------
- Trefferquote, Gewinn und Verlust sind konstant (keine Marktphasen).
- Es werden keine Transaktionskosten oder Slippage berücksichtigt.
- Die Strategien sind flexibel und können leicht erweitert werden.
- Die Simulation eignet sich besonders zum Vergleich von
  Positionsgrößen-Strategien unter identischen Bedingungen.

Monte-Carlo-Simulation
----------------------
Für jede Strategie werden mehrere Monte-Carlo-Simulationen durchgeführt.
Dabei wird die Reihenfolge der Trades mehrfach zufällig durchmischt (Shuffling),
um die Robustheit der Strategie gegenüber unterschiedlichen Trade-Abfolgen zu
testen. So lassen sich auch seltene Pechsträhnen und Glücksserien realistisch
abbilden.

Beispiel: 
Angenommen, du hast 100 Trades und stellst 1000 Monte-Carlo-Simulationen ein,
dann werden insgesamt 1000 verschiedene, zufällig gemischte Handelsserien pro
Strategie simuliert. Das ergibt bei 20 Strategien insgesamt 20.000
Simulationsläufe. Die Ergebnisse werden statistisch ausgewertet und als
Durchschnittswerte sowie Extremwerte (Minimum/Maximum) für jede Strategie
ausgegeben.

Beispielaufruf
--------------
python MyTradingSimulator_sub.py --hit_rate 0.81 --avg_win 307 --avg_loss 506

Standardmäßig wird jede Strategie mit 1000 Monte-Carlo-Simulationen getestet,
d.h. die Reihenfolge der Trades wird pro Strategie 1000-mal zufällig geshuffled.
So werden insgesamt 20.000 Simulationsläufe (20 Strategien × 1000 Shuffles)
durchgeführt und ausgewertet.

Einbau von Gewinn- und Verlustserien
------------------------------------
Um die Simulation noch realistischer zu machen, können Gewinn- und
Verlustserien (Streaks) eingebaut werden. Dabei werden die Trades nicht
vollständig zufällig verteilt, sondern es werden gezielt Phasen mit mehreren
Gewinnen oder Verlusten hintereinander erzeugt. So lassen sich typische
Marktphasen wie Gewinnsträhnen oder Pechserien abbilden.

Eine Möglichkeit ist, die Trefferquote für bestimmte Abschnitte der
Handelsserie temporär zu erhöhen oder zu senken, oder gezielt Blöcke von
Gewinnen und Verlusten zu erzeugen. Dadurch werden Strategien auf ihre
Robustheit gegenüber längeren Gewinn- oder Verlustphasen getestet.

Beispiel:  
Statt 100 Einzeltrades zufällig zu mischen, werden z.B. 10 Gewinnserien mit je
5 Gewinnen und 10 Verlustserien mit je 5 Verlusten erzeugt und dann die
Reihenfolge dieser Blöcke gemischt. Alternativ kann die Trefferquote für
bestimmte Zeiträume auf z.B. 90% (Gewinnphase) oder 30% (Verlustphase)
gesetzt werden.

So lässt sich analysieren, wie die verschiedenen Positionsgrößen-Strategien
auf längere Gewinn- oder Verlustserien reagieren und wie robust sie in
schwierigen Marktphasen sind.

Weitere Optionen siehe --help.