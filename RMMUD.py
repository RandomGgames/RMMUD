import json
import logging
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
from send2trash import send2trash
from urllib.parse import urlparse, urlunparse
logger = logging.getLogger(__name__)

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
    def __init__(self, name: str, enabled: bool, game_version: str, mod_loader: typing.Literal['Fabric', 'Forge'], directory: Path = None, mod_urls: list = []):
        self.name = str(name)
        self.enabled = bool(enabled)
        self.mod_loader = str(mod_loader)
        self.game_version = str(game_version)
        self.directory = Path(directory) if directory is not None else None
        self.mod_urls = list(mod_urls)
    
    def __str__(self):
        return str(vars(self))

class Modrinth:
    url_header = {'User-Agent': 'RandomGgames/RMMUD (randomggamesofficial@gmail.com)'}
    _instances = {}
    
    def _validate_url(url):
        if url.netloc != 'modrinth.com':
            raise ValueError('URL link does not go to modrinth.com')
    
    class Mod:
        def __new__(cls, url: urlparse, game_version: str, mod_loader: str):
            isntance_key = (url.geturl(), game_version, mod_loader)
            existing_instance = Modrinth._instances.get(isntance_key)
            
            if existing_instance:
                return existing_instance
            else:
                new_instance = super().__new__(cls)
                new_instance._already_exists = False
                Modrinth._instances[isntance_key] = new_instance
                return new_instance
        
        def __init__(self, url: urlparse, game_version: str, mod_loader: str):
            if self._already_exists: return
            
            self.url = url
            Modrinth._validate_url(self.url)
            self._validate_url(self.url)
            
            url_path_split = self.url.path.split('/')[1:]
            self.slug = url_path_split[1]
            if len(url_path_split) == 4:
                self.mod_version = url_path_split[3]
            else:
                self.mod_version = None
            self.mod_loader = str(mod_loader)
            self.game_version = str(game_version)
            
            self.file_name = None
            self.download_url = None
            self.mod_file = None
            
            self._mod_key = (self.url.geturl(), game_version, mod_loader)
            self._already_exists = True
            
        def _validate_url(self, url):
            try:
                url_path_split = url.path.split('/')[1:]
            except Exception as e:
                raise ValueError('Invalid URL. The path should contain more path objects.')
            if len(url_path_split) not in (2, 4):
                raise ValueError(f'Invalid URL. The path should contain a slug and optionally a specific version.')
            if url_path_split[0] not in ('mod', 'plugin', 'datapack'):
                raise ValueError('Invalid URL. The path should contain a mod.')
        
        def _get_version(self):
            base_url = urlparse(f'https://api.modrinth.com/v2/project/{self.slug}/version')
            if self.mod_version is None:
                query = f'loaders=["{self.mod_loader}"]&game_versions=["{self.game_version}"]'
            else:
                query = f'loaders=["{self.mod_loader}"]'
            print(base_url.geturl())
            print(query)
            url = urlunparse(base_url._replace(query = query))
            print(url)
            response = requests.get(url, headers = Modrinth.url_header).json()
            if self.mod_version is None:
                desired_mod_version = sorted(response, key = lambda x: datetime.fromisoformat(x['date_published'][:-1]), reverse = True)
                if len(desired_mod_version) == 0:
                    return None
                else:
                    return desired_mod_version[0]
            else:
                return next((v for v in response if v['version_number'] == self.mod_version), None)
        
        def download(self, instance_dir: Path):
            logger.info(f'Updating {self.slug} for {self.game_version} in "{instance_dir}"')
            if self.mod_file is None:
                mod_version = self._get_version()
                if mod_version is None:
                    logger.warning(f'Could not find compatable version of {self.slug} for {self.mod_loader} {self.game_version}.')
                    return None
                
                mod_version_files = mod_version['files']
                if any(file['primary'] == True in file for file in mod_version_files):
                    mod_version_files = [file for file in mod_version_files if file['primary'] == True]
                mod_version_file = mod_version_files[0]
                
                self.file_name = mod_version_file['filename']
                self.download_url = mod_version_file['url']
                self.mod_file = requests.get(self.download_url, headers = Modrinth.url_header).content
            
            
            copy_dir = os.path.join(instance_dir, 'mods')
            copy_path = os.path.join(copy_dir, self.file_name)
            
            if not os.path.exists(instance_dir):
                class DirectoryNotFoundError(FileNotFoundError): pass
                raise DirectoryNotFoundError(f'The minecraft directory "{instance_dir}" cannot be found.')
            
            if os.path.exists(copy_path) and checkIfZipIsCorrupted(copy_path):
                logger.info(f'    You already have "{copy_path}" downloaded but it\'s corrupted. Deleting...')
                os.remove(copy_path)
                logger.info(f'    Deleted "{copy_path}".')
            
            if not os.path.exists(copy_path):
                with open(copy_path, 'wb') as f:
                    f.write(self.mod_file)
                    logger.info(f'    Downloaded "{self.file_name}" into "{copy_dir}".')

def createDir(dir: Path) -> None:
    try:
        if not os.path.exists(dir):
            logger.debug(f'    Creating dir "{str(dir)}"...')
            os.makedirs(dir)
            logger.info(f'    Created dir.')
    except Exception as e:
        logger.error(f'An error occured while creating dir due to {repr(e)}.')
        raise e

def extractNestedStrings(iterable: str | list | dict | tuple) -> list[str]:
    logger.debug('    Extracting nested strings...')
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
        logger.debug('    Extracted nested strings.')
        return extracted_strings
    except Exception as e:
        logger.error(f'An error occured while extracting nested strings due to {repr(e)}')
        raise e

def readYAML(path: str) -> dict:
    try:
        logger.debug(f'    Reading the YAML file located at "{path}"...')
        with open(path, 'r') as f:
            data = yaml.load(f, yaml.SafeLoader)
            logger.debug(f'    Read the YAML file located at "{path}".')
            return data
    except Exception as e:
        logger.error(f'    An error occured while reading the YAML file located at "{path}" due to {repr(e)}')
        raise e

def checkIfZipIsCorrupted(path: str) -> bool:
    try:
        logger.debug(f'    Checking if zip located at "{path}" is corrupted.')
        if not os.path.exists(path):
            logger.debug(f'    Could not check if zip is corrupted. It does not exist.')
            return None
        with zipfile.ZipFile(path) as zip_file:
            zip_file.testzip()
            logger.debug(f'    Checked if zip is corrupted (it\'s not).')
            return False
    except zipfile.BadZipFile as e:
        logger.debug(f'    Checked if zip is corrupted (it is) with the error {repr(e)}')
        return True
    except Exception as e:
        logger.error(f'An error occurred while checking if zip is corrupted due to {repr(e)}')
        raise e

def compareTwoVersions(v1: str, v2: str) -> typing.Literal['higher', 'lower', 'same']:
    try:
        logger.debug(f'    Comparing two versions together...')
        v1_list = list(map(int, v1.split('.')))
        v2_list = list(map(int, v2.split('.')))
        max_elements = max(len(v1_list), len(v2_list))
        
        while len(v1_list) < max_elements:
            v1_list.append(0)
        while len(v2_list) < max_elements:
            v2_list.append(0)
        
        for i in range(min(len(v1_list), len(v2_list))):
            if v1_list[i] > v2_list[i]:
                logger.debug('    v1 is higher than v2.')
                return 'higher'
            elif v1_list[i] < v2_list[i]:
                logger.debug(f'    v1 is lower than v2.')
                return 'lower'
        logger.debug(f'    v1 is the same as v2.')
        return 'same'
    except Exception as e:
        logger.error(f'An error occured while comparing two versions together due to {repr(e)}')
        raise e

def getGithubLatestReleaseTag(url: str, include_prereleases: bool = False) -> str:
    try:
        logger.debug('    Getting latest github release version...')
        versions: list[dict] = requests.get(url).json()
        if not include_prereleases:
            versions = [version for version in versions if not version.get('prerelease')]
        latest_version = versions[0].get('tag_name', None)
        logger.debug('    Got latest github release version.')
        return latest_version
    except Exception as e:
        logger.error(f'    An error occured while getting latest github release version due to {repr(e)}')
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
                logger.info(f'    There is an update available! ({current_version} (current) → {github_version} (latest))')
                promptToOpenURL('downloads page', 'Would you like to open the downloads page?', 'https://github.com/RandomGgames/RMMUD/releases')
                exit()
            except:
                return None
        case 'lower':
            logger.info(f'    You are currently using a pre-release or work-in-progress version! If you encounter any bugs or issues, please report any issues here: https://github.com/RandomGgames/RMMUD/issues. Thanks!')
            return False
        case 'same':
            logger.info(f'    You are already on the latest version.')
            return None

def verifyAttributeTypes(values: dict, types: dict[typing.Union[type, tuple[type, ...]]]) -> bool:
    logger.debug('    Verifying attribute types...')
    for key, val in values.items():
        expected_type = types[key]
        if not isinstance(val, expected_type):
            raise TypeError(f'Attribute "{key}" should be of type{"s" if isinstance(expected_type, tuple) else ""} "{expected_type}" but got "{type(val)}"')
    logger.debug('    Verified attribute types.')
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
        logger.info(f'    LOADED CONFIG FILE.')
        return Configuration(**yaml_data)
    except Exception as e:
        logger.error(f'An error occured while loading config file due to {repr(e)}')
        raise e

def loadInstanceFile(path: Path) -> Instance | None:
    try:
        logger.debug(f'    Loading instance file...')
        read_data = readYAML(path)
        data = {}
        data['name'] = os.path.splitext(os.path.basename(path))[0]
        data['enabled'] = read_data['Enabled']
        data['mod_loader'] = read_data['Loader']
        data['game_version'] = read_data['Version']
        data['directory'] = read_data['Directory']
        data['mod_urls'] = extractNestedStrings(read_data['Mods'])
        attribute_types = {
            "name": str,
            "enabled": bool,
            "mod_loader": str,
            "game_version": str,
            "directory": str,
            "mod_urls": list,
        }
        verifyAttributeTypes(data, attribute_types)
        logger.debug(f'    Loaded instance file.')
        return Instance(**data)
    except Exception as e:
        logger.error(f'An error occured while loading instance file due to {repr(e)}')
        raise e

def loadInstances(instances_dir: str) -> list[Instance]:
    logger.info(f'LOADING INSTANCES...')
    enabled_instances = []
    try:
        for instance_file in [file for file in os.listdir(instances_dir) if file.endswith('.yaml')]:
            instance_path = os.path.join(instances_dir, instance_file)
            instance_name = os.path.splitext(instance_file)[0]
            instance = loadInstanceFile(instance_path)
            
            if instance.enabled:
                enabled_instances.append(instance)
                logger.info(f'    Loaded enabled instance "{instance_name}"')
            else:
                logger.info(f'    Ignoring disabled instance "{instance_name}"')
        logger.info(f'LOADED INSTANCES.')
        if len(enabled_instances) == 0:
            return None
        return enabled_instances
    except Exception as e:
        logger.error(f'An error occured while loading instance files due to {repr(e)}')
        raise e

#def downloadCurseforgeMod(mod_id: str, mod_loader: str, minecraft_version: str, mod_version: str, download_dir: str, instance_dirs: list[str], curseforge_api_key: str) -> None:
#    logger.info(f'Updating {mod_id} for {mod_loader} {minecraft_version}')
    
#    # Getting mod ID
#    logger.debug(f'Getting mod ID from CurseForge')
#    url = 'https://api.curseforge.com/v1/mods/search'
#    params = {'gameId': '432','slug': mod_id, 'classId': '6'}
#    curseforge_header = {'Accept': 'application/json','x-api-key': curseforge_api_key}
#    try:
#        response = requests.get(url, params, headers = curseforge_header).json()['data']
#        curseforge_mod_id = response[0]['id']
#    except Exception as e:
#        logger.warning(f'Could not fetch CurseForge ID for "{mod_id}": {repr(e)}')
#        return
    
#    # Get latest or desired mod version
#    logger.debug(f'Getting files from CurseForge')
#    curseforge_mod_loader = { 'forge': 1, 'fabric': 4 }.get(mod_loader, None)
#    if mod_version == 'latest_version':
#        try:
#            url = (f'https://api.curseforge.com/v1/mods/{curseforge_mod_id}/files')
#            params = {'gameVersion': str(minecraft_version), 'modLoaderType': curseforge_mod_loader}
#            response = requests.get(url, params = params, headers = curseforge_header).json()['data']
#            desired_mod_version_file = list(file for file in response if minecraft_version in file['gameVersions'])[0]
#        except Exception as e:
#            logger.warning(f'Could not find "{mod_id}" for {mod_loader} {minecraft_version}. https://www.curseforge.com/minecraft/mc-mods/{mod_id}')
#            return
#    else:
#        try:
#            desired_mod_version_file = requests.get(f'https://api.curseforge.com/v1/mods/{curseforge_mod_id}/files/{mod_version}', params = {'modLoaderType': curseforge_mod_loader}, headers = curseforge_header).json()['data']
#        except Exception as e:
#            logger.warning(f'Could not find "{mod_id} {mod_version}" for {mod_loader} {minecraft_version}')
    
#    logger.debug(f'Downloading desired version from CurseForge')
#    file_name = desired_mod_version_file['fileName']
#    download_url = desired_mod_version_file['downloadUrl']
#    if download_url == None:
#        logger.debug(f'Mod dev has disabled extenal program support for this mod, but I have a workaround ;)')
#        download_url = f'https://edge.forgecdn.net/files/{str(desired_mod_version_file["id"])[0:4]}/{str(desired_mod_version_file["id"])[4:7]}/{file_name}'
#    download_path = os.path.join(download_dir, mod_loader, minecraft_version)
#    downloaded_file_path = os.path.join(download_path, file_name)
    
#    if not os.path.exists(downloaded_file_path) or checkIfZipIsCorrupted(downloaded_file_path):
#        try:
#            response = requests.get(download_url, headers = curseforge_header)
#            with open(downloaded_file_path, 'wb') as f: f.write(response.content)
#        except Exception as e:
#            logger.warning(f'Could not download "{mod_id}": {e}')
#            return
#        logger.info(f'Downloaded "{file_name}" into "{download_path}"')
    
#    logger.debug(f'Copying downloaded file into instance(s)')
#    for instance_dir in instance_dirs:
#        instance_dir = os.path.join(instance_dir, 'mods')
#        instance_file_path = os.path.join(instance_dir, file_name)
#        if os.path.exists(instance_dir) and os.path.exists(downloaded_file_path):
#            if not os.path.isfile(instance_file_path) or checkIfZipIsCorrupted(instance_file_path):
#                try:
#                    shutil.copy(downloaded_file_path, instance_file_path)
#                    logger.info(f'Copied "{downloaded_file_path}" to "{instance_dir}"')
#                except Exception as e:
#                    logger.warning(f'Could not copy "{downloaded_file_path}" into "{instance_dir}": {e}')
#                    continue

def updateMods(instances: typing.List[Instance], config: Configuration) -> None:
    logger.info('UPDATING MODS...')
    
    for instance in instances:
        name = instance.name
        mod_loader = instance.mod_loader
        game_version = instance.game_version
        directory = instance.directory
        mod_urls = instance.mod_urls
        
        #logger.debug(dict(vars(instance).items()))
        
        for mod_url in mod_urls:
            mod_url = urlparse(mod_url)
            
            match mod_url.netloc:
                case 'modrinth.com':
                    Modrinth.Mod(mod_url, game_version, mod_loader.lower()).download(directory)
                    pass
                case _:
                    logger.warning(f'Cannot update {mod_url.geturl()}. Script cannot currently handle URLs from {mod_url.netloc}.')
        
    #mods_set = mods_set.dataset
    #
    #try:
    #    logger.info(f'Creating folders to download mods into...')
    #    for game_version in mods_set:
    #        for mod_loader in mods_set[game_version]:
    #            path = os.path.join(config.downloads_folder, game_version, mod_loader)
    #            createDir(path)
    #except Exception as e:
    #    logger.exception(f'Could not create folder to download mods into due to {repr(e)}')
    #    raise e
    
    #for game_version in mods_set:
    #    for loader in mods_set[game_version]:
    #        for mod_url in mods_set[game_version][loader]:
    #            dirs = mods_set[game_version][loader][mod_url]
    #            url = urlparse(mod_url)
    #            netloc = url.netloc
    #            #logger.debug(f'{url = }')
    #            #logger.debug(f'{netloc = }')
    #            #logger.debug(f'{game_version = }, {loader = }, {mod_url = }, {dirs = }')
    #            
    #            match netloc:
    #                case 'modrinth.com':
    #                    pass
    #                    mod = Modrinth.Mod(url, game_version)
    #                    logger.debug(f'{str(mod) = }')
    #                    #downloadModrinthMod(mod_id, mod_loader, minecraft_version, mod_version, config['Downloads Folder'], instance_dirs)
    #                case 'curseforge.com':
    #                    pass
    #                    #downloadCurseforgeMod(mod_id, mod_loader, minecraft_version, mod_version, config['Downloads Folder'], instance_dirs, config['CurseForge API Key'])
    #                case _:
    #                    logger.warning(f'This script cannot handle urls from {netloc}. If you wish to be able to use this site, request it on the GitHub page!')
    #                    pass
    #logger.info('DONE UPDATING MODS')

#def deleteDuplicateMods(instances: list[Instance]) -> None: # TODO Rework this to work with class
#    logger.info(f'DELETING OUTDATED MODS')
    
#    def scanFolder(instance_dir: str) -> None:
#        logger.debug(f'Scanning for old mods')
#        instance_dir = os.path.join(instance_dir, 'mods')
#        ids: dict[str, dict[float, str]] = {}
        
#        if os.path.exists(instance_dir):
#            for mod_file in [f for f in os.listdir(instance_dir) if f.endswith('.jar')]:
#                mod_path = os.path.join(instance_dir, mod_file)
#                date_created = os.path.getctime(mod_path)
#                with zipfile.ZipFile(mod_path) as zip_file:
#                    with zip_file.open('fabric.mod.json') as f:
#                        id = json.load(f, strict=False)['id']
#                        ids.setdefault(id, {})
#                ids[id][date_created] = mod_path
            
#            ids = {key: dates for key, dates in ids.items() if len(dates) > 1}
            
#            if ids:
#                logger.debug(f'Deleting old mods')
#                for mod_id, dates in ids.items():
#                    latest_date = max(dates.keys())
#                    for date_created, path in dates.items():
#                        if date_created != latest_date:
#                            try:
#                                os.remove(path)
#                                logger.info(f'Deleted old {mod_id} file: "{path}"')
#                            except Exception as e:
#                                logger.warning(f'Could not delete old {mod_id} file "{path}": {e}')
#            else:
#                logger.debug(f'No old mods to delete')
#        else:
#            logger.warning(f'Could not delete old mods in "{instance_dir}": Could not find "{instance_dir}"')
    
#    for instance_name, instance in instances.items():
#        logger.info(f'Deleting old mods from instance: {instance_name}')
#        if instance['Loader'] == 'fabric':
#            instance_dir = instance['Directory']
#            scanFolder(instance_dir)
#        else:
#            logger.warning(f'Cannot auto-delete old mods in {instance_dir}: Only fabric mods supported atm.')

def main():
    config = loadConfig()
    
    createDir(config.instances_folder)
    
    #logger.debug(f'Config: {config}')
    
    if config.check_for_updates: checkForUpdate()
    
    enabled_instances = loadInstances(config.instances_folder)
    #for instance in instances: logger.debug(f'Instance: {instance}')
    
    #mods_set = ModsSet(instances)
    #logger.debug(f'{str(mods_set) = }')
    
    if enabled_instances is None:
        logger.info(f'No enabled instances exist!')
    else:
        updateMods(enabled_instances, config)
        #deleteDuplicateMods(instances)

if __name__ == '__main__':
    if os.path.exists('latest.log'): open('latest.log', 'w').close() # Clear latest.log if it exists
    
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
    
    try:
        main()
    except Exception as e:
        logger.error(f'{repr(e)}\nThe script could no longer continue to function due to the error described above. Please fix the issue described or go to https://github.com/RandomGgames/RMMUD to request help/report a bug')
        input('Press any key to exit.')
        exit(1)
