import datetime
import logging
import requests

VERSION = "0.0.0"

class github:
    def checkForUpdate(update_chcking: bool):
        #📝 Double check that this is still working correctly. If not, rewrite :P
            logging.info('CHECKING FOR RMMUD UPDATE:')
            if update_chcking:
                try:
                    latest_release = requests.get('https://api.github.com/repos/RandomGgames/RMMUD/releases/latest').json()
                    latest_version = str(latest_release['tag_name'])
                except Exception as e:
                    if latest_release['message'][:23] == 'API rate limit exceeded':
                        reset_time = round((requests.get('https://api.github.com/rate_limit').json()['resources']['core']['reset'] - datetime.now().timestamp()) / 60, 1)
                        logging.info(f'	[WARN] Could not retreive latest GitHub release version due to exceeding API limit. It wil reset in {reset_time} minutes.')
                    else:
                        logging.info(f'	[WARN] Could not retreive latest GitHub release version. {repr(e)}')
                    return
                if VERSION == latest_version:
                    logging.info(f'	You have the latest release!')
                elif len(VERSION) > 3 and VERSION[:3] <= latest_version:
                    logging.info(f'	Your updater is out of date ({VERSION} vs {latest_version}). Updating now!')
                    github.downloadLatestRelease(latest_release)
                elif len(VERSION) > 3 and not VERSION[:3] <= latest_version:
                    logging.info(f'	Working on a new release ay? Good luck!')
                elif VERSION < latest_version:
                    logging.info(f'	Your updater is out of date ({VERSION} vs {latest_version}). Updating now!')
                    github.downloadLatestRelease(latest_release)
                elif VERSION > latest_version:
                    logging.info(f'	Your updater is... wait... says here that I am more up to date than the latest release? How did you manage to do that...? HOW??')
                return
            else:
                logging.info(f'	Checking for updates is disabled.')
                return

    def downloadLatestRelease(github_data: dict):
        #📝 Get this working
            rmmud_data = [asset for asset in github_data['assets'] if asset['name'] == 'RMMUD.py']
            if len(rmmud_data) > 0:
                download_url = rmmud_data['browser_download_url']
                file_name = rmmud_data['name']
                logging.info(f'	Downloading RMMUD.py...')
                try:
                    open(file_name, 'wb').write(requests.get(download_url).content).close()
                    logging.info(f'	Downloaded {file_name} V{github_data["tag_name"]}')
                    logging.info(f'Download has completed. Please re-open the updater!')
                    input('Press any key to close.')
                    exit()
                except Exception as e:
                    logging.info(f'	[WARN] Error downloading RMMUD.py. {repr(e)}')
            else:
                logging.info(f'	[WARN] Error retreiving RMMUD.py asset from GitHub. Canceling auto-update.')
                return