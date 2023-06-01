import os
import openai
from openai.embeddings_utils import get_embedding


def get_api_key():
    api_key = os.environ.get("OPENAI_API_KEY")

    if api_key is None:
        return None
    return api_key


def test_api_access(api_key):
    openai.api_key = api_key
    response = openai.Completion.create(model="text-davinci-003", prompt="what color is the sky", temperature=0, max_tokens=7)
    print(response)
