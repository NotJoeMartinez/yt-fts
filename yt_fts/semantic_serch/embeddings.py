import openai
# from openai.embeddings_utils import get_embedding


def fetch_embedding(api_key, text):

    openai.api_key = api_key

    res = openai.Embedding.create(
        input=text, model="text-embedding-ada-002"
    )["data"][0]["embedding"]

    return res 