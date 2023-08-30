from elevenlabs_unleashed.account import create_account
import os
import threading
from elevenlabs import generate, stream, set_api_key, get_api_key
from elevenlabs.api import User
from elevenlabs.api.error import APIError
import json
import sys
import pathlib

def __get_datadir() -> pathlib.Path:
    # https://stackoverflow.com/a/61901696
    """
    Returns a parent directory path
    where persistent application data can be stored.

    - linux: ~/.local/share
    - macOS: ~/Library/Application Support
    - windows: C:/Users/<USER>/AppData/Roaming
    """

    home = pathlib.Path.home()

    if sys.platform == "win32":
        return home / "AppData/Roaming"
    elif sys.platform == "linux":
        return home / ".local/share"
    elif sys.platform == "darwin":
        return home / "Library/Application Support"

DATADIR = __get_datadir()
MAX_REQUEST_CHARACTERS = 2700

class UnleashedTTS():
    """
    This class is a wrapper around the ElevenLabs API.
    It handles the creation of accounts and the selection of the account to use for each request.

    :param accounts_save_path: The path to the file where the accounts are saved. Defaults to ``~/.local/share/elevenlabs_accounts.json`` on Linux, ``~/Library/Application Support/elevenlabs_accounts.json`` on macOS and ``C:/Users/<USER>/AppData/Roaming/elevenlabs_accounts.json`` on Windows.
    :param nb_accounts: The number of accounts to create. Defaults to 4.
    :param create_accounts_threads: The number of threads to use to create the accounts. Defaults to 2.
    """
    def __init__(self, accounts_save_path: str = DATADIR / "elevenlabs_accounts.json", nb_accounts: int = 4, create_accounts_threads: int = 2):
        self.accounts_save_path = accounts_save_path
        self.nb_accounts = nb_accounts
        self.__check_accounts_file()
        self.__populate_accounts(create_accounts_threads)


        self.__update_accounts_thread = threading.Thread(target=UnleashedTTS.__update_accounts, args=[self]) # type: ignore
        self.__update_accounts_thread.start()
    
    def speak(self, message: str, voice = "Josh", model = "eleven_multilingual_v1"):
        print("[ElevenLabs] Selecting account...")

        try:
            self.__select_account(len(message))
        except Exception as e:
            print("[ElevenLabs] Exception: ", e)
            return

        audio_stream = generate(
            text=message,
            voice=voice,
            model=model,
            stream=True
        )

        print("[ElevenLabs] Starting the stream...")
        try:
            stream(audio_stream) # type: ignore
            # Restart accounts thread
            self.__update_accounts_thread = threading.Thread(target=UnleashedTTS.__update_accounts, args=[self])
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

    def __check_accounts_file(self):
        if not os.path.exists(self.accounts_save_path):
            print(f"[ElevenLabs] Accounts file not found. Creating it at {self.accounts_save_path}")
            with open(self.accounts_save_path, "w") as f:
                json.dump([], f)

        # Check if the file is corrupted
        try:
            with open(self.accounts_save_path, "r") as f:
                accounts = json.load(f)
        except json.decoder.JSONDecodeError:
            print("[ElevenLabs] Accounts file is corrupted. Deleting it...")
            os.remove(self.accounts_save_path)
            self.__check_accounts_file()
            return
        
        # Check if the file contains valid accounts
        for account in accounts:
            if not ("username" in account and "password" in account and "api_key" in account) or \
                    not (isinstance(account["username"], str) and isinstance(account["password"], str) and isinstance(account["api_key"], str)):
                print("[ElevenLabs] Accounts file is corrupted. Deleting it...")
                os.remove(self.accounts_save_path)
                self.__check_accounts_file()
                return

    def __populate_accounts(self, create_accounts_threads: int):
        with open(self.accounts_save_path, "r") as f:
            self.accounts = json.load(f)
        
        while len(self.accounts) < self.nb_accounts:
            # Print at the beginning of the line
            print(f"\r[ElevenLabs] Creating accounts... ({len(self.accounts)}/{self.nb_accounts})", end="")
            threads = []
            for i in range(min(create_accounts_threads, self.nb_accounts - len(self.accounts))):
                thread = threading.Thread(target=self.__create_account)
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()

        print("\r[ElevenLabs] Accounts created.                           ")
        with open(self.accounts_save_path, "w") as f:
            json.dump(self.accounts, f)

    def __create_account(self):
        email, password, api_key = create_account()
        self.accounts.append({
            "username": email,
            "password": password,
            "api_key": api_key
        })


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
    
