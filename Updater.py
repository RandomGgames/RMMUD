from ast import excepthandler
import datetime
import json
import os
import requests
import shutil
from zipfile import ZipFile

run_time = datetime.datetime.now().strftime("%Y-%m-%d")
if os.path.exists("mod_manager_logs/latest.log"): open("mod_manager_logs/latest.log", "w").close()
def log(text, end = "\n"):
	"""
	Prints text to the console and appends date, time, and text to a logs.txt file text. class str. The text to log
	"""
	if not os.path.exists("mod_manager_logs"): os.makedirs("mod_manager_logs")
	print(str(text), end = end)
	with open(f"mod_manager_logs/{run_time}.log", "a", encoding="UTF-8") as file: file.write(f"{str(text)}\n")
	with open(f"mod_manager_logs/latest.log", "a", encoding="UTF-8") as file: file.write(f"{str(text)}\n")

def logExit(text, end = "\n"):
	log(text, end = end)
	exit()


log(f"[{datetime.datetime.now()}] RUNNING MOD UPDATER")

"""
LOAD CONFIG
"""
log("[INFO] LOADING CONFIG:")
try:
	with open("Manager Config.json") as f:
		config = json.load(f)
		download_mods_location = config["download_mods_location"]
		instances = config["instances"]
		headers = {"Accept": "application/json", "x-api-key": config["x-api-key"]}
		log("	Config read successfully.")
except Exception as e:
	logExit(f"	[WARN] Could not read config file. Please fix the following error: {repr(e)}")

if not os.path.exists(download_mods_location):
	os.makedirs(download_mods_location)
	log(f"	[INFO] Created folder {download_mods_location}")

log(f"	Done")


"""UPDATING MODS"""
log("[INFO] PROCESSING LIST OF MODS:")
cache = {}
for instance_index, instance in enumerate(instances):
	instance_text = instance_index + 1
	try:
		loader = instance['loader'].capitalize()
		version = instance['version']
		mods_directory = f"{instance['directory']}/mods"
		links = instance['mod_links']	
	except Exception as e:
		logExit(f"	[WARN] Instance {instance_text} is missing the key: {repr(e)}")
	
	#for dir in [mods_directory, resource_packs_directory, shaderpacks_directory]:
	#	if not os.path.exists(dir):
	#		log(f"	[WARN]: Could not find dir \"{dir}\".")
	

	if not os.path.exists(f"{download_mods_location}/{loader}/{version}"):
		try:
			os.makedirs(f"{download_mods_location}/{loader}/{version}")
			log(f"	[INFO] Created folder {download_mods_location}/{loader}/{version}")
		except Exception as e:
			log(f"	[WARN] Could not create {download_mods_location}/{loader}/{version}. {repr(e)}")

	
	if loader == "Fabric":
		curseforge_modLoaderType = 4
		log(f"	Updating {version} mods in {mods_directory}...")

		for link in links:
			if link[-1] == "/": link = link[:-1] #Remove trailing / from link sif it has one at the end
			
			if link[0:45] == "https://www.curseforge.com/minecraft/mc-mods/":
				if link[45:len(link)] != "":
					slug = link[45:len(link)]
					if not any(x in slug for x in ["/", " ", "\\"]):
						log(f"		Updating: {slug}")

						if link not in cache:
							log(f"			Caching {slug} for {version}...")
							cache[link] = {"versions": {}}

							curseforge_mod = requests.get("https://api.curseforge.com/v1/mods/search", params = {"gameId": "432","slug": slug, "classId": "6"}, headers = headers).json()["data"]
							if len(curseforge_mod) > 0:
								curseforge_id = curseforge_mod[0]["id"]
							
								curseforge_files = requests.get(f"https://api.curseforge.com/v1/mods/{curseforge_id}/files", params = {"gameVersion": version, "modLoaderType": curseforge_modLoaderType}, headers = headers).json()["data"]
								if len(curseforge_files) > 0:
									latest_curseforge_file = curseforge_files[0]
									file_name = latest_curseforge_file["fileName"]
									download_url = latest_curseforge_file["downloadUrl"]
									if download_url == "": download_url = f"https://edge.forgecdn.net/files/{latest_curseforge_file['id'][0:4]}/{latest_curseforge_file['id'][4:7]}/{file_name}"

									if not os.path.exists(f"{download_mods_location}/{loader}/{version}/{file_name}"):
										try:
											open(f"{download_mods_location}/{loader}/{version}/{file_name}", "wb").write(requests.get(download_url).content)
											log(f"			[INFO] Downloaded {file_name} to {download_mods_location}/{loader}/{version}")
										except Exception as e:
											log(f"			[WARN] Could not download file. {repr(e)}")

									cache[link]["versions"][version] = f"{download_mods_location}/{loader}/{version}/{file_name}"
								else: log(f"			[WARN] Cannot find any {version} compatable versions of this mod.")

							else:
								log(f"		[WARN] Could not find mod {slug}. Make sure the url {link} is valid and not a redirect!")

						if link in cache:
							if not os.path.exists(f"{mods_directory}/{os.path.basename(cache[link]['versions'][version])}"):
								try:
									shutil.copyfile(cache[link]["versions"][version], f"{mods_directory}/{os.path.basename(cache[link]['versions'][version])}")
									log(f"			[INFO] Copied \"{cache[link]['versions'][version]}\" into \"{mods_directory}\"")
								except Exception as e:
									log(f"			[WARN] Something went wrong copying \"{cache[link]['versions'][version]}\" into \"{mods_directory}\". {repr(e)}")
							else: log(f"			{slug} is already up to date.")
					
					else: log(f'		[WARN] Invlalid slug: "{slug}"')
				
				else:  log(f"	[WARN] Links must be to a mod page. {link} is not a valid mod page link.")

			elif link[0:25] == "https://modrinth.com/mod/":
				if link[25:len(link)] != "":
					slug = link[25:len(link)]
					if not any(x in slug for x in ["/", " ", "\\"]):
						log(f"		Updating: {slug}")
						
						if link not in cache:
							log(f"			Caching {slug} for {version}...")
							cache[link] = {"versions": {}}
							
							modrinth_files = requests.get(f'https://api.modrinth.com/v2/project/{slug}/version?game_versions=["{version}"]').json()
							if len(modrinth_files) > 0:
								latest_version = modrinth_files[0]
								
								project_id = latest_version['project_id']
								mod_version = latest_version['version_number']
								file_name = latest_version['files'][0]['filename']
								download_url = f'https://cdn.modrinth.com/data/{project_id}/versions/{mod_version}/{file_name}'
							
								if not os.path.exists(f'{download_mods_location}/{loader}/{version}/{file_name}'):
									try:
										open(f"{download_mods_location}/{loader}/{version}/{file_name}", "wb").write(requests.get(download_url).content)
										log(f"			[INFO] Downloaded {file_name} to {download_mods_location}/{loader}/{version}")
									except Exception as e:
										log(f"			[WARN] Could not download file. {repr(e)}")

								cache[link]["versions"][version] = f"{download_mods_location}/{loader}/{version}/{file_name}"
							
							else:
								log(f"			[WARN] Could not find mod {slug}. Make sure the url {link} is valid and not a redirect!")

						if link in cache:
							if not os.path.exists(f"{mods_directory}/{os.path.basename(cache[link]['versions'][version])}"):
								try:
									shutil.copyfile(cache[link]["versions"][version], f"{mods_directory}/{os.path.basename(cache[link]['versions'][version])}")
									log(f"			[INFO] Copied \"{cache[link]['versions'][version]}\" into \"{mods_directory}\"")
								except Exception as e:
									log(f"			[WARN] Something went wrong copying \"{cache[link]['versions'][version]}\" into \"{mods_directory}\". {repr(e)}")
							else: log(f"			{slug} is already up to date.")	
					
					else: log(f'		[WARN] Invlalid slug: "{slug}"')
				
				else:  log(f"	[WARN] Links must be to a mod page. {link} is not a valid mod page link.")


	elif loader == "Forge":
		curseforge_modLoaderType = 1
		log(f"	[WARN] Script does not currently support {loader} mods yet. Ignoring instance {instance_text}.")
		
	else:
		log(f"	[WARN] Script does not support {loader} mods. Ignoring instance {instance_text}. Suggest support via github under the issue tracker https://github.com/RandomGgames/Minecraft-Mod-Manager")
	
log(f"	Done")


"""DELETE OLD MODS"""
log("[INFO] DELETING OLD MODS")

directories = []
for instance in instances:
	mods_directory = f"{instance['directory']}/mods"
	version = instance['version']
	loader = instance['loader'].capitalize()

	if f"{config['download_mods_location']}/{loader}/{version}" not in directories:
		directories.append(f"{config['download_mods_location']}/{loader}/{version}")

	if loader == "Fabric":
		if mods_directory not in directories:
			directories.append(mods_directory)

for directory in directories:
	log(f"	Scanning {directory}...")
	cache = {}
	for mod in [file for file in os.listdir(directory) if file.endswith(".jar")]:
		path = f"{directory}/{mod}"
		tmodified = os.path.getmtime(path)
		with ZipFile(path, "r") as modzip:
			with modzip.open("fabric.mod.json", "r") as modinfo:
				mod_id = json.load(modinfo, strict=False)["id"]
			modinfo.close()
		modzip.close()
		if mod_id not in cache:
			cache[mod_id] = {'path': path, 'tmodified': tmodified}
		else:
			if tmodified > cache[mod_id]['tmodified']:
				os.remove(cache[mod_id]['path'])
				log(f"		[INFO] Deleted {os.path.basename(cache[mod_id]['path'])}")
				cache[mod_id] = {'path': path, 'tmodified': tmodified}
			else:
				os.remove(path)
				log(f"		[INFO] Deleted {os.path.basename(path)}")

log(f"	Done")
