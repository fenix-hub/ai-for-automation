import os, sys, logging, ray

from ray.rllib.algorithms import ppo

import drlclass.routeplannerfull_ss
sys.setrecursionlimit(100000)

if 'SUMO_HOME' in os.environ:
	sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
	sys.exit("please declare environment variable 'SUMO_HOME'")
osPlattform = sys.platform

if str(osPlattform)=="Linux":
	sumoBinary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui')
else:
	sumoBinary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui.exe')
# """ Logger """
logger = logging.getLogger(__name__)

# """ sumo binaries and scenario setup """




# """ Logger """
logger = logging.getLogger(__name__)

# """ sumo binaries and scenario setup """

import shutil
def main ():
	# init directory in which to save checkpoints

	sux="_priority"
	sux="_curve"
	sux="_routing"





	#Second case
	startEdge = "30029586#4"
	endEdge = "29316823#0"

	#First case
	startEdge = "29316823#0"
	endEdge = "30029586#4"

	#NESO
	startEdge="24888729#2"
	endEdge ="-24884068#4"

	#SONE
	startEdge="-24884068#4"
	endEdge ="24888729#2"
	#First case
	startEdge = "29316823#0"
	endEdge = "30029586#4"

	#EO
	startEdge ="29980631#1"
	endEdge ="30029586#5"

	#OE
	startEdge ="30029586#5"
	endEdge ="24888729#1"
	#First case
	startEdge = "29316823#0"
	endEdge = "30029586#4"

	chkpt_root = "drl_model_sumo_full"

	shutil.rmtree(chkpt_root, ignore_errors=True, onerror=None)

	# init directory in which to log results
	ray_results = "{}/ray_results/".format(os.getenv("HOME"))
	shutil.rmtree(ray_results, ignore_errors=True, onerror=None)

	# start Ray -- add `local_mode=True` here for debugging
	ray.init(ignore_reinit_error=True)

	lstPointsRoute = []

	# cluster 1
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
	            #"pathTrafficFile": "cluster_1/route_07-00_10-00.xml",
	            "pathNetFile": "bari1_map.net.xml",
	            "pathConfigFile": "bari.sumocfg",
				"startEdge": startEdge,
				"endEdge": endEdge,
	        },
	        "num_workers": 0,
	    },
	)

	status = "{:2d} reward {:6.2f}/{:6.2f}/{:6.2f} len {:4.2f} saved {}"

	i=0
	j=5
	chkpt_file=""
	import datetime
	ct = datetime.datetime.now()
	print("current time:-", ct)
	while True:
		result = agent.train()
		i=i+1
		if j==i:
			chkpt_file = agent.save(chkpt_root)
			print("Save Trainset n:",j)
			j=j+5

		print(status.format(
			i + 1,
			result["episode_reward_min"],
			result["episode_reward_mean"],
			result["episode_reward_max"],
			result["episode_len_mean"],
			chkpt_file
		))
		if result["episode_reward_mean"] >=10:
			chkpt_file = agent.save(chkpt_root)
			break

	agent.stop()
	ct = datetime.datetime.now()
	print("current time:-", ct)

if __name__ == "__main__":
	main()