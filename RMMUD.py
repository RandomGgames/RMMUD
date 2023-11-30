import logging
logger = logging.getLogger(__name__)
import json
import os
import requests
import shutil
import sys
import webbrowser
import yaml
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Literal, Union, List, Dict
from urllib.parse import urlparse

__version_info__ = (3, 7, 1)
__version__ = '.'.join(str(x) for x in __version_info__)

# sydney = <3 for gian 4 evr
# ^^^ My girlfriend wrote this for me, I am not removing it.

class Configuration:
    def __init__(self, check_for_updates: bool, downloads_folder: str = 'RMMUDDownloads', instances_folder: str = 'RMMUDInstances', curseforge_api_key: str | None = None):
        self.check_for_updates = bool(check_for_updates)
        self.downloads_folder = Path(downloads_folder)
        self.instances_folder = Path(instances_folder)
        if curseforge_api_key is not None and len(curseforge_api_key) == 60 and curseforge_api_key.startswith('$2a$10$'):
            self.curseforge_api_key = str(curseforge_api_key)
        else:
            self.curseforge_api_key = None
    
    def __str__(self):
        return f"Configuration: check_for_updates={self.check_for_updates}, downloads_folder='{self.downloads_folder}', instances_folder='{self.instances_folder}', curseforge_api_key='{self.curseforge_api_key}'"

class Instance:
    def __init__(self, name: str, enabled: bool, version: str, loader: Literal['Fabric', 'Forge'], directory: Path = None, mods: list = []):
        self.name = str(name)
        self.enabled = bool(enabled)
        self.loader = str(loader)
        self.version = str(version)
        self.directory = Path(directory) if directory is not None else None
        self.mods = list(mods)
    
    def __str__(self):
        return str(vars(self))

class ModsSet:
    def __init__(self, instances: list[Instance]):
        self.instances = instances
        self.dataset = self.generate_dataset()
    
    def generate_dataset(self) -> Dict[str, Dict[str, Dict[str, List[Path]]]]:
        mod_set = {}
        for instance in self.instances:
            for mod in instance.mods:
                version, loader, directory = instance.version, instance.loader, instance.directory
                mod_set.setdefault(version, {}).setdefault(loader, {}).setdefault(mod, [])
                if directory not in mod_set[version][loader][mod]: mod_set[version][loader][mod].append(directory)
        return mod_set
    
    def __str__(self):
        return str(self.dataset)

class Modrinth:
    class Mod:
        def __init__(self, url: urlparse):
            
            def _validate_url(self, url: urlparse):
                try:
                    url_path_split = self.url_path.split('/')
                except Exception as e:
                    raise ValueError('Invalid URL. The path should contain more path objects.')
                if url_path_split[1] != 'mod':
                    raise ValueError('Invalid URL. The path should contain the type and slug|id.')
                try:
                    self.slug = url_path_split[2]
                except Exception as e:
                    raise ValueError('Invalid URL. The path should contain the slug|id.')
                return True
                
                
                
            
            self.url = url
            self.url_path = url.path
            self.url_netloc = url.netloc
            self.url_params = url.params
            
        def __str__(self):
            return str(vars(self))
    
    def download(self, path):
        base_url = (f'https://api.modrinth.com/v2/project/{self.slug}/version')
    
    #    if mod_version == 'latest_version':
    #        params = {'loaders': [mod_loader], 'game_versions': [minecraft_version]}
    #    else:
    #        params = {'loaders': [mod_loader]}
    #    url = f'{base_url}?{"&".join([f"{key}={json.dumps(value)}" for key, value in params.items()])}'
    #    try:
    #        modrinth_header = {'User-Agent': 'RandomGgames/RMMUD (randomggamesofficial@gmail.com)'}
    #        response = requests.get(url, headers = modrinth_header).json()
    #    except Exception as e:
    #        logger.warning(f'Could not update "{mod_id}": {e}')
    #        return
    #    response = sorted(response, key = lambda x: datetime.fromisoformat(x['date_published'][:-1]), reverse = True)
    #    if mod_version == 'latest_version':
    #        if len(response) > 0:
    #            desired_mod_version = response[0]
    #        else:
    #            logger.warning(f'Could not find "{mod_id}" for {mod_loader} {minecraft_version}. https://modrinth.com/mod/{mod_id}')
    #            return
    #    else:
    #        if len(response) > 0:
    #            desired_mod_version = [version for version in response if version['version_number'] == mod_version][0]
    #        else:
    #            logger.warning(f'Could not find "{mod_id} {mod_version}" for {mod_loader} {minecraft_version}')
    #            return
    #    desired_mod_version_files = desired_mod_version['files']
    #    if any(file['primary'] == True in file for file in desired_mod_version_files):
    #        desired_mod_version_files = [file for file in desired_mod_version_files if file['primary'] == True]
    #    desired_mod_version_file = desired_mod_version_files[0]
    

def extractNestedStrings(iterable: str | list | dict | tuple) -> list[str]:
    logger.debug('Extracting nested strings...')
    def extract(iterable: str | list | dict | tuple) -> list[str]:
        strings: list[str] = []
        match iterable:
            case dict():
                for value in iterable.values():
                    strings += extract(value)
            case list() | tuple():
                for item in iterable:
                    strings += extract(item)
            case str():
                if iterable not in strings:
                    strings.append(iterable)
            case _:
                if isinstance(iterable, type(None)):
                    pass
                else:
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
            logger.debug(f'Read the YAML file located at "{path}".')
            return data
    except Exception as e:
        logger.error(f'An error occured while reading the YAML file located at "{path}" due to {repr(e)}')
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

def compareTwoVersions(v1: str, v2: str) -> Literal['higher', 'lower', 'same']:
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
                logger.debug('v1 is higher than v2.')
                return 'higher'
            elif v1_list[i] < v2_list[i]:
                logger.debug(f'v1 is lower than v2.')
                return 'lower'
        logger.debug(f'v1 is the same as v2.')
        return 'same'
    except Exception as e:
        logger.error(f'An error occured while comparing two versions together due to {repr(e)}')
        raise e

def getGithubLatestReleaseTag(url: str, include_prereleases: bool = False) -> str:
    try:
        logger.debug('Getting latest github release version...')
        versions: list[dict] = requests.get(url).json()
        if not include_prereleases:
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
        open_update = input(f'{prompt_message} Y/N: ').lower()
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
        url = 'https://api.github.com/repos/RandomGgames/RMMUD/releases'
        github_version = getGithubLatestReleaseTag(url)
    except Exception as e:
        logger.warning(f'An error occured while getting github\'s version due to {repr(e)}. Due to this error, checking for updates could not continue.')
        return None
    
    try:
        version_check = compareTwoVersions(github_version, __version__)
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
            logger.info(f'You are currently using a pre-release or work-in-progress version! If you encounter any bugs or issues, please report any issues here: https://github.com/RandomGgames/RMMUD/issues. Thanks!')
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

def verifyAttributeTypes(values: dict, types: dict[Union[type, tuple[type, ...]]]) -> bool:
    logger.debug('Verifying attribute types...')
    for key, val in values.items():
        expected_type = types[key]
        if not isinstance(val, expected_type):
            raise TypeError(f'Attribute "{key}" should be of type{"s" if isinstance(expected_type, tuple) else ""} "{expected_type}" but got "{type(val)}"')
    logger.debug('Verified attribute types.')
    return True

def loadConfig(config_path: str = "RMMUDConfig.yaml") -> Configuration:
    try:
        logger.info(f'LOADING CONFIG FILE...')
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
        logger.info(f'LOADED CONFIG FILE.')
        return Configuration(**yaml_data)
    except Exception as e:
        logger.error(f'An error occured while loading config file due to {repr(e)}')
        raise e

def loadInstanceFile(path: Path) -> Instance | None:
    try:
        logger.debug(f'Loading instance file...')
        read_data = readYAML(path)
        data = {}
        data['name'] = os.path.splitext(os.path.basename(path))[0]
        data['enabled'] = read_data['Enabled']
        data['loader'] = read_data['Loader']
        data['version'] = read_data['Version']
        data['directory'] = read_data['Directory']
        data['mods'] = extractNestedStrings(read_data['Mods'])
        attribute_types = {
            "name": str,
            "enabled": bool,
            "loader": str,
            "version": str,
            "directory": str,
            "mods": list,
        }
        verifyAttributeTypes(data, attribute_types)
        logger.debug(f'Loaded instance file.')
        return Instance(**data)
    except Exception as e:
        logger.error(f'An error occured while loading instance file due to {repr(e)}')
        raise e

def loadInstances(instances_dir: str) -> list[Instance]:
    try:
        logger.info(f'LOADING INSTANCES...')
        enabled_instances = []
        if not os.path.exists(instances_dir):
            logger.debug(f'Creating folder "{instances_dir}"')
            os.makedirs(instances_dir)
            logger.debug(f'Created folder "{instances_dir}".')
    except Exception as e:
        logger.error(f'An error occured while creating folder "{instances_dir}" due to {repr(e)}')
        raise e
    try:
        for instance_file in [file for file in os.listdir(instances_dir) if file.endswith('.yaml')]:
            instance_path = os.path.join(instances_dir, instance_file)
            instance_name = os.path.splitext(instance_file)[0]
            instance = loadInstanceFile(instance_path)
            
            if instance.enabled:
                enabled_instances.append(instance)
                logger.info(f'Loaded enabled instance "{instance_name}"')
            else:
                logger.info(f'Ignoring disabled instance "{instance_name}"')
        logger.info(f'LOADED INSTANCES.')
        return enabled_instances
    except Exception as e:
        logger.error(f'An error occured while loading instance files due to {repr(e)}')
        raise e

def downloadModrinthMod(mod_id: str, mod_loader: str, minecraft_version: str, mod_version: str, download_dir: str, instance_dirs: list[str]) -> None:
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
    response = sorted(response, key = lambda x: datetime.fromisoformat(x['date_published'][:-1]), reverse = True)
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

def updateMods(mods_set: dict, config: Configuration) -> None:
    mods_set = mods_set.dataset
    
    try:
        logger.debug(f'Creating folders to download mods into...')
        for version in mods_set:
            for loader in mods_set[version]:
                path = os.path.join(config.downloads_folder, loader, version)
                if not os.path.exists(path):
                    os.makedirs(path)
                    logger.debug(f'Created "{path}"')
    except Exception as e:
        logger.exception(f'Could not create folder to download mods into due to {repr(e)}')
        raise e
    
    for version in mods_set:
        for loader in mods_set[version]:
            for mod_url in mods_set[version][loader]:
                dirs = mods_set[version][loader][mod_url]
                url = urlparse(mod_url)
                netloc = url.netloc
                #logger.debug(f'{url = }')
                #logger.debug(f'{netloc = }')
                #logger.debug(f'{version = }, {loader = }, {mod_url = }, {dirs = }')
                
                match netloc:
                    case 'modrinth.com':
                        pass
                        mod = Modrinth.Mod(url)
                        print(f'{str(mod) = }')
                        #downloadModrinthMod(mod_id, mod_loader, minecraft_version, mod_version, config['Downloads Folder'], instance_dirs)
                    case 'curseforge.com':
                        pass
                        #downloadCurseforgeMod(mod_id, mod_loader, minecraft_version, mod_version, config['Downloads Folder'], instance_dirs, config['CurseForge API Key'])
                    case _:
                        pass

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
    
    #logger.debug(f'Config: {config}')
    
    if config.check_for_updates: checkForUpdate()
    
    instances = loadInstances(config.instances_folder)
    #for instance in instances: logger.debug(f'Instance: {instance}')
    
    mods_set = ModsSet(instances)
    #logger.debug(f'{str(mods_set) = }')
    
    if len(instances) == 0:
        logger.info(f'No instances exist!')
    else:
        updateMods(mods_set, config)
        #deleteDuplicateMods(instances)
    
    logger.info('DONE.')

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
