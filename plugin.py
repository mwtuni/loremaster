import os
import json
import pyttsx3
import logging
import sys
import threading
import re
from datetime import datetime
from ctypes import byref, windll, wintypes
from openai import OpenAI
import logging
from queue import Queue

# Suppress excessive debug logs from comtypes and pyttsx3 internals
for noisy_module in ["comtypes", "pyttsx3.drivers", "comtypes.client._events"]:
    logging.getLogger(noisy_module).setLevel(logging.WARNING)

speech_queue = Queue()
STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
BUFFER_SIZE = 4096

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set.")

client = OpenAI(api_key=api_key)

# Configure logging
logging.basicConfig(
    filename="loremaster.log",
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_event(message):
    logging.info(message)
    print(f"[LOG] {message}")

def read_command():
    try:
        pipe = windll.kernel32.GetStdHandle(STD_INPUT_HANDLE)
        chunks = []

        while True:
            message_bytes = wintypes.DWORD()
            buffer = bytes(BUFFER_SIZE)
            success = windll.kernel32.ReadFile(
                pipe,
                buffer,
                BUFFER_SIZE,
                byref(message_bytes),
                None
            )

            if not success:
                log_event('Error reading from command pipe')
                return None

            chunk = buffer.decode('utf-8', errors='ignore')[:message_bytes.value]
            chunks.append(chunk)

            if message_bytes.value < BUFFER_SIZE:
                break

        raw_data = ''.join(chunks).strip()
        log_event(f'Read raw input: {repr(raw_data)}')

        # Extract the FIRST valid JSON object with regex (robust solution)
        json_match = re.search(r'{.*}', raw_data, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            log_event(f'Extracted JSON string: {repr(json_str)}')
            parsed_json = json.loads(json_str)
            return parsed_json
        else:
            log_event("No valid JSON object found in input (regex extraction failed).")
            return None

    except json.JSONDecodeError as e:
        log_event(f'JSONDecodeError: {e}; raw data was: {repr(raw_data)}')
        return None
    except Exception as e:
        log_event(f'Exception in read_command(): {e}')
        return None

def write_response(response):
    try:
        pipe = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        json_message = json.dumps(response) + '<<END>>'
        message_bytes = json_message.encode('utf-8')

        bytes_written = wintypes.DWORD()
        windll.kernel32.WriteFile(
            pipe,
            message_bytes,
            len(message_bytes),
            byref(bytes_written),
            None
        )
    except Exception as e:
        log_event(f'Error writing response: {e}')

def speech_worker():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    while True:
        text, female = speech_queue.get()
        try:
            selected_voice = None
            for voice in voices:
                vname = voice.name.lower()
                vid = voice.id.lower()
                if female and ("female" in vname or "zira" in vid or "eva" in vid):
                    selected_voice = voice
                    break
                elif not female and ("male" in vname or "david" in vid or "mark" in vid):
                    selected_voice = voice
                    break

            log_event(f"Voice selection: {'female' if female else 'male'} requested.")

            if selected_voice:
                engine.setProperty('voice', selected_voice.id)
                log_event(f"Using voice: name='{selected_voice.name}', id='{selected_voice.id}'")
            else:
                log_event("No matching voice found. Using default.")

            log_event(f"Speaking: {text}")
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            log_event(f"Error in speak(): {e}")
        speech_queue.task_done()

speech_thread = threading.Thread(target=speech_worker, daemon=True)
speech_thread.start()

def speak(text, female=True):
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        selected_voice = None
        for voice in voices:
            vname = voice.name.lower()
            vid = voice.id.lower()
            if female and ("female" in vname or "zira" in vid or "eva" in vid):
                selected_voice = voice
                break
            elif not female and ("male" in vname or "david" in vid or "mark" in vid):
                selected_voice = voice
                break

        log_event(f"Voice selection: {'female' if female else 'male'} requested.")

        if selected_voice:
            engine.setProperty('voice', selected_voice.id)
            log_event(f"Using voice: name='{selected_voice.name}', id='{selected_voice.id}'")
        else:
            log_event("No matching voice found. Using default.")

        log_event(f"Speaking: {text}")
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        log_event(f"Error in speak(): {e}")

def parse_message(natural_input):
    prompt = f"""
    Your task is to extract structured data from a natural language question to a video game character.

    Always respond ONLY with valid minified JSON like this:
    {{"game":"<game>","character":"<character>","sex":"male/female","message":"<message>"}}

    Make sure every field is always populated, even if you have to guess or infer the game.

    Input: {natural_input}
    Output:
    """
    try:
        log_event(f"Prompt to OpenAI:\n{prompt.strip()}")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        raw = response.choices[0].message.content
        log_event(f"Raw OpenAI response: {repr(raw)}")

        match = re.search(r'{.*}', raw, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in response.")

        json_str = match.group(0)
        log_event(f"Extracted JSON string: {json_str}")
        parsed = json.loads(json_str)
        log_event(f"Parsed message: {parsed}")
        return parsed
    except Exception as e:
        log_event(f"Error in parse_message(): {e}")
        fallback = {"game": "Unknown", "character": "Unknown", "sex": "male", "message": natural_input}
        log_event(f"Falling back to: {fallback}")
        return fallback

chat_history = []
conversation_style = None
active_character = None
active_game = None

def talk(params):
    global chat_history, conversation_style, active_character, active_game
    user_input = params.get("input", "")
    log_event(f"Input received: {user_input}")

    parsed = parse_message(user_input)

    if parsed["message"].lower().startswith("set style "):
        conversation_style = parsed["message"][10:].strip()
        log_event(f"Conversation style set to: {conversation_style}")
        return {"success": True, "message": f"Style set to '{conversation_style}'"}

    if parsed["character"] != active_character or parsed["game"] != active_game:
        log_event(f"Context switched from {active_character}/{active_game} to {parsed['character']}/{parsed['game']}. Resetting history.")
        chat_history = []
        active_character = parsed["character"]
        active_game = parsed["game"]

    style_prompt = f" Speak in a {conversation_style} style." if conversation_style else ""
    system_prompt = f"""
You are {parsed['character']} from {parsed['game']}.{style_prompt}
Respond fully in character and keep the tone natural, using knowledge and voice appropriate to the character.
If the user asks for a specific fact or game-related detail (such as item locations, codes, puzzle solutions, or mechanics), always give the exact, correct answer as clearly as possible.
If the user is asking for a lore opinion, emotional reflection, or casual dialogue, stay immersive and in character.
Keep responses concise (2–4 sentences), but prioritize clarity and usefulness when giving game-related answers.
"""

    chat_history.append({"role": "user", "content": parsed["message"]})

    messages = [{"role": "system", "content": system_prompt}] + chat_history[-10:]

    token_estimate = sum(len(m['content']) for m in messages) // 4
    log_event(f"Estimated context tokens: {token_estimate}")

    if token_estimate > 12000:
        chat_history = chat_history[len(chat_history)//2:]
        messages = [{"role": "system", "content": system_prompt}] + chat_history[-10:]
        log_event("Context limit exceeded. Chat history halved.")

    try:
        log_event(f"Sending OpenAI chat completion with messages: {messages}")
        chat_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )
        reply = chat_response.choices[0].message.content.strip()
        chat_history.append({"role": "assistant", "content": reply, "style": conversation_style})
        log_event(f"Generated reply: {reply}")

        response = {"success": True, "message": reply}
        write_response(response)
        speech_queue.put((reply, parsed.get('sex', '').lower() == 'female'))
        return None
    except Exception as e:
        log_event(f"Error in talk(): {e}")
        return {"success": False, "message": "An error occurred."}

def initialize():
    log_event("Initializing plugin")
    return {"success": True, "message": "LoreMaster plugin initialized successfully"}

def main():
    log_event("LoreMaster plugin started.")
    while True:
        cmd = read_command()
        if not cmd:
            continue

        tool_calls = cmd.get("tool_calls", [])
        if not tool_calls:
            log_event("No tool_calls found in input. Skipping.")
            continue

        for call in tool_calls:
            if call["func"] == "talk":
                resp = talk(call["params"])
                if resp:
                    write_response(resp)
            elif call["func"] == "initialize":
                resp = initialize()
                write_response(resp)
            elif call["func"] == "shutdown":
                log_event("Shutting down plugin.")
                sys.exit(0)

def selftest():
    log_event("Running selftest...")
    example_input = {"input": "Ask a warrior character about their quest for justice."}
    response = talk(example_input)
    log_event(f"Selftest result: {response}")

if __name__ == "__main__":
    if os.getenv("SELFTEST") == "1":
        log_event("SELFTEST environment variable detected.")
        selftest()
        sys.exit(0)
    else:
        main()
