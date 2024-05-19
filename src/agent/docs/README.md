# Bridge Agent

## Instruction

To run a game setting for a specific board from .pbn file.

```bash
# This script will run the simulation until all boards have been played
python game.py --boardfile agent/boards/declarer.pbn --playonly True --boardno 1 --auto True

# Simulate all boards in a tournament record
python game.py --boardfile agent/boards/eyc00pbn/A1A10101.PBN --playonly True --boardno 1 --auto True

# Simulate all boards in a folder and log the results
python game.py --boarddir agent/boards/simulate --playonly True --boardno 1 --auto True --log True
```

## Tests

To run tests.

```python
# Run a single test case
python -m unittest agent/tests/test_cardset.py

# Run the test suite
python -m unittest discover -s agent/tests/
```

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
