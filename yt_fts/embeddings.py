import chromadb
from openai import OpenAI
from sqlite_utils import Database
from rich.progress import track
from rich.console import Console

from tenacity import retry, wait_random_exponential, stop_after_attempt
from .config import get_db_path


def get_all_subs_by_channel_id(channel_id):
    
    db = Database("subtitles.db")

    parsed_subs = []
    subs = db.execute("""
        SELECT s.subtitle_id, s.video_id, s.timestamp, s.text 
        FROM Subtitles s
        JOIN Videos v ON s.video_id = v.video_id
        WHERE v.channel_id = ?
        """, [channel_id]).fetchall()
    
    for sub in subs:
        split_subs = sub[3].strip().split(" ")
        if len(split_subs) > 1: 
            parsed_subs.append(sub)

    return parsed_subs


def add_embeddings_to_chroma(subs):

    chroma_client = make_chroma_db()
    collection = chroma_client.get_or_create_collection(name="subEmbeddings")

    for sub in track(subs, description="Getting embeddings"):
        subtitle_id = str(sub[0])
        video_id = sub[1]
        timestamp = sub[2]
        text = sub[3]

        print(f"subtitle_id: {subtitle_id}, video_id: {video_id}, timestamp: {timestamp}, text: {text}")

        embedding = get_embedding(text)

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


def search_chroma_db(query):

    console = Console()

    client = chromadb.PersistentClient(path="./persist")
    collection = client.get_collection(name="subEmbeddings")

    search_embedding = get_embedding(query)

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

