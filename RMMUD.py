import json
import logging
import os
import shutil
import sys
import webbrowser
import zipfile
from datetime import datetime
from urllib.parse import urlparse
import importlib.util
if importlib.util.find_spec("requests") is None:
    os.system("pip install requests")
import requests
if importlib.util.find_spec("yaml") is None:
    os.system("pip install pyyaml")
import yaml

__version_info__ = (3, 7, 0)
__version__ = '.'.join(str(x) for x in __version_info__)

# sydney = <3 for gian 4 evr
# ^^^ My girlfriend wrote this for me, I am not removing it.

def extractNestedStrings(iterable):
    logging.debug('Extracting nested strings')
    def extract(iterable):
        strings = []
        if type(iterable) is dict:
            for value in iterable.values():
                strings += extract(value)
        elif type(iterable) is list:
            for item in iterable:
                strings += extract(item)
        elif type(iterable) is str:
            if iterable not in strings:
                strings.append(iterable)
        return strings
    logging.debug('Done extracting nested strings')
    return extract(iterable)

def readYAML(path):
    logging.debug(f'Reading the YAML file "{path}".')
    try:
        with open(path, 'r') as f:
            data = yaml.load(f, yaml.SafeLoader)
            logging.debug(f'Done reading the YAML file.')
            return data
    except Exception as e:
        logging.error(f'Could not read the YAML file "{path}".')
        logging.exception(e)
        raise e

def checkIfZipIsCorrupted(path):
    try:
        with zipfile.ZipFile(path) as zip_file:
            zip_file.testzip()
            logging.debug(f'The ZIP file "{path}" is not corrupted.')
            return False
    except zipfile.BadZipFile as e:
        logging.warning(f'The ZIP file "{path}" is corrupted or not a valid ZIP file.')
        logging.exception(e)
        return True
    except Exception as e:
        logging.error(f'An error occurred while checking if "{path}" is corrupted.')
        logging.exception(e)
        raise e

def getLatestReleaseVersion(tags_url = "https://api.github.com/repos/RandomGgames/RMMUD/tags"):
    logging.debug('Getting latest github release version.')
    try:
        release_version = requests.get(tags_url).json()[0]["name"]
        logging.debug(f'Done getting latest github release version ({release_version}).')
        return release_version
    except Exception as e:
        logging.warning(f'Could not get latest github release version.')
        logging.exception(e)
        raise e

def compareVersions(compare_version: str, current_version: str = __version__):
    logging.debug(f'Comparing two versions together')
    current_parts = current_version.split('.')
    compare_parts = compare_version.split('.')
    for i in range(max(len(current_parts), len(compare_parts))):
        current_part = int(current_parts[i]) if i < len(current_parts) else 0
        compare_part = int(compare_parts[i]) if i < len(compare_parts) else 0
        if int(compare_part) > int(current_part):
            logging.debug(f'The compare_version is higher than the current_version')
            return 'higher'
        elif int(compare_part) < int(current_part):
            logging.debug(f'The compare_version is lower than the current_version')
            return 'lower'
    logging.debug(f'The compare_version is the same as the current_version')
    return 'same'

def checkForUpdate():
    logging.info('Checking for an RMMUD update.')
    
    current_version = __version__
    logging.debug(f'{current_version = }')
    
    try:
        github_version = getLatestReleaseVersion()
    except Exception as e:
        logging.warning('Could not check for an RMMUD Update.')
        logging.exception(e)
        return None
    logging.debug(f'{github_version = }')
    
    logging.debug('Comparing github and current versions.')
    version_check = compareVersions(github_version, __version__)
    if version_check == "higher":
        logging.info(f'There is an update available! ({current_version} (current) → {github_version} (latest)).\nDo you want to open the GitHub releases page to download it right now? (yes/no): ')
        open_update = input('Open releases page? ').lower()
        if open_update in ("yes", "y"):
            url = "https://github.com/RandomGgames/RMMUD/releases"
            webbrowser.open(url)
            exit()
    elif version_check == "lower":
        logging.info(f'You are on what seems like a work in progress version, as it is higher than the latest release. Please report any bugs onto the github page at https://github.com/RandomGgames/RMMUD')
        return False
    elif version_check == "same":
        logging.info(f'You are on the latest version already.')
        return None

def copyToFolders(file_path, destination_path):
    logging.debug(f'Copying "{file_path}" into "{destination_path}".')
    try:
        shutil.copy2(file_path, destination_path)
        logging.debug(f'Successfully coppied.')
        return
    except Exception as e:
        logging.warning(f'Could not copy "{file_path}" into "{destination_path}".')
        logging.exception(e)
        raise e

def loadConfigFile(path = "RMMUDConfig.yaml"):
    logging.info(f'Loading config.')
    
    try:
        config = readYAML(path)
    except Exception as e:
        logging.error(f'Could not load config.')
        logging.exception(e)
        raise e
    
    logging.debug(f'Verifying config variable types.')
    config['CurseForge API Key'] = config.get('CurseForge API Key', None)
    if isinstance(config['CurseForge API Key'], str) and len(config['CurseForge API Key']) != 60:
        config['CurseForge API Key'] = None
    if config['CurseForge API Key'] is not None and not isinstance(config['CurseForge API Key'], str):
        raise TypeError("Curseforge API key should be a string or None.")
    config['Check for RMMUD Updates'] = config.get('Check for RMMUD Updates', True)
    if not isinstance(config['Check for RMMUD Updates'], bool):
        raise TypeError("Check for updates should be a boolean value.")
    config['Downloads Folder'] = config.get('Downloads Folder', 'RMMUDDownloads')
    if not isinstance(config['Downloads Folder'], str):
        raise TypeError("Downloads folder should be a string.")
    config['Instances Folder'] = config.get('Instances Folder', 'RMMUDInstances')
    if not isinstance(config['Instances Folder'], str):
        raise TypeError("Instances folder should be a string.")
    logging.debug(f'Done verifying config variable types.')
    
    logging.debug(f'Done loading config.')
    return config

def loadInstanceFile(path):
    logging.debug(f'Reading instance file "{path}".')
    
    try:
        data = readYAML(path)
    except Exception as e:
        logging.error(f'Could not load config.')
        logging.exception(e)
        raise e
    
    logging.debug(f'Verifying instance variable types.')
    data['Enabled'] = data.get('Enabled', True)
    if not isinstance(data['Enabled'], bool):
        raise TypeError(f'The Enabled option in the instance file "{path}" should be a boolean.')
    data['Loader'] = data.get(data['Loader'], "")
    if not isinstance(data['Loader'], str):
        raise TypeError(f'The Loader option in the instance file "{path}" should be a string.')
    data['Directory'] = data.get(data['Directory'], "")
    if not isinstance(data['Directory'], (str, type(None))):
        raise TypeError(f'The Directory option in the instance file "{path}" should be a string or None.')
    data['Mods'] = data['Mods'] if data['Mods'] else None
    if not isinstance(data['Mods'], (str, list, dict, type(None))):
        raise TypeError(f'The Mods option in the instance file "{path}" should be either a string, list, dictionary, or None.')
    data['Version'] = data.get(data['Version'], "")
    if not isinstance(data['Version'], str):
        raise TypeError(f'The Version option in the instance file "{path}" should be a string.')
    logging.debug(f'Done verifying instance variable types.')
    
    logging.debug(f'Done reading instance file')
    return data

def loadInstances(instances_dir: str):
    logging.info(f'LOADING INSTANCES')
    
    if not os.path.exists(instances_dir):
        os.makedirs(instances_dir)
    
    enabled_instances = {}
    for instance_file in [f for f in os.listdir(instances_dir) if f.endswith('.yaml')]:
        instance_path = os.path.join(instances_dir, instance_file)
        instance_name = os.path.splitext(instance_file)[0]
        try:
            instance = loadInstanceFile(instance_path)
            if not instance['Enabled']:
                logging.info(f'Ignoring disabled instance "{instance_file}"')
                continue
            logging.info(f'Loading enabled instance "{instance_file}"')
            instance.pop('Enabled')
            instance['Loader'] = str(instance['Loader']).lower()
            instance['Version'] = str(instance['Version'])
            instance['Directory'] = str(instance['Directory'])
            enabled_instances[instance_name] = instance
        except Exception as e:
            logging.warning(f'Could not load instance "{instance_name}"')
            logging.exception(e)
            logging.warning(f'Ignoring this file.')
            pass
    return enabled_instances

def parseInstances(instances):
    logging.debug('Parsing enabled instances')
    parsed_instances = {}
    
    for instance_name, instance in instances.items():
        mod_loader = str(instance['Loader']).lower()
        minecraft_version = str(instance['Version'])
        instance_dir = str(instance['Directory'])
        mods = extractNestedStrings(instance['Mods'])
        
        for mod_url in mods:
            url_authority = urlparse(mod_url).netloc
            mod_version = 'latest_version'
            if url_authority == "": continue # Probably a disabled mod just ignore it.
            url_authority = url_authority.lstrip('www.')
            
            if url_authority == 'modrinth.com':
                url_path = urlparse(mod_url).path
                url_path_split = url_path.split('/')[1:]
                
                if url_path_split[0] not in ('mod', 'plugin', 'datapack'):
                    continue
                
                mod_id = url_path_split[1]
                
                if len(url_path_split) == 4 and url_path_split[2] == 'version':
                    mod_version = url_path_split[3]
            
            elif url_authority == 'curseforge.com':
                url_path = urlparse(mod_url).path
                url_path_split = url_path.split('/')[1:]
                
                if url_path_split[0] != 'minecraft' or url_path_split[1] != 'mc-mods':
                    logging.warning(f'Url "{mod_url}" is not for a minecraft mod!')
                    continue
                
                mod_id = url_path_split[2]
                
                if len(url_path_split) == 5 and url_path_split[3] == 'files':
                    mod_version = url_path_split[4]
            
            else: # Unsupported website
                logging.warning(f'Mod manager cannot handle URLs from "{url_authority}". {mod_url}')
                continue
            
            parsed_instances.setdefault(mod_loader, {}).setdefault('mods', {}).setdefault(minecraft_version, {}).setdefault(mod_id, {}).setdefault(url_authority, {}).setdefault(mod_version, {}).setdefault('directories', [])
            
            if instance_dir not in parsed_instances[mod_loader]['mods'][minecraft_version][mod_id][url_authority][mod_version]['directories']:
                parsed_instances[mod_loader]['mods'][minecraft_version][mod_id][url_authority][mod_version]['directories'].append(instance_dir)
    
    return parsed_instances

# REVIEW
def downloadModrinthMod(mod_id, mod_loader, minecraft_version, mod_version, download_dir, instance_dirs):
    logging.info(f'Updating {mod_id} for {mod_loader} {minecraft_version}')
    
    logging.debug(f'Getting files from Modrinth')
    base_url = (f'https://api.modrinth.com/v2/project/{mod_id}/version')
    if mod_version == 'latest_version':
        params = {'loaders': [mod_loader], 'game_versions': [minecraft_version]}
    else:
        params = {'loaders': [mod_loader]}
    url = f'{base_url}?{"&".join([f"{key}={json.dumps(value)}" for key, value in params.items()])}'
    try:
        modrinth_header = {'User-Agent': 'RandomGgames/RMMUD (randomggamesofficial@gmail.com)'}
        response = requests.get(url, headers = modrinth_header).json()
    except Exception as e:
        logging.warning(f'Could not update "{mod_id}": {e}')
        return
    response = sorted(response, key=lambda x: datetime.fromisoformat(x['date_published'][:-1]), reverse = True)
    if mod_version == 'latest_version':
        if len(response) > 0:
            desired_mod_version = response[0]
        else:
            logging.warning(f'Could not find "{mod_id}" for {mod_loader} {minecraft_version}. https://modrinth.com/mod/{mod_id}')
            return
    else:
        if len(response) > 0:
            desired_mod_version = [version for version in response if version['version_number'] == mod_version][0]
        else:
            logging.warning(f'Could not find "{mod_id} {mod_version}" for {mod_loader} {minecraft_version}')
            return
    desired_mod_version_files = desired_mod_version['files']
    if any('primary' == True in file for file in desired_mod_version_files):
        desired_mod_version_files = [file for file in desired_mod_version_files if file['primary'] == True]
    desired_mod_version_file = desired_mod_version_files[0]
    
    logging.debug(f'Downloading desired version from Modrinth')
    download_url = desired_mod_version_file['url']
    file_name = desired_mod_version_file['filename']
    download_path = os.path.join(download_dir, mod_loader, minecraft_version)
    downloaded_file_path = os.path.join(download_path, file_name)
    
    if not (os.path.exists(downloaded_file_path) or checkIfZipIsCorrupted(downloaded_file_path)):
        try:
            response = requests.get(download_url, headers = modrinth_header)
        except Exception as e:
            logging.warning(f'Could not download "{mod_id}": {e}')
            return
        try:
            with open(downloaded_file_path, 'wb') as f: f.write(response.content)
        except Exception as e:
            logging.warning(f'Could not save file "{file_name}" to "{download_path}": {e}')
            return
        logging.info(f'Downloaded "{file_name}" into "{download_path}"')
    
    logging.debug(f'Copying downloaded file into instance(s)')
    for instance_dir in instance_dirs:
        instance_dir = os.path.join(instance_dir, 'mods')
        instance_file_path = os.path.join(instance_dir, file_name)
        if os.path.exists(instance_dir):
            if os.path.exists(downloaded_file_path):
                if not (os.path.isfile(instance_file_path) or checkIfZipIsCorrupted(instance_file_path)):
                    try:
                        shutil.copy(downloaded_file_path, instance_file_path)
                        logging.info(f'Copied "{downloaded_file_path}" into "{instance_dir}"')
                    except Exception as e:
                        logging.warning(f'Could not copy "{downloaded_file_path}" into "{instance_dir}": {e}')
                        continue
            else:
                logging.warning(f'Could not copy "{downloaded_file_path}" into "{instance_dir}": Could not find "{downloaded_file_path}"')
        else:
            logging.warning(f'Could not copy "{downloaded_file_path}" into "{instance_dir}": Could not find "{instance_dir}"')

# REVIEW
def downloadCurseforgeMod(mod_id, mod_loader, minecraft_version, mod_version, download_dir, instance_dirs, curseforge_api_key):
    logging.info(f'Updating {mod_id} for {mod_loader} {minecraft_version}')
    
    # Getting mod ID
    logging.debug(f'Getting mod ID from CurseForge')
    url = 'https://api.curseforge.com/v1/mods/search'
    params = {'gameId': '432','slug': mod_id, 'classId': '6'}
    curseforge_header = {'Accept': 'application/json','x-api-key': curseforge_api_key}
    try:
        response = requests.get(url, params, headers = curseforge_header).json()['data']
        curseforge_mod_id = response[0]['id']
    except Exception as e:
        logging.warning(f'Could not fetch CurseForge ID for "{mod_id}": {repr(e)}')
        return
    
    # Get latest or desired mod version
    logging.debug(f'Getting files from CurseForge')
    curseforge_mod_loader = { 'forge': 1, 'fabric': 4 }.get(mod_loader, None)
    if mod_version == 'latest_version':
        try:
            url = (f'https://api.curseforge.com/v1/mods/{curseforge_mod_id}/files')
            params = {'gameVersion': str(minecraft_version), 'modLoaderType': curseforge_mod_loader}
            response = requests.get(url, params = params, headers = curseforge_header).json()['data']
            desired_mod_version_file = list(file for file in response if minecraft_version in file['gameVersions'])[0]
        except Exception as e:
            logging.warning(f'Could not find "{mod_id}" for {mod_loader} {minecraft_version}. https://www.curseforge.com/minecraft/mc-mods/{mod_id}')
            return
    else:
        try:
            desired_mod_version_file = requests.get(f'https://api.curseforge.com/v1/mods/{curseforge_mod_id}/files/{mod_version}', params = {'modLoaderType': curseforge_mod_loader}, headers = curseforge_header).json()['data']
        except Exception as e:
            logging.warning(f'Could not find "{mod_id} {mod_version}" for {mod_loader} {minecraft_version}')
    
    logging.debug(f'Downloading desired version from CurseForge')
    file_name = desired_mod_version_file['fileName']
    download_url = desired_mod_version_file['downloadUrl']
    if download_url == None:
        logging.debug(f'Mod dev has disabled extenal program support for this mod, but I have a workaround ;)')
        download_url = f'https://edge.forgecdn.net/files/{str(desired_mod_version_file["id"])[0:4]}/{str(desired_mod_version_file["id"])[4:7]}/{file_name}'
    download_path = os.path.join(download_dir, mod_loader, minecraft_version)
    downloaded_file_path = os.path.join(download_path, file_name)
    
    if not (os.path.exists(downloaded_file_path) or checkIfZipIsCorrupted(downloaded_file_path)):
        try:
            response = requests.get(download_url, headers = curseforge_header)
            with open(downloaded_file_path, 'wb') as f: f.write(response.content)
        except Exception as e:
            logging.warning(f'Could not download "{mod_id}": {e}')
            return
        logging.info(f'Downloaded "{file_name}" into "{download_path}"')
    
    logging.debug(f'Copying downloaded file into instance(s)')
    for instance_dir in instance_dirs:
        instance_dir = os.path.join(instance_dir, 'mods')
        instance_file_path = os.path.join(instance_dir, file_name)
        if os.path.exists(instance_dir) and os.path.exists(downloaded_file_path):
            if not (os.path.isfile(instance_file_path) or checkIfZipIsCorrupted(instance_file_path)):
                try:
                    shutil.copy(downloaded_file_path, instance_file_path)
                    logging.info(f'Copied "{downloaded_file_path}" to "{instance_dir}"')
                except Exception as e:
                    logging.warning(f'Could not copy "{downloaded_file_path}" into "{instance_dir}": {e}')
                    continue

# REVIEW
def updateMods(instances, config: list):
    logging.debug(f'Creating folders to download mods into')
    for mod_loader in instances:
        for minecraft_version in instances[mod_loader]['mods']:
            try:
                dir = os.path.join(config['Downloads Folder'], mod_loader, minecraft_version)
                os.makedirs(dir, exist_ok = True)
            except Exception as e:
                logging.warning(f'Could not create download folder {dir}: {e}')
                raise e
    
    logging.info(f'UPDATING MODS')
    for mod_loader in instances:
        for minecraft_version in instances[mod_loader]['mods']:
            for mod_id in instances[mod_loader]['mods'][minecraft_version]:
                for website in instances[mod_loader]['mods'][minecraft_version][mod_id]:
                    for mod_version in instances[mod_loader]['mods'][minecraft_version][mod_id][website]:
                        instance_dirs = instances[mod_loader]['mods'][minecraft_version][mod_id][website][mod_version]['directories']
                        if website == 'modrinth.com':
                            downloadModrinthMod(mod_id, mod_loader, minecraft_version, mod_version, config['Downloads Folder'], instance_dirs)
                        elif website == 'curseforge.com':
                            downloadCurseforgeMod(mod_id, mod_loader, minecraft_version, mod_version, config['Downloads Folder'], instance_dirs)

# REVIEW
def deleteDuplicateMods(instances):
    logging.info(f'DELETING OUTDATED MODS')
    
    def scanFolder(instance_dir):
        logging.debug(f'Scanning for old mods')
        instance_dir = os.path.join(instance_dir, 'mods')
        ids = {}
        
        if os.path.exists(instance_dir):
            for mod_file in [f for f in os.listdir(instance_dir) if f.endswith('.jar')]:
                mod_path = os.path.join(instance_dir, mod_file)
                date_created = os.path.getctime(mod_path)
                with zipfile.ZipFile(mod_path) as zip_file:
                    with zip_file.open('fabric.mod.json') as f:
                        id = json.load(f, strict=False)['id']
                        ids.setdefault(id, {})
                ids[id][date_created] = mod_path
            
            ids = {key: dates for key, dates in ids.items() if len(dates) > 1}
            
            if ids:
                logging.debug(f'Deleting old mods')
                for mod_id, dates in ids.items():
                    latest_date = max(dates.keys())
                    for date_created, path in dates.items():
                        if date_created != latest_date:
                            try:
                                os.remove(path)
                                logging.info(f'Deleted old {mod_id} file: "{path}"')
                            except Exception as e:
                                logging.warning(f'Could not delete old {mod_id} file "{path}": {e}')
            else:
                logging.debug(f'No old mods to delete')
        else:
            logging.warning(f'Could not delete old mods in "{instance_dir}": Could not find "{instance_dir}"')
    
    for instance_name, instance in instances.items():
        logging.info(f'Deleting old mods from instance: {instance_name}')
        if instance['Loader'] == 'fabric':
            instance_dir = instance['Directory']
            scanFolder(instance_dir)
        else:
            logging.warning(f'Cannot auto-delete old mods in {instance_dir}: Only fabric mods supported atm.')

# REVIEW
def main():
    logging.debug(f'Running main body of script')
    
    config = loadConfigFile()
    
    if config['Check for RMMUD Updates']: checkForUpdate()
    
    instances = loadInstances(config['Instances Folder'])
    
    parsed_instances = parseInstances(instances)
    
    if len(parsed_instances) == 0:
        logging.info(f'No instances exist!')
    else:
        updateMods(parsed_instances)
        deleteDuplicateMods(instances)
    
    logging.info('Done.')

if __name__ == '__main__':
    # Clear latest.log if it exists
    if os.path.exists('latest.log'):
        open('latest.log', 'w').close()
    
    # Set up logging
    logging.basicConfig(
        level = logging.DEBUG,
        format = '%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
        datefmt = '%Y/%m/%d %H:%M:%S',
        encoding = 'utf-8',
        handlers = [
            logging.FileHandler('latest.log', encoding = 'utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.debug('Logging initialized.')
    
    # Call main function
    try:
        main()
    except Exception as e:
        input(f'The script could no longer continue to function due to the error described above. Please fix the issue described or go to https://github.com/RandomGgames/RMMUD to request help/report a bug')
        exit()
