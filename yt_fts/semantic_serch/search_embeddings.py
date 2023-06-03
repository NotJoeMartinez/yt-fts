import sqlite3 
import pickle
import numpy as np
import heapq
from sklearn.metrics.pairwise import cosine_similarity
from yt_fts.utils import time_to_secs
from yt_fts.search_utils import get_channel_name_from_video_id
from yt_fts.db_utils import get_title_from_db


def search_using_embedding(search_embedding, top_n, channel_id=None):
    con = sqlite3.connect('subtitles.db')
    cur = con.cursor()
    if channel_id is None:
        cur.execute("SELECT * FROM Embeddings")
    else:
        cur.execute(f"SELECT * FROM Embeddings WHERE video_id IN (SELECT video_id FROM Videos WHERE channel_id = '{channel_id}')")
    rows = cur.fetchall()

    heap = []

    for row in rows:
        db_embedding = pickle.loads(row[4]) 
        similarity = cosine_similarity([search_embedding], [db_embedding])

        if len(heap) < top_n or similarity > heap[0][0]:
            if len(heap) == top_n:
                heapq.heappop(heap)
            heapq.heappush(heap, (similarity, row))

    con.close()


    for sim, row in sorted(heap, reverse=True):

        print("")
        quote = row[3]
        timestamp = row[2]
        time = time_to_secs(timestamp)
        video_id= row[1]
        link = f"https://youtu.be/{video_id}?t={time}"
        channel_name = get_channel_name_from_video_id(video_id)
        video_title = get_title_from_db(video_id)

        print("")
        print(f"{channel_name}: \"{video_title}\"")
        print(f"") 
        print(f"    Quote: \"{quote}\"")
        print(f"    Time Stamp: {timestamp}")
        print(f"    Video ID: {video_id}")
        print(f"    Link: {link}")
