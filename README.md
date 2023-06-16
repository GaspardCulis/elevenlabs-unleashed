# 11Labs Unleashed

Provides unlimited ElevenLabs API calls.

## Usage

Create an account

```py
from elevenlabs_unleashed.account import create_account

username, password, api_key = create_account()
```

Automatic API key renewal

```py
from elevenlabs_unleashed.manager import ELUAccountManager
from elevenlabs import generate, set_api_key, play, api

eluac = ELUAccountManager(set_api_key, nb_accounts= 2) # Creates a queue of API keys
eluac.next() # First call will block the thread until keys are generated, and call set_api_key

def speak(self, message: str):
    try:
        audio = generate(
            text=message,
            voice="Josh", # I like this one
            model="eleven_multilingual_v1"
        )
    except elevenlabs.api.error.RateLimitError as e:
        print("[ElevenLabs] Maximum number of requests reached. Getting a new API key...")
        eluac.next() # Uses next API key in queue, should be instant as nb_accounts > 1, and will generate a new key in a background thread.
        speak(message)
        return

    print("[ElevenLabs] Starting the stream...")
    play(audio)
```

## How it works

11Labs Unleashed is basically just a web scraper (selenium) that creates unlimited 11Labs accounts programatically.

The `ELUAccountManager` stores an array of API keys populated in a FIFO queue manner. When calling *next()*, it returns the last API key in the queue (making sure it is not empty), and refills the queue, making the API key renewal instant after the first *next()* call as long as nb_accounts is greater than 1 (defaults to 2, more would be overkill).

## Installation

```bash
pip install elevenlabs-unleashed
```

## Dependencies

You need the [chromedriver](https://chromedriver.chromium.org/downloads) in your PATH.

## TODO

- Automatic account deletion when max API usage reached
- Less crappy Python code and better API
- Try not to get sued by 11Labs

## Notes

This library is very unstable and I guess won't work for long. It only relies on the fact that 11Labs account creation is easily bot-able. Also some minor [11Labs website](https://beta.elevenlabs.io/) changes might break my crappy web scraping.

If you find issues don't hesitate to submit a PR if you find a fix.

## Credits

Thanks to the ElevenLabs team for making the best multi-lingual TTS models in the world. But because the API pricing is such expensive, this library had to be done.
