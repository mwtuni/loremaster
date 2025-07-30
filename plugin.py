import os
import json
import pyttsx3
import logging
import sys
import threading
import re
from datetime import datetime
from ctypes import byref, windll, wintypes
from queue import Queue
import base64
from PIL import ImageGrab
from io import BytesIO
import ollama

# Suppress excessive debug logs from comtypes and pyttsx3 internals
for noisy_module in ["comtypes", "pyttsx3.drivers", "comtypes.client._events"]:
    logging.getLogger(noisy_module).setLevel(logging.WARNING)

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

# Speech queue for text-to-speech
speech_queue = Queue()

class LLMHandler:
    def __init__(self):
        # Attempt to get the API key from the environment variable
        self.api_key = os.environ.get("OPENAI_API_KEY")

        # If not found, try to load it from config.json
        if not self.api_key:
            try:
                with open("config.json", "r") as config_file:
                    config = json.load(config_file)
                    self.api_key = config.get("OPENAI_API_KEY")
                    if self.api_key:
                        log_event("Loaded OPENAI_API_KEY from config.json.")
            except FileNotFoundError:
                log_event("config.json not found. OPENAI_API_KEY not set.")
            except json.JSONDecodeError:
                log_event("Error decoding config.json. OPENAI_API_KEY not set.")

        self.ollama_model = "llava:13b"
        self.client = None
        self.use_openai = False

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.use_openai = True
                log_event("Using OpenAI for LLM.")
            except ImportError:
                log_event("OpenAI library not available. Falling back to Ollama.")
        else:
            try:
                import ollama
                self.client = ollama
                log_event(f"Using Ollama for LLM with model '{self.ollama_model}'.")
            except ImportError:
                raise ImportError("Neither OpenAI nor Ollama is available. Install the required libraries.")

    def chat(self, messages):
        if self.use_openai:
            # OpenAI chat invocation
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0
            )
            return response.choices[0].message.content
        else:
            # Ollama chat invocation
            response = self.client.chat(model=self.ollama_model, messages=messages)
            if "message" in response and "content" in response["message"]:
                return response["message"]["content"]
            else:
                raise ValueError("Invalid response format from Ollama.")

class Plugin:
    def __init__(self):
        self.llm_handler = LLMHandler()
        self.chat_history = []
        self.conversation_style = None
        self.active_character = None
        self.active_game = None

    def capture_and_encode_screenshot(self):
        """Capture a screenshot, resize it to 512x512, and encode it in Base64."""
        try:
            screenshot = ImageGrab.grab()
            resized_screenshot = screenshot.resize((512, 512))  # Reduce resolution
            buffer = BytesIO()
            resized_screenshot.save(buffer, format="JPEG", quality=50)  # Use JPEG with reduced quality
            buffer.seek(0)
            base64_screenshot = base64.b64encode(buffer.getvalue()).decode("utf-8")
            log_event("Screenshot captured, resized, and encoded successfully.")
            return base64_screenshot
        except Exception as e:
            log_event(f"Error capturing or encoding screenshot: {e}")
            return None

    def parse_message(self, natural_input):
        system_prompt = """
        Your task is to extract structured data from a natural language question to a video game character.

        Always respond ONLY with valid minified JSON like this:
        {"game":"<game>","character":"<character>","sex":"male/female","message":"<message>"}

        Make sure every field is always populated, even if you have to guess or infer the game.

        Example:
        Input: Ask Ciri from Witcher what she thinks about destiny.
        Output: {"game":"The Witcher","character":"Ciri","sex":"female","message":"What do you think about destiny?"}
        """
        user_prompt = f"Input: {natural_input}\nOutput:"

        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ]

        try:
            log_event(f"Prompt to LLM:\nSystem: {system_prompt.strip()}\nUser: {user_prompt.strip()}")
            raw = self.llm_handler.chat(messages)
            log_event(f"Raw LLM response: {repr(raw)}")

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

    def analyze_screen(self, user_query, character_info):
        """Analyze the screen using LLAVA while maintaining character role."""
        # Capture and encode the screenshot
        image_b64 = self.capture_and_encode_screenshot()
        if not image_b64:
            return "Failed to capture or process the screen image."

        # Create a character-aware prompt for LLAVA
        character_prompt = f"""You are {character_info['character']} from {character_info['game']}. 
        Analyze this screenshot and respond as this character would. 
        Stay completely in character while describing what you see on the screen.
        Keep your response natural and in the character's voice.
        
        User asks: {user_query}"""

        # For Ollama, images are passed directly in the messages array
        messages = [
            {
                "role": "user", 
                "content": character_prompt,
                "images": [image_b64]  # Pass the base64 image data directly
            }
        ]

        # Send the request to LLAVA via Ollama
        try:
            response = ollama.chat(model="llava", messages=messages)
            return response["message"]["content"]
        except Exception as e:
            log_event(f"Error in analyze_screen(): {e}")
            return "An error occurred while analyzing the screen."

    def talk(self, params):
        user_input = params.get("input", "")
        log_event(f"Input received: {user_input}")

        # Parse the message first to get character info
        parsed = self.parse_message(user_input)

        # Check if the query asks about the screen
        if "on the screen" in user_input.lower() or "in the image" in user_input.lower():
            log_event("Screen-related query detected. Using LLAVA for analysis.")
            
            # Update context if character changed
            if parsed["character"] != self.active_character or parsed["game"] != self.active_game:
                log_event(f"Context switched from {self.active_character}/{self.active_game} to {parsed['character']}/{parsed['game']}. Resetting history.")
                self.chat_history = []
                self.active_character = parsed["character"]
                self.active_game = parsed["game"]
            
            # Analyze screen while maintaining character role
            screen_response = self.analyze_screen(parsed["message"], parsed)
            
            response = {"success": True, "message": screen_response}
            write_response(response)
            speech_queue.put((screen_response, parsed.get('sex', '').lower() == 'female'))
            return None

        # Continue with normal processing for non-screen queries
        if parsed["message"].lower().startswith("set style "):
            self.conversation_style = parsed["message"][10:].strip()
            log_event(f"Conversation style set to: {self.conversation_style}")
            return {"success": True, "message": f"Style set to '{self.conversation_style}'"}

        if parsed["character"] != self.active_character or parsed["game"] != self.active_game:
            log_event(f"Context switched from {self.active_character}/{self.active_game} to {parsed['character']}/{parsed['game']}. Resetting history.")
            self.chat_history = []
            self.active_character = parsed["character"]
            self.active_game = parsed["game"]

        style_prompt = f" Speak in a {self.conversation_style} style." if self.conversation_style else ""
        system_prompt = f"""
        You are {parsed['character']} from {parsed['game']}.{style_prompt}
        Respond fully in character and keep the tone natural, using knowledge and voice appropriate to the character.
        If the user asks for a specific fact or game-related detail (such as item locations, codes, puzzle solutions, or mechanics), always give the exact, correct answer as clearly as possible.
        If the user is asking for a lore opinion, emotional reflection, or casual dialogue, stay immersive and in character.
        Keep responses concise (2–4 sentences), but prioritize clarity and usefulness when giving game-related answers.
        """

        self.chat_history.append({"role": "user", "content": parsed["message"]})

        messages = [{"role": "system", "content": system_prompt}] + self.chat_history[-10:]

        token_estimate = sum(len(m['content']) for m in messages) // 4
        log_event(f"Estimated context tokens: {token_estimate}")

        if token_estimate > 12000:
            self.chat_history = self.chat_history[len(self.chat_history)//2:]
            messages = [{"role": "system", "content": system_prompt}] + self.chat_history[-10:]
            log_event("Context limit exceeded. Chat history halved.")

        try:
            log_event(f"Sending chat completion with messages: {messages}")
            reply = self.llm_handler.chat(messages)
            self.chat_history.append({"role": "assistant", "content": reply, "style": self.conversation_style})
            log_event(f"Generated reply: {reply}")

            response = {"success": True, "message": reply}
            write_response(response)
            speech_queue.put((reply, parsed.get('sex', '').lower() == 'female'))
            return None
        except Exception as e:
            log_event(f"Error in talk(): {e}")
            return {"success": False, "message": "An error occurred."}

    def initialize(self):
        log_event("Initializing plugin")
        return {"success": True, "message": "LoreMaster plugin initialized successfully"}

    def shutdown(self):
        log_event("Shutting down plugin.")
        sys.exit(0)

def read_command():
    try:
        pipe = windll.kernel32.GetStdHandle(-10)
        chunks = []

        while True:
            message_bytes = wintypes.DWORD()
            buffer = bytes(4096)
            success = windll.kernel32.ReadFile(
                pipe,
                buffer,
                4096,
                byref(message_bytes),
                None
            )

            if not success:
                log_event('Error reading from command pipe')
                return None

            chunk = buffer.decode('utf-8', errors='ignore')[:message_bytes.value]
            chunks.append(chunk)

            if message_bytes.value < 4096:
                break

        raw_data = ''.join(chunks).strip()
        log_event(f'Read raw input: {repr(raw_data)}')

        json_match = re.search(r'{.*}', raw_data, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            log_event(f"Extracted JSON string: {repr(json_str)}")
            return json.loads(json_str)
        else:
            log_event("No valid JSON object found in input.")
            return None
    except Exception as e:
        log_event(f"Exception in read_command(): {e}")
        return None

def write_response(response):
    try:
        pipe = windll.kernel32.GetStdHandle(-11)
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
        log_event(f"Error writing response: {e}")

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

def main():
    plugin = Plugin()
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
                resp = plugin.talk(call["params"])
                if resp:
                    write_response(resp)
            elif call["func"] == "initialize":
                resp = plugin.initialize()
                write_response(resp)
            elif call["func"] == "shutdown":
                plugin.shutdown()

def selftest():
    log_event("Running selftest...")
    try:
        # Example input for testing
        example_input = {"input": "Ask Ciri from Witcher which weapons she is wielding and what her outfit is in the screen. Also describe your pose."}

        # Create an instance of the Plugin class
        plugin = Plugin()

        # Call the `talk` function directly with the example input
        response = plugin.talk(example_input)

        # Log and print the result
        if response:
            log_event(f"Selftest result: {response}")
            print(f"Selftest result: {response}")
        else:
            log_event("Selftest failed: No response generated.")
            print("Selftest failed: No response generated.")
    except Exception as e:
        # Log and print any errors encountered during the selftest
        log_event(f"Error during selftest: {e}")
        print(f"Error during selftest: {e}")

    # Add a delay to allow the speech thread to finish
    log_event("Waiting for speech thread to complete...")
    import time
    time.sleep(50)
    log_event("Selftest completed.")

if __name__ == "__main__":
    if os.getenv("SELFTEST") == "1":
        log_event("SELFTEST environment variable detected.")
        selftest()
        sys.exit(0)
    else:
        main()