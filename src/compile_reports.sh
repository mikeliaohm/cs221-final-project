# Compile individual reports from different agents
python agent/analyze.py --dir agent/logs/reports &&
# Not all agents have run the games in this file so we will skip it
# rm agent/logs/summary/A1A10303.json_performance.json &&
# Compile the performance report into a results.json file
python agent/performances.py &&
# Plot the results
python agent/results/chart.py