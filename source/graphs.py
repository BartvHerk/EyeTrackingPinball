import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np

from IO import import_stats
from stats import VEL_BIN_EDGES, FLIPPER_BIN_EDGES, FIX_BIN_EDGES, SAC_BIN_EDGES, PUR_BIN_EDGES, histogram_to_counts_centers


def run_graphing():
    stats = import_stats()

    # plot_mistakes(stats)
    plot_skill(stats)
    # plot_looking(stats)
    # plot_nasa(stats)
    # plots_vel_flip(stats)
    # plots_duration(stats, 'Fixations', 'fix', FIX_BIN_EDGES, (50, 250))
    # plots_duration(stats, 'Saccades', 'sac', SAC_BIN_EDGES, (0, 125))
    # plots_duration(stats, 'Ball gaze pursuits', 'pur', PUR_BIN_EDGES, (0, 1))


def plot_mistakes(stats):
    TLX_Norm, TLX_High, _, _ = get_TLX_scores(stats)
    mistakes = []
    for participant in stats:
        mistakes.append(stats[participant]['global']['Mistakes'])
    # TLX_Difference = np.array(TLX_High) - np.array(TLX_Norm)

    # Regression line
    slope, intercept = np.polyfit(TLX_High, mistakes, 1)
    x_vals = np.linspace(min(TLX_High), max(TLX_High), 100)
    y_vals = intercept + slope * x_vals

    # Plot
    plt.figure(figsize=(7, 4.5))
    plt.scatter(TLX_High, mistakes)
    plt.plot(x_vals, y_vals, color='red', label='Regression line')
    plt.xlabel("High demand TLX")
    plt.ylabel("Mistakes #")
    plt.legend()
    plt.title("Relation Between High Demand TLX and Number of Mistakes Made")
    # plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.xlim(0, 21)
    plt.show()

    # Test
    # import statsmodels.api as sm
    # x_with_const = sm.add_constant(TLX_High)
    # model = sm.OLS(mistakes, x_with_const)
    # results = model.fit()
    # print(results.summary())


def plot_skill(stats):
    reflexes, experience_pinball = [], []
    for participant in stats:
        reflexes.append(stats[participant]['global']['Reflexes'])
        experience_pinball.append(stats[participant]['global']['Exp_Pinball'])
    
    # Experience
    scores = np.array(experience_pinball)
    bins = np.arange(0, 6) - 0.5 # -0.5 to 4.5
    counts, _ = np.histogram(scores, bins=bins)

    plt.figure(figsize=(5, 4))
    plt.bar(range(5), counts, width=0.6, color='skyblue', edgecolor='black')
    plt.xticks(range(5))
    plt.xlabel("Experience score")
    plt.ylabel("Number of Participants")
    plt.title("Self-Reported Experience Scores")
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.ylim(0, 12)
    plt.show()

    # Reflexes
    scores = np.array(reflexes)
    bins = np.arange(0, 8) - 0.5 # -0.5 to 6.5
    counts, _ = np.histogram(scores, bins=bins)

    plt.figure(figsize=(5, 4))
    plt.bar(range(7), counts, width=0.6, color='skyblue', edgecolor='black')
    plt.xticks(range(7))
    plt.xlabel("Reflex score")
    plt.ylabel("Number of Participants")
    plt.title("Self-Reported Reflex Scores")
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()



def plot_looking(stats):
    task_keys = ["norm", "high"]

    data = []
    for condition in ["percent_looking_default", "percent_looking_multiball"]:
        for task_key in task_keys:
            data_current = []
            for participant in stats:
                data_current.append(stats[participant][task_key][condition])
            data.append(data_current)
    
    plt.figure(figsize=(6, 4.5))
    plot = plt.boxplot(data, widths=0.4, patch_artist=True, boxprops=dict(facecolor='lightskyblue'))
    for median in plot['medians']:
        median.set_color('black')
    plt.xticks([1, 2, 3, 4], ["Norm, single ball", "High, single ball", "Norm, multiball", "High, multiball"])
    plt.ylabel(f"Percentage gaze on field")
    plt.title(f"Percentage of Time Gaze Was on Field per Condition")
    plt.gca().yaxis.set_major_formatter(PercentFormatter(xmax=1))
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()


def plot_nasa(stats):
    TLX_Norm, TLX_High, TLX_First, TLX_Second = get_TLX_scores(stats)
    
    # Plot
    plt.figure(figsize=(5, 4.5))
    plot = plt.boxplot([TLX_Norm, TLX_High], widths=0.4, patch_artist=True, boxprops=dict(facecolor='lightskyblue'))
    for median in plot['medians']:
        median.set_color('black')
    plt.xticks([1, 2], ["Normal", "High demand"])
    plt.ylabel("Task load index")
    plt.title("Task Load Index per Session Condition")
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.ylim(0, 21)
    plt.show()

    plt.figure(figsize=(5, 4.5))
    plot = plt.boxplot([TLX_First, TLX_Second], widths=0.4, patch_artist=True, boxprops=dict(facecolor='lightskyblue'))
    for median in plot['medians']:
        median.set_color('black')
    plt.xticks([1, 2], ["First session", "Second session"])
    plt.ylabel("Task load index")
    plt.title("Task Load Index per Session")
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.ylim(0, 21)
    plt.show()


def plots_vel_flip(stats):
    # Velocity and flipper distance
    bin_centers_vel = 0.5 * (VEL_BIN_EDGES[:-1] + VEL_BIN_EDGES[1:])
    bin_centers_flip = 0.5 * (FLIPPER_BIN_EDGES[:-1] + FLIPPER_BIN_EDGES[1:])
    task_keys = ["norm", "high"]
    conditions_vel = ["vel_hist_default", "vel_hist_multiball"]
    conditions_flip = ["flip_hist_default", "flip_hist_multiball"]

    flat_data_vel, flat_data_flip = [], []
    for condition in conditions_vel:
        for task_key in task_keys:
            reconstructed = []
            for participant in stats:
                hist = np.array(stats[participant][task_key][condition])
                raw_data = histogram_to_counts_centers(hist, bin_centers_vel)
                reconstructed.append(raw_data)
            flat_data_vel.append(np.concatenate(reconstructed))
        
    for condition in conditions_flip:
        for task_key in task_keys:
            reconstructed = []
            for participant in stats:
                hist = np.array(stats[participant][task_key][condition])
                raw_data = histogram_to_counts_centers(hist, bin_centers_flip)
                reconstructed.append(raw_data)
            flat_data_flip.append(np.concatenate(reconstructed))

    # Velocity violin plot
    plt.figure(figsize=(7, 4.5))
    plt.violinplot(flat_data_vel, showmeans=True, showmedians=False, widths=0.8)
    plt.xticks([1, 2, 3, 4], ["Norm, single ball", "High, single ball", "Norm, multiball", "High, multiball"])
    plt.ylabel("Angular velocity (deg/s)")
    plt.title("Angular Gaze Velocity per Condition")
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.ylim(0, 100)
    plt.show()

    # Flippers violin plot
    plt.figure(figsize=(7, 4.5))
    plt.violinplot(flat_data_flip, showmeans=True, showmedians=False, widths=0.8)
    plt.xticks([1, 2, 3, 4], ["Norm, single ball", "High, single ball", "Norm, multiball", "High, multiball"])
    plt.ylabel("Distance (cm)")
    plt.title("Distance Between Gaze Point and Flippers per Condition")
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.ylim(0, 100)
    plt.show()


def plots_duration(stats, name, shorthand, bin_edges, ylim):
    task_keys = ["norm", "high"]

    # Box plot
    val_per_second_data = []
    for condition in [f"{shorthand}_per_second_default", f"{shorthand}_per_second_multiball"]:
        for task_key in task_keys:
            val_per_second = []
            for participant in stats:
                val_per_second.append(stats[participant][task_key][condition])
            val_per_second_data.append(val_per_second)
    
    plt.figure(figsize=(6, 4.5))
    plot = plt.boxplot(val_per_second_data, widths=0.4, patch_artist=True, boxprops=dict(facecolor='lightskyblue'))
    for median in plot['medians']:
        median.set_color('black')
    plt.xticks([1, 2, 3, 4], ["Norm, single ball", "High, single ball", "Norm, multiball", "High, multiball"])
    plt.ylabel(f"{name} per second")
    plt.title(f"{name} per Second per Condition")
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

    # Violin plot
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    conditions_val = [f"{shorthand}_hist_default", f"{shorthand}_hist_multiball"]
    flat_data_val = []
    for condition in conditions_val:
        for task_key in task_keys:
            reconstructed = []
            for participant in stats:
                hist = np.array(stats[participant][task_key][condition])
                raw_data = histogram_to_counts_centers(hist, bin_centers)
                reconstructed.append(raw_data)
            flat_data_val.append(np.concatenate(reconstructed))
    
    plt.figure(figsize=(7, 4.5))
    plt.violinplot(flat_data_val, showmeans=True, showmedians=False, widths=0.8)
    plt.xticks([1, 2, 3, 4], ["Norm, single ball", "High, single ball", "Norm, multiball", "High, multiball"])
    plt.ylabel(f"{name} duration (ms)")
    plt.title(f"{name} duration per Condition")
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.ylim(ylim[0], ylim[1])
    plt.show()


def get_TLX_scores(stats):
    TLX_Norm = []
    TLX_High = []
    TLX_First = []
    TLX_Second = []
    for participant in stats:
        TLX_Norm.append(stats[participant]['global']['TLX_Norm'])
        TLX_High.append(stats[participant]['global']['TLX_High'])
        TLX_First.append(stats[participant]['global']['TLX_First'])
        TLX_Second.append(stats[participant]['global']['TLX_Second'])
    return TLX_Norm, TLX_High, TLX_First, TLX_Second