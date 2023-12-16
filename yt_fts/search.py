
import pickle
import sqlite3

from .download import get_channel_id_from_input
from .db_utils import * 
from .utils import *
from rich.console import Console


# full text search
def fts_search(text, scope, channel_id=None, video_id=None):
    """
    Calls search functions and prints the results 
    """

    if scope == "all":
        res = search_all(text)
    
    if scope == "channel":
        channel_id = get_channel_id_from_input(channel_id)
        res = search_channel(channel_id, text)
    
    if scope == "video":
        res = search_video(video_id, text)

    if len(res) == 0:
        show_message("no_matches_found")
        exit()

    return res


# pretty print search results
def print_fts_res(res):

    console = Console()

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

    # sort by channel name
    fts_res = sorted(fts_res, key=lambda x: x["channel_name"])


    console.print("")
    for quote in fts_res: 

        console.print(f"[magenta][italic]\"[bold][link={quote['link']}]{quote['subs']}[/link][/bold]\"[/italic][/magenta]", style="magenta")
        print("")
        console.print(f"    Channel: {quote['channel_name']}",style="none")
        print(f"    Title: {quote['video_title']}")
        print(f"    Time Stamp: {quote['time_stamp']}")
        console.print(f"    Video ID: {quote['video_id']}")
        console.print(f"    Link: {quote['link']}")
        console.print("")
    
    print_summary(summary_data)


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



# semantic search
def semantic_search(text, search_id, scope, limit, export=False):
    pass

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


