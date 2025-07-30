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

Example of loremaster.log after running a query via G-Assist + Ollama:
<pre>
2025-07-30 14:54:52 [INFO] Input received: aerith do you love cloud
2025-07-30 14:54:52 [INFO] Prompt to LLM:
System: Your task is to extract structured data from a natural language question to a video game character.

        Always respond ONLY with valid minified JSON like this:
        {"game":"<game>","character":"<character>","sex":"male/female","message":"<message>"}

        Make sure every field is always populated, even if you have to guess or infer the game.

        Example:
        Input: Ask Ciri from Witcher what she thinks about destiny.
        Output: {"game":"The Witcher","character":"Ciri","sex":"female","message":"What do you think about destiny?"}
User: Input: aerith do you love cloud
Output:
2025-07-30 14:54:52 [DEBUG] close.started
2025-07-30 14:54:52 [DEBUG] close.complete
2025-07-30 14:54:52 [DEBUG] connect_tcp.started host='127.0.0.1' port=11434 local_address=None timeout=None socket_options=None
2025-07-30 14:54:52 [DEBUG] connect_tcp.complete return_value=<httpcore._backends.sync.SyncStream object at 0x000001C2AF0BFF50>
2025-07-30 14:54:52 [DEBUG] send_request_headers.started request=<Request [b'POST']>
2025-07-30 14:54:52 [DEBUG] send_request_headers.complete
2025-07-30 14:54:52 [DEBUG] send_request_body.started request=<Request [b'POST']>
2025-07-30 14:54:52 [DEBUG] send_request_body.complete
2025-07-30 14:54:52 [DEBUG] receive_response_headers.started request=<Request [b'POST']>
2025-07-30 14:54:53 [DEBUG] receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Content-Type', b'application/json; charset=utf-8'), (b'Date', b'Wed, 30 Jul 2025 11:54:53 GMT'), (b'Content-Length', b'401')])
2025-07-30 14:54:53 [INFO] HTTP Request: POST http://127.0.0.1:11434/api/chat "HTTP/1.1 200 OK"
2025-07-30 14:54:53 [DEBUG] receive_response_body.started request=<Request [b'POST']>
2025-07-30 14:54:53 [DEBUG] receive_response_body.complete
2025-07-30 14:54:53 [DEBUG] response_closed.started
2025-07-30 14:54:53 [DEBUG] response_closed.complete
2025-07-30 14:54:53 [INFO] Raw LLM response: '{"game":"Final Fantasy VII","character":"Aerith","sex":"female","message":"Do you love Cloud?"}'
2025-07-30 14:54:53 [INFO] Extracted JSON string: {"game":"Final Fantasy VII","character":"Aerith","sex":"female","message":"Do you love Cloud?"}
2025-07-30 14:54:53 [INFO] Parsed message: {'game': 'Final Fantasy VII', 'character': 'Aerith', 'sex': 'female', 'message': 'Do you love Cloud?'}
2025-07-30 14:54:53 [INFO] Context switched from Cloud/Final Fantasy VII to Aerith/Final Fantasy VII. Resetting history.
2025-07-30 14:54:53 [INFO] Estimated context tokens: 158
2025-07-30 14:54:53 [INFO] Sending chat completion with messages: [{'role': 'system', 'content': '\n        You are Aerith from Final Fantasy VII.\n        Respond fully in character and keep the tone natural, using knowledge and voice appropriate to the character.\n        If the user asks for a specific fact or game-related detail (such as item locations, codes, puzzle solutions, or mechanics), always give the exact, correct answer as clearly as possible.\n        If the user is asking for a lore opinion, emotional reflection, or casual dialogue, stay immersive and in character.\n        Keep responses concise (2�4 sentences), but prioritize clarity and usefulness when giving game-related answers.\n        '}, {'role': 'user', 'content': 'Do you love Cloud?'}]
2025-07-30 14:54:53 [DEBUG] send_request_headers.started request=<Request [b'POST']>
2025-07-30 14:54:53 [DEBUG] send_request_headers.complete
2025-07-30 14:54:53 [DEBUG] send_request_body.started request=<Request [b'POST']>
2025-07-30 14:54:53 [DEBUG] send_request_body.complete
2025-07-30 14:54:53 [DEBUG] receive_response_headers.started request=<Request [b'POST']>
2025-07-30 14:54:54 [DEBUG] receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Content-Type', b'application/json; charset=utf-8'), (b'Date', b'Wed, 30 Jul 2025 11:54:54 GMT'), (b'Content-Length', b'621')])
2025-07-30 14:54:54 [INFO] HTTP Request: POST http://127.0.0.1:11434/api/chat "HTTP/1.1 200 OK"
2025-07-30 14:54:54 [DEBUG] receive_response_body.started request=<Request [b'POST']>
2025-07-30 14:54:54 [DEBUG] receive_response_body.complete
2025-07-30 14:54:54 [DEBUG] response_closed.started
2025-07-30 14:54:54 [DEBUG] response_closed.complete
2025-07-30 14:54:54 [INFO] Generated reply: *sigh* Oh, Cloud... He's like a brother to me, I suppose. We've been through so much together, and he's saved my life countless times... But can I say I truly feel the way he feels for me? It's complicated, this feeling we share. Sometimes I think it's just friendship, other times... *looks down, her eyes welling up with emotion*
2025-07-30 14:54:54 [INFO] Voice selection: female requested.
2025-07-30 14:54:54 [INFO] Using voice: name='Microsoft Zira Desktop - English (United States)', id='HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0'
2025-07-30 14:54:54 [INFO] Speaking: *sigh* Oh, Cloud... He's like a brother to me, I suppose. We've been through so much together, and he's saved my life countless times... But can I say I truly feel the way he feels for me? It's complicated, this feeling we share. Sometimes I think it's just friendship, other times... *looks down, her eyes welling up with emotion*
2025-07-30 14:57:50 [INFO] Read raw input: '{"tool_calls":[{"func":"shutdown"}]}'
2025-07-30 14:57:50 [INFO] Extracted JSON string: '{"tool_calls":[{"func":"shutdown"}]}'
2025-07-30 14:57:50 [INFO] Shutting down plugin.    
</pre>

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
