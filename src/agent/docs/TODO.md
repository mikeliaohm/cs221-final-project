# TODOs

Baseline Agent

- Randomly shuffle the cards and distribute them between the two players with hidden hands.
- Rule based game playing strategy where the agent will try to win the current trick at all costs.

Intelligent Agent

- Randomly shuffle the cards and distribute them between the two players with hidden hands.
- Use CSP solver to find where the high cards are held by whom. Initial experiments found that 13 card assignment are solvable in one call but 26 card assignments all at once are just out of the question.
- Play the card with the highest score after running DDS solver.
- Use minimax to simulate the game? (might not have time to implement and it's not a very important feature either)
