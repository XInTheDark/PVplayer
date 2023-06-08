## PVplayer

A revolutionary new tool for chess analysis that uses a chess engine
such as [Stockfish](https://github.com/official-stockfish/Stockfish) or [Lc0](https://github.com/LeelaChessZero/lc0)
to keep calculating the best lines starting from a position using a creative 'iterative iterative deepening' approach.
It can even be used to provide a more accurate evaluation of a position than the engine.

### Requirements
- `python-chess` library
- An executable chess engine (e.g. Stockfish). The path to the executable can be modified in [config.yml](src/config.yml).

### Sample usage
```
cd src
python3 PV_trace.py
```

### Configuration
There are many terms in `config.yml` that can be modified to suit your needs. 
This includes the limits for evaluation, number of PV moves to use for each iteration, etc. 
Modifying these terms may increase/decrease the accuracy and speed of the analysis.