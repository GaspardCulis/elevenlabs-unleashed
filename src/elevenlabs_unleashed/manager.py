import threading
from elevenlabs_unleashed.account import create_account
from typing import Callable, Tuple

class ELUAccountManager():
    def __init__(self, set_api_key_callback: Callable[[str], None], nb_accounts: int = 2):
        self.__api_key_callback = set_api_key_callback
        self.__nb_accounts = nb_accounts
        self.accounts = []
        self.__threads = []

    def __create_account(self):
        self.accounts.append(create_account())

    def __create_accounts_async(self):
        self.__threads = []
        for i in range(self.__nb_accounts - len(self.accounts)):
            thread = threading.Thread(target=self.__create_account)
            thread.start()
            self.__threads.append(thread)

    def next(self) -> Tuple[str, str, str]:
        """
        Takes the next account from the list and returns the email, password and api key, creating new accounts if needed.
        This function is thread-blocking if no account is available, until a new account is created
        """
        if len(self.accounts) == 0:
            if len(self.__threads) == 0:
                self.__create_accounts_async()
            for thread in self.__threads:
                thread.join()
            self.__threads = []
        account = self.accounts.pop()
        self.__api_key_callback(account[2])
        self.__create_accounts_async()
        return account[0], account[1], account[2]