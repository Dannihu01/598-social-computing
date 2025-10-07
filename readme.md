## Getting Started
### Get the environment variables
1. change `.env_template` to just `env`. 
2. Fill the signing secret from chat
3. Retrieve an API key for a free instance of Gemini [here](https://aistudio.google.com/u/1/api-keys)
*You can do this with any gmail account I think, umich accounts are blocked from AI studio RIP*
### Local Development
1. create a `.venv` using `python -m venv .venv`
*As of 9.29, I'm using Python version 3.11.9*
2. For windows, use `.venv/Scripts/Activate`
3. then, do `python app.py`. This will launch the app on `host:8080`
4. launch another terminal, using ngrok (need to install). Run the following:
        `ngrok http 8080`
5. Do `/ask [your prompt]` in the sandbox to start a chat

### TODOs to make Dev easier
1. Better file management; Once we figure out a process, routes should be segmented on their function