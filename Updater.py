import json
from msilib import _directories
import requests
import os
import datetime
run_time = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
from zipfile import ZipFile
import shutil

def log(text):
	"""
	Prints text to the console and appends date, time, and text to a logs.txt file text. class str. The text to log
	"""
	#timestamp = (datetime.datetime.now().strftime("%b %d, %Y @ %I:%M %Ss %p")) #Formated time. Example output: Jan 14, 2021 @ 12:02 30s AM
	if not os.path.exists('logs'): os.makedirs('logs')
	timestamp = (datetime.datetime.now()) # 2022-06-07 15:38:00.960363
	print(str(text))
	with open(f"logs/{run_time}.log", "a", encoding="UTF-8") as file: file.write(f"[{timestamp}] {str(text)}\n")

def logExit(text):
	log(text)
	exit()

class CurseforgeMod:
	def __init__(self, slug, version):
		data = requests.get('https://api.curseforge.com/v1/mods/search', params = {'gameId': '432','slug': slug, 'classId': '6'}, headers = headers).json()['data']
		try: self.data = data[0]
		except: logExit(f"[CurseforgeMod.files/WARN] FATAL ERROR: Could not find mod \"https://www.curseforge.com/minecraft/mc-mods/{slug}\". Please make sure the URL is still valid.")
		self.id = self.data['id']
		self.url = self.data['links']['websiteUrl']
		self.version = version
		
		files = requests.get(f"https://api.curseforge.com/v1/mods/{self.id}/files", params = {'gameVersion': self.version, 'modLoaderType': 4}, headers = headers).json()['data']
		if len(files) != 0 : self.files = files
		else: self.files = None

		if self.files:
			download_url = requests.get(f"https://api.curseforge.com/v1/mods/{self.id}/files/{self.files[0]['id']}/download-url", headers = headers)
			if download_url.content == b"": self.download_url = f"https://edge.forgecdn.net/files/{str(self.files[0]['id'])[0:4]}/{str(self.files[0]['id'])[4:7]}/{self.files[0]['fileName']}"
			else: self.download_url = download_url.json()['data']
		else:
			self.download_url = None
			log(f"[CurseforgeMod.files/WARN] Cannot find {self.version} file for {self.url}")

	def __str__(self):
		return {'data': self.data, 'id': self.id, 'url': self.url, 'files': self.files, 'download_url': self.download_url}

	pass #REWORK downloadLatestFile INTO SEPERATE FUNCTIONS WITHIN CLASS
	def downloadLatestFile(self, download_location, copy_locations):
		if self.download_url:
			file_name = self.files[0]['fileName']
			if not os.path.exists(f"{download_location}/{file_name}"):
				try:
					open(f"{download_location}/{file_name}", 'wb').write(requests.get(self.download_url).content)
					log(f"[CurseforgeMod.downloadLatestFile/INFO] Downloaded {self.version} mod \"{file_name}\"")
					return f"{download_location}/{file_name}"
				except Exception as e: log(f"[CurseforgeMod.downloadLatestFile/WARN] Error downloading {self.url}. {e}")
			#else: log(f"[CurseforgeMod.downloadLatestFile/INFO] Already have latest mod {file_name}")
			if os.path.exists(f"{download_location}/{file_name}"):
				for copy_location in copy_locations:
					try:
						if not os.path.exists(f"{copy_location}/{file_name}"):
							shutil.copyfile(f"{download_location}/{file_name}", f"{copy_location}/{file_name}")
							log(f"[CurseforgeMod.downloadLatestFile/INFO] Copied \"{download_location}/{file_name}\" to \"{copy_location}\"")
						#else: log(f"[CurseforgeMod.downloadLatestFile/INFO] Directory \"{copy_location}\" already contains \"{file_name}\"")
					except Exception as e: log(f"[CurseforgeMod.downloadLatestFile/WARN] Could not copy mod \"{download_location}/{file_name}\" to \"{copy_location}\". {e}")
		else: return None


"""LOAD CONFIG"""
try:
	with open('Manager Config.json') as f: config = json.load(f)
except Exception as e:
	logExit(f'[Load Config/WARN] FATAL ERROR: Loading config file. {e}')
if len(config['x-api-key']) != 60 or config['x-api-key'][:7] != '$2a$10$':
	logExit("[Load Config/WARN] FATAL ERROR: x-api-key doesn't look valid. Please provide a valid API key.")
headers = {'Accept': 'application/json', 'x-api-key': config['x-api-key']}

HAD_ERROR = False
for instance in config['instances']:
	if not os.path.isdir(instance['directory']):
		HAD_ERROR = True
		log(f"[Load Config/WARN] Location \"{instance['directory']}\" is invalid/doesn't exist!")
if HAD_ERROR:
	logExit('[Load Config/WARN] FATAL ERROR: Cannot continue until directories listed above can be found.')


"""CREATING ORGANIZED MOD DIRECTORY"""
organized_config = {} # {'1.18.2': {'fabric_api': ['mods']}}

for instance in config['instances']:
	version = instance['version']
	directory = instance['directory']
	if version not in organized_config:
		organized_config[version] = {}
	for mod_link in instance['mod_links']:
		if mod_link[0:45] == 'https://www.curseforge.com/minecraft/mc-mods/':
			if mod_link[-1] != '/':
				slug = mod_link[45:]
				if '/' not in slug or ' ' not in slug or '\\' not in slug:
					if slug not in organized_config[version]:
						organized_config[version][slug] = {'directories': []}
					organized_config[version][slug]['directories'].append(directory)
				else: log(f'[Organizing Config/WARN] Invlalid slug: "{slug}"')
			else: log(f'[Organizing Config/WARN] Remove trailing "/" at the end of the url! "{mod_link}"')
		else: log(f'[Organizing Config/WARN] "{mod_link}" must be a curseforge mod link.')

for version in organized_config:
	try:
		if not os.path.exists(f"{config['download_mods_location']}/{version}"): os.makedirs(f"{config['download_mods_location']}/{version}")
	except Exception as e:
		logExit('[Organizing Config/WARN] FATAL ERROR: Could not generate folders to download mods into.')
#print(f"Organized_config: {json.dumps(organized_config)}")


"""DOWNLOADING MODS"""
for version in organized_config:
	for slug in organized_config[version]:
		CurseforgeMod(slug, version).downloadLatestFile(f"{config['download_mods_location']}/{version}", organized_config[version][slug]['directories'])


"""DELETE OLD MODS"""
versions = []
for instance in config['instances']:
	version = instance['version']
	if version not in versions:
		versions.append(version)
#print(f"{versions = }")

directories = []
for version in versions:
	directories.append(f"{config['download_mods_location']}/{version}")
for instance in config['instances']:
	directory = instance['directory']
	if directory not in directories:
		directories.append(directory)
#print(f"{directories = }")

for directory in directories:
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
				cache[mod_id] = {'path': path, 'tmodified': tmodified}
				log(f"[DeleteOldMods/INFO] Deleted {cache[mod_id]['path']}")
			else:
				os.remove(path)
				log(f"[DeleteOldMods/INFO] Deleted {path}")


log(f"Done")
