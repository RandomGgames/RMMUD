import os
import yaml

def main():
	with open("RMMUDConfig.yaml", "r") as f: config = yaml.safe_load(f)
	print(config)
	
	for instance in [file for file in os.listdir("RMMUDInstances") if file.endswith(".yaml")]:
		with open(f"RMMUDInstances/{instance}", "r") as f: config = yaml.safe_load(f)
		print(config)

if __name__ == "__main__":
	main()
