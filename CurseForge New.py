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
from RMMUD import checkIfZipIsCorrupted
from RMMUD import config
from send2trash import send2trash
from urllib.parse import urlparse, urlunparse
logger = logging.getLogger(__name__)

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

config = Configuration(False, 'RMMUDDownloads', 'RMMUDInstances', '$2a$10$VEg5CYH3/pRVCjImNGJH6OOzDWGo9aAGfZOnqbkq5J1eoBbRtefaW')

class CurseForge:
    _instances = {}
    
    class Mod:
        def __new__(cls, url: urlparse, game_version: str, mod_loader: str):
            isntance_key = (url.geturl(), game_version, mod_loader)
            existing_instance = CurseForge._instances.get(isntance_key)
            
            if existing_instance:
                return existing_instance
            else:
                new_instance = super().__new__(cls)
                new_instance._already_exists = False
                CurseForge._instances[isntance_key] = new_instance
                return new_instance
        
        def __init__(self, url: urlparse, game_version: str, mod_loader: str):
            if self._already_exists: return
            
            self.url = url
            self._validate_url(self.url)
            
            url_path_split = self.url.path.split('/')[1:]
            self.slug = url_path_split[2]
            if len(url_path_split) == 5:
                self.mod_version = url_path_split[4]
            else:
                self.mod_version = None
            self.mod_loader = str(mod_loader)
            self.game_version = str(game_version)
            
            self.file_name = None
            self.download_url = None
            self.mod_file = None
            self.mod_id = None
            
            self._mod_key = (self.url.geturl(), game_version, mod_loader)
            self._already_exists = True
        
        def _validate_url(self, url):
            try:
                url_path_split = url.path.split('/')[1:]
            except Exception as e:
                raise ValueError('Invalid URL. The path should contain more path objects.')
            if len(url_path_split) not in (3, 5):
                raise ValueError(f'Invalid URL. The path should contain a slug and optionally a specific version.')
            if url_path_split[0] != 'minecraft':
                raise ValueError(f'Invalid URL. The link should be for Minecraft.')
            if url_path_split[1] != 'mc-mods':
                raise ValueError('Invalid URL. The link should go to a mod.')
        
        def _get_id(self):
            url = 'https://api.curseforge.com/v1/mods/search'
            params = {'gameId': '432','slug': self.slug, 'classId': '6'}
            curseforge_header = {'Accept': 'application/json','x-api-key': config.curseforge_api_key}
            response = requests.get(url, params, headers = curseforge_header).json()['data']
            if len(response) == 0:
                return None
            else:
                self.mod_id = response[0]['id']
        
        def _get_version(self):
            #if mod_version == 'latest_version':
            #    try:
            #        url = (f'https://api.curseforge.com/v1/mods/{curseforge_mod_id}/files')
            #        params = {'gameVersion': str(minecraft_version), 'modLoaderType': curseforge_mod_loader}
            #        response = requests.get(url, params = params, headers = curseforge_header).json()['data']
            #        desired_mod_version_file = list(file for file in response if minecraft_version in file['gameVersions'])[0]
            #    except Exception as e:
            #        logger.warning(f'Could not find "{mod_id}" for {mod_loader} {minecraft_version}. https://www.curseforge.com/minecraft/mc-mods/{mod_id}')
            #        return
            #else:
            #    try:
            #        desired_mod_version_file = requests.get(f'https://api.curseforge.com/v1/mods/{curseforge_mod_id}/files/{mod_version}', params = {'modLoaderType': curseforge_mod_loader}, headers = curseforge_header).json()['data']
            #    except Exception as e:
            #        logger.warning(f'Could not find "{mod_id} {mod_version}" for {mod_loader} {minecraft_version}')
            
            
            curseforge_mod_loader = { 'forge': 1, 'fabric': 4 }.get(self.mod_loader.lower(), None)
            base_url = urlparse(f'https://api.modrinth.com/v2/project/{self.slug}/version')
            if self.mod_version is None:
                query = f'loaders=["{self.mod_loader}"]&game_versions=["{self.game_version}"]'
            else:
                query = f'loaders=["{self.mod_loader}"]'
            print(base_url.geturl())
            print(query)
            url = urlunparse(base_url._replace(query = query))
            print(url)
            response = requests.get(url, headers = CurseForge.url_header).json()
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
            
            if self.mod_id is None:
                self._get_id()
                if self.mod_id is None:
                    logger.warning(f'Could not retrieve mod ID of {self.slug} for {self.mod_loader} {self.game_version}.')
            
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
