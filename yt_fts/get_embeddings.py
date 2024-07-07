from openai import OpenAI
from rich.progress import track
from rich.console import Console

from .config import get_chroma_client


def add_embeddings_to_chroma(subs: list, openai_client: object) -> None:
    chroma_client = get_chroma_client()
    collection = chroma_client.get_or_create_collection(name="subEmbeddings")

    for sub in track(subs, description="Getting embeddings"):
        channel_id = sub['channel_id']
        video_id = sub['video_id']
        start_time = sub['start_time']
        text = sub['text'] 

        if text == '':
            continue

        embedding = get_embedding(text, "text-embedding-ada-002", openai_client)

        meta_data = {
            "channel_id": channel_id,
            "video_id": video_id,
            "start_time": start_time,
        }

        collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[meta_data],
            ids=[video_id + "_" + str(start_time)],
        )


def get_embedding(text, model="text-embedding-ada-002", client=None):
    if client is None:
        client = OpenAI()
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding
