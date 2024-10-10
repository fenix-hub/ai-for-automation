import os, sys, logging, ray
from ray.rllib.algorithms import ppo
import drlclass.routeplannerfull_ss
import shutil
import csv
import datetime
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

def main():
    # Directory checkpoint
    chkpt_root = "drl_model_sumo_full"
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

    agent = ppo.PPO(
        env=drlclass.routeplannerfull_ss.Routeplanner,
        config={
            "env_config": {
                "lstPoints": lstPointsRoute,
                "flagPriorityReward": False,
                "folder": "drlbari\salvisantilio",
                "pathRouteFile": "random.rou.xml",
                "pathNetFile": "bari1_map.net.xml",
                "pathConfigFile": "bari.sumocfg",
                "startEdge": startEdge,
                "endEdge": endEdge,
            },
            "num_workers": 0,
        },
    )

    status = "{:2d} reward {:6.2f}/{:6.2f}/{:6.2f} len {:4.2f} saved {}"

    i = 0
    j = 5
    chkpt_file = ""
    ct = datetime.datetime.now()
    print("current time:-", ct)

    # CSV file configuration
    csv_file = "training_results.csv"
    fields = ['Episode', 'Reward Min', 'Reward Mean', 'Reward Max', 'Episode Length', 'Checkpoint']

    # Scrivi l'intestazione del CSV
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(fields)

    while True:
        result = agent.train()
        i += 1

        # Scrittura nel file CSV
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                i + 1,
                result["env_runners"]["episode_reward_min"],
                result["env_runners"]["episode_reward_mean"],
                result["env_runners"]["episode_reward_max"],
                result["env_runners"]["episode_len_mean"],
                chkpt_file
            ])

        # Stampa i risultati
        print(status.format(
            i + 1,
            result["env_runners"]["episode_reward_min"],
            result["env_runners"]["episode_reward_mean"],
            result["env_runners"]["episode_reward_max"],
            result["env_runners"]["episode_len_mean"],
            chkpt_file
        ))

        # Salva il checkpoint se la reward media supera 10
        if result["env_runners"]["episode_reward_min"] >= -5:
            chkpt_file = agent.save(chkpt_root)
            break

    agent.stop()
    ct = datetime.datetime.now()
    print("current time:-", ct)

if __name__ == "__main__":
    main()
