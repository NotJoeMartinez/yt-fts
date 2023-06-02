import openai
import sqlite3 

from progress.bar import Bar
from tenacity import retry, wait_random_exponential, stop_after_attempt


def get_openai_embeddings(subs, api_key):
    conn = sqlite3.connect("embeddings.db")
    cur = conn.cursor()

    bar = Bar('Generating embeddings', max=len(subs))
    for sub in subs:
        subtitle_id = sub[0]
        video_id = sub[1]
        timestamp = sub[2]
        text = sub[3]

        embedding = get_embedding(api_key, text)
        vector_str = ','.join(map(str, embedding))

        cur.execute(""" 
            INSERT INTO Embeddings (subtitle_id, video_id, timestamp, text, embeddings)
            VALUES (?, ?, ?, ?, ?)
            """, [subtitle_id, video_id, timestamp, text, vector_str])
        conn.commit()
        bar.next()

    bar.finish()
    conn.close()


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_embedding(api_key, text: str, model="text-embedding-ada-002") -> list[float]:
    openai.api_key = api_key
    return openai.Embedding.create(input=[text], model=model)["data"][0]["embedding"]