# chat-centrifugo
sample chat app using centrifugo and fastapi.

# Initial steps
- install [centrifugo](https://centrifugal.dev/)
  - `centrifugo genconfig` in the project dir, creating config.json
  - edit config to make it run on localhost:8888
  
    ```
      "http_server": {
         "port": "8888"
      }
    ```
  - run centrifugo: `centrifugo`
- run `./main.py`, either with venv or with uv:
  `uv run main.py`
