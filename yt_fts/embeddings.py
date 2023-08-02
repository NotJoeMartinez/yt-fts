import openai
import sqlite3 
import pickle

from rich.progress import track
from rich.console import Console

from tenacity import retry, wait_random_exponential, stop_after_attempt
from .config import get_db_path

def get_openai_embeddings(subs, api_key):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()

    for sub in track(subs, description="Getting embeddings"):
        subtitle_id = sub[0]
        video_id = sub[1]
        timestamp = sub[2]
        text = sub[3]

        embedding = get_embedding(api_key, text)
        embeddings_blob = pickle.dumps(embedding)

        cur.execute(""" 
            INSERT INTO Embeddings (subtitle_id, video_id, timestamp, text, embeddings)
            VALUES (?, ?, ?, ?, ?)
            """, [subtitle_id, video_id, timestamp, text, embeddings_blob])
        conn.commit()

    conn.close()


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_embedding(api_key, text: str, model="text-embedding-ada-002") -> list[float]:
    openai.api_key = api_key
    return openai.Embedding.create(input=[text], model=model)["data"][0]["embedding"]

