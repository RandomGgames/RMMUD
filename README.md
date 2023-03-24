# RMMUD
RMMUD is short for "RandomGgames' Minecraft Mod Updater and Downloader". This is a python script which automatically downloads latest versions of mods and copies them into as many mods folders as you set up with just one click (after configuration that is)! I specifically made this because I have many minecraft instances spanning different versions as well as having a few server folders. I've made this script so I can update the mods in all of them all at once!

# Requirements
- Python 3. https://www.python.org/downloads/
- Requests library. `pip install requests`
- YAML library. `pip install pyyaml`
- Your own CurseForge API key if using Curseforge links. https://console.curseforge.com/?#/api-keys

# How to use
- Extract files into a folder
- Open the "RMMUDConfig.yaml" file and add a CurseForge API
- Configure the instances
- Run "RMMUD.py"

# Features:
- [x] Fabric Curseforge mods support
- [x] Fabric Modrinth mods support
- [x] Auto-delete outdated fabric mods
- [ ] Auto-delete outdated forge mods
- [x] Forge Curseforge mods support(?)
- [X] Forge Modrinth mods support(?)

### Possible future features
- [ ] Auto-download mod dependencies
- [ ] CurseForge Resource pack support
- [ ] Curseforge Shaderpack Support
