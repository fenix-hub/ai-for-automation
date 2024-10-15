import os, sys, logging, ray
from ray.rllib.algorithms import ppo
import drlclass.routeplannerfull_ss
import shutil
import csv
import datetime
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
import requests
sys.setrecursionlimit(100000)

if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

osPlattform = sys.platform

if str(osPlattform) == "Linux":
    sumoBinary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui')
else:
    sumoBinary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui.exe')

logger = logging.getLogger(__name__)


# First, we register the environment as usual
def routeplanner_env_creator(env_config):
    return drlclass.routeplannerfull_ss.Routeplanner(env_config)

# Custom AlgorithmConfig class for PPO
class CustomPPOConfig(PPOConfig):
    def __init__(self, lstPointsRoute, folder, pathRouteFile, pathNetFile, pathConfigFile, startEdge, endEdge, gui):
        super().__init__()
        # Set the environment to the registered one
        self.environment(
            "routeplanner_env",
            env_config = {
                "lstPoints": lstPointsRoute,
                "flagPriorityReward": False,
                "folder":folder,
                "pathRouteFile": pathRouteFile,
                "pathNetFile": pathNetFile,
                "pathConfigFile": pathConfigFile,
                "startEdge": startEdge,
                "endEdge": endEdge,
                "gui": gui
            }
        )

        # Algorithm-specific settings for PPO
        # self.framework("torch")  # Use PyTorch as the backend, you can switch to "tf" for TensorFlow if needed

        # Add other PPO-specific settings here if needed
        # For example:
        self.lr = 0.0003  # Adjust the learning rate
        self.train_batch_size = 4000
        self.sgd_minibatch_size = 128
        self.num_sgd_iter = 10
        self.clip_param = 0.2
        self.entropy_coeff = 0.01
        self.num_rollout_workers = 0


# Function to check if a checkpoint exists, then return the checkpoint file
def load_checkpoint(agent, checkpoint_path):
    if os.path.exists(checkpoint_path):
        print(f"Loading checkpoint from {checkpoint_path}")
        agent.restore(checkpoint_path)
        # extract the checkpoint file name
        checkpoint_files = os.listdir(checkpoint_path)
        return checkpoint_files[0] if checkpoint_files else None
    else:
        print("Checkpoint file path does not exist, starting fresh.")
        return None


clean = False
gui = False
remote = True

def main():
    # Directory checkpoint
    chkpt_root = "drl_model_sumo_full"

    if clean:
        shutil.rmtree(chkpt_root, ignore_errors=True, onerror=None)

        # Directory risultati Ray
        ray_results = "{}/ray_results/".format(os.getenv("HOME"))
        shutil.rmtree(ray_results, ignore_errors=True, onerror=None)

    # Inizializza Ray
    ray.init(ignore_reinit_error=True)

    lstPointsRoute = []

    # Configurazione del percorso
    startEdge = "-30701540"
    endEdge = "-25586000#4"

    # Register the custom environment with RLlib
    register_env("routeplanner_env", routeplanner_env_creator)

    # Create a config instance
    config = CustomPPOConfig(
        lstPointsRoute=lstPointsRoute,
        folder="salvisantilio",
        pathRouteFile="random.rou.xml",
        pathNetFile="bari1_map.net.xml",
        pathConfigFile="bari.sumocfg",
        startEdge=startEdge,
        endEdge=endEdge,
        gui = gui
    )

    # Build the PPO agent from the config
    agent = config.build()

    # Load the checkpoint if it exists
    chkpt_file = load_checkpoint(agent, chkpt_root)

    status = "{:2d} reward {:6.2f}/{:6.2f}/{:6.2f} len {:4.2f} saved {}"

    i = 0
    j = 5
    ct = datetime.datetime.now()
    print("current time:-", ct)

    # CSV file configuration
    fields = ['Episode', 'Reward Min', 'Reward Mean', 'Reward Max', 'Episode Length', 'Timestamp', 'Checkpoint']
    csv_file = f'training_results_{ct.strftime("%Y%m%d-%H%M%S")}.csv'
    results_path = "training_results/" + csv_file

    # Scrivi l'intestazione del CSV
    with open(results_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(fields)

    while True:
        result = agent.train()
        i += 1

        # Scrittura nel file CSV
        with open(results_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                i,
                result["episode_reward_min"],
                result["episode_reward_mean"],
                result["episode_reward_max"],
                result["episode_len_mean"],
                datetime.datetime.fromtimestamp(result["timestamp"]),
                chkpt_file
            ])

        # Stampa i risultati
        print(status.format(
            i,
            result["episode_reward_min"],
            result["episode_reward_mean"],
            result["episode_reward_max"],
            result["episode_len_mean"],
            datetime.datetime.fromtimestamp(result["timestamp"]),
            chkpt_file
        ))

        if remote:
            url = 'https://ai-for-automation-simple-backend.onrender.com/submit'
            data = {
                'episode': i,
                'reward_min': result["episode_reward_min"],
                'reward_mean': result["episode_reward_mean"],
                'reward_max': result["episode_reward_max"],
                'episode_length': result["episode_len_mean"],
                'timestamp': ct,
                #'episode_timestamp': datetime.datetime.fromtimestamp(result["timestamp"]),
                'checkpoint': chkpt_file
            }

            response = requests.post(url, data=data)

            print(response.text)

        # Save the checkpoint if reward min exceeds threshold
        # if result["episode_reward_min"] >= -5:
        #    _ = agent.save(chkpt_root)
        ### (Q) Perchè sulla base del reward minimo e non del reward medio?

        if result["episode_reward_mean"] >= -5:
            _ = agent.save(chkpt_root)

    agent.stop()
    ct = datetime.datetime.now()
    print("current time:-", ct)

if __name__ == "__main__":
    main()
