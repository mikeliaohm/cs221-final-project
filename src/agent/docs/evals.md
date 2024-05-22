To create a Python program that compares the performance of agents based on the output files from bridge games, you can follow these steps:

1. **Read and Parse JSON Files**: Load the JSON files.
2. **Extract Relevant Data**: Extract the scores and tricks won by each agent.
3. **Compare the Performance**: Compare the agents based on the extracted data.

Here's a sample implementation of the program:

```python
import os
import json
from typing import List, Dict

def load_json_files(directory: str) -> List[Dict]:
    """
    Load all JSON files from the specified directory.
    """
    json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
    data = []
    for file in json_files:
        with open(os.path.join(directory, file), 'r') as f:
            data.append(json.load(f))
    return data

def extract_performance_data(json_data: List[Dict]) -> List[Dict]:
    """
    Extract performance data from the loaded JSON data.
    """
    performance_data = []
    for data in json_data:
        # Assuming the JSON structure contains 'agent', 'score', and 'tricks_won' keys
        agent_data = {
            'agent': data.get('agent', 'Unknown Agent'),
            'score': data.get('score', 0),
            'tricks_won': data.get('tricks_won', 0)
        }
        performance_data.append(agent_data)
    return performance_data

def compare_agents(performance_data: List[Dict]) -> None:
    """
    Compare agents based on their scores and tricks won.
    """
    # Sort agents by score and tricks won
    sorted_by_score = sorted(performance_data, key=lambda x: x['score'], reverse=True)
    sorted_by_tricks = sorted(performance_data, key=lambda x: x['tricks_won'], reverse=True)
    
    print("Agents sorted by score:")
    for agent in sorted_by_score:
        print(f"Agent: {agent['agent']}, Score: {agent['score']}, Tricks Won: {agent['tricks_won']}")
    
    print("\nAgents sorted by tricks won:")
    for agent in sorted_by_tricks:
        print(f"Agent: {agent['agent']}, Score: {agent['score']}, Tricks Won: {agent['tricks_won']}")

def main(directory: str):
    json_data = load_json_files(directory)
    performance_data = extract_performance_data(json_data)
    compare_agents(performance_data)

if __name__ == "__main__":
    directory = 'path_to_your_directory'  # Replace with your directory path
    main(directory)
```

### Explanation

1. **Loading JSON Files**: The `load_json_files` function loads all JSON files from a specified directory.
2. **Extracting Performance Data**: The `extract_performance_data` function extracts relevant data such as agent name, score, and tricks won from the loaded JSON data.
3. **Comparing Agents**: The `compare_agents` function sorts and prints the agents based on their scores and tricks won.

### Running the Program

- Place your JSON files in a directory.
- Update the `directory` variable in the `main` function to point to your directory.
- Run the script to see the comparison of agents.

This program assumes that the JSON files contain keys like `agent`, `score`, and `tricks_won`. Adjust the keys based on your actual JSON structure. If you provide more details about the JSON structure, I can refine the script accordingly.