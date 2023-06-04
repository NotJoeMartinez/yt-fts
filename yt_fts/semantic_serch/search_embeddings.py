import sqlite3 
import pickle
import heapq

import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from rich.console import Console

from yt_fts.utils import time_to_secs
from yt_fts.search_utils import get_channel_name_from_video_id
from yt_fts.db_utils import get_title_from_db
from yt_fts.search_utils import print_search_results

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


    semantic_res = []

    for sim, row in sorted(heap, reverse=True):
        quote_match = {}

        quote = row[3]
        timestamp = row[2]
        time = time_to_secs(timestamp)
        video_id= row[1]
        link = f"https://youtu.be/{video_id}?t={time}"
        channel_name = get_channel_name_from_video_id(video_id)
        video_title = get_title_from_db(video_id)
        
        quote_match["channel_name"] = channel_name
        quote_match["video_title"] = video_title
        quote_match["subs"] = quote
        quote_match["time_stamp"] = timestamp
        quote_match["video_id"] = video_id
        quote_match["link"] = link

        semantic_res.append(quote_match)

    print_search_results(semantic_res)


