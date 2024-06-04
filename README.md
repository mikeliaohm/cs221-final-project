# A Bridge Agent - CS221 Final Project

This repo hosts the source code for the course project - A Bridge Agent. The implementation includes a Baseline, an Oracle, and minimax agents with different configurations. Also, there is an implementation of a probabilistic inference model which we solve using a CSP solver. The CSP class and solver algorithm are reproduced from the HW. Other than these, all implementation was started from scratch since the start of the 2024 Spring quarter.

These implementations can be found inside the [src/agent](./src/agent/) folder. The final results of the performances of the various agents are included in [src/agent/results](./src/agent/results/). The datasets are located in [src/agent/boards/dataset](./src/agent/boards/dataset/). This folder contains the data we use to compile the final reports. Some other datasets can be found in [src/agent/boards/other_dataset](./src/agent/boards/other_dataset/).

We reuse the game simulator built by Lorand Dali. As a result, the repo was originally created as a fork from [BEN](https://github.com/lorserker/ben). There is some refactoring in [game.py](./src/game.py), which define the game simulator, in order to install our own agents to play the game. Most other files are left unchanged. The original README file has been renamed as [README_BEN](README_BEN.md). Our own agents share some interfaces with the robots in BEN to interact with the game engine. This is to keep the states consistent with those kept by the game engine. The engine checks state consistency from time to time (such as number of cards remaining, etc).

Finally, through those interfaces, the engine invokes will invoke an agent when it's the agent's turn to play the card. There are more arguments passed in than we need. As our agents are self-contained (meaning that our agents keep their own states for the different algorithms for card playing), some of the arguments passed through the interfaces are left unused.

## Instruction

To run a game setting for a specific board from .pbn file.

```bash
# This script will run the simulation until all boards have been played
python game.py --boardfile agent/boards/other_dataset/declarer.pbn --playonly True --auto True

# Simulate all boards in a tournament record
python game.py --boardfile agent/boards/other_dataset/eyc00pbn/A1A10101.PBN --playonly True --auto True

# Simulate all boards in a folder and log the results
python game.py --boarddir agent/boards/other_dataset/simulate --playonly True --auto True --log True
```

To select the various agents to run the simulator, use `--agents` with the following options.

1. Baseline -> "baseline"
2. Oracle -> "oracle"
3. Minimax -> "minimax"
4. Minimax_Bayes -> "minimaxbayes"
5. Minimax_Opt -> "minimaxopt"

To increase the search depth in the minimax agents, try alter the the search depth when the recurse function is invoked [recurse](https://github.com/mikeliaohm/bridge/blob/046e17301754c233bb18aeb3ddc1dfcbfb6f55f3/src/agent/minimax_agent.py#L145-L146).

To enable logging, run the simulator with `--log True`.

## Tests

To run tests.

```python
# Run a single test case
python -m unittest agent/tests/test_cardset.py

# Run the test suite
python -m unittest discover -s agent/tests/
```

## Analyze the performance of various agents

First, move the logs from the game simulation from each of the agents to be compared. For example, we will put the results from the three agents in the folder of agent/logs such that

```text
-- reports
   -- baseline
      -- result1.json
      -- result2.json
   -- minimax
      -- result1.json
      -- result2.json
   -- oracle
      -- result1.json
      -- result2.json
```

Then run the following command to compile the results into two separate files that group together the performances of the three agents, baseline, minimax, and oracle.

```python
# Compile individual reports from different agents
python agent/analyze.py --dir agent/logs/reports

# Compile the performance report into a results.json file
python agent/performances.py

# Plot the results
python agent/results/chart.py
```

The above commands are grouped together in [compile_reports](./src/compile_reports.sh) script.

## Card to Index Mapping

```text
0: SA   1: SK   2: SQ   3: SJ   4: ST   5: S9   6: S8   7: S7   8: S6   9: S5   10: S4  11: S3  12: S2
13: HA  14: HK  15: HQ  16: HJ  17: HT  18: H9  19: H8  20: H7  21: H6  22: H5  23: H4  24: H3  25: H2
26: DA  27: DK  28: DQ  29: DJ  30: DT  31: D9  32: D8  33: D7  34: D6  35: D5  36: D4  37: D3  38: D2
39: CA  40: CK  41: CQ  42: CJ  43: CT  44: C9  45: C8  46: C7  47: C6  48: C5  49: C4  50: C3  51: C2
```

## Sample PBN file

The pbn file has the format looks like the following.

```text
% PBN 1.0
% EXPORT
%
[Event ""]
[Site ""]
[Date "1999.09.08"]
[Board "1"]
[West "GIB 2.6.2"]
[North "GIB 2.6.2"]
[East "GIB 2.6.2"]
[South "Robert Vasicek"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "N:AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983"]
[Declarer "N"]
[Contract "6D"]
[Result "13"]
[Score "NS 940"]
[Auction "N"]
1D 2H 3C 3H
3S Pass 4D Pass
5C Pass 5H Pass
6D Pass Pass Pass
[Play "E"]
C7 C4 C9 CJ
DQ D4 D3 DA
D9 DK D7 D2
H9 C5 C3 CK
H8 D8 H6 H7
H2 CA C8 C2
H5 CQ HK HT
*

[Event ""]
[Site "#"]
[Date "1999.09.10"]
[Board "1"]
[West "GIB 2.6.3"]
[North "GIB 2.6.3"]
[East "GIB 2.6.3"]
[South "Vlad"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "N:AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983"]
[Declarer "N"]
[Contract "6D"]
[Result "13"]
[Score "NS 940"]
[Auction "N"]
1D      2H      3C      3H
Pass    4H      5D      Pass
5H      X       6D      Pass
Pass    Pass    
[Play "E"]
DQ D4 D7 DA 
H2 D8 H6 H7 
D9 DK D3 D2 
H9 DJ C3 D5 
*

[Event "#"]
[Site ""]
[Date "1999.09.02"]
[Board "1"]
[West "GIB 2.6.3"]
[North "GIB 2.6.3"]
[East "GIB 2.6.3"]
[South "ALBERT"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "N:AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983"]
[Declarer "N"]
[Contract "5DX"]
[Result "12"]
[Score "NS 650"]
[Auction "N"]
1D 3H 4H Pass
5D X Pass Pass
Pass
[Play "E"]
HA D4 HK H7
D9 DK D3 D2
DQ D8 D7 DT
H5 DJ HQ HT
*

[Event ""]
[Site "#"]
[Date "1999.09.12"]
[Board "1"]
[West "GIB 2.6.3"]
[North "GIB 2.6.3"]
[East "GIB 2.6.3"]
[South "Danellakis D"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "N:AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983"]
[Declarer "N"]
[Contract "6D"]
[Result "13"]
[Score "NS 940"]
[Auction "N"]
1D      2H      3C      3H
Pass    4H      5D      Pass
5H      X       6D      Pass
Pass    Pass    
[Play "E"]
C7 C4 C3 CK 
D9 DK D7 D2 
DQ D4 D3 DA 
*

[Event "#"]
[Site "#"]
[Date "1999.09.04"]
[Board "1"]
[West "GIB 2.6.3"]
[North "GIB 2.6.3"]
[East "GIB 2.6.3"]
[South "max3"]
[Dealer "N"]
[Vulnerable "None"]
[Deal "N:AJ4.T7.AT652.KJ2 K73.A985432.Q9.7 985..KJ84.AQT654 QT62.KQJ6.73.983"]
[Declarer "N"]
[Contract "5HX"]
[Result "5"]
[Score "NS -1400"]
[Auction "N"]
1D      2H      3C      3H
Pass    4H      5D      Pass
5H      X       Pass    Pass
Pass    
[Play "E"]
D9 D4 D3 DT 
DQ DK D7 DA 
C7 CT C3 C2 
H5 C6 C9 CJ 
S3 S5 SQ SA 
H9 C4 H6 H7 
SK S8 S6 S4 
S7 S9 ST SJ 
H8 D8 HJ D6 
H4 C5 HK HT 
H2 CQ S2 D2 
HA DJ HQ CK 
H3 CA C8 D5 
```
