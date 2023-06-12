<div align="center">
   <h2>PVplayer</h2>
   A free and powerful chess analysis tool.
</div>
<br>


## 1) PVtrace tool

A revolutionary new tool for chess analysis that uses a chess engine
such as [Stockfish](https://github.com/official-stockfish/Stockfish) or [Lc0](https://github.com/LeelaChessZero/lc0)
to keep calculating the best lines starting from a position using a creative 'iterative iterative deepening' approach.
It can even be used to provide a more accurate evaluation of a position than the engine.

### How it works
Modern chess engines are extremely good at calculating the best move in a position.
However, one of its main weaknesses is evaluation. This tool is used to fix the following two main problems:
1) Evaluation can be unreliable.
This means that even though the best moves are usually very stable, the evaluation can fluctuate a lot in some positions.
This tool solves this problem by forcing the engine to re-evaluate the position after every few best moves are played,
resulting in increasingly accurate evaluation as the game progresses.
For instance, PVplayer with 10 iterations and 100 million nodes per iteration
usually provides a more accurate evaluation than Stockfish with 1 billion nodes, especially in complicated positions
where over-pruning causes a single search run to be unreliable.
2) Evaluation can be vague and meaningless. Especially after the
[Stockfish eval was normalized](https://github.com/official-stockfish/Stockfish/commit/ad2aa8c),
a +1.0 eval is now tied to a "50% win probability". This causes a huge problem for human users who have no idea whether
this +1.0 eval is enough to force a win. PVplayer solves this problem by running the search deep enough into the game
to calculate to a tablebase position where the Win/Loss/Draw is confirmed.

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


## 2) PVengine (WIP)

A one-of-a-kind engine that makes better use of the power of strong engines (e.g. Stockfish).

### How it works
Heavily inspired by the idea of PVtrace, PVengine searches each move using a chess engine, then
traces the PV line in every iteration for each move in order to provide an accurate evaluation of each move.
It then chooses the move with the best PV evaluation.

### Requirements
The same as PVtrace (see above).

### Sample usage
```
cd src
python3 engine_main.py
```

PVengine follows the UCI protocol, so you can type UCI commands just like in other engines.
