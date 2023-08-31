<div align="center">
   <h2>PVplayer</h2>
   A free and powerful chess analysis tool.
</div>
<br>

PVplayer is a revolutionary new tool for chess analysis that uses a chess engine
such as [Stockfish](https://github.com/official-stockfish/Stockfish)
or [Lc0](https://github.com/LeelaChessZero/lc0) in order to provide accurate evaluations.

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
to calculate to a position where the eval is more meaningful.
Of course, this approach is not perfect, as the engine may not be able to always find the best move in the position,
but based on our assumption that modern engines are better at finding best moves than evaluating positions,
it will overall be more accurate than the engine itself.

### Basic requirements
- A working Python3 installation
- `python-chess` library
- An executable chess engine (e.g. Stockfish). 

## PVengine
A one-of-a-kind engine that makes better use of the power of strong engines (e.g. Stockfish).

### How it works
Being firmly based on the concept of PVplayer, PVengine searches each move using a chess engine, then
traces the PV line in every iteration for each move in order to provide an accurate evaluation of each move.
It then chooses the move with the best PV evaluation.

### Sample usage
```
cd src/engine
python3 engine_main.py
```

### Building
A shell script for building an executable for the engine (on Linux-based systems) is available at `engine_build.sh`, 
which uses pyinstaller. To build a faster executable (especially at startup), use `engine_build_fast.sh` instead.
The scripts can be slightly modified for building on Windows as well.

### Configuration
PVengine follows the UCI protocol, so you can type UCI commands just like in other engines, or use it in a chess GUI.
Options are set using the UCI interface only.


## PVtrace
A simple tool for tracing the PV line of a position.
This is essentially a simplified version of PVengine.

### Usage
```
cd src/tool
python3 PV_trace.py
```


### Other utilities
Available in the `src/utils` folder - used for various purposes.

---

## PVplayer Wiki
For articles on many topics related to PVplayer, including FAQs, please see the [project wiki](
https://github.com/XInTheDark/PVplayer/wiki).