import sqlite3 
import numpy as np
import heapq
from sklearn.metrics.pairwise import cosine_similarity
from yt_fts.utils import time_to_secs


def search_using_embedding(search_embedding, top_n):
    con = sqlite3.connect('embeddings.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM Embeddings")
    rows = cur.fetchall()

    heap = []

    for row in rows:
        embedding_str = row[4]
        db_embedding = np.fromstring(embedding_str[1:-1], sep=',') 
        similarity = cosine_similarity([search_embedding], [db_embedding])

        if len(heap) < top_n or similarity > heap[0][0]:
            if len(heap) == top_n:
                heapq.heappop(heap)
            heapq.heappush(heap, (similarity, row))

    con.close()


    for sim, row in sorted(heap, reverse=True):

        print("")
        print("=====================================")
        quote = row[3]
        timestamp = row[2]
        time = time_to_secs(timestamp)
        vid_id = row[1]
        link = f"https://youtu.be/{vid_id}?t={time}"
        print(f"Quote: \"{quote}\"")
        print(f"Time Stamp: {timestamp}")
        print(f"Video ID: {vid_id}")
        print(f"Link: {link}")
