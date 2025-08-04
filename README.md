# LoreMaster Plugin for NVIDIA G-Assist

**Talk to your favorite game characters using natural language.**
LoreMaster brings game characters to life using voice synthesis and GPT-4o integration. Ask lore questions, request puzzle solutions, or engage with warrior, mage, and other character archetypes.

Built in under 24 hours for the [NVIDIA Project G-Assist Hackathon](https://developer.nvidia.com/g-assist-hackathon)
Tag: `#AIonRTXHackathon` • Twitter: [@NVIDIAGeForce](https://twitter.com/NVIDIAGeForce)

**Disclaimer**: This plugin is not affiliated with any game companies. Character names and game titles are the property of their respective owners.

---

## Features
* Queries via chat or speech (NVIDIA NeMo STT, ALT+V)
* Voice-enabled character responses using `pyttsx3`
* Accurate responses for in-game details (e.g., puzzle solutions, unlock codes)
* Switch response style (e.g., sarcastic, serious, emotional)
* Maintains character/game context across messages
* LLM-powered character emulation using OpenAI GPT-4o
* Compatible with G-Assist JSON protocol

---

## Installation & Setup

### 1. Set Up Virtual Environment

```batch
setup.bat
```

This script:

* Creates `.venv`
* Activates the environment
* Installs dependencies from `requirements.txt`

> Requires Python 3.10+
> Ensure `OPENAI_API_KEY` is set in your environment

---

### 2. Build the Plugin

```batch
build.bat
```

This will:

* Compile the plugin into an executable using PyInstaller
* Place all necessary files in `dist\loremaster\`

Example output:

```
dist/
└── loremaster/
    ├── g-assist-plugin-loremaster.exe
    ├── manifest.json
    └── config.json
```

---

### 3. Install the Plugin in G-Assist

To make the plugin available to G-Assist you have to place it into plugins folder.

**Open administrator command prompt**
```text
powershell -Command "Start-Process cmd -ArgumentList ('/k cd /d \"' + (Get-Location).Path + '\"') -Verb RunAs"
```

**In administrator command prompt, copy `dist\loremaster` to plugins**
```text
xcopy "dist\loremaster" "%PROGRAMDATA%\NVIDIA Corporation\nvtopps\rise\plugins\loremaster" /E /I /Y
```

Or copy the files manually using File Explorer (you’ll be prompted for admin access). 

Restart G-Assist to enable the plugin.

---

## Example Commands

```text
/loremaster ask a warrior character about their legendary weapon
/loremaster ask a mysterious character about unlocking hidden treasures
/loremaster ask a healer character what they think about combat
/loremaster set style sarcastic
/loremaster ask a knight character if they know proper sword techniques
```

---

## Demo Video

https://youtu.be/gzQvNmVxp_8

---

## Next Steps (after hackathon)
* Local LLM Integration via Ollama: Enable users to leverage powerful, locally-hosted LLMs through Ollama for improved privacy, reduced latency, and offline capabilities.
* Vision-Language Model (VLM) Integration: Introduce advanced visual interaction by integrating a VLM that interacts directly with the game screen, enabling richer, context-aware conversations with game characters based on in-game visuals.

---

## Files Overview

| File               | Purpose                         |
| ------------------ | ------------------------------- |
| `plugin.py`        | Core plugin logic               |
| `manifest.json`    | G-Assist plugin manifest        |
| `config.json`      | Plugin configuration            |
| `requirements.txt` | Python dependencies             |
| `build.bat`        | Builds plugin using PyInstaller |
| `setup.bat`        | Sets up virtual environment     |
| `dist/loremaster/` | Output folder for built plugin  |

---

## Author

Built by Mika Wilén, aka. mwtuni
Repo: [https://github.com/mwtuni/loremaster](https://github.com/mwtuni/loremaster)

---

## License

This project is licensed under the MIT License. See `LICENSE` file for details.

**Legal Disclaimer**: This software is not affiliated with any game companies or publishers. All game titles, character names, and related intellectual property are the property of their respective owners. This plugin is intended for personal, educational, and transformative use only. Users are responsible for ensuring their use complies with applicable copyright and trademark laws.
