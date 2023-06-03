import openai
import sqlite3 
import pickle

from progress.bar import Bar
from tenacity import retry, wait_random_exponential, stop_after_attempt

def get_openai_embeddings(subs, api_key):
    conn = sqlite3.connect("subtitles.db")
    cur = conn.cursor()

    bar = Bar('Generating embeddings', max=len(subs))
    for sub in subs:
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
        bar.next()

    bar.finish()
    conn.close()


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_embedding(api_key, text: str, model="text-embedding-ada-002") -> list[float]:
    openai.api_key = api_key
    return openai.Embedding.create(input=[text], model=model)["data"][0]["embedding"]


# save embedding string 
# should take a string for search_string and array of embeddings for search_embedding
def save_search_embedding(search_string, search_embedding):
    search_embedding_blob = pickle.dumps(search_embedding)
    con = sqlite3.connect("subtitles.db")
    cur = con.cursor()

    cur.execute(""" 
        INSERT INTO SemanticSearchHist (search_str, embeddings)
        VALUES (?, ?)
        """, [search_string, search_embedding_blob])
    con.commit()
    con.close()


# get embedding blob if exists 
# should return an array of embeddings
def search_semantic_search_hist(search_string):
    con = sqlite3.connect("subtitles.db")
    cur = con.cursor()

    cur.execute(""" 
        SELECT embeddings FROM SemanticSearchHist 
        WHERE search_str = ?
        """, [search_string])
    res = cur.fetchone()
    if res is None:
        return None
    else:
        return pickle.loads(res[0])


# check if semantic search has been enabled for channel
def check_ss_enabled(channel_id=None):
    con = sqlite3.connect("subtitles.db")
    cur = con.cursor()

    if channel_id is None:
        cur.execute(""" 
            SELECT channel_id FROM SemanticSearchEnabled 
            """)
    else:
        cur.execute(""" 
            SELECT channel_id FROM SemanticSearchEnabled 
            WHERE channel_id = ?
            """, [channel_id])

    res = cur.fetchone()
    if res is None:
        return False 
    else:
        return True 

# enable semantic search for channel
def enable_ss(channel_id):
    con = sqlite3.connect("subtitles.db")
    cur = con.cursor()

    cur.execute(""" 
        INSERT INTO SemanticSearchEnabled (channel_id)
        VALUES (?)
        """, [channel_id])
    con.commit()
    con.close() 