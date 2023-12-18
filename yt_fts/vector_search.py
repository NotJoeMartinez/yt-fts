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
        start_time = metadata[i]["start_time"]
        link = f"https://youtu.be/{video_id}?t={time_to_secs(start_time)}"
        channel_name = get_channel_name_from_video_id(video_id)
        channel_id = metadata[i]["channel_id"]
        title = get_title_from_db(video_id)


        match = {
            "channel_name": channel_name,
            "channel_id": channel_id, 
            "video_title": title,
            "subs": text,
            "start_time": start_time,
            "video_id": video_id,
            "link": link,
        }
        res.append(match)

    return res


def print_vector_search_results(res):
    """
    {
    'channel_name': 'Peter Whidden', 
    'video_title': 'Training AI to Play Pokemon with Reinforcement Learning - YouTube', 
    'subs': 'choosing a Pokemon and winning its first', 
    'start_time': '00:22:14.909', 
    'video_id': 'DcYLT37ImBY', 
    'link': 'https://youtu.be/DcYLT37ImBY?t=1331'}
    """
    console = Console()

    for match in res:
        link = match["link"]
        text = match["subs"]
        time_stamp = match["start_time"]    
        channel_id = match["channel_id"]
        video_id = match["video_id"]
        title = match["video_title"]
        channel_name = match["channel_name"]


        console.print(f"[magenta][italic]\"[bold][link={link}]{text}[/link][/bold]\"[/italic][/magenta]", style="magenta")
        print("")
        console.print(f"    Channel: {channel_name} - ({channel_id})",style="none")
        print(f"    Title: {title}")
        print(f"    Time Stamp: {time_stamp}")
        console.print(f"    Video ID: {video_id}")
        console.print(f"    Link: {link}")
        console.print("")



def delte_channel_from_chroma_db(channel_id):
    chroma_path = get_or_make_chroma_path()
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_collection(name="subEmbeddings")
    collection.delete(where={"channel_id": channel_id})