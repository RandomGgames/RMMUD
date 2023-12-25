import logging
import os
import shutil
from RMMUD import checkIfZipIsCorrupted
import requests
logger = logging.getLogger(__name__)

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