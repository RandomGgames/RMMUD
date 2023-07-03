# Dev Branch
This branch is under active development!! Nothing here is confirmed to be coming to the official realease or working correctly and may only be for testing purposes. Suggestions and feedback are welcome! If you wish to help contribute to RMMUD, this would be the branch to do it in! Do not use this branch otherwise!! You have been warned. I will not be held responsible for any issues that occur.

# RMMUD
RMMUD is short for "RandomGgames' Minecraft Mod Updater and Downloader". This is a python script which automatically downloads latest versions of mods and copies them into instance folders/server folders with just one click (after configuration that is)! I specifically made this because I have many minecraft instances spanning different versions as well as having a few server folders. I've made this script so I can update the mods in all of them all at once!

# Requirements
- Python 3. https://www.python.org/downloads/
- Requests library. `pip install requests` (Can be installed via the provided InstallRequiredLibs.bat file)
- YAML library. `pip install pyyaml` (Can be installed via the provided InstallRequiredLibs.bat file)
- Your own CurseForge API key if using Curseforge links. https://console.curseforge.com/?#/api-keys
  - Log in
  - Close the popup menu in the middle of the screen if it pops up
  - Click the API keys icon on the left side
  - Copy key from here

# How to use
- Extract files to a folder (not extract here)
- Configure the instances inside the RMMUDInstanced folder
- Open the "RMMUDConfig.yaml" file and add a CurseForge API if using CurseForge links anywhere
- Run "RMMUD.py"

# Features:
- [x] Fabric Modrinth mods support
- [x] Auto-delete outdated fabric mods
- [x] Fabric Curseforge mods support
- [x] Auto-delete outdated forge mods(?)
- [x] Forge Curseforge mods support(?)
- [X] Forge Modrinth mods support(?)

### Possible future features
- [ ] Auto-download mod dependencies
- [ ] Modrinth Resource pack support
- [ ] Modrinth Shader pack support
- [ ] CurseForge Resource pack support
- [ ] Curseforge Shaderpack Support
