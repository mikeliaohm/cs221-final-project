import os
import json
from collections import defaultdict

AGENTS_TYPES = ["minimax", "baseline", "oracle"]

def process_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def aggregate_results(data):
    total_tricks_result = defaultdict(int)
    total_scores_result = defaultdict(int)
    total_tricks_by_declarer = defaultdict(lambda: defaultdict(int))
    total_scores_by_declarer = defaultdict(lambda: defaultdict(int))
    count_by_declarer = defaultdict(int)
    game_count = 0

    for game_id, game_data in data.items():
        oracle_tricks = game_data["oracle_tricks"]
        oracle_score = game_data["oracle_score"]
        game_count += 1
        declarer = game_data["Declarer"]
        count_by_declarer[declarer] += 1
        for key, value in game_data.items():
            if not any(key.startswith(agent) for agent in AGENTS_TYPES):
                continue
            
            if key.endswith("_tricks"):
                total_tricks_result[key] += value - oracle_tricks
                total_tricks_by_declarer[declarer][key] += value - oracle_tricks
            if key.endswith("_score"):
                total_scores_result[key] += value - oracle_score
                total_scores_by_declarer[declarer][key] += value - oracle_score


    return total_tricks_result, total_scores_result, total_tricks_by_declarer, total_scores_by_declarer, count_by_declarer, game_count

def compute_averages(total_tricks_result, total_scores_result, file_count, game_count,
                     total_tricks_by_declarer, total_scores_by_declarer, count_by_declarer):
    average_tricks_result = {agent: total / game_count for agent, total in total_tricks_result.items()}
    average_scores_result = {agent: total / game_count for agent, total in total_scores_result.items()}

    average_tricks_by_declarer = {declarer: {agent: total / count_by_declarer[declarer]
                                             for agent, total in totals.items()}
                                  for declarer, totals in total_tricks_by_declarer.items()}
    average_scores_by_declarer = {declarer: {agent: total / count_by_declarer[declarer]
                                             for agent, total in totals.items()}
                                  for declarer, totals in total_scores_by_declarer.items()}

    return average_tricks_result, average_scores_result, average_tricks_by_declarer, average_scores_by_declarer

def main(directory):
    total_tricks_result = defaultdict(int)
    total_scores_result = defaultdict(int)
    total_tricks_by_declarer = defaultdict(lambda: defaultdict(int))
    total_scores_by_declarer = defaultdict(lambda: defaultdict(int))
    count_by_declarer = defaultdict(int)
    file_count = 0
    total_game_count = 0

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            data = process_file(file_path)
            file_tricks_result, file_scores_result, file_tricks_by_declarer, \
                file_scores_by_declarer, file_count_by_declarer, game_count = aggregate_results(data)

            for agent, value in file_tricks_result.items():
                total_tricks_result[agent] += value
            for agent, value in file_scores_result.items():
                total_scores_result[agent] += value
            for declarer, agent_dict in file_tricks_by_declarer.items():
                for agent, value in agent_dict.items():
                    total_tricks_by_declarer[declarer][agent] += value
            for declarer, agent_dict in file_scores_by_declarer.items():
                for agent, value in agent_dict.items():
                    total_scores_by_declarer[declarer][agent] += value
            for declarer, count in file_count_by_declarer.items():
                count_by_declarer[declarer] += count

            file_count += 1
            total_game_count += game_count

    avg_tricks_result, avg_scores_result, avg_tricks_by_declarer, avg_scores_by_declarer = compute_averages(
        total_tricks_result, total_scores_result, file_count, total_game_count,
        total_tricks_by_declarer, total_scores_by_declarer, count_by_declarer
    )

    # Dump the results into a JSON file
    results = {
        "Total Tricks Difference": total_tricks_result,
        "Total Scores Difference": total_scores_result,
        "Average Tricks Difference": avg_tricks_result,
        "Average Scores Difference": avg_scores_result,
        "Total Tricks Difference by Declarer": total_tricks_by_declarer,
        "Total Scores Difference by Declarer": total_scores_by_declarer,
        "Average Tricks Difference by Declarer": avg_tricks_by_declarer,
        "Average Scores Difference by Declarer": avg_scores_by_declarer
    }

    output_file = "agent/results/results.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as file:
        json.dump(results, file)

    print("Average Tricks Difference:")
    print(avg_tricks_result)
    print("\nAverage Scores Difference:")
    print(avg_scores_result)
    print("\nAverage Tricks Difference by Declarer:")
    print(avg_tricks_by_declarer)
    print("\nAverage Scores Difference by Declarer:")
    print(avg_scores_by_declarer)

if __name__ == "__main__":
    main("agent/logs/summary/")