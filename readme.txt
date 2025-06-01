DpsSimulator.py - Übersicht
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
Dabei wird die Reihenfolge der Trades mehrfach zufällig durchmischt
(Shuffling), um die Robustheit der Strategie gegenüber unterschiedlichen
Trade-Abfolgen zu testen. So lassen sich auch seltene Pechsträhnen und
Glücksserien realistisch abbilden.

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
d.h. die Reihenfolge der Trades wird pro Strategie 1000-mal zufällig
geshuffled. So werden insgesamt 20.000 Simulationsläufe (20 Strategien × 1000
Shuffles) durchgeführt und ausgewertet.

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

Erweiterte Modelle für realistischere Simulationen
==================================================

Markov-Modelle (1. und 2. Ordnung)
----------------------------------
Was ist ein Markov-Modell?
Ein Markov-Modell beschreibt, dass das Ergebnis eines Trades nicht völlig
unabhängig vom vorherigen ist, sondern von der Historie beeinflusst wird. In
der Praxis bedeutet das: Nach einem Gewinn ist die Wahrscheinlichkeit für
einen weiteren Gewinn (oder Verlust) oft anders als nach einem Verlust. Das
Modell kann so Gewinn- und Verlustserien (Streaks) realistischer abbilden.

Markov 1. Ordnung:  
Hier hängt die Gewinnwahrscheinlichkeit eines Trades nur vom Ergebnis des
unmittelbar vorherigen Trades ab.
- Beispiel: Nach einem Gewinn ist die Gewinnwahrscheinlichkeit z.B. 80%,
  nach einem Verlust nur 40%.
- Parameter:  
  --use_markov  
  --p_win_after_win (z.B. 0.8)  
  --p_win_after_loss (z.B. 0.4)  

Markov 2. Ordnung:  
Hier hängt die Gewinnwahrscheinlichkeit eines Trades von den letzten ZWEI
Ergebnissen ab.
- Beispiel: Nach zwei Gewinnen in Folge ist die Wahrscheinlichkeit für einen
  weiteren Gewinn z.B. 85%, nach Gewinn+Verlust vielleicht 60%, usw.
- Parameter:  
  --use_markov2  
  --p_win_ww (nach zwei Gewinnen)  
  --p_win_wl (nach Gewinn, dann Verlust)  
  --p_win_lw (nach Verlust, dann Gewinn)  
  --p_win_ll (nach zwei Verlusten)  

Warum ist das sinnvoll?  
In echten Märkten treten oft Phasen auf, in denen Gewinne oder Verluste
gehäuft auftreten (Streaks, Clustering). Einfache Zufallsmodelle
unterschätzen diese Effekte. Mit Markov-Modellen werden solche Phasen
realistisch simuliert, was die Robustheit und das Risiko von Strategien
besser testet.

Regime-Switching-Modell
-----------------------
Was ist ein Regime-Switching-Modell?
Hier wird die Handelsserie in verschiedene Marktphasen ("Regimes")
unterteilt, z.B. Bullenmarkt, Seitwärtsphase, Crash. Jede Phase hat eigene
Parameter für Trefferquote, Gewinn und Verlust. Die Länge und Reihenfolge
der Phasen kann frei gewählt werden.

Beispiel:  
1. 300 Trades mit hoher Trefferquote (z.B. 90%) und hohem Gewinn  
2. 200 Trades mit neutralen Parametern  
3. 500 Trades mit niedriger Trefferquote (z.B. 20%) und hohem Verlust  

Parameter:  
  --use_regime  
  --regimes '[{"length":300,"hit_rate":0.9,"avg_win":200,"avg_loss":100},
              {"length":200,"hit_rate":0.5,"avg_win":100,"avg_loss":100},
              {"length":500,"hit_rate":0.2,"avg_win":100,"avg_loss":200}]'

Warum ist das sinnvoll?  
Finanzmärkte wechseln zwischen verschiedenen Zuständen (Trends,
Seitwärtsphasen, Krisen). Strategien, die in einem Regime funktionieren,
können im nächsten scheitern. Mit Regime-Switching lässt sich testen, wie
robust eine Strategie über verschiedene Marktphasen hinweg ist. Das macht
die Simulation deutlich praxisnäher und zeigt, wie Strategien auf
schwierige Marktbedingungen reagieren.

Vergleich der Modelle
---------------------
- Zufallsmodell: Jeder Trade ist unabhängig, keine Streaks, keine
  Marktphasen.
- Markov 1./2. Ordnung: Abhängigkeit von 1 oder 2 vorherigen Trades,
  realistische Gewinn-/Verlustserien.
- Regime-Switching: Explizite Marktphasen mit eigenen Parametern,
  simuliert z.B. Bullenmarkt, Crash, Seitwärtsphase.

Fazit:  
Mit Markov- und Regime-Switching-Modellen werden die Simulationen deutlich
realistischer. Sie helfen, Strategien auf ihre Robustheit gegenüber echten
Marktbedingungen zu testen und Schwächen in bestimmten Phasen frühzeitig zu
erkennen.

Weitere Optionen siehe --help.