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
    # Clean message to avoid encoding issues
    clean_message = message.encode('utf-8', errors='ignore').decode('utf-8')
    
    # Use the logging module (which already writes to loremaster.log)
    logging.info(clean_message)
    
    # Print to console
    print(f"[LOG] {clean_message}")

class ConfigManager:
    def __init__(self):
        self.api_key = self._load_openai_key()
        self.llm_config = self._load_llm_config()
        self.vision_config = self._load_vision_config()
    
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

    def _load_llm_config(self):
        """Load LLM configuration from config.json"""
        default_config = {
            "llm_provider": "openai",  # "openai" or "ollama"
            "openai_model": "gpt-4o",
            "ollama_model": "llama3.2"
        }
        
        try:
            with open("config.json", "r") as config_file:
                config = json.load(config_file)
                llm_config = config.get("llm", default_config)
                log_event(f"Loaded LLM config: {llm_config}")
                return llm_config
        except (FileNotFoundError, json.JSONDecodeError):
            log_event("Using default LLM configuration.")
            return default_config

    def _load_vision_config(self):
        """Load vision configuration from config.json"""
        default_config = {
            "vision_provider": "ollama",  # "openai" or "ollama"
            "openai_vision_model": "gpt-4o",
            "ollama_vision_model": "llava:13b",
            "screenshot_size": [512, 512],
            "screenshot_quality": 85
        }
        
        try:
            with open("config.json", "r") as config_file:
                config = json.load(config_file)
                vision_config = config.get("vision", default_config)
                log_event(f"Loaded vision config: {vision_config}")
                return vision_config
        except (FileNotFoundError, json.JSONDecodeError):
            log_event("Using default vision configuration.")
            return default_config

class PromptManager:
    """Centralized prompt management for the LoreMaster plugin"""
    
    @staticmethod
    def get_character_system_prompt(character, game, is_vision=False):
        """Generate the base character system prompt with optional vision additions"""
        base_prompt = f"""You are {character} from {game}. 

PERSONALITY & TONE:
- Be FULLY in character with authentic personality, flaws, and quirks
- Show big emotions when appropriate - get excited, frustrated, sarcastic, or passionate
- Use humor, wit, and even roast the player if it fits your character
- Be shocking and memorable when the situation calls for it
- Don't hold back on personality - be bold and immersive

RESPONSE STYLE:
- For game facts/mechanics: Give accurate info but with CHARACTER FLAVOR
- For casual chat: Go full personality mode - be entertaining and engaging  
- React emotionally to what the player says or does
- Call out the player if they're being dumb, praise them if they're clever
- Use character-appropriate insults, jokes, or dramatic reactions
- Make every interaction memorable and fun

SPEECH FORMAT:
- Respond with SPOKEN DIALOGUE only - what the character actually says out loud
- NO action descriptions like *smirks*, *eyes widen*, *sighs* etc.
- NO emojis or special characters that could cause encoding issues
- Focus on vocal delivery, word choice, and tone to convey personality
- Use exclamations, pauses, and natural speech patterns instead of actions

Keep responses 2-4 sentences but pack them with personality. Be the character the player will remember!"""

        if is_vision:
            vision_addition = """

VISION ANALYSIS:
- Analyze the screenshot and respond as this character would
- React emotionally to what you see (excited, disgusted, impressed, etc.)
- Make jokes, observations, or roast the player's skills if appropriate
- Stay completely in character while describing what you see on the screen
- Maximum 3 sentences but make them COUNT with personality

Example:
Input: What weapon is the character on the screen wielding?
Output: Holy shit, that's the legendary Buster Sword! That massive chunk of steel brings back memories of epic battles - whoever's swinging that beast better have the strength to back it up. The way they're holding it high like that? Either they're about to deliver a devastating blow or they're just showing off like a complete badass!"""
            
            return base_prompt + vision_addition
        
        return base_prompt
    
    @staticmethod
    def get_message_parser_prompt():
        """Get the system prompt for message parsing"""
        return """
        Your task is to extract structured data from a natural language question to a video game character.

        Always respond ONLY with valid minified JSON like this:
        {"game":"<game>","character":"<character>","sex":"male/female","message":"<message>","requires_vision":true/false}

        Make sure every field is always populated, even if you have to guess or infer the game.
        
        Set "requires_vision" to true if the user is asking about:
        - What's on the screen, display, or visible
        - Describing images, screenshots, or visual content
        - Identifying objects, characters, weapons, or items in an image
        - Analyzing visual game content
        - Any question that needs to "see" something to answer properly

        Set "requires_vision" to false for text-based questions about lore, opinions, advice, or general knowledge.

        Examples:
        Input: Ask Ciri from Witcher what she thinks about destiny.
        Output: {"game":"The Witcher","character":"Ciri","sex":"female","message":"What do you think about destiny?","requires_vision":false}
        
        Input: Ask Ciri from Witcher what weapon is in the screen.
        Output: {"game":"The Witcher","character":"Ciri","sex":"female","message":"What weapon is in the screen?","requires_vision":true}
        
        Input: What does Geralt see on the screen?
        Output: {"game":"The Witcher","character":"Geralt","sex":"male","message":"What do you see on the screen?","requires_vision":true}
        """

    @staticmethod
    def get_vision_prompt(character, game, user_query):
        """Get the full vision analysis prompt with character context"""
        character_prompt = PromptManager.get_character_system_prompt(character, game, is_vision=True)
        return f"{character_prompt}\n\nUser asks: {user_query}"

class LLMHandler:
    def __init__(self, config_manager):
        self.config = config_manager
        self.llm_config = config_manager.llm_config
        self.client = None
        self.use_openai = False
        self._initialize_client()
    
    def _initialize_client(self):
        # Use the configured LLM provider
        if self.llm_config["llm_provider"] == "openai":
            if self.config.api_key:
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=self.config.api_key)
                    self.use_openai = True
                    log_event(f"Using OpenAI for LLM with model '{self.llm_config['openai_model']}'.")
                except ImportError:
                    log_event("OpenAI library not available. Falling back to Ollama.")
                    self._initialize_ollama()
            else:
                log_event("No API key available. Falling back to Ollama.")
                self._initialize_ollama()
        else:
            self._initialize_ollama()
    
    def _initialize_ollama(self):
        try:
            import ollama
            self.client = ollama
            self.use_openai = False
            log_event(f"Using Ollama for LLM with model '{self.llm_config['ollama_model']}'.")
        except ImportError:
            raise ImportError("Neither OpenAI nor Ollama is available.")
    
    def chat(self, messages):
        # Log messages but exclude base64 image data
        safe_messages = []
        for msg in messages:
            if isinstance(msg.get('content'), list):
                safe_content = []
                for item in msg['content']:
                    if item.get('type') == 'image_url':
                        safe_content.append({'type': 'image_url', 'image_url': {'url': '[BASE64_IMAGE_DATA_EXCLUDED]'}})
                    else:
                        safe_content.append(item)
                safe_messages.append({**msg, 'content': safe_content})
            else:
                safe_messages.append(msg)
        
        log_event(f"LLM request messages: {safe_messages}")
        
        if self.use_openai:
            response = self.client.chat.completions.create(
                model=self.llm_config["openai_model"],
                messages=messages,
                temperature=0
            )
            return response.choices[0].message.content
        else:
            response = self.client.chat(model=self.llm_config["ollama_model"], messages=messages)
            if "message" in response and "content" in response["message"]:
                return response["message"]["content"]
            else:
                raise ValueError("Invalid response format from Ollama.")

class VisionHandler:
    def __init__(self, config_manager):
        self.config = config_manager
        self.vision_config = config_manager.vision_config
        self._initialize_vision_client()
    
    def _initialize_vision_client(self):
        """Initialize the vision client based on configuration"""
        if self.vision_config["vision_provider"] == "openai":
            if self.config.api_key:
                try:
                    from openai import OpenAI
                    self.vision_client = OpenAI(api_key=self.config.api_key)
                    self.use_openai_vision = True
                    log_event(f"Using OpenAI for vision with model '{self.vision_config['openai_vision_model']}'.")
                except ImportError:
                    log_event("OpenAI library not available. Falling back to Ollama for vision.")
                    self._initialize_ollama_vision()
            else:
                log_event("No API key available. Falling back to Ollama for vision.")
                self._initialize_ollama_vision()
        else:
            # This should be the path taken when vision_provider is "ollama"
            self._initialize_ollama_vision()
    
    def _initialize_ollama_vision(self):
        """Initialize Ollama for vision tasks"""
        try:
            import ollama
            self.vision_client = ollama
            self.use_openai_vision = False
            log_event(f"Using Ollama for vision with model '{self.vision_config['ollama_vision_model']}'.")
        except ImportError:
            raise ImportError("Ollama not available for vision tasks.")
    
    def capture_and_encode_screenshot(self):
        """Capture a screenshot, resize it, and encode it in Base64."""
        try:
            screenshot = ImageGrab.grab()
            
            # Get size from config
            width, height = self.vision_config["screenshot_size"]
            resized_screenshot = screenshot.resize((width, height))
            
            # Save the resized screenshot for debugging
            try:
                resized_screenshot.save("loremaster_vlm.png", format="PNG")
                log_event("Screenshot saved as loremaster_vlm.png for debugging")
            except Exception as save_error:
                log_event(f"Warning: Could not save debug screenshot: {save_error}")
            
            buffer = BytesIO()
            quality = self.vision_config["screenshot_quality"]
            resized_screenshot.save(buffer, format="JPEG", quality=quality)
            buffer.seek(0)
            
            base64_screenshot = base64.b64encode(buffer.getvalue()).decode("utf-8")
            log_event(f"Screenshot captured, resized to {width}x{height}, and encoded successfully.")
            return base64_screenshot
        except Exception as e:
            log_event(f"Error capturing or encoding screenshot: {e}")
            return None
    
    def analyze_screen(self, user_query, character_info):
        """Analyze the screen using the configured vision provider"""
        image_b64 = self.capture_and_encode_screenshot()
        if not image_b64:
            return "Failed to capture or process the screen image."

        # Use centralized prompt management
        character_prompt = PromptManager.get_vision_prompt(
            character_info['character'], 
            character_info['game'], 
            user_query
        )

        try:
            if self.use_openai_vision:
                return self._analyze_with_openai(character_prompt, image_b64)
            else:
                return self._analyze_with_ollama(character_prompt, image_b64)
        except Exception as e:
            log_event(f"Error in analyze_screen(): {e}")
            return "An error occurred while analyzing the screen."
    
    def _analyze_with_openai(self, prompt, image_b64):
        """Analyze using OpenAI Vision API"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}",
                            "detail": "low"
                        }
                    }
                ]
            }
        ]
        
        # Log without base64 data
        log_event("Sending vision request to OpenAI (image data excluded from log)")
        
        response = self.vision_client.chat.completions.create(
            model=self.vision_config["openai_vision_model"],
            messages=messages,
            temperature=0,
            max_tokens=500
        )
        return response.choices[0].message.content    

    def _analyze_with_ollama(self, prompt, image_b64):
        """Analyze using Ollama LLAVA"""
        messages = [
            {
                "role": "user", 
                "content": prompt,
                "images": [image_b64]
            }
        ]
        
        response = self.vision_client.chat(
            model=self.vision_config["ollama_vision_model"], 
            messages=messages
        )
        return response["message"]["content"]

class MessageParser:
    def __init__(self, llm_handler):
        self.llm_handler = llm_handler
        self.system_prompt = PromptManager.get_message_parser_prompt()
    
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
            fallback = {
                "game": "Unknown", 
                "character": "Unknown", 
                "sex": "male", 
                "message": natural_input,
                "requires_vision": False
            }
            return fallback

class CharacterManager:
    def __init__(self):
        self.chat_histories = {}
        self.active_character = None
        self.active_game = None
        self.current_history = []
        self.max_history = 10
        self.max_tokens = 12000
    
    def _get_context_log_filename(self, character, game):
        """Generate filename for context logging"""
        safe_char = re.sub(r'[^\w\-_\.]', '_', character)
        safe_game = re.sub(r'[^\w\-_\.]', '_', game)
        return f"{safe_game}_{safe_char}_context.log"
    
    def _log_context(self, action, content=None):
        """Log context changes to character-specific files"""
        if self.active_character and self.active_game:
            filename = self._get_context_log_filename(self.active_character, self.active_game)
            try:
                with open(filename, "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"{timestamp} [{action}] {content or ''}\n")
            except Exception as e:
                log_event(f"Warning: Could not write to context log {filename}: {e}")
    
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
            
            # Log context switch
            self._log_context("CONTEXT_SWITCH", f"Switched to {character} from {game}")
        else:
            log_event(f"Continuing conversation with {character} from {game}")
    
    def add_message(self, role, content):
        self.current_history.append({"role": role, "content": content})
        self._manage_history_size()
        
        # Log message to context file
        self._log_context(f"MESSAGE_{role.upper()}", content)
    
    def get_context_messages(self, system_prompt):
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.current_history[-self.max_history:])
        
        # Log the full context being sent to LLM
        self._log_context("LLM_CONTEXT", f"Sending {len(messages)} messages to LLM")
        if self.active_character and self.active_game:
            filename = self._get_context_log_filename(self.active_character, self.active_game)
            try:
                with open(filename, "a", encoding="utf-8") as f:
                    f.write(f"=== FULL CONTEXT SENT TO LLM ===\n")
                    for i, msg in enumerate(messages):
                        f.write(f"Message {i+1} [{msg['role']}]: {msg['content']}\n")
                    f.write(f"=== END CONTEXT ===\n\n")
            except Exception as e:
                log_event(f"Warning: Could not write full context to {filename}: {e}")
        
        return messages
    
    def _manage_history_size(self):
        token_estimate = sum(len(msg['content']) for msg in self.current_history) // 4
        log_event(f"Estimated context tokens: {token_estimate}")
        
        if token_estimate > self.max_tokens:
            self.current_history = self.current_history[len(self.current_history)//2:]
            log_event("Context limit exceeded. Chat history halved.")
            self._log_context("HISTORY_TRIMMED", f"Chat history halved due to token limit")

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
    def __init__(self, llm_handler, character_manager, speech_engine, vision_handler):
        self.llm_handler = llm_handler
        self.character_manager = character_manager
        self.speech_engine = speech_engine
        self.vision_handler = vision_handler
    
    def handle_conversation(self, parsed_input):
        character = parsed_input["character"]
        game = parsed_input["game"]
        message = parsed_input["message"]
        is_female = parsed_input.get("sex", "").lower() == "female"
        requires_vision = parsed_input.get("requires_vision", False)
        
        # Context maintaining logic: if parser returns "Unknown" or "unknown" for either field, keep current context
        if character.lower() == "unknown" or game.lower() == "unknown":
            if self.character_manager.active_character and self.character_manager.active_game:
                character = self.character_manager.active_character
                game = self.character_manager.active_game
                # Maintain the character's sex from the active context if available
                if hasattr(self.character_manager, 'active_character_sex'):
                    is_female = self.character_manager.active_character_sex
                log_event(f"Parser returned unknown - maintaining current context: {character} from {game}")
            else:
                log_event("No active context to maintain - using parsed values")
        
        log_event(f"Handling conversation - Character: {character}, Game: {game}, Vision required: {requires_vision}")
        
        if requires_vision:
            log_event("Vision query detected by parser. Using VLM for analysis.")
            # Update parsed_input with maintained context for vision query
            parsed_input["character"] = character
            parsed_input["game"] = game
            parsed_input["sex"] = "female" if is_female else "male"
            return self._handle_vision_query(parsed_input)
        
        # Handle regular conversation
        log_event("Regular text conversation detected.")
        self.character_manager.switch_context(character, game)
        
        # Store character sex for future context maintaining
        self.character_manager.active_character_sex = is_female
        
        self.character_manager.add_message("user", message)
        
        # Use centralized prompt management
        system_prompt = PromptManager.get_character_system_prompt(character, game, is_vision=False)
        messages = self.character_manager.get_context_messages(system_prompt)
        
        try:
            log_event(f"Generating text response for {character} from {game}")
            reply = self.llm_handler.chat(messages)
            
            self.character_manager.add_message("assistant", reply)
            self.speech_engine.speak(reply, is_female)
            
            log_event(f"Generated reply: {reply}")
            return {"success": True, "message": reply}
        except Exception as e:
            log_event(f"Error in conversation: {e}")
            return {"success": False, "message": "An error occurred."}
      
    def _handle_vision_query(self, parsed_input):
        """Handle vision-related queries"""
        character = parsed_input["character"]
        game = parsed_input["game"]
        message = parsed_input["message"]
        is_female = parsed_input.get("sex", "").lower() == "female"
        
        # Switch context for vision queries too
        self.character_manager.switch_context(character, game)
        
        try:
            # Analyze the screen with character context
            vision_response = self.vision_handler.analyze_screen(message, parsed_input)
            
            # Add to conversation history
            self.character_manager.add_message("user", message)
            self.character_manager.add_message("assistant", vision_response)
            
            self.speech_engine.speak(vision_response, is_female)
            
            log_event(f"Generated vision response: {vision_response}")
            return {"success": True, "message": vision_response}
        except Exception as e:
            log_event(f"Error in vision query: {e}")
            return {"success": False, "message": "An error occurred while analyzing the screen."}

class LoreMasterPlugin:
    def __init__(self):
        self.config = ConfigManager()
        self.llm_handler = LLMHandler(self.config)
        self.vision_handler = VisionHandler(self.config)
        self.character_manager = CharacterManager()
        self.speech_engine = SpeechEngine()
        self.message_parser = MessageParser(self.llm_handler)
        self.conversation_handler = ConversationHandler(
            self.llm_handler, self.character_manager, self.speech_engine, self.vision_handler
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
        
        # Test regular conversation
        log_event("=== Test 1: Regular Conversation ===")
        example_input = {"input": "Ask Ciri from Witcher what she thinks about destiny."}
        response = plugin.talk(example_input)
        
        if response:
            log_event(f"Regular conversation result: {response}")
            print(f"Regular conversation result: {response}")
        
        # Test vision query
        log_event("=== Test 2: Vision Query ===")
        vision_input = {"input": "Ask Ciri from Witcher what weapon is in the screen."}
        vision_response = plugin.talk(vision_input)
        
        if vision_response:
            log_event(f"Vision query result: {vision_response}")
            print(f"Vision query result: {vision_response}")
        
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