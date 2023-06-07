## PVplayer

A simple tool for chess analysis that uses a chess engine such as [Stockfish](github.com/official-stockfish/Stockfish) 
to keep calculating the best lines starting from a position.
It can be used to provide a close estimation of a position's evaluation, 
and can be more accurate than the engine's evaluation in one iteration.

### Requirements
- `python-chess` library
- An executable chess engine (e.g. Stockfish). The path to the executable can be modified in [config.yml](src/config.yml).

### Sample usage
```
cd src
python3 PV_trace.py
```

### Configuration
There are many terms in PV_trace.py that can be modified to suit your needs. 
This includes the limits for evaluation, number of PV moves to use for each iteration, etc. 
Modifying these terms may increase or decrease the accuracy of the analysis.