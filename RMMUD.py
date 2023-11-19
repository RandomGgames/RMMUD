import logging
logger = logging.getLogger(__name__)
import json
import os
import requests
import shutil
import sys
import typing
import webbrowser
import yaml
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

__version_info__ = (3, 7, 1)
__version__ = '.'.join(str(x) for x in __version_info__)

# sydney = <3 for gian 4 evr
# ^^^ My girlfriend wrote this for me, I am not removing it.

class Configuration:
    def __init__(self, check_for_updates: bool, downloads_folder: str = 'RMMUDDownloads', instances_folder: str = 'RMMUDInstances', curseforge_api_key: str | None = None):
        self.check_for_updates = bool(check_for_updates)
        self.downloads_folder = str(downloads_folder)
        self.instances_folder = str(instances_folder)
        self.curseforge_api_key = str(curseforge_api_key) if curseforge_api_key is not None else None
    
    def __str__(self):
        return f"Configuration: check_for_updates={self.check_for_updates}, downloads_folder='{self.downloads_folder}', instances_folder='{self.instances_folder}', curseforge_api_key='{self.curseforge_api_key}'"

class Instance:
    def __init__(self, enabled: bool, version: str, loader: typing.Literal['Fabric', 'Forge'], directory: Path = None, mods: list = []):
        self.enabled = bool(enabled)
        self.loader = loader
        self.directory = Path(directory) if directory is not None else None
        self.mods = mods
        self.version = str(version)

def extractNestedStrings(iterable: str | list | dict | tuple) -> list[str]:
    logger.debug('Extracting nested strings...')
    def extract(iterable: str | list | dict | tuple) -> list[str]:
        strings: list[str] = []
        match iterable:
            case dict():
                for value in iterable.values():
                    strings += extract(value)
            case (list(), tuple()):
                for item in iterable:
                    strings += extract(item)
            case str():
                if iterable not in strings:
                    strings.append(iterable)
            case _:
                logger.warning(f'An invalid variable "{iterable}" of type "{type(iterable)}" was ignored.')
        return strings
    try:
        extracted_strings = extract(iterable)
        logger.debug('Extracted nested strings.')
        return extracted_strings
    except Exception as e:
        logger.error(f'An error occured while extracting nested strings due to {repr(e)}')
        raise e

def readYAML(path: str) -> dict:
    try:
        logger.debug(f'Reading the YAML file located at "{path}"...')
        with open(path, 'r') as f:
            data = yaml.load(f, yaml.SafeLoader)
            logger.debug(f'YAML file read completed.')
            return data
    except Exception as e:
        logger.error(f'An error occured while reading the YAML file due to {repr(e)}')
        raise e

def checkIfZipIsCorrupted(path: str) -> bool:
    try:
        logger.debug(f'Checking if zip located at "{path}" is corrupted.')
        with zipfile.ZipFile(path) as zip_file:
            zip_file.testzip()
            logger.debug(f'Checked if zip is corrupted (it\'s not).')
            return False
    except zipfile.BadZipFile as e:
        logger.debug(f'Checked if zip is corrupted (it is).')
        logger.exception(e)
        return True
    except Exception as e:
        logger.error(f'An error occurred while checking if zip is corrupted due to {repr(e)}')
        raise e

def compareTwoVersions(v1: str, v2: str) -> typing.Literal['higher', 'lower', 'same']:
    try:
        logger.debug(f'Comparing two versions together...')
        v1_list = list(map(int, v1.split('.')))
        v2_list = list(map(int, v2.split('.')))
        max_elements = max(len(v1_list), len(v2_list))
        
        while len(v1_list) < max_elements:
            v1_list.append(0)
        while len(v2_list) < max_elements:
            v2_list.append(0)
        
        for i in range(min(len(v1_list), len(v2_list))):
            if v1_list[i] > v2_list[i]:
                logging.debug('v1 is higher than v2.')
                return 'higher'
            elif v1_list[i] < v2_list[i]:
                logging.debug(f'v1 is lower than v2.')
                return 'lower'
        logging.debug(f'v1 is the same as v2.')
        return 'same'
    except Exception as e:
        logger.error(f'An error occured while comparing two versions together due to {repr(e)}')
        raise e

def getGithubLatestReleaseTag(url: str, include_prerelleases: bool = False) -> str:
    try:
        logger.debug('Getting latest github release version...')
        versions: list[dict] = requests.get(url).json()
        if not include_prerelleases:
            versions = [version for version in versions if not version.get('prerelease')]
        latest_version = versions[0].get('tag_name', None)
        logger.debug('Got latest github release version.')
        return latest_version
    except Exception as e:
        logger.error(f'An error occured while getting latest github release version due to {repr(e)}')
        raise e

def promptToOpenURL(url_name: str, prompt_message: str, url: str) -> None | bool:
    try:
        logger.debug(f'Prompting to open {url_name}...')
        open_update = input(f'{prompt_message} Y/N').lower()
        if open_update in ('y'):
            logger.debug('Prompt approved.')
            logger.debug(f'Opening {url_name}...')
            webbrowser.open(url)
            logger.debug(f'Opened {url_name}...')
            return True
        else:
            logger.debug('Prompt denied.')
            return False
    except Exception as e:
        logger.warning(f'An error occured while prompting to open {url_name} due to {repr(e)}')
        return False

def checkForUpdate() -> bool | None:
    logger.info('Checking for an RMMUD update...')
    
    try:
        current_version = __version__
        logging.debug(f'Getting github\'s version...')
        github_version = getGithubLatestReleaseTag()
        logging.debug(f'Got github\'s version.')
    except Exception as e:
        logger.warning(f'An error occured while getting github\'s version due to {repr(e)}. Due to this error, checking for updates could not continue.')
        return None
    
    try:
        logger.debug('Comparing two versions...')
        version_check = compareTwoVersions(github_version, __version__)
        logger.debug(f'Compared two versions.')
    except Exception as e:
        logger.warning(f'An error occured while comparing two versions due to {repr(e)}. Due to this error, checking for updates could not continue.')
        return None
    
    match version_check:
        case 'higher':
            try:
                logger.info(f'There is an update available! ({current_version} (current) → {github_version} (latest))')
                promptToOpenURL('downloads page', 'Would you like to open the downloads page?', 'https://github.com/RandomGgames/RMMUD/releases')
                exit()
            except:
                return None
        case 'lower':
            logger.info(f'You are on what seems like a work in progress version, as it is higher than the latest release. Please report any bugs onto the github page at https://github.com/RandomGgames/RMMUD')
            return False
        case 'same':
            logger.info(f'You are already on the latest version.')
            return None

def copyToPathOrPaths(file_path: Path, destination_file_path_or_paths: Path | list[Path]) -> None:
    match destination_file_path_or_paths:
        case destination_file_path if isinstance(destination_file_path, Path):
            logger.debug(f'Copying "{file_path}" into "{destination_file_path}".')
            try:
                shutil.copy2(file_path, destionation_file_path)
                logger.debug(f'Successfully coppied.')
            except Exception as e:
                logger.warning(f'An error occured while copying "{file_path}" to "{destination_file_path}" due to {repr(e)}')
        case destination_file_paths if isinstance(destination_file_paths, list[Path]):
            for destionation_file_path in destination_file_path_or_paths:
                logger.debug(f'Copying "{file_path}" into "{destination_file_path}".')
                try:
                    shutil.copy2(file_path, destionation_file_path)
                    logger.debug(f'Successfully coppied.')
                except Exception as e:
                    logger.warning(f'An error occured while copying "{file_path}" to "{destination_file_path}" due to {repr(e)}')
        case _:
            logger.warning(f'Could not copy file to path(s) due to invalid destination input "{destination_file_path_or_paths}"')
            raise ValueError(destination_file_path_or_paths)

def verifyAttributeTypes(values: dict, types: dict[typing.Union[type, tuple[type, ...]]]) -> bool:
    logger.debug('Verifying attribute types...')
    for key, val in values.items():
        expected_type = types[key]
        if not isinstance(val, expected_type):
            raise TypeError(f'Attribute "{key}" should be of type{"s" if isinstance(expected_type, tuple) else ""} "{expected_type}" but got "{type(val)}"')
    logger.debug('Verified attribute types.')
    return True

def loadConfig(config_path: str = "RMMUDConfig.yaml") -> Configuration:
    try:
        logger.debug(f'Loading config file...')
        read_data = readYAML(config_path)
        yaml_data = {}
        yaml_data['check_for_updates'] = read_data['Check for RMMUD Updates']
        yaml_data['downloads_folder'] = read_data['Downloads Folder']
        yaml_data['instances_folder'] = read_data['Instances Folder']
        yaml_data['curseforge_api_key'] = read_data['CurseForge API Key']
        attribute_types = {
            'check_for_updates': bool,
            'downloads_folder': str,
            'instances_folder': str,
            'curseforge_api_key': (str, type(None))
        }
        verifyAttributeTypes(yaml_data, attribute_types)
        logger.debug(f'Loaded config file.')
        return Configuration(**yaml_data)
    except Exception as e:
        logger.error(f'An error occured while loading config file due to {repr(e)}')
        raise e

def loadInstanceFile(path: str) -> typing.Type[Instance]: # TODO Rework this to work with class
    try:
        logger.debug(f'Reading instance file "{path}".')
        data = readYAML(path)
    except Exception as e:
        logger.error(f'Could not load config.')
        logger.exception(e)
        raise e
    
    logger.debug(f'Verifying instance variable types.')
    
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
    
    logger.debug(f'Done verifying instance variable types.')
    
    data["Loader"] = data["Loader"].lower()
    
    logger.debug(f'Done reading instance file')
    return data

def loadInstances(instances_dir: str) -> list[Instance]: # TODO Rework this to work with class
    logger.info(f'LOADING INSTANCES')
    
    if not os.path.exists(instances_dir):
        try:
            os.makedirs(instances_dir)
            logger.debug(f'Created folder "{instances_dir}"')
        except Exception as e:
            logger.error(f'Could not create "{instances_dir}".')
            logger.exception(e)
            raise e
    
    enabled_instances: list[Instance] = {}
    for instance_file in [f for f in os.listdir(instances_dir) if f.endswith('.yaml')]:
        instance_path = os.path.join(instances_dir, instance_file)
        instance_name = os.path.splitext(instance_file)[0]
        try:
            instance = loadInstanceFile(instance_path)
            if not instance['Enabled']:
                logger.info(f'Ignoring disabled instance "{instance_file}"')
                continue
            else:
                logger.info(f'Loading enabled instance "{instance_file}"')
                instance.pop('Enabled')
                enabled_instances[instance_name] = instance
        except Exception as e:
            logger.warning(f'Could not load instance "{instance_name}". Ignoring this file.')
            logger.exception(e)
            continue
    return enabled_instances

def parseInstances(instances: list[Instance]) -> Instance: # TODO This function is probably no longer required...
#    logger.debug('Parsing enabled instances')
#    
#    for instance_name, instance in instances.items():
#        mod_loader = str(instance['Loader']).lower()
#        minecraft_version = str(instance['Version'])
#        instance_dir = str(instance['Directory'])
#        mods = extractNestedStrings(instance['Mods'])
#        
#        for mod_url in mods:
#            url_authority = urlparse(mod_url).netloc
#            mod_version = 'latest_version'
#            if url_authority == "": continue # Probably a disabled mod just ignore it.
#            url_authority = url_authority.lstrip('www.')
#            
#            if url_authority == 'modrinth.com':
#                url_path = urlparse(mod_url).path
#                url_path_split = url_path.split('/')[1:]
#                
#                if url_path_split[0] not in ('mod', 'plugin', 'datapack'):
#                    continue
#                
#                mod_id = url_path_split[1]
#                
#                if len(url_path_split) == 4 and url_path_split[2] == 'version':
#                    mod_version = url_path_split[3]
#            
#            elif url_authority == 'curseforge.com':
#                url_path = urlparse(mod_url).path
#                url_path_split = url_path.split('/')[1:]
#                
#                if url_path_split[0] != 'minecraft' or url_path_split[1] != 'mc-mods':
#                    logger.warning(f'Url "{mod_url}" is not for a minecraft mod!')
#                    continue
#                
#                mod_id = url_path_split[2]
#                
#                if len(url_path_split) == 5 and url_path_split[3] == 'files':
#                    mod_version = url_path_split[4]
#            
#            else: # Unsupported website
#                logger.warning(f'Mod manager cannot handle URLs from "{url_authority}". {mod_url}')
#                continue
#            
#            parsed_instances.setdefault(mod_loader, {}).setdefault('mods', {}).setdefault(minecraft_version, {}).setdefault(mod_id, {}).setdefault(url_authority, {}).setdefault(mod_version, {}).setdefault('directories', [])
#            
#            if instance_dir not in parsed_instances[mod_loader]['mods'][minecraft_version][mod_id][url_authority][mod_version]['directories']:
#                parsed_instances[mod_loader]['mods'][minecraft_version][mod_id][url_authority][mod_version]['directories'].append(instance_dir)
#    
#    return parsed_instances
    pass

def downloadModrinthMod(mod_id: str, mod_loader: str, minecraft_version: str, mod_version: str,
                        download_dir: str, instance_dirs: list[str]) -> None:
    logger.info(f'Updating {mod_id} for {mod_loader} {minecraft_version}')
    
    logger.debug(f'Getting files from Modrinth')
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
        logger.warning(f'Could not update "{mod_id}": {e}')
        return
    response = sorted(response, key=lambda x: datetime.fromisoformat(x['date_published'][:-1]), reverse = True)
    if mod_version == 'latest_version':
        if len(response) > 0:
            desired_mod_version = response[0]
        else:
            logger.warning(f'Could not find "{mod_id}" for {mod_loader} {minecraft_version}. https://modrinth.com/mod/{mod_id}')
            return
    else:
        if len(response) > 0:
            desired_mod_version = [version for version in response if version['version_number'] == mod_version][0]
        else:
            logger.warning(f'Could not find "{mod_id} {mod_version}" for {mod_loader} {minecraft_version}')
            return
    desired_mod_version_files = desired_mod_version['files']
    if any(file['primary'] == True in file for file in desired_mod_version_files):
        desired_mod_version_files = [file for file in desired_mod_version_files if file['primary'] == True]
    desired_mod_version_file = desired_mod_version_files[0]
    
    logger.debug(f'Downloading desired version from Modrinth')
    download_url = desired_mod_version_file['url']
    file_name = desired_mod_version_file['filename']
    download_path = os.path.join(download_dir, mod_loader, minecraft_version)
    downloaded_file_path = os.path.join(download_path, file_name)
    
    if not os.path.exists(downloaded_file_path) or checkIfZipIsCorrupted(downloaded_file_path):
        try:
            response = requests.get(download_url, headers = modrinth_header)
        except Exception as e:
            logger.warning(f'Could not download "{mod_id}": {e}')
            return
        try:
            with open(downloaded_file_path, 'wb') as f: f.write(response.content)
        except Exception as e:
            logger.warning(f'Could not save file "{file_name}" to "{download_path}": {e}')
            return
        logger.info(f'Downloaded "{file_name}" into "{download_path}"')
    
    logger.debug(f'Copying downloaded file into instance(s)')
    for instance_dir in instance_dirs:
        instance_dir = os.path.join(instance_dir, 'mods')
        instance_file_path = os.path.join(instance_dir, file_name)
        if os.path.exists(instance_dir):
            if os.path.exists(downloaded_file_path):
                if not os.path.isfile(instance_file_path) or checkIfZipIsCorrupted(instance_file_path):
                    try:
                        shutil.copy(downloaded_file_path, instance_file_path)
                        logger.info(f'Copied "{downloaded_file_path}" into "{instance_dir}"')
                    except Exception as e:
                        logger.warning(f'Could not copy "{downloaded_file_path}" into "{instance_dir}": {e}')
                        continue
            else:
                logger.warning(f'Could not copy "{downloaded_file_path}" into "{instance_dir}": Could not find "{downloaded_file_path}"')
        else:
            logger.warning(f'Could not copy "{downloaded_file_path}" into "{instance_dir}": Could not find "{instance_dir}"')

def downloadCurseforgeMod(mod_id: str, mod_loader: str, minecraft_version: str, mod_version: str, download_dir: str, instance_dirs: list[str], curseforge_api_key: str) -> None:
    logger.info(f'Updating {mod_id} for {mod_loader} {minecraft_version}')
    
    # Getting mod ID
    logger.debug(f'Getting mod ID from CurseForge')
    url = 'https://api.curseforge.com/v1/mods/search'
    params = {'gameId': '432','slug': mod_id, 'classId': '6'}
    curseforge_header = {'Accept': 'application/json','x-api-key': curseforge_api_key}
    try:
        response = requests.get(url, params, headers = curseforge_header).json()['data']
        curseforge_mod_id = response[0]['id']
    except Exception as e:
        logger.warning(f'Could not fetch CurseForge ID for "{mod_id}": {repr(e)}')
        return
    
    # Get latest or desired mod version
    logger.debug(f'Getting files from CurseForge')
    curseforge_mod_loader = { 'forge': 1, 'fabric': 4 }.get(mod_loader, None)
    if mod_version == 'latest_version':
        try:
            url = (f'https://api.curseforge.com/v1/mods/{curseforge_mod_id}/files')
            params = {'gameVersion': str(minecraft_version), 'modLoaderType': curseforge_mod_loader}
            response = requests.get(url, params = params, headers = curseforge_header).json()['data']
            desired_mod_version_file = list(file for file in response if minecraft_version in file['gameVersions'])[0]
        except Exception as e:
            logger.warning(f'Could not find "{mod_id}" for {mod_loader} {minecraft_version}. https://www.curseforge.com/minecraft/mc-mods/{mod_id}')
            return
    else:
        try:
            desired_mod_version_file = requests.get(f'https://api.curseforge.com/v1/mods/{curseforge_mod_id}/files/{mod_version}', params = {'modLoaderType': curseforge_mod_loader}, headers = curseforge_header).json()['data']
        except Exception as e:
            logger.warning(f'Could not find "{mod_id} {mod_version}" for {mod_loader} {minecraft_version}')
    
    logger.debug(f'Downloading desired version from CurseForge')
    file_name = desired_mod_version_file['fileName']
    download_url = desired_mod_version_file['downloadUrl']
    if download_url == None:
        logger.debug(f'Mod dev has disabled extenal program support for this mod, but I have a workaround ;)')
        download_url = f'https://edge.forgecdn.net/files/{str(desired_mod_version_file["id"])[0:4]}/{str(desired_mod_version_file["id"])[4:7]}/{file_name}'
    download_path = os.path.join(download_dir, mod_loader, minecraft_version)
    downloaded_file_path = os.path.join(download_path, file_name)
    
    if not os.path.exists(downloaded_file_path) or checkIfZipIsCorrupted(downloaded_file_path):
        try:
            response = requests.get(download_url, headers = curseforge_header)
            with open(downloaded_file_path, 'wb') as f: f.write(response.content)
        except Exception as e:
            logger.warning(f'Could not download "{mod_id}": {e}')
            return
        logger.info(f'Downloaded "{file_name}" into "{download_path}"')
    
    logger.debug(f'Copying downloaded file into instance(s)')
    for instance_dir in instance_dirs:
        instance_dir = os.path.join(instance_dir, 'mods')
        instance_file_path = os.path.join(instance_dir, file_name)
        if os.path.exists(instance_dir) and os.path.exists(downloaded_file_path):
            if not os.path.isfile(instance_file_path) or checkIfZipIsCorrupted(instance_file_path):
                try:
                    shutil.copy(downloaded_file_path, instance_file_path)
                    logger.info(f'Copied "{downloaded_file_path}" to "{instance_dir}"')
                except Exception as e:
                    logger.warning(f'Could not copy "{downloaded_file_path}" into "{instance_dir}": {e}')
                    continue

def updateMods(instances: list[Instance], config: Configuration) -> None: # TODO Rework this to work with class
    logger.debug(f'Creating folders to download mods into')
    for mod_loader in instances:
        for minecraft_version in instances[mod_loader]['mods']:
            dir = ""
            try:
                dir = os.path.join(config['Downloads Folder'], mod_loader, minecraft_version)
                os.makedirs(dir, exist_ok = True)
            except Exception as e:
                logger.warning(f'Could not create download folder {dir}: {e}')
                raise e
    
    logger.info(f'UPDATING MODS')
    for mod_loader in instances:
        for minecraft_version in instances[mod_loader]['mods']:
            for mod_id in instances[mod_loader]['mods'][minecraft_version]:
                for website in instances[mod_loader]['mods'][minecraft_version][mod_id]:
                    for mod_version in instances[mod_loader]['mods'][minecraft_version][mod_id][website]:
                        instance_dirs = instances[mod_loader]['mods'][minecraft_version][mod_id][website][mod_version]['directories']
                        if website == 'modrinth.com':
                            downloadModrinthMod(mod_id, mod_loader, minecraft_version, mod_version, config['Downloads Folder'], instance_dirs)
                        elif website == 'curseforge.com':
                            downloadCurseforgeMod(mod_id, mod_loader, minecraft_version, mod_version, config['Downloads Folder'], instance_dirs, config['CurseForge API Key'])

def deleteDuplicateMods(instances: list[Instance]) -> None: # TODO Rework this to work with class
    logger.info(f'DELETING OUTDATED MODS')
    
    def scanFolder(instance_dir: str) -> None:
        logger.debug(f'Scanning for old mods')
        instance_dir = os.path.join(instance_dir, 'mods')
        ids: dict[str, dict[float, str]] = {}
        
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
                logger.debug(f'Deleting old mods')
                for mod_id, dates in ids.items():
                    latest_date = max(dates.keys())
                    for date_created, path in dates.items():
                        if date_created != latest_date:
                            try:
                                os.remove(path)
                                logger.info(f'Deleted old {mod_id} file: "{path}"')
                            except Exception as e:
                                logger.warning(f'Could not delete old {mod_id} file "{path}": {e}')
            else:
                logger.debug(f'No old mods to delete')
        else:
            logger.warning(f'Could not delete old mods in "{instance_dir}": Could not find "{instance_dir}"')
    
    for instance_name, instance in instances.items():
        logger.info(f'Deleting old mods from instance: {instance_name}')
        if instance['Loader'] == 'fabric':
            instance_dir = instance['Directory']
            scanFolder(instance_dir)
        else:
            logger.warning(f'Cannot auto-delete old mods in {instance_dir}: Only fabric mods supported atm.')

def main():
    logger.debug(f'Running main body of script')
    
    config = loadConfig()
    
    print(config)
    
    #try:
    #    if config['Check for RMMUD Updates']: checkForUpdate()
    #except Exception as e:
    #    logger.warning(f'Could not check for updates due to {repr(e)}... Update checks will have to be done manually due to the current or latest version tag.')
    
    #instances = loadInstances(config['Instances Folder'])
    #parsed_instances = parseInstances(instances)
    
    #if len(parsed_instances) == 0:
    #    logger.info(f'No instances exist!')
    #else:
    #    updateMods(parsed_instances, config)
    #    deleteDuplicateMods(instances)
    
    logger.info('Done.')

if __name__ == '__main__':
    # Clear latest.log if it exists
    if os.path.exists('latest.log'):
        open('latest.log', 'w').close()
    
    # Set up logger
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
    logger.debug('Logging initialized.')
    
    # Call main function
    try:
        main()
    except Exception as e:
        logger.error(f'{repr(e)}\nThe script could no longer continue to function due to the error described above. Please fix the issue described or go to https://github.com/RandomGgames/RMMUD to request help/report a bug')
        input('Press any key to exit.')
        exit(1)
