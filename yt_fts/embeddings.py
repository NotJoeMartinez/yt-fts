import chromadb

from .config import get_or_make_chroma_path

from openai import OpenAI
from rich.progress import track
from rich.console import Console


def add_embeddings_to_chroma(subs, openai_client):

    chroma_path = get_or_make_chroma_path()
    chroma_client = chroma_client = chromadb.PersistentClient(path=chroma_path) 
    collection = chroma_client.get_or_create_collection(name="subEmbeddings")

    for sub in track(subs, description="Getting embeddings"):
        subtitle_id = str(sub[0])
        video_id = sub[1]
        timestamp = sub[2]
        text = sub[3]
        channel_id = sub[4]

        embedding = get_embedding(text, "text-embedding-ada-002", openai_client)

        meta_data = {
            "subtitle_id": subtitle_id,
            "video_id": video_id,
            "timestamp": timestamp,
            "channel_id": channel_id
        }

        collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[meta_data],
            ids=[subtitle_id]
        )


def make_chroma_db():
    chroma_client = chromadb.PersistentClient(path="./persist")
    return chroma_client


def get_embedding(text, model="text-embedding-ada-002", client=OpenAI()):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding

