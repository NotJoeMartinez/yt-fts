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

        embedding = get_embedding(text, "text-embedding-ada-002", openai_client)

        meta_data = {
            "subtitle_id": subtitle_id,
            "video_id": video_id,
            "timestamp": timestamp
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


def search_chroma_db(text, openai_client):

    console = Console()

    chroma_client = chromadb.PersistentClient(path="./persist")
    collection = chroma_client.get_collection(name="subEmbeddings")

    search_embedding = get_embedding(text, "text-embedding-ada-002", openai_client)

    res = collection.query(
        query_embeddings=[search_embedding],
        n_results=10,
        # where_document={"$contains":"search_string"}
        # where={"metadata_field": "is_equal_to_this"},
        )

    documents = res["documents"][0]
    ids = res["ids"][0]
    metadata = res["metadatas"][0]


    for i in range(len(documents)):
        text = documents[i]
        subtitle_id = ids[i]
        meta = metadata[i]

        console.print(f"{meta}\n{subtitle_id}: {text}")


def get_embedding(text, model="text-embedding-ada-002", client=OpenAI()):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding

