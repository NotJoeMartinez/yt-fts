import chromadb

from rich.console import Console
from sqlite_utils import Database

from .utils import time_to_secs
from .embeddings import get_embedding
from .config import get_or_make_chroma_path 
from .db_utils import get_channel_name_from_video_id, get_title_from_db
from .download import get_channel_id_from_input 

def search_chroma_db(
        text, 
        scope, 
        channel_id=None, 
        video_id=None, 
        limit=10,
        openai_client=None):

    chroma_path = get_or_make_chroma_path()
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_collection(name="subEmbeddings")

    search_embedding = get_embedding(text, "text-embedding-ada-002", openai_client)

    scope_options = {}

    if scope == "all":
        scope_options = {}
    if scope == "channel":
        scope_options = {"channel_id": get_channel_id_from_input(channel_id)}
    if scope == "video":
        scope_options = {"video_id": video_id}

    chroma_res = collection.query(
        query_embeddings=[search_embedding],
        n_results=limit,
        where=scope_options,
        )


    documents = chroma_res["documents"][0]
    metadata = chroma_res["metadatas"][0]

    res = []

    for i in range(len(documents)):
        text = documents[i]
        video_id = metadata[i]["video_id"]
        subtitle_id = metadata[i]["subtitle_id"] 
        time_stamp = metadata[i]["timestamp"]
        link = f"https://youtu.be/{video_id}?t={time_to_secs(time_stamp)}"
        channel_name = get_channel_name_from_video_id(video_id)
        title = get_title_from_db(video_id)

        match = {
            "subtitle_id": subtitle_id,
            "channel_name": channel_name,
            "video_title": title,
            "subs": text,
            "time_stamp": time_stamp,
            "video_id": video_id,
            "link": link,
        }
        res.append(match)

    return res

def print_vector_search_results(res):
    """
    {'subtitle_id': '492', 
    'channel_name': 'Peter Whidden', 
    'video_title': 'Training AI to Play Pokemon with Reinforcement Learning - YouTube', 
    'subs': 'choosing a Pokemon and winning its first', 
    'time_stamp': '00:22:14.909', 
    'video_id': 'DcYLT37ImBY', 
    'link': 'https://youtu.be/DcYLT37ImBY?t=1331'}
    """
    console = Console()

    for match in res:
        link = match["link"]
        text = match["subs"]
        time_stamp = match["time_stamp"]    
        video_id = match["video_id"]
        title = match["video_title"]
        channel_name = match["channel_name"]


        console.print(f"[magenta][italic]\"[bold][link={link}]{text}[/link][/bold]\"[/italic][/magenta]", style="magenta")
        print("")
        console.print(f"    Channel: {channel_name}",style="none")
        print(f"    Title: {title}")
        print(f"    Time Stamp: {time_stamp}")
        console.print(f"    Video ID: {video_id}")
        console.print(f"    Link: {link}")
        console.print("")


# save embedding string 
# should take a string for search_string and array of embeddings for search_embedding
# def save_search_embedding(search_string, search_embedding):

#     search_embedding_blob = pickle.dumps(search_embedding)
#     con = sqlite3.connect(get_db_path())
#     cur = con.cursor()

#     cur.execute(""" 
#         INSERT INTO SemanticSearchHist (search_str, embeddings)
#         VALUES (?, ?)
#         """, [search_string, search_embedding_blob])
#     con.commit()
#     con.close()


# get embedding blob if exists 
# should return an array of embeddings
# def search_semantic_search_hist(search_string):
#     con = sqlite3.connect(get_db_path())
#     cur = con.cursor()

#     cur.execute(""" 
#         SELECT embeddings FROM SemanticSearchHist 
#         WHERE search_str = ?
#         """, [search_string])
#     res = cur.fetchone()
#     if res is None:
#         return None
#     else:
#         return pickle.loads(res[0])



