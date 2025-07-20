# LoreMaster Plugin for NVIDIA G-Assist

**Talk to your favorite game characters using natural language.**
LoreMaster brings game characters to life using voice synthesis and GPT-4o integration. Ask lore questions, request puzzle solutions, or just challenge Cloud about his oversized sword.

Built in under 24 hours for the [NVIDIA Project G-Assist Hackathon](https://developer.nvidia.com/g-assist-hackathon)
Tag: `#AIonRTXHackathon` • Twitter: [@NVIDIAGeForce](https://twitter.com/NVIDIAGeForce)

---

## Features

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

To make the plugin available to G-Assist:

**Copy `dist\loremaster` to:**

```
%PROGRAMDATA%\NVIDIA Corporation\nvtopps\rise\plugins\
```

> This step requires administrator privileges.

#### Instructions

1. Open Command Prompt as Administrator
2. Run:

```cmd
xcopy dist\loremaster "%PROGRAMDATA%\NVIDIA Corporation\nvtopps\rise\plugins\" /E /Y
```

Or copy the files manually using File Explorer (you’ll be prompted for admin access).

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

Built by Mika Wilén
Repo: [https://github.com/mwtuni/loremaster](https://github.com/mwtuni/loremaster)

---

## License

This project is licensed under the MIT License. See `LICENSE` file for details.
