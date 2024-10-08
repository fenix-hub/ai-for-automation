import os, sys, logging, ray

from ray.rllib.algorithms import ppo

import drlclass.routeplannerfull

sys.setrecursionlimit(100000)

if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
osPlattform = sys.platform

if str(osPlattform) == "Linux":
    sumoBinary = os.path.join(os.environ["SUMO_HOME"], "bin", "sumo-gui")
else:
    sumoBinary = os.path.join(os.environ["SUMO_HOME"], "bin", "sumo-gui.exe")
# """ Logger """
logger = logging.getLogger(__name__)

# """ sumo binaries and scenario setup """


# """ Logger """
logger = logging.getLogger(__name__)

# """ sumo binaries and scenario setup """

scenario = "scenario5"


import shutil


def main():
    # init directory in which to save checkpoints

    sux = "_priority"
    sux = "_curve"
    sux = "_routing"

    # Second case
    startEdge = "30029586#4"
    endEdge = "29316823#0"

    # First case
    startEdge = "29316823#0"
    endEdge = "30029586#4"

    # NESO
    startEdge = "24888729#2"
    endEdge = "-24884068#4"

    # SONE
    startEdge = "-24884068#4"
    endEdge = "24888729#2"
    # First case
    startEdge = "29316823#0"
    endEdge = "30029586#4"

    # EO
    startEdge = "29980631#1"
    endEdge = "30029586#5"

    # OE
    startEdge = "30029586#5"
    endEdge = "24888729#1"
    # First case
    startEdge = "29316823#0"
    endEdge = "30029586#4"

    chkpt_root = "drl_model_sumo_full"

    shutil.rmtree(chkpt_root, ignore_errors=True, onerror=None)

    # init directory in which to log results
    ray_results = "{}/ray_results/".format(os.getenv("HOME"))
    shutil.rmtree(ray_results, ignore_errors=True, onerror=None)

    # start Ray -- add `local_mode=True` here for debugging
    ray.init(ignore_reinit_error=True)

    # 	agent = ppo.PPO(env=drlclass.routeplanner.Routeplanner, config={
    # 		"env_config": {"startEdge":startEdge, "endEdge":endEdge,"flagPriorityReward":False,"folder":"scenario5","pathRouteFile":"example_drl.rou.xml"},
    # 		"num_workers": 0
    # 	})

    # Strada piu breve

    lstPointsRoute = [
        ["24884189#1", "29975386#3"],
        ["29975386#3", "24884189#1"],
        ["24884189#1", "29975386#3"],
        ["29975386#3", "24884189#1"],
        ["29975386#3", "-29975400#3"],
    ]

    lstPointsRoute = [
        ["29975400#3", "29975386#1"],
        ["29975386#1", "29975400#3"],
        ["69135107#0", "29976859#7"],
        ["29976859#7", "69135107#0"],
    ]

    lstPointsRoute = [["29975400#3", "69135107#0"]]
    agent = ppo.PPO(
        env=drlclass.routeplannerfull.Routeplanner,
        config={
            "env_config": {
                "lstPoints": lstPointsRoute,
                "flagPriorityReward": False,
                "folder": "./scenario5",
                "pathRouteFile": "example_drl.rou.xml",
                "pathNetFile": "murat_liberta.net.xml",
                "pathConfigFile": "osm.sumocfg",
            },
            "num_workers": 0,
        },
    )

    status = "{:2d} reward {:6.2f}/{:6.2f}/{:6.2f} len {:4.2f} saved {}"

    i = 0
    j = 5
    chkpt_file = ""
    import datetime

    ct = datetime.datetime.now()
    print("current time:-", ct)
    while True:
        result = agent.train()
        i = i + 1
        if j == i:
            chkpt_file = agent.save(chkpt_root)
            print("Save Trainset n:", j)
            j = j + 5

        print(
            status.format(
                i + 1,
                result["episode_reward_min"],
                result["episode_reward_mean"],
                result["episode_reward_max"],
                result["episode_len_mean"],
                chkpt_file,
            )
        )
        if result["episode_reward_mean"] >= 10:
            chkpt_file = agent.save(chkpt_root)
            break

    agent.stop()
    ct = datetime.datetime.now()
    print("current time:-", ct)


if __name__ == "__main__":
    main()

    """
	agent = ppo.PPO(env=select_env, config={
		"env_config": {},
		"num_workers": 1,
		"max_episode_steps" : 60
	})
	"""
    # config = ppo.PPOConfig()
    # config = config.training(gamma=0.9, lr=0.01, kl_coeff=0.3)
    # config = config.resources(num_gpus=0)

    # config = config.rollouts(num_rollout_workers=0)

    # config.evaluation(evaluation_config={"explore": False})
    # agent = ppo.PPO(env=drlclass.routeplanner.Routeplanner, config=config)

# 	agent = ppo.PPO(env=drlclass.routeplannertraffic.Routeplanner, config={
# 		"env_config": {"startEdge":startEdge, "endEdge":endEdge,"folder":"scenario5","pathRouteFile":"example_drl.rou.xml"},
# 		"num_workers": 0
# 	})
