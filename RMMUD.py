import json
import logging
import os
import requests
import shutil
import sys
import webbrowser
import yaml
import zipfile
from datetime import datetime
from urllib.parse import urlparse
from typing import Literal, Type, TypedDict, overload

__version_info__ = (3, 7, 0)
__version__ = '.'.join(str(x) for x in __version_info__)

# sydney = <3 for gian 4 evr
# ^^^ My girlfriend wrote this for me, I am not removing it.

Mods = dict[str, list[str] | dict[str, list[str]]] | list[str] | str
Config = TypedDict("Config", {
    "CurseForge API Key": str | None,
    "Check for RMMUD Updates": bool,
    "Downloads Folder": str,
    "Instances Folder": str,
})
Instance = TypedDict("Instance", {
    "Enabled": bool,
    "Loader": str,
    "Directory": str | None,
    "Mods": Mods,
    "Version": str
})
Instances = dict[str, Instance]
ParsedInstances = dict[str, dict[str, dict[str, dict[
    str, dict[str, dict[str, dict[str, list[str]]]]]]]]
CFHashes = TypedDict("CFHashes", {
    "value": str,
    "algo": int
})
CFGameVersion = TypedDict("CFGameVersion", {
    "gameVersionName": str,
    "gameVersionPadded": int,
    "gameVersion": str,
    "gameVersionReleaseDate": str,
    "gameVersionTypeId": int
})
CFDependencies = TypedDict("CFDependencies", {
    "modId": int,
    "relationType": int
})
CFModules = TypedDict("CFModules", {
    "name": str,
    "fingerprint": int
})
CFVersionFile = TypedDict("CFVersionFile", {
    "id": int,
    "gameId": int,
    "modId": int,
    "isAvailable": bool,
    "displayName": str,
    "fileName": str,
    "releaseType": int,
    "fileStatus": int,
    "hashes": list[CFHashes],
    "fileDate": str,
    "fileLength": int,
    "downloadCount": int,
    "downloadUrl": str | None,
    "gameVersions": list[str],
    "sortableGameVersions": list[CFGameVersion],
    "dependencies": list[CFDependencies],
    "alternateFileId": int,
    "isServerPack": bool,
    "fileFingerprint": int,
    "modules": list[CFModules]
})

def extractNestedStrings(iterable: str | list | dict | tuple) -> list[str]:
    logging.debug('Extracting nested strings')
    def extract(iterable: str | list | dict | tuple) -> list[str]:
        strings: list[str] = []
        match iterable:
            case dict():
                for value in iterable.values():
                    if isinstance(value, list):
                        strings += extract(value)
                        continue
                    for subvalue in value:
                        strings += extract(subvalue)
            case (list, tuple):
                for item in iterable:
                    strings += extract(item)
            case str():
                if iterable not in strings:
                    strings.append(iterable)
            case _:
                logging.debug(f'Cannot handle {iterable} which is type {type(iterable).__name__}. It will be ignored.')
        return strings
    logging.debug('Done extracting nested strings')
    return extract(iterable)

def readYAML(path: str) -> Config | Instance:
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

def checkIfZipIsCorrupted(path: str) -> bool:
    logging.debug(f'Checking if "{path}" is corrupted.')
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

def getGithubLatestReleaseTag(tags_url: str = "https://api.github.com/repos/RandomGgames/RMMUD/tags") -> str:
    logging.debug('Getting latest github release version.')
    try:
        release_version: str = requests.get(tags_url).json()[0]["name"]
        logging.debug(f'Done getting latest github release version ({release_version}).')
        return release_version
    except Exception as e:
        logging.warning(f'Could not get latest github release version.')
        logging.exception(e)
        raise e

def compareTwoVersions(compare_version: str, current_version: str = __version__):
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

def checkForUpdate() -> bool | None:
    logging.info('Checking for an RMMUD update.')
    
    current_version = __version__
    logging.debug(f'{current_version = }')
    
    try:
        github_version = getGithubLatestReleaseTag()
    except Exception as e:
        logging.warning('Could not check for an RMMUD Update.')
        logging.exception(e)
        return None
    logging.debug(f'{github_version = }')
    
    logging.debug('Comparing github and current versions.')
    version_check = compareTwoVersions(github_version, __version__)
    match version_check:
        case "higher":
            logging.info(f'There is an update available! ({current_version} (current) → {github_version} (latest)).\nDo you want to open the GitHub releases page to download it right now? (yes/no): ')
            open_update = input('Open releases page? ').lower()
            if open_update in ("yes", "y"):
                url = "https://github.com/RandomGgames/RMMUD/releases"
                webbrowser.open(url)
                exit()
        case "lower":
            logging.info(f'You are on what seems like a work in progress version, as it is higher than the latest release. Please report any bugs onto the github page at https://github.com/RandomGgames/RMMUD')
            return False
        case "same":
            logging.info(f'You are on the latest version already.')
            return None

def copyToFolders(file_path: str, destination_path: str) -> None:
    logging.debug(f'Copying "{file_path}" into "{destination_path}".')
    try:
        shutil.copy2(file_path, destination_path)
        logging.debug(f'Successfully coppied.')
        return
    except Exception as e:
        logging.warning(f'Could not copy "{file_path}" into "{destination_path}".')
        logging.exception(e)
        raise e

def loadConfigFile(path: str = "RMMUDConfig.yaml") -> Config:
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
    
    defaults = {
        "Check for RMMUD Updates": True,
        "Downloads Folder": "RMMUDDownloads",
        "Instances Folder": "RMMUDInstances"
    }
    
    for key, value in defaults.items():
        config[key] = config.get(key, value)
        if not isinstance(config[key], type(value)):
            raise TypeError(f"{key} should be a {type(value).__name__}.")
    
    logging.debug(f'Done verifying config variable types.')
    
    logging.debug(f'Done loading config.')
    return config

def loadInstanceFile(path: str) -> Instance:
    logging.debug(f'Reading instance file "{path}".')
    
    try:
        data = readYAML(path)
    except Exception as e:
        logging.error(f'Could not load config.')
        logging.exception(e)
        raise e
    
    logging.debug(f'Verifying instance variable types.')
    
    defaults = {
        "Enabled": True,
        "Loader": "",
        "Directory": ["", None],
        "Mods": [None, "", [...], {...: ...}],
        "Version": ""
    }
    
    for key, value in defaults.items():
        if not isinstance(value, list):
            data[key] = data.get(key, value)
            if not isinstance(data[key], type(value)):
                raise TypeError(f"The {key} option in the instance file {path} should be a {type(value).__name__}.")
        else:
            data[key] = data.get(key, value[1])
            if not any(isinstance(data[key], type(val)) for val in value):
                raise TypeError(f"The {key} option in the instance file {path} " +
                                f"should be a {' / '.join(str(type(val).__name__) for val in value)}")
    
    logging.debug(f'Done verifying instance variable types.')
    
    data["Loader"] = data["Loader"].lower()
    
    logging.debug(f'Done reading instance file')
    return data

def loadInstances(instances_dir: str) -> Instances:
    logging.info(f'LOADING INSTANCES')
    
    if not os.path.exists(instances_dir):
        try:
            os.makedirs(instances_dir)
            logging.debug(f'Created folder "{instances_dir}"')
        except Exception as e:
            logging.error(f'Could not create "{instances_dir}".')
            logging.exception(e)
            raise e
    
    enabled_instances: Instances = {}
    for instance_file in [f for f in os.listdir(instances_dir) if f.endswith('.yaml')]:
        instance_path = os.path.join(instances_dir, instance_file)
        instance_name = os.path.splitext(instance_file)[0]
        try:
            instance = loadInstanceFile(instance_path)
            if not instance['Enabled']:
                logging.info(f'Ignoring disabled instance "{instance_file}"')
                continue
            else:
                logging.info(f'Loading enabled instance "{instance_file}"')
                instance.pop('Enabled')
                enabled_instances[instance_name] = instance
        except Exception as e:
            logging.warning(f'Could not load instance "{instance_name}". Ignoring this file.')
            logging.exception(e)
            continue
    return enabled_instances

def parseInstances(instances: Instances) -> ParsedInstances:
    logging.debug('Parsing enabled instances')
    parsed_instances: ParsedInstances = {}
    
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

def downloadModrinthMod(mod_id: str, mod_loader: str, minecraft_version: str, mod_version: str,
                        download_dir: str, instance_dirs: list[str]) -> None:
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
    if any(file['primary'] == True in file for file in desired_mod_version_files):
        desired_mod_version_files = [file for file in desired_mod_version_files if file['primary'] == True]
    desired_mod_version_file = desired_mod_version_files[0]
    
    logging.debug(f'Downloading desired version from Modrinth')
    download_url = desired_mod_version_file['url']
    file_name = desired_mod_version_file['filename']
    download_path = os.path.join(download_dir, mod_loader, minecraft_version)
    downloaded_file_path = os.path.join(download_path, file_name)
    
    if not os.path.exists(downloaded_file_path) or checkIfZipIsCorrupted(downloaded_file_path):
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
                if not os.path.isfile(instance_file_path) or checkIfZipIsCorrupted(instance_file_path):
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

def downloadCurseforgeMod(mod_id: str, mod_loader: str, minecraft_version: str, mod_version: str,
                          download_dir: str, instance_dirs: list[str], curseforge_api_key: str) -> None:
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
    
    if not os.path.exists(downloaded_file_path) or checkIfZipIsCorrupted(downloaded_file_path):
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
            if not os.path.isfile(instance_file_path) or checkIfZipIsCorrupted(instance_file_path):
                try:
                    shutil.copy(downloaded_file_path, instance_file_path)
                    logging.info(f'Copied "{downloaded_file_path}" to "{instance_dir}"')
                except Exception as e:
                    logging.warning(f'Could not copy "{downloaded_file_path}" into "{instance_dir}": {e}')
                    continue

def updateMods(instances: ParsedInstances, config: Config) -> None:
    logging.debug(f'Creating folders to download mods into')
    for mod_loader in instances:
        for minecraft_version in instances[mod_loader]['mods']:
            directory = ""
            try:
                directory = os.path.join(config['Downloads Folder'], mod_loader, minecraft_version)
                os.makedirs(directory, exist_ok = True)
            except Exception as e:
                logging.warning(f'Could not create download folder {directory}: {e}')
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
                            if config['CurseForge API Key'] == None:
                                logging.warning("No CurseForge API key is given, skipping mod...")
                                continue
                            downloadCurseforgeMod(mod_id, mod_loader, minecraft_version, mod_version, config['Downloads Folder'], instance_dirs, config['CurseForge API Key'])

def deleteDuplicateMods(instances: Instances) -> None:
    logging.info(f'DELETING OUTDATED MODS')
    
    def scanFolder(instance_dir: str) -> None:
        logging.debug(f'Scanning for old mods')
        instance_dir = os.path.join(instance_dir, 'mods')
        ids: dict[str, dict[float, str]] = {}
        
        if os.path.exists(instance_dir):
            for mod_file in [f for f in os.listdir(instance_dir) if f.endswith('.jar')]:
                mod_path = os.path.join(instance_dir, mod_file)
                date_created = os.path.getctime(mod_path)
                with zipfile.ZipFile(mod_path) as zip_file:
                    with zip_file.open('fabric.mod.json') as f:
                        mod_id = json.load(f, strict=False)['id']
                        ids.setdefault(mod_id, {})
                ids[mod_id][date_created] = mod_path
            
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

def main():
    logging.debug(f'Running main body of script')
    
    config = loadConfigFile()
    if config['Check for RMMUD Updates']: checkForUpdate()
    
    instances = loadInstances(config['Instances Folder'])
    parsed_instances = parseInstances(instances)
    
    if len(parsed_instances) == 0:
        logging.info(f'No instances exist!')
    else:
        updateMods(parsed_instances, config)
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
        logging.error(e)
        input(f'The script could no longer continue to function due to the error described above. Please fix the issue described or go to https://github.com/RandomGgames/RMMUD to request help/report a bug')
        exit(1)
