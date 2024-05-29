import json
import matplotlib.pyplot as plt

# Load the results from the JSON file
with open('agent/results/results.json', 'r') as file:
    results = json.load(file)

# Define a mapping from long names to shorter names
name_mapping = {
    "minimax_d2_tricks": "minimax_d2",
    "oracle_tricks": "oracle",
    "baseline_tricks": "baseline",
    "minimax_d1_csp_tricks": "minimax_d1_csp",
    "minimax_d1_tricks": "minimax_d1",
    "minimax_d1_csp_shown_out_rand_declarer_tricks": "minimax_d1_csp_rand_dec",
    "minimax_d1_csp_shown_out_tricks": "minimax_d1_csp_shown",
    "minimax_d2_score": "minimax_d2",
    "oracle_score": "oracle",
    "baseline_score": "baseline",
    "minimax_d1_csp_score": "minimax_d1_csp",
    "minimax_d1_score": "minimax_d1",
    "minimax_d1_csp_shown_out_rand_declarer_score": "minimax_d1_csp_rand_dec",
    "minimax_d1_csp_shown_out_score": "minimax_d1_csp_shown"
}

# Define the custom order for the bars
custom_order = ["oracle", "baseline", "minimax_d1", "minimax_d2", "minimax_d1_csp", "minimax_d1_csp_shown", "minimax_d1_csp_rand_dec"]

# Function to map long names to short names and order them
def map_and_order_names(data):
    mapped_data = {name_mapping.get(k, k): v for k, v in data.items()}
    ordered_data = {k: mapped_data[k] for k in custom_order if k in mapped_data}
    return ordered_data

# Function to plot a bar chart
def plot_bar_chart(data, title, ylabel):
    data = map_and_order_names(data)
    agents = list(data.keys())
    values = list(data.values())

    fig, ax = plt.subplots()
    bars = ax.bar(agents, values, color='blue')

    ax.set_xlabel('Agents')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    
    # Add value labels on top of bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), ha='center', va='bottom')

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Plot Total Tricks Difference
plot_bar_chart(results["Total Tricks Difference"], "Total Tricks Difference Against Oracle", "Total Tricks Difference")

# Plot Total Scores Difference
plot_bar_chart(results["Total Scores Difference"], "Total Scores Difference Against Oracle", "Total Scores Difference")

# Plot Average Tricks Difference
plot_bar_chart(results["Average Tricks Difference"], "Average Tricks Difference Against Oracle", "Average Tricks Difference")

# Plot Average Scores Difference
plot_bar_chart(results["Average Scores Difference"], "Average Scores Difference Against Oracle", "Average Scores Difference")

# Function to plot bar charts by declarer
def plot_bar_chart_by_declarer(data, title, ylabel):
    data = {declarer: map_and_order_names(agent_data) for declarer, agent_data in data.items()}
    declarers = list(data.keys())
    agents = list(next(iter(data.values())).keys())
    x = range(len(agents))

    for declarer in declarers:
        values = [data[declarer][agent] for agent in agents]
        
        fig, ax = plt.subplots()
        bars = ax.bar(x, values, color='blue')
        ax.set_xticks(x)
        ax.set_xticklabels(agents)

        ax.set_xlabel('Agents')
        ax.set_ylabel(ylabel)
        ax.set_title(f"{title} ({declarer} Declarer)")
        
        # Add value labels on top of bars
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), ha='center', va='bottom')

        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

# Plot Total Tricks Difference by Declarer
plot_bar_chart_by_declarer(results["Total Tricks Difference by Declarer"], "Total Tricks Difference Against Oracle", "Total Tricks Difference")

# Plot Total Scores Difference by Declarer
plot_bar_chart_by_declarer(results["Total Scores Difference by Declarer"], "Total Scores Difference Against Oracle", "Total Scores Difference")

# Plot Average Tricks Difference by Declarer
plot_bar_chart_by_declarer(results["Average Tricks Difference by Declarer"], "Average Tricks Difference Against Oracle", "Average Tricks Difference")

# Plot Average Scores Difference by Declarer
plot_bar_chart_by_declarer(results["Average Scores Difference by Declarer"], "Average Scores Difference Against Oracle", "Average Scores Difference")