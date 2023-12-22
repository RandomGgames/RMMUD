import logging
import os
import requests
import shutil
import typing
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse
logger = logging.getLogger(__name__)
from RMMUD import checkIfZipIsCorrupted

ModLoaders = typing.Literal['fabric', 'forge', 'quilt']

class Modrinth:
    url_header = {'User-Agent': 'RandomGgames/RMMUD (randomggamesofficial@gmail.com)'}
    
    def _validate_url(url):
        if url.netloc != 'modrinth.com':
            raise ValueError('URL link does not go to modrinth.com')
    
    class Mod:
        def __init__(self, url: typing.Union[str, urlparse], game_version: str, mod_loader: ModLoaders):
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
            
        def download(self, copy_dirs: typing.List[Path]):
            mod_version = self._get_version()
            if mod_version is None: raise LookupError('Could not find mod version.')
            
            mod_version_files = mod_version['files']
            if any(file['primary'] == True in file for file in mod_version_files):
                mod_version_files = [file for file in mod_version_files if file['primary'] == True]
            mod_version_file = mod_version_files[0]
            
            file_name = mod_version_file['filename']
            download_url = mod_version_file['url']
            mod_file = None
            
            for copy_dir in copy_dirs:
                copy_path = os.path.join(copy_dir, file_name)
                
                if os.path.exists(copy_dir):
                    
                    if not os.path.exists(copy_path) or checkIfZipIsCorrupted(copy_path):
                        
                        if mod_file is None:
                            mod_file = requests.get(download_url, headers = Modrinth.url_header)
                        
                        with open(copy_path, 'wb') as f:
                            f.write(mod_file.content)
                            logger.info(f'Downloaded "{file_name}" into "{copy_path}"')
                        
            
            #self.download_path = os.path.join(self.file_name)
            #
            #if (not os.path.exists(self.download_path) or checkIfZipIsCorrupted(self.download_path)) and os.path.exists(download_dir):
            #    try:
            #        
            #        for copy_destination in copy_to_paths:
            #            try:
            #                logger.debug(f'    Copying {self.download_path} into {copy_destination}...')
            #                shutil.copy(self.download_path, copy_destination)
            #                logger.info(f'    Copied mod into "{copy_destination}".')
            #            except Exception as e:
            #                logger.debug
            #            
            #    except Exception as e:
            #        logger.error(f'Could not download mod due to {repr(e)}')
            #        raise e

test = Modrinth.Mod('https://modrinth.com/mod/fabric-api', '1.20.2', 'fabric')._get_version()
pass
exit()