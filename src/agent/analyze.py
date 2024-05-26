import os
import json
from typing import List, Dict
import argparse

def load_json_files(json_files: List[str]) -> List[Dict]:
    """
    Load all JSON files from the specified directory.
    """
    data = {}
    for file in json_files:
        agent_name = file.split('/')[-2]
        with open(file, 'r') as f:
            data[agent_name] = json.load(f)
    return data

def extract_performance_data(json_data: Dict) -> Dict:
    """
    Extract performance data from the loaded JSON data.
    """
    performance_data = {}
    for agent, records in json_data.items():
        for data in records:
            board_no = data['Board number']
            if board_no not in performance_data:
                performance_data[board_no] = {
                    'Declarer': data['Declarer'],
                    'Contract': data['Contract'],
                    'Deal': data['Deal']}

            current_data = performance_data[board_no]
            current_data[f'{agent}_score'] = data['Score']
            current_data[f'{agent}_tricks'] = data['Tricks won']
            performance_data[board_no] = current_data
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
    subdirectories = []
    for d in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, d)):
            subdirectories.append(os.path.join(directory, d))

    # Lookup JSON files in subdirectories
    reports = {}
    for subdirectory in subdirectories:
        for f in os.listdir(subdirectory):
            if f.endswith('.json'):
                if f not in reports:
                    reports[f] = [os.path.join(subdirectory, f)]
                else:
                    reports[f].append(os.path.join(subdirectory, f))

    for database, files in reports.items():
        print(f"Loading Database: {database}")
        json_data = load_json_files(files)
        performance_data = extract_performance_data(json_data)
        # Dump the performance data to a JSON file
        with open(f'{database}_performance.json', 'w') as f:
            json.dump(performance_data, f, indent=4)

        # compare_agents(performance_data)

def parse_arguments():
    """
    Parse the argument that specifies the directory.
    """
    parser = argparse.ArgumentParser(description='Analyze performance data.')
    parser.add_argument('--dir', type=str, help='Path to the directory containing JSON files')
    args = parser.parse_args()
    return args.dir

if __name__ == "__main__":
    directory = parse_arguments()
    main(directory)