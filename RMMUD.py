from datetime import datetime
from urllib.parse import urlparse
from zipfile import ZipFile
import json
import logging
log = logging.getLogger(__name__)
import os
import requests
import shutil
import sys
import yaml

# sydney = <3 for gian 4 evr
# ^^^ My girlfriend wrote this for me, I am not removing it.

logging_level = logging.INFO
downloads_dir = 'RMMUDDownloads'
instances_dir = 'RMMUDInstances'
config_path = 'RMMUDConfig.yaml'
modrinth_header = {'User-Agent': 'RandomGgames/RMMUD/tree/dev (randomggamesofficial@gmail.com)'}
rmmud_config = None

__version_info__ = (3, 6, 0)
__version__ = '.'.join(str(x) for x in __version_info__)

def validateKeyTypes(dictionary_to_check: dict, key_type_pairs: dict = None):
    log.debug('Validating dictionary key types')
    for key in key_type_pairs.keys():
        if not key in dictionary_to_check:
            raise KeyError(f'Missing key: {key}')
        if not isinstance(dictionary_to_check[key], key_type_pairs[key]):
            raise TypeError(f'Key type incorrect: "{dictionary_to_check[key]}" should be type "{key_type_pairs[key]}"')
    return True

def extractNestedStrings(iterable):
    log.debug('Extracting nested strings')
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
    return extract(iterable)

def readYAML(path):
    log.debug(f'Reading YAML file "{path}"')
    try:
        with open(path, 'r') as f: read = yaml.safe_load(f)
        return read
    except Exception as e:
        raise e

def loadInstances(instances_dir: str = instances_dir):
    log.info(f'LOADING INSTANCES')
    if not os.path.exists(instances_dir):
        os.makedirs(instances_dir)
    
    enabled_instances = {}
    key_type_pairs = {
        'Enabled': bool,
        'Loader': str,
        'Version': (str, int, float),
        'Directory': (str, type(None)),
        'Mods': (list, dict)
    }
    for instance_file in [f for f in os.listdir(instances_dir) if f.endswith('.yaml')]:
        instance_path = os.path.join(instances_dir, instance_file)
        instance = readYAML(instance_path)
        validateKeyTypes(instance, key_type_pairs)
        if not instance['Enabled']:
            log.info(f'Ignoring disabled instance "{instance_file}"')
            continue
        log.info(f'Loading enabled instance "{instance_file}"')
        instance.pop('Enabled')
        instance['Loader'] = str(instance['Loader']).lower()
        instance['Version'] = str(instance['Version'])
        instance['Directory'] = str(instance['Directory'])
        instance_name = os.path.splitext(os.path.basename(instance_path))[0]
        enabled_instances[instance_name] = instance
    return enabled_instances

def parseInstances(instances):
    log.debug('Parsing enabled instances')
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
                    continue # If it's not a mod or datapack it's not supported.
                mod_id = url_path_split[1]
                if len(url_path_split) == 4:
                    if url_path_split[2] == 'version':
                        mod_version = url_path_split[3]
            
            elif url_authority == 'curseforge.com':
                url_path = urlparse(mod_url).path
                url_path_split = url_path.split('/')[1:]
                if url_path_split[0] != 'minecraft':
                    log.warning(f'Url "{mod_url}" is not for minecraft!')
                    continue
                if url_path_split[1] not in ('mc-mods'):
                    log.warning(f'Url "{mod_url}" is not for a minecraft mod!')
                    continue
                mod_id = url_path_split[2]
                if len(url_path_split) == 5 and url_path_split[3] == 'files':
                    mod_version = url_path_split[4]
            
            else: # Unsupported website
                log.warning(f'Mod manager cannot parse URLs from "{url_authority}". {mod_url}')
                continue
            
            parsed_instances.setdefault(mod_loader, {}).setdefault('mods', {}).setdefault(minecraft_version, {}).setdefault(mod_id, {}).setdefault(url_authority, {}).setdefault(mod_version, {}).setdefault('directories', [])
            if instance_dir not in parsed_instances[mod_loader]['mods'][minecraft_version][mod_id][url_authority][mod_version]['directories']:
                parsed_instances[mod_loader]['mods'][minecraft_version][mod_id][url_authority][mod_version]['directories'].append(instance_dir)
    
    return parsed_instances

def zipIsCorrupted(path):
    if os.path.exists(path):
        log.debug(f'Verifying integrity of "{path}".')
        with ZipFile(path) as zip_file:
            if zip_file.testzip() is not None:
                log.debug(f'Could not verify integrity of "{path}". Probably corrupted.')
                return True
            else:
                return False
    else:
        return None

def downloadModrinthMod(mod_id, mod_loader, minecraft_version, mod_version, download_dir, instance_dirs):
    log.info(f'Updating {mod_id} for {mod_loader} {minecraft_version}')
    
    log.debug(f'Getting files from Modrinth')
    base_url = (f'https://api.modrinth.com/v2/project/{mod_id}/version')
    if mod_version == 'latest_version':
        params = {'loaders': [mod_loader], 'game_versions': [minecraft_version]}
    else:
        params = {'loaders': [mod_loader]}
    url = f'{base_url}?{"&".join([f"{key}={json.dumps(value)}" for key, value in params.items()])}'
    try:
        response = requests.get(url, headers = modrinth_header).json()
    except Exception as e:
        log.warning(f'Could not update "{mod_id}": {e}')
        return
    response = sorted(response, key=lambda x: datetime.fromisoformat(x['date_published'][:-1]), reverse = True)
    if mod_version == 'latest_version':
        if len(response) > 0:
            desired_mod_version = response[0]
        else:
            log.warning(f'Could not find "{mod_id}" for {mod_loader} {minecraft_version}. https://modrinth.com/mod/{mod_id}')
            return
    else:
        if len(response) > 0:
            desired_mod_version = [version for version in response if version['version_number'] == mod_version][0]
        else:
            log.warning(f'Could not find "{mod_id} {mod_version}" for {mod_loader} {minecraft_version}')
            return
    desired_mod_version_files = desired_mod_version['files']
    if any('primary' == True in file for file in desired_mod_version_files):
        desired_mod_version_files = [file for file in desired_mod_version_files if file['primary'] == True]
    desired_mod_version_file = desired_mod_version_files[0]
    
    log.debug(f'Downloading desired version from Modrinth')
    download_url = desired_mod_version_file['url']
    file_name = desired_mod_version_file['filename']
    download_path = os.path.join(download_dir, mod_loader, minecraft_version)
    downloaded_file_path = os.path.join(download_path, file_name)
    
    if not (os.path.exists(downloaded_file_path) or zipIsCorrupted(downloaded_file_path)):
        try:
            response = requests.get(download_url, headers = modrinth_header)
        except Exception as e:
            log.warning(f'Could not download "{mod_id}": {e}')
            return
        try:
            with open(downloaded_file_path, 'wb') as f: f.write(response.content)
        except Exception as e:
            log.warning(f'Could not save file "{file_name}" to "{download_path}": {e}')
            return
        log.info(f'Downloaded "{file_name}" into "{download_path}"')
    
    log.debug(f'Copying downloaded file into instance(s)')
    for instance_dir in instance_dirs:
        instance_dir = os.path.join(instance_dir, 'mods')
        instance_file_path = os.path.join(instance_dir, file_name)
        if os.path.exists(instance_dir) and os.path.exists(downloaded_file_path):
            if not (os.path.isfile(instance_file_path) or zipIsCorrupted(instance_file_path)):
                try:
                    shutil.copy(downloaded_file_path, instance_file_path)
                    log.info(f'Copied "{downloaded_file_path}" into "{instance_dir}"')
                except Exception as e:
                    log.warning(f'Could not copy "{downloaded_file_path}" into "{instance_dir}": {e}')
                    continue

def downloadCurseforgeMod(mod_id, mod_loader, minecraft_version, mod_version, download_dir, instance_dirs):
    log.info(f'Updating {mod_id} for {mod_loader} {minecraft_version}')
    
    # Getting mod ID
    log.debug(f'Getting mod ID from CurseForge')
    url = ('https://api.curseforge.com/v1/mods/search')
    params = {'gameId': '432','slug': mod_id, 'classId': '6'}
    try:
        response = requests.get(url, params, headers = rmmud_config['Header']).json()['data']
        curseforge_mod_id = response[0]['id']
    except Exception as e:
        log.warning(f'Could not fetch CurseForge ID for "{mod_id}": {e}')
        return
    
    # Get latest or desired mod version
    log.debug(f'Getting files from CurseForge')
    curseforge_mod_loader = { 'forge': 1, 'fabric': 4 }.get(mod_loader, None)
    if mod_version == 'latest_version':
        try:
            url = (f'https://api.curseforge.com/v1/mods/{curseforge_mod_id}/files')
            params = {'gameVersion': str(minecraft_version), 'modLoaderType': curseforge_mod_loader}
            response = requests.get(url, params = params, headers = rmmud_config['Header']).json()['data']
            desired_mod_version_file = list(file for file in response if minecraft_version in file['gameVersions'])[0]
        except Exception as e:
            log.warning(f'Could not find "{mod_id}" for {mod_loader} {minecraft_version}. https://www.curseforge.com/minecraft/mc-mods/{mod_id}')
            return
    else:
        try:
            desired_mod_version_file = requests.get(f'https://api.curseforge.com/v1/mods/{curseforge_mod_id}/files/{mod_version}', params = {'modLoaderType': curseforge_mod_loader}, headers = rmmud_config['Header']).json()['data']
        except Exception as e:
            log.warning(f'Could not find "{mod_id} {mod_version}" for {mod_loader} {minecraft_version}')
    
    log.debug(f'Downloading desired version from CurseForge')
    file_name = desired_mod_version_file['fileName']
    download_url = desired_mod_version_file['downloadUrl']
    if download_url == None:
        log.debug(f'Mod dev has disabled extenal program support for this mod, but I have a workaround ;)')
        download_url = f'https://edge.forgecdn.net/files/{str(desired_mod_version_file["id"])[0:4]}/{str(desired_mod_version_file["id"])[4:7]}/{file_name}'
    download_path = os.path.join(download_dir, mod_loader, minecraft_version)
    downloaded_file_path = os.path.join(download_path, file_name)
    
    if not (os.path.exists(downloaded_file_path) or zipIsCorrupted(downloaded_file_path)):
        try:
            response = requests.get(download_url, headers = rmmud_config['Header'])
            with open(downloaded_file_path, 'wb') as f: f.write(response.content)
        except Exception as e:
            log.warning(f'Could not download "{mod_id}": {e}')
            return
        log.info(f'Downloaded "{file_name}" into "{download_path}"')
    
    log.debug(f'Copying downloaded file into instance(s)')
    for instance_dir in instance_dirs:
        instance_dir = os.path.join(instance_dir, 'mods')
        instance_file_path = os.path.join(instance_dir, file_name)
        if os.path.exists(instance_dir) and os.path.exists(downloaded_file_path):
            if not (os.path.isfile(instance_file_path) or zipIsCorrupted(instance_file_path)):
                try:
                    shutil.copy(downloaded_file_path, instance_file_path)
                    log.info(f'Copied "{downloaded_file_path}" to "{instance_dir}"')
                except Exception as e:
                    log.warning(f'Could not copy "{downloaded_file_path}" into "{instance_dir}": {e}')
                    continue

def loadConfig(file_path: str = config_path):
    global rmmud_config
    with open(file_path, 'r') as f: rmmud_config = yaml.safe_load(f)
    key_type_pairs = {'CurseForge API Key': str, 'Check for RMMUD Updates': bool}
    validateKeyTypes(rmmud_config, key_type_pairs)
    rmmud_config['Header'] = {'Accept': 'application/json','x-api-key': rmmud_config['CurseForge API Key']}
    return rmmud_config

def update_mods(instances):
    log.debug(f'Creating folders to download mods into')
    global downloads_dir
    for mod_loader in instances:
        for minecraft_version in instances[mod_loader]['mods']:
            try:
                dir = os.path.join(downloads_dir, mod_loader, minecraft_version)
                os.makedirs(dir, exist_ok = True)
            except Exception as e:
                log.warning(f'Could not create download folder {dir}: {e}')
                raise e
    
    log.info(f'UPDATING MODS')
    for mod_loader in instances:
        for minecraft_version in instances[mod_loader]['mods']:
            for mod_id in instances[mod_loader]['mods'][minecraft_version]:
                for website in instances[mod_loader]['mods'][minecraft_version][mod_id]:
                    for mod_version in instances[mod_loader]['mods'][minecraft_version][mod_id][website]:
                        instance_dirs = instances[mod_loader]['mods'][minecraft_version][mod_id][website][mod_version]['directories']
                        if website == 'modrinth.com':
                            downloadModrinthMod(mod_id, mod_loader, minecraft_version, mod_version, downloads_dir, instance_dirs)
                        elif website == 'curseforge.com':
                            downloadCurseforgeMod(mod_id, mod_loader, minecraft_version, mod_version, downloads_dir, instance_dirs)

def deleteDuplicateMods(instances):
    def scanFolder(instance_dir):
        log.debug(f'Scanning for old mods')
        instance_dir = os.path.join(instance_dir, 'mods')
        ids = {}
        for mod_file in [f for f in os.listdir(instance_dir) if f.endswith('.jar')]:
            mod_path = os.path.join(instance_dir, mod_file)
            date_created = os.path.getctime(mod_path)
            with ZipFile(mod_path) as zip:
                with zip.open('fabric.mod.json') as f:
                    id = json.load(f, strict=False)['id']
                    ids.setdefault(id, {})
            ids[id][date_created] = mod_path
        with open('TEMP.json', 'w') as f: json.dump(ids, f, indent="\t")
        
        for key in list(ids.keys()):
            if len(ids[key]) == 1:
                del ids[key]
        
        if len(ids) > 0:
            log.debug(f'Deleting old mods')
            for mod_id, dates in ids.items():
                latest_date = max(dates.keys())
                for date_created, path in dates.items():
                    if date_created != latest_date:
                        try:
                            os.remove(path)
                            log.info(f'Deleted old {mod_id} file: "{path}"')
                        except Exception as e:
                            log.warning(f'Could not delete old {mod_id} file "{path}": {e}')
        else:
            log.debug(f'No old mods to delete')
            
    
    log.info(f'DELETING OUTDATED MODS')
    for instance_name, instance in instances.items():
        log.info(f'Deleting old mods from instance: {instance_name}')
        if instance['Loader'] == 'fabric':
            instance_dir = instance['Directory']
            scanFolder(instance['Directory'])
        else:
            log.warning(f'Cannot auto-delete old mods in {instance_dir}: Only fabric mods supported atm.')
    pass

def main():
    #Load config
    loadConfig()
    
    instances = loadInstances()
    #with open('TEMP.json', 'w') as f: json.dump(instances, f, indent="\t")
    
    parsed_instances = parseInstances(instances)
    
    update_mods(parsed_instances)
    
    deleteDuplicateMods(instances)
    
    log.info('Done.')

if __name__ == '__main__':
    #Clear latest.log if it exists
    if os.path.exists('latest.log'):
        open('latest.log', 'w').close()
    #Set up logging
    logging.basicConfig(
        level = logging_level,
        format = '%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
        datefmt = '%Y/%m/%d %H:%M:%S',
        encoding = 'utf-8',
        handlers = [
            logging.FileHandler('latest.log', encoding = 'utf-8'),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    log.debug('Logging initialized.')
    
    #Call main function
    main()