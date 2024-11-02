import matplotlib.pyplot as plt
import pandas as pd
import os

def plot_metrics_from_csv(csv_file):
   
    df = pd.read_csv(csv_file, index_col=False)
    filename = os.path.basename(csv_file)

    fig, axs = plt.subplots(2, 2, figsize=(10, 10))
    title = "Training : " + filename.split('_')[-1].replace('.csv', '')  # Estrae la parte "YYYYMMDD-HHMMSS"
    fig.suptitle(title, fontsize=12,family='serif')  
    
    subtitle = "Weights: DISTANCE_LESS=0.5 | DISTANCE_MORE=-0.5 | TRUNCATE_EPISODE_VALUE= 120 | ARRIVING=5 | CURVE=0 | TRAFFIC_PENALTY = 0.2 | NO_TRAFFIC_REWARD = 0 | TRAFFIC_IDX= 4"
    annotations= "Single predefined path"
    fig.text(0.5, 0.94, subtitle, ha='center', fontsize=10, family='serif')
    fig.text(0.5,0.92,annotations, ha='center', fontsize=6, family = 'serif')

    # Reward Min
    axs[0, 0].plot(df["Episode"], df["Reward Min"], label="Reward Min", color="blue")
    axs[0, 0].set_title("Reward Min")
    #axs[0, 0].axvline(x=49, color='black', linestyle='--')
    #axs[0, 0].set_xlabel("Episode")
    axs[0, 0].set_ylabel("Reward Min")

    # Reward Mean
    axs[0, 1].plot(df["Episode"], df["Reward Mean"], label="Reward Mean", color="green")
    axs[0, 1].set_title("Reward Mean")
    #axs[0, 1].axvline(x=49, color='black', linestyle='--')
    #axs[0, 1].set_xlabel("Episode")
    axs[0, 1].set_ylabel("Reward Mean")

    # Reward Max
    axs[1, 0].plot(df["Episode"], df["Reward Max"], label="Reward Max", color="red")
    axs[1, 0].set_title("Reward Max")
    #axs[1, 0].axvline(x=49, color='black', linestyle='--')
    axs[1, 0].set_xlabel("Episode")
    axs[1, 0].set_ylabel("Reward Max")

    # Episode Length
    axs[1, 1].plot(df["Episode"], df["Episode Length"], label="Episode Length", color="orange")
    axs[1, 1].set_title("Episode Length")
    #axs[1, 1].axvline(x=49, color='black', linestyle='--')
    axs[1, 1].set_xlabel("Episode")
    axs[1, 1].set_ylabel("Episode Length")

    plt.savefig(filename.split('_')[-1].replace('.csv', '.png'))
    plt.show()
    

# Esempio di utilizzo della funzione:
results_path = 'training_results_20241101-165748.csv'
plot_metrics_from_csv(results_path)
