# LoreMaster Plugin for NVIDIA G-Assist

**Talk to your favorite game characters using natural language.**
LoreMaster brings game characters to life using voice synthesis and GPT-4o integration. Ask lore questions, request puzzle solutions, or just challenge Cloud about his oversized sword.

Built in under 24 hours for the [NVIDIA Project G-Assist Hackathon](https://developer.nvidia.com/g-assist-hackathon)
Tag: `#AIonRTXHackathon` • Twitter: [@NVIDIAGeForce](https://twitter.com/NVIDIAGeForce)

![Cloud holding a sword](resources/cloud_holding_a_sword.png)

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
/loremaster cloud of ff7, what about the sword?! compensating much?
/loremaster vincent of ff7, tell me the correct notes to unlock your ultimate weapon
/loremaster aerith, what do you really think about the sword?
/loremaster set style sarcastic
/loremaster cloud, do you even know how to use that thing?
```

---

## Demo Video

https://youtu.be/gzQvNmVxp_8

---

## Dev branch features:

Development continues in the dev branch with new features that go beyond the original 1-day hackathon build.

Latest update:

* Support for Ollama as a fallback when OPENAI_API_KEY is not set.
This allows users to run LoreMaster privately and offline (requires Ollama installed and running).
This enhancement enables private, local communication with characters, improving accessibility and reducing reliance on external APIs.

---

## Developer Notes 

The plugin generates a loremaster.log file in the plugin directory. This log captures all protocol messages and can be useful for debugging and understanding G-Assist communication.

Developers can set the environment variable SELFTEST=1 and run the plugin directly with Python (plugin.py) to test functionality without G-Assist.

This is especially helpful for rapid prototyping and testing alternative models or configurations during development.

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
