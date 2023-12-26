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
from urllib.parse import urlparse, ParseResult, urlencode, urljoin
from send2trash import send2trash
logger = logging.getLogger(__name__)

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

class Modrinth:
    url_header = {'User-Agent': 'RandomGgames/RMMUD (randomggamesofficial@gmail.com)'}
    _instances = {}
    
    def __new__(cls, **kwargs):
        isntance_key = tuple(kwargs.values())
        existing_instance = Modrinth._instances.get(isntance_key)
        
        if existing_instance:
            return existing_instance
        else:
            new_instance = super().__new__(cls)
            Modrinth._instances[isntance_key] = new_instance
            return new_instance
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
            match key:
                case 'url':
                    url_path_split = self.url.path.split('/')[1:]
                    self.project_type = url_path_split[0]
                    self.slug = url_path_split[1]
    
    def _get_project(self):
        base_url = 'https://api.modrinth.com/v2/project'
        url = f'{base_url}/{self.slug}'
        response = requests.get(url, headers = Modrinth.url_header).json()
        if response:
            self.project = response
            return self.project
    
    def _get_projects(self):
        base_url = 'https://api.modrinth.com/v2/projects'
        formatted_ids = ', '.join(f'"{id}"' for id in self.slugs)
        search_param = f'?ids=[{formatted_ids}]'
        url = f'{base_url}{search_param}'
        response = requests.get(url, headers = Modrinth.url_header).json()
        if response:
            self.projects = response
            return self.projects
    
    def _list_versions(self):
        url = f'https://api.modrinth.com/v2/project/{self.slug}/version'
        response = requests.get(url, headers = Modrinth.url_header).json()
        if response:
            self.versions_list = response
            return self.versions_list
    
    def _get_versions(self):
        url = f'https://api.modrinth.com/v2/project/{self.slug}/version'
        if hasattr(self, 'loader') and hasattr(self, 'game_version'):
            url = f'{url}?loaders=["{self.loader}"]&game_versions=["{self.game_version}"]'
        elif hasattr(self, 'loader'):
            url = f'{url}?loaders=["{self.loader}"]'
        elif hasattr(self, 'game_version'):
            url = f'{url}?game_versions=["{self.game_version}"]'
        response = requests.get(url, headers = Modrinth.url_header).json()
        if response:
            self.versions_list = response
            return self.versions_list
        
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
    
    def download(self) -> None:
        if not hasattr(self, 'mod_file'):
            if not hasattr(self, 'versions_list'):
                self._get_versions()
                mod_version_files = self.versions_list['files']
                if any(file['primary'] == True in file for file in mod_version_files):
                    mod_version_files = [file for file in mod_version_files if file['primary'] == True]
                mod_version_file = mod_version_files[0]
                
                self.file_name = mod_version_file['filename']
                self.download_url = mod_version_file['url']
                self.mod_file = requests.get(self.download_url, headers = Modrinth.url_header).content

Modrinth(url = urlparse('https://modrinth.com/mod/fabric-api'), game_version = '1.20.2', loader = 'fabric').download(Path('./test'))
pass

    #def get_project(self, slug: str) -> dict:
    #    base_url = urlparse(f'https://api.modrinth.com/v2/project/{self.slug}')
    #    if self.mod_version is None:
    #        query = f'loaders=["{self.mod_loader}"]&game_versions=["{self.game_version}"]'
    #    else:
    #        query = f'loaders=["{self.mod_loader}"]'
    #    print(base_url.geturl())
    #    print(query)
    #    url = urlunparse(base_url._replace(query = query))
    #    print(url)
    #    response = requests.get(url, headers = Modrinth.url_header).json()
    
    #class Mod:
    #    def __new__(cls, url: urlparse, game_version: str, mod_loader: str):
    #        isntance_key = (url.geturl(), game_version, mod_loader)
    #        existing_instance = Modrinth._instances.get(isntance_key)
            
    #        if existing_instance:
    #            return existing_instance
    #        else:
    #            new_instance = super().__new__(cls)
    #            new_instance._already_exists = False
    #            Modrinth._instances[isntance_key] = new_instance
    #            return new_instance
        
    #    def __init__(self, url: urlparse, game_version: str, mod_loader: str):
    #        if self._already_exists: return
            
    #        self.url = url
    #        Modrinth._validate_url(self.url)
    #        self._validate_url(self.url)
            
    #        url_path_split = self.url.path.split('/')[1:]
    #        self.slug = url_path_split[1]
    #        if len(url_path_split) == 4:
    #            self.mod_version = url_path_split[3]
    #        else:
    #            self.mod_version = None
    #        self.mod_loader = str(mod_loader)
    #        self.game_version = str(game_version)
            
    #        self.file_name = None
    #        self.download_url = None
    #        self.mod_file = None
            
    #        self._mod_key = (self.url.geturl(), game_version, mod_loader)
    #        self._already_exists = True
            
    #    def _validate_url(self, url):
    #        try:
    #            url_path_split = url.path.split('/')[1:]
    #        except Exception as e:
    #            raise ValueError('Invalid URL. The path should contain more path objects.')
    #        if len(url_path_split) not in (2, 4):
    #            raise ValueError(f'Invalid URL. The path should contain a slug and optionally a specific version.')
    #        if url_path_split[0] not in ('mod', 'plugin', 'datapack'):
    #            raise ValueError('Invalid URL. The link should go to a mod.')
        
    #    def _get_version(self):
    #        base_url = urlparse(f'https://api.modrinth.com/v2/project/{self.slug}/version')
    #        if self.mod_version is None:
    #            query = f'loaders=["{self.mod_loader}"]&game_versions=["{self.game_version}"]'
    #        else:
    #            query = f'loaders=["{self.mod_loader}"]'
    #        print(base_url.geturl())
    #        print(query)
    #        url = urlunparse(base_url._replace(query = query))
    #        print(url)
    #        response = requests.get(url, headers = Modrinth.url_header).json()
    #        if self.mod_version is None:
    #            desired_mod_version = sorted(response, key = lambda x: datetime.fromisoformat(x['date_published'][:-1]), reverse = True)
    #            if len(desired_mod_version) == 0:
    #                return None
    #            else:
    #                return desired_mod_version[0]
    #        else:
    #            return next((v for v in response if v['version_number'] == self.mod_version), None)
        
    #    def download(self, instance_dir: Path):
    #        logger.info(f'Updating {self.slug} for {self.game_version} in "{instance_dir}"')
    #        if self.mod_file is None:
    #            mod_version = self._get_version()
    #            if mod_version is None:
    #                logger.warning(f'Could not find compatable version of {self.slug} for {self.mod_loader} {self.game_version}.')
    #                return None
                
    #            mod_version_files = mod_version['files']
    #            if any(file['primary'] == True in file for file in mod_version_files):
    #                mod_version_files = [file for file in mod_version_files if file['primary'] == True]
    #            mod_version_file = mod_version_files[0]
                
    #            self.file_name = mod_version_file['filename']
    #            self.download_url = mod_version_file['url']
    #            self.mod_file = requests.get(self.download_url, headers = Modrinth.url_header).content
            
            
    #        copy_dir = os.path.join(instance_dir, 'mods')
    #        copy_path = os.path.join(copy_dir, self.file_name)
            
    #        if not os.path.exists(instance_dir):
    #            class DirectoryNotFoundError(FileNotFoundError): pass
    #            raise DirectoryNotFoundError(f'The minecraft directory "{instance_dir}" cannot be found.')
            
    #        if os.path.exists(copy_path) and checkIfZipIsCorrupted(copy_path):
    #            logger.info(f'    You already have "{copy_path}" downloaded but it\'s corrupted. Deleting...')
    #            os.remove(copy_path)
    #            logger.info(f'    Deleted "{copy_path}".')
            
    #        if not os.path.exists(copy_path):
    #            with open(copy_path, 'wb') as f:
    #                f.write(self.mod_file)
    #                logger.info(f'    Downloaded "{self.file_name}" into "{copy_dir}".')