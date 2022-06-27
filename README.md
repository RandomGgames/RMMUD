# Minecraft Mod Manager
This is a python script which automatically downloads latest versions of mods and copies them into as many mods folders as you set up with just one click (after configuration that is)! I specifically made this because I have many minecraft instances spanning different versions as well as having a few server folders. I've made this script so I can update the mods in all of them all at once!

# Requirements
- Python 3. https://www.python.org/downloads/
- Requests library. `pip install requests`
- Your own CurseForge API key if using Curseforge links. https://console.curseforge.com/?#/api-keys

# How to use
- Extract files into a folder
- Open the "Manager Config.json" file and configure settings
- Run "Updater.py"

# Features:
- [x] Fabric Curseforge mods support
- [x] Fabric Modrinth mods support
- [x] Forge Curseforge mods support
- [x] Forge Modrinth? mods support
- [ ] Auto-download mod dependencies
- [ ] Auto-delete outdated mods
- [ ] CurseForge Resource pack support
- [ ] Curseforge Shaderpack Support
