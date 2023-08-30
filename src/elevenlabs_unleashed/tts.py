import os
import threading
from elevenlabs import generate, stream, set_api_key, get_api_key
from elevenlabs.api import User
from elevenlabs.api.error import APIError
import json

MAX_REQUEST_CHARACTERS = 2700

class UnleashedTTS():
    def __init__(self, voice = "Josh", model = "eleven_multilingual_v1"):
        self.voice = voice
        self.model = model
        self.accounts: list = json.load(open(os.getenv("ELEVENLABS_ACCOUNTS_PATH"), "r")) # type: ignore
        self.__update_accounts_thread = threading.Thread(target=ElevenLabs.__update_accounts, args=[self]) # type: ignore
        self.__update_accounts_thread.start()
    
    def speak(self, message: str):
        print("[ElevenLabs] Selecting account...")

        try:
            self.__select_account(len(message))
        except Exception as e:
            print("[ElevenLabs] Exception: ", e)
            return

        audio_stream = generate(
            text=message,
            voice=self.voice,
            model=self.model,
            stream=True
        )

        print("[ElevenLabs] Starting the stream...")
        try:
            stream(audio_stream) # type: ignore
            # Restart accounts thread
            self.__update_accounts_thread = threading.Thread(target=ElevenLabs.__update_accounts, args=[self])
            self.__update_accounts_thread.start()
        except (APIError) as e:
            print(e)
            if e.message and e.message.startswith("Unusual activity detected."):
                print("[ElevenLabs] Unusual activity detected. Speak again in a few hours.")
            else:
                print("[ElevenLabs] Text is too long. Splitting into multiple requests...")

                i = MAX_REQUEST_CHARACTERS
                while i > 0 and not (message[i] in [".", "!", "?"]):
                    i -= 1

                if i == 0:
                    print("[ElevenLabs] No punctuation found. Splitting at max characters...")
                    i = MAX_REQUEST_CHARACTERS

                self.speak(message[:i])
                self.speak(message[i:])

    def __select_account(self, text_length: int):
        self.__update_accounts_thread.join()
        self.accounts.sort(key=lambda x: x["character_count"], reverse=True)
        for account in self.accounts:
            if account["character_limit"] - account["character_count"] >= text_length:
                if get_api_key() != account["api_key"]:
                    print("[ElevenLabs] Switching to account: " + account["username"] + " (" + str(account["character_count"]) + "/" + str(account["character_limit"]) + ")")
                set_api_key(account["api_key"])
                return
        raise Exception("No account available to handle the text length")
    
    def __update_accounts(self):
        print("[ElevenLabs] Updating accounts...")
        # Select the account with the highest usage which can handle the text length
        for i in range(len(self.accounts)):
            set_api_key(self.accounts[i]["api_key"])
            user = User.from_api()
            self.accounts[i]["character_count"] = user.subscription.character_count
            self.accounts[i]["character_limit"] = user.subscription.character_limit
        print("[ElevenLabs] Accounts updated")
    
