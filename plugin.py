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

# Configure logging
logging.basicConfig(
    filename="loremaster.log",
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Suppress excessive debug logs
for noisy_module in ["comtypes", "pyttsx3.drivers", "comtypes.client._events"]:
    logging.getLogger(noisy_module).setLevel(logging.WARNING)

def log_event(message):
    logging.info(message)
    print(f"[LOG] {message}")

class ConfigManager:
    def __init__(self):
        self.api_key = self._load_openai_key()
        self.ollama_model = "llama3.2"
        self.openai_model = "gpt-4o"
    
    def _load_openai_key(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            try:
                with open("config.json", "r") as config_file:
                    config = json.load(config_file)
                    api_key = config.get("OPENAI_API_KEY")
                    if api_key:
                        log_event("Loaded OPENAI_API_KEY from config.json.")
            except (FileNotFoundError, json.JSONDecodeError):
                log_event("Config file not found or invalid.")
        return api_key

class LLMHandler:
    def __init__(self, config_manager):
        self.config = config_manager
        self.client = None
        self.use_openai = False
        self._initialize_client()
    
    def _initialize_client(self):
        api_key = self.config.api_key
        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                self.use_openai = True
                log_event("Using OpenAI for LLM.")
            except ImportError:
                log_event("OpenAI library not available. Falling back to Ollama.")
                self._initialize_ollama()
        else:
            self._initialize_ollama()
    
    def _initialize_ollama(self):
        try:
            import ollama
            self.client = ollama
            log_event(f"Using Ollama for LLM with model '{self.config.ollama_model}'.")
        except ImportError:
            raise ImportError("Neither OpenAI nor Ollama is available.")
    
    def chat(self, messages):
        if self.use_openai:
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
                temperature=0
            )
            return response.choices[0].message.content
        else:
            response = self.client.chat(model=self.config.ollama_model, messages=messages)
            if "message" in response and "content" in response["message"]:
                return response["message"]["content"]
            else:
                raise ValueError("Invalid response format from Ollama.")

class MessageParser:
    def __init__(self, llm_handler):
        self.llm_handler = llm_handler
        self.system_prompt = """
        Your task is to extract structured data from a natural language question to a video game character.

        Always respond ONLY with valid minified JSON like this:
        {"game":"<game>","character":"<character>","sex":"male/female","message":"<message>"}

        Make sure every field is always populated, even if you have to guess or infer the game.

        Example:
        Input: ciri from witcher, what do you think about destiny
        Output: {"game":"The Witcher","character":"Ciri","sex":"female","message":"What do you think about destiny?"}
        """
    
    def parse(self, natural_input):
        user_prompt = f"Input: {natural_input}\nOutput:"
        messages = [
            {"role": "system", "content": self.system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ]
        
        try:
            log_event(f"Parsing input: {natural_input}")
            raw = self.llm_handler.chat(messages)
            log_event(f"Raw parsing response: {repr(raw)}")
            
            match = re.search(r'{.*}', raw, re.DOTALL)
            if not match:
                raise ValueError("No JSON object found in response.")
            
            json_str = match.group(0)
            parsed = json.loads(json_str)
            log_event(f"Parsed result: {parsed}")
            return parsed
        except Exception as e:
            log_event(f"Error in parse(): {e}")
            fallback = {"game": "Unknown", "character": "Unknown", "sex": "male", "message": natural_input}
            return fallback

class CharacterManager:
    def __init__(self):
        self.chat_histories = {}
        self.active_character = None
        self.active_game = None
        self.current_history = []
        self.max_history = 10
        self.max_tokens = 12000
    
    def switch_context(self, character, game):
        context_key = f"{character}:{game}"
        
        if self.active_character != character or self.active_game != game:
            log_event(f"Context switched from {self.active_character}/{self.active_game} to {character}/{game}")
            
            if self.active_character and self.active_game:
                old_key = f"{self.active_character}:{self.active_game}"
                self.chat_histories[old_key] = self.current_history.copy()
            
            self.current_history = self.chat_histories.get(context_key, [])
            self.active_character = character
            self.active_game = game
    
    def add_message(self, role, content):
        self.current_history.append({"role": role, "content": content})
        self._manage_history_size()
    
    def get_context_messages(self, system_prompt):
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.current_history[-self.max_history:])
        return messages
    
    def _manage_history_size(self):
        token_estimate = sum(len(msg['content']) for msg in self.current_history) // 4
        log_event(f"Estimated context tokens: {token_estimate}")
        
        if token_estimate > self.max_tokens:
            self.current_history = self.current_history[len(self.current_history)//2:]
            log_event("Context limit exceeded. Chat history halved.")

class SpeechEngine:
    def __init__(self):
        self.speech_queue = Queue()
        self._start_worker()
    
    def _start_worker(self):
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()
    
    def speak(self, text, is_female=False):
        self.speech_queue.put((text, is_female))
    
    def _speech_worker(self):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        while True:
            text, is_female = self.speech_queue.get()
            try:
                selected_voice = None
                for voice in voices:
                    vname = voice.name.lower()
                    vid = voice.id.lower()
                    
                    if is_female and ("female" in vname or "zira" in vid or "eva" in vid):
                        selected_voice = voice
                        break
                    elif not is_female and ("male" in vname or "david" in vid or "mark" in vid):
                        selected_voice = voice
                        break
                
                if selected_voice:
                    engine.setProperty('voice', selected_voice.id)
                    log_event(f"Using voice: {selected_voice.name}")
                
                log_event(f"Speaking: {text}")
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                log_event(f"Speech error: {e}")
            self.speech_queue.task_done()

class PipeHandler:
    @staticmethod
    def read_command():
        try:
            pipe = windll.kernel32.GetStdHandle(-10)
            chunks = []

            while True:
                message_bytes = wintypes.DWORD()
                buffer = bytes(4096)
                success = windll.kernel32.ReadFile(pipe, buffer, 4096, byref(message_bytes), None)

                if not success:
                    return None

                chunk = buffer.decode('utf-8', errors='ignore')[:message_bytes.value]
                chunks.append(chunk)

                if message_bytes.value < 4096:
                    break

            raw_data = ''.join(chunks).strip()
            log_event(f'Read raw input: {repr(raw_data)}')

            json_match = re.search(r'{.*}', raw_data, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return None
        except Exception as e:
            log_event(f"Exception in read_command(): {e}")
            return None

    @staticmethod
    def write_response(response):
        try:
            pipe = windll.kernel32.GetStdHandle(-11)
            json_message = json.dumps(response) + '<<END>>'
            message_bytes = json_message.encode('utf-8')
            bytes_written = wintypes.DWORD()
            windll.kernel32.WriteFile(pipe, message_bytes, len(message_bytes), byref(bytes_written), None)
        except Exception as e:
            log_event(f"Error writing response: {e}")

class ConversationHandler:
    def __init__(self, llm_handler, character_manager, speech_engine):
        self.llm_handler = llm_handler
        self.character_manager = character_manager
        self.speech_engine = speech_engine
    
    def handle_conversation(self, parsed_input):
        character = parsed_input["character"]
        game = parsed_input["game"]
        message = parsed_input["message"]
        is_female = parsed_input.get("sex", "").lower() == "female"
        
        self.character_manager.switch_context(character, game)
        self.character_manager.add_message("user", message)
        
        system_prompt = f"""
        You are {character} from {game}.
        Respond fully in character and keep the tone natural, using knowledge and voice appropriate to the character.
        If the user asks for a specific fact or game-related detail (such as item locations, codes, puzzle solutions, or mechanics), always give the exact, correct answer as clearly as possible.
        If the user is asking for a lore opinion, emotional reflection, or casual dialogue, stay immersive and in character.
        Keep responses concise (2–4 sentences), but prioritize clarity and usefulness when giving game-related answers.
        """
        
        messages = self.character_manager.get_context_messages(system_prompt)
        
        try:
            log_event(f"Generating response for {character} from {game}")
            reply = self.llm_handler.chat(messages)
            
            self.character_manager.add_message("assistant", reply)
            self.speech_engine.speak(reply, is_female)
            
            log_event(f"Generated reply: {reply}")
            return {"success": True, "message": reply}
        except Exception as e:
            log_event(f"Error in conversation: {e}")
            return {"success": False, "message": "An error occurred."}

class LoreMasterPlugin:
    def __init__(self):
        self.config = ConfigManager()
        self.llm_handler = LLMHandler(self.config)
        self.character_manager = CharacterManager()
        self.speech_engine = SpeechEngine()
        self.message_parser = MessageParser(self.llm_handler)
        self.conversation_handler = ConversationHandler(
            self.llm_handler, self.character_manager, self.speech_engine
        )
    
    def talk(self, params):
        user_input = params.get("input", "")
        log_event(f"Input received: {user_input}")
        
        parsed = self.message_parser.parse(user_input)
        result = self.conversation_handler.handle_conversation(parsed)
        
        return result
    
    def initialize(self):
        log_event("LoreMaster plugin initialized")
        return {"success": True, "message": "LoreMaster plugin initialized successfully"}
    
    def shutdown(self):
        log_event("Shutting down plugin")
        sys.exit(0)

def main():
    plugin = LoreMasterPlugin()
    pipe_handler = PipeHandler()
    log_event("LoreMaster plugin started")
    
    while True:
        cmd = pipe_handler.read_command()
        if not cmd:
            continue
        
        tool_calls = cmd.get("tool_calls", [])
        if not tool_calls:
            continue
        
        for call in tool_calls:
            if call["func"] == "talk":
                resp = plugin.talk(call["params"])
                if resp:
                    pipe_handler.write_response(resp)
            elif call["func"] == "initialize":
                resp = plugin.initialize()
                pipe_handler.write_response(resp)
            elif call["func"] == "shutdown":
                plugin.shutdown()

def selftest():
    log_event("Running selftest...")
    try:
        plugin = LoreMasterPlugin()
        example_input = {"input": "Ask Ciri from Witcher what she thinks about destiny."}
        response = plugin.talk(example_input)
        
        if response:
            log_event(f"Selftest result: {response}")
            print(f"Selftest result: {response}")
        else:
            log_event("Selftest failed: No response generated.")
            print("Selftest failed: No response generated.")
    except Exception as e:
        log_event(f"Error during selftest: {e}")
        print(f"Error during selftest: {e}")

    log_event("Waiting for speech thread to complete...")
    import time
    time.sleep(10)
    log_event("Selftest completed.")

if __name__ == "__main__":
    if os.getenv("SELFTEST") == "1":
        log_event("SELFTEST environment variable detected.")
        selftest()
        sys.exit(0)
    else:
        main()