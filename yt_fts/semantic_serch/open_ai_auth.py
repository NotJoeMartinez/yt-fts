import os

def get_api_key():
    api_key = os.environ.get("OPENAI_API_KEY")

    if api_key is None:
        return None
    return api_key
