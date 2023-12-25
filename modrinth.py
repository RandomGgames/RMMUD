import logging
import os
import requests
import shutil
import sys
import os
import typing
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from RMMUD import checkIfZipIsCorrupted
logger = logging.getLogger(__name__)

logging.basicConfig(
        level = logging.INFO,
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

ModLoaders = typing.Literal['fabric', 'forge']

class Modrinth:
    url_header = {'User-Agent': 'RandomGgames/RMMUD (randomggamesofficial@gmail.com)'}
    _instances = {}
    
    def _validate_url(url):
        if url.netloc != 'modrinth.com':
            raise ValueError('URL link does not go to modrinth.com')
    
    class Mod:
        def __new__(cls, url: typing.Union[str, urlparse], game_version: str, mod_loader: ModLoaders):
            url = urlparse(url)
            isntance_key = (url.geturl(), game_version, mod_loader)
            existing_instance = Modrinth._instances.get(isntance_key)
            
            if existing_instance:
                return existing_instance
            else:
                new_instance = super().__new__(cls)
                new_instance._already_exists = False
                Modrinth._instances[isntance_key] = new_instance
                return new_instance
        
        def __init__(self, url: typing.Union[str, urlparse], game_version: str, mod_loader: ModLoaders):
            if self._already_exists: return
            
            self.url = urlparse(url)
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
            if url_path_split[0] != 'mod':
                raise ValueError('Invalid URL. The path should contain a mod.')
        
        def _get_version(self):
            base_url = urlparse(f'https://api.modrinth.com/v2/project/{self.slug}/version')
            if self.mod_version is None:
                query = f'loader=["{self.mod_loader}"]&game_versions=["{self.game_version}"]'
            else:
                query = f'loader=["{self.mod_loader}"]'
            url = urlunparse(base_url._replace(query = query))
            response = requests.get(url, headers = Modrinth.url_header).json()
            if self.mod_version is None:
                desired_mod_version = sorted(response, key = lambda x: datetime.fromisoformat(x['date_published'][:-1]), reverse = True)[0]
            else:
                desired_mod_version = next((v for v in response if v['version_number'] == self.mod_version), None)
            return desired_mod_version
            
        def download(self, instance_dirs: typing.List[Path]):
            if self.mod_file is None:
                mod_version = self._get_version()
                if mod_version is None: raise LookupError('Could not find mod version.')
                
                mod_version_files = mod_version['files']
                if any(file['primary'] == True in file for file in mod_version_files):
                    mod_version_files = [file for file in mod_version_files if file['primary'] == True]
                mod_version_file = mod_version_files[0]
                
                self.file_name = mod_version_file['filename']
                self.download_url = mod_version_file['url']
            
            for instance_dir in instance_dirs:
                copy_dir = os.path.join(instance_dir, 'mods')
                copy_path = os.path.join(copy_dir, self.file_name)
                
                if not os.path.exists(instance_dir):
                    class DirectoryNotFoundError(FileNotFoundError): pass
                    raise DirectoryNotFoundError(f'The directory "{instance_dir}" does not exist.')
                    
                if not os.path.exists(copy_path) or checkIfZipIsCorrupted(copy_path):
                    if self.mod_file is None:
                        self.mod_file = requests.get(self.download_url, headers = Modrinth.url_header).content
                    
                    with open(copy_path, 'wb') as f:
                        f.write(self.mod_file)
                        logger.info(f'Downloaded "{self.file_name}" into "{copy_dir}"')

Modrinth.Mod('https://modrinth.com/mod/fabric-api', '1.20.2', 'fabric').download([Path('./test')])
Modrinth.Mod('https://modrinth.com/mod/fabric-api', '1.20.2', 'fabric').download([Path('./test')])
Modrinth.Mod('https://modrinth.com/mod/fabric-api', '1.20.4', 'fabric').download([Path('./test')])
Modrinth.Mod('https://modrinth.com/mod/fabric-api/version/0.91.0+1.20.1', '1.20.2', 'fabric').download([Path('./test')])
exit()