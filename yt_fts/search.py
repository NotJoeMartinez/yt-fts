
import pickle
import sqlite3
import heapq

from .db_utils import * 
from .utils import *
from rich.console import Console


# full text search
def get_text(channel_id, text):
    """
    Calls search functions and prints the results 
    """
    if channel_id == "all":
        res = search_all(text)
    else:
        res = search_channel(channel_id, text)

    if len(res) == 0:
        show_message("no_matches_found")
        exit()
    
    fts_res = []
    channel_names = []
    for quote in res:

        quote_match = {}

        video_id = quote["video_id"]
        time_stamp = quote["timestamp"]
        time = time_to_secs(time_stamp)
        link = f"https://youtu.be/{video_id}?t={time}"

        quote_match["channel_name"] = get_channel_name_from_video_id(video_id)
        channel_names.append(quote_match["channel_name"])

        quote_match["video_title"] = get_title_from_db(video_id)
        quote_match["subs"] = quote["text"].strip()
        quote_match["time_stamp"] = time_stamp
        quote_match["video_id"] = video_id
        quote_match["link"] = link 

        fts_res.append(quote_match)

    summary_data = {
        "num_matches": len(res),
        "num_channels": len(set(channel_names)),
        "num_videos": len(set([quote["video_id"] for quote in res]))
    } 

    print_search_results(fts_res)
    print_summary(summary_data)


# semantic search
def semantic_search(text, search_id, scope, limit, export=False):

    from sklearn.metrics.pairwise import cosine_similarity
    from yt_fts.config import get_db_path


    # check history for embeddings
    # generate new ones for search string if not found
    hist = search_semantic_search_hist(text)
    if hist is None:
        import os
        from yt_fts.embeddings import get_embedding 

        api_key = os.environ.get("OPENAI_API_KEY")
        print(f"Generating embeddings for \"{text}\"")
        search_embedding = get_embedding(api_key, text)
        save_search_embedding(text, search_embedding)
    else:
        search_embedding = hist



    con = sqlite3.connect(get_db_path())
    cur = con.cursor()

    # select embeddings based on scope
    if scope == "all":
        cur.execute("SELECT * FROM Embeddings")
    elif scope == "video":
        cur.execute(f"SELECT * FROM Embeddings WHERE video_id = '{search_id}'")
    else:
        cur.execute(f"SELECT * FROM Embeddings WHERE video_id IN (SELECT video_id FROM Videos WHERE channel_id = '{search_id}')")


    # find top n matches
    rows = cur.fetchall()
    heap = []

    for row in rows:
        db_embedding = pickle.loads(row[4]) 
        similarity = cosine_similarity([search_embedding], [db_embedding])

        if len(heap) < limit or similarity > heap[0][0]:
            if len(heap) == limit:
                heapq.heappop(heap)
            heapq.heappush(heap, (similarity, row))

    con.close()


    channel_names = []
    semantic_res = []

    for sim, row in sorted(heap, reverse=True):
        quote_match = {}

        quote = row[3]
        timestamp = row[2]
        time = time_to_secs(timestamp)
        video_id= row[1]
        link = f"https://youtu.be/{video_id}?t={time}"
        channel_name = get_channel_name_from_video_id(video_id)
        channel_names.append(channel_name)
        video_title = get_title_from_db(video_id)
        
        quote_match["channel_name"] = channel_name
        quote_match["video_title"] = video_title
        quote_match["subs"] = quote
        quote_match["time_stamp"] = timestamp
        quote_match["video_id"] = video_id
        quote_match["link"] = link

        semantic_res.append(quote_match)

    if export == True:
        return semantic_res

    print_search_results(semantic_res)
    summary_data = {
        "num_matches": len(semantic_res),
        "num_channels": len(set(channel_names)),
        "num_videos": len(set([quote["video_id"] for quote in semantic_res]))
    } 
    print_summary(summary_data)

# video search
def get_text_by_video_id(video_id, text):
    res = search_video(video_id, text)
    if len(res) == 0:
        show_message("no_matches_found")
        exit()

    fts_res = []
    for quote in res:

        quote_match = {}

        video_id = quote["video_id"]
        time_stamp = quote["timestamp"]
        time = time_to_secs(time_stamp)
        link = f"https://youtu.be/{video_id}?t={time}"

        quote_match["channel_name"] = get_channel_name_from_video_id(video_id)
        quote_match["video_title"] = get_title_from_db(video_id)
        quote_match["subs"] = quote["text"].strip()
        quote_match["time_stamp"] = time_stamp
        quote_match["video_id"] = video_id
        quote_match["link"] = link 

        fts_res.append(quote_match)

    print_search_results(fts_res)



# save embedding string 
# should take a string for search_string and array of embeddings for search_embedding
def save_search_embedding(search_string, search_embedding):

    search_embedding_blob = pickle.dumps(search_embedding)
    con = sqlite3.connect(get_db_path())
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
    con = sqlite3.connect(get_db_path())
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
    con = sqlite3.connect(get_db_path())
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
    con = sqlite3.connect(get_db_path())
    cur = con.cursor()

    cur.execute(""" 
        INSERT INTO SemanticSearchEnabled (channel_id)
        VALUES (?)
        """, [channel_id])
    con.commit()
    con.close() 



# pretty print search results
def print_search_results(res):

    """
    format of res:
    [
        {
            "channel_name": "channel_name",
            "video_title": "video_title",
            "subs": "subs",
            "time_stamp": "time_stamp",
            "video_id": "video_id",
            "link": "link"
        }
    ]
    """
    # sort by channel name
    res = sorted(res, key=lambda x: x["channel_name"])

    console = Console()

    console.print("")
    for quote in res: 

        console.print(f"[magenta][italic]\"[bold][link={quote['link']}]{quote['subs']}[/link][/bold]\"[/italic][/magenta]", style="magenta")
        print("")
        console.print(f"    Channel: {quote['channel_name']}",style="none")
        print(f"    Title: {quote['video_title']}")
        print(f"    Time Stamp: {quote['time_stamp']}")
        console.print(f"    Video ID: {quote['video_id']}")
        console.print(f"    Link: {quote['link']}")
        console.print("")


def print_summary(summary_data):
    """
    "num_matches": num_matches,
    "num_channels": num_channels,
    "num_videos": num_videos,
    """
    console = Console()

    console.print("")
    console.print(f"Found [bold]{summary_data['num_matches']}[/bold] matches in [bold]{summary_data['num_videos']}[/bold] videos from [bold]{summary_data['num_channels']}[/bold] channels")
    pass