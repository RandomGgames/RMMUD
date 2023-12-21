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

class Modrinth:
    def __init__(self, url: str) -> None:
        self.url = urlparse(url)
        self._validate_url()
    
    def _validate_url(self):
        if self.url.netloc != 'modrinth.com':
            raise ValueError('URL link does not go to modrinth.com')
    
    class Mod:
        def __init__(self, game_version: str) -> None:
            self.parent_class = 'Modrinth'
            self.game_version = game_version
            self._validate_url()
        
        def _validate_url(self):
            pass

test = Modrinth('https://modrinth.com/mod/fabric-api').Mod('1.20.2')

exit()

            #try:
            #    url_path_split = self.url.path.split('/')[1:]
            #except Exception as e:
            #    raise ValueError('Invalid URL. The path should contain more path objects.')
            #if url_path_split[0] != 'mod':
            #    raise ValueError('Invalid URL. The path should contain the type and slug|id.')
            #try:
            #    self.slug = url_path_split[1]
            #except Exception as e:
            #    raise ValueError('Invalid URL. The path should contain the slug|id.')
            #if len(url_path_split) >= 4 and url_path_split[2] == 'version':
            #    self.mod_version = url_path_split[3]
        
#        def _get_version(self):
#            base_url = urlparse(f'https://api.modrinth.com/v2/project/{self.slug}/version')
#            if self.mod_version == 'latest':
#                query = f'loader=["{self.mod_loader}"]&game_versions=["{self.game_version}"]'
#            else: # Use specific mod version given in URL
#                query = f'loader=["{self.mod_loader}"]'
#            url = urlunparse(base_url._replace(query = query))
            
#            response = requests.get(url, headers = Modrinth.url_header).json()
            
#            try:
#                if self.mod_version == 'latest':
#                    response = sorted(response, key = lambda x: datetime.fromisoformat(x['date_published'][:-1]), reverse = True)
#                    desired_mod_version = response[0]
#                else:
#                    desired_mod_version = next((v for v in response if v['version_number'] == self.mod_version), None)
#                return desired_mod_version
#            except Exception as e:
#                logger.info(f'    Cannot find {self.mod_version} version of {self.slug}...')
#                raise e
        
#        def download(self, download_dir, copy_to_paths):
#            version = self._get_version()
#            if version is None:
#                raise LookupError('Could not find mod version.')
            
#            desired_mod_version_files = version['files']
#            if any(file['primary'] == True in file for file in desired_mod_version_files):
#                desired_mod_version_files = [file for file in desired_mod_version_files if file['primary'] == True]
#            desired_mod_version_file = desired_mod_version_files[0]
            
#            self.file_name = desired_mod_version_file['filename']
#            self.download_url = desired_mod_version_file['url']
#            self.download_path = os.path.join(download_dir, self.file_name)
            
#            if (not os.path.exists(self.download_path) or checkIfZipIsCorrupted(self.download_path)) and os.path.exists(download_dir):
#                try:
#                    logger.debug(f'    Downloading "{self.slug}" into "{download_dir}"...')
#                    response = requests.get(self.download_url, headers = Modrinth.url_header)
#                    with open(self.download_path, 'wb') as f: f.write(response.content)
#                    logger.info(f'    Downloaded "{self.file_name}" into "{download_dir}"')
                    
#                    for copy_destination in copy_to_paths:
#                        try:
#                            logger.debug(f'    Copying {self.download_path} into {copy_destination}...')
#                            shutil.copy(self.download_path, copy_destination)
#                            logger.info(f'    Copied mod into "{copy_destination}".')
#                        except Exception as e:
#                            logger.debug
                        
#                except Exception as e:
#                    logger.error(f'Could not download mod due to {repr(e)}')
#                    raise e

#test = Modrinth('https://modrinth.com/mod/fabric-api').Mod('1.20.2')
#pass
