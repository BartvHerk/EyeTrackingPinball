import matplotlib.pyplot as plt
import numpy as np

from IO import import_stats
from stats import VEL_BIN_EDGES, FLIPPER_BIN_EDGES


def run_graphing():
    stats = import_stats()

    nasa_plot(stats)
    violin_plots(stats)


def nasa_plot(stats):
    TLX_Norm = []
    TLX_High = []
    for participant in stats:
        TLX_Norm.append(stats[participant]['global']['TLX_Norm'])
        TLX_High.append(stats[participant]['global']['TLX_High'])
    
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


def violin_plots(stats):
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
                scaled_counts = (hist * 1000).astype(int) # Scale up
                raw_data = np.repeat(bin_centers_vel, scaled_counts)
                reconstructed.append(raw_data)
            flat_data_vel.append(np.concatenate(reconstructed))
        
    for condition in conditions_flip:
        for task_key in task_keys:
            reconstructed = []
            for participant in stats:
                hist = np.array(stats[participant][task_key][condition])
                scaled_counts = (hist * 1000).astype(int) # Scale up
                raw_data = np.repeat(bin_centers_flip, scaled_counts)
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





# def figure_histogram(data, bin_edges):
#     plt.figure(figsize=(10, 5))
#     bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
#     plt.bar(bin_centers, data, width=np.diff(bin_edges), align='center')
#     plt.xscale('log')
#     plt.xlabel('Value')
#     plt.ylabel('Frequency')
#     plt.title('Histogram with Log-Spaced Bins')
#     plt.grid(True, which="both", ls="--")
#     plt.show()