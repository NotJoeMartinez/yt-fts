import chromadb
import sys
from openai import OpenAI
from yt_fts.embeddings import get_embedding
from yt_fts.config import get_or_make_chroma_path
from yt_fts.utils import time_to_secs
from yt_fts.db_utils import get_channel_name_from_video_id, get_title_from_db
from pprint import pprint

def main():

    view_by_channel_id("UCO2QPmnJFjdvJ6ch-pe27dQ")


def view_collections(chroma_path):
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_collection(name="subEmbeddings")
    print(collection.peek())
    print(collection.count())


def view_by_channel_id(channel_id):
    chroma_path = get_or_make_chroma_path()
    chroma_client = chromadb.PersistentClient(path=chroma_path)

    collection = chroma_client.get_collection(name="subEmbeddings")

    chroma_res = collection.get(
        where={"channel_id": channel_id}
        )
    
    for meta in chroma_res["metadatas"]:
        pprint(meta["video_id"])



def delete_stuff():
    chroma_path = get_or_make_chroma_path()
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_collection(name="subEmbeddings")

    collection.delete(
        where={"channel_id": "UCF0ZSm2AmSkJ2b2sLMlgLFg"}
    )

def search_collections(chroma_path, text):
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_collection(name="subEmbeddings")

    search_embedding = get_embedding(text, "text-embedding-ada-002", OpenAI())

    chroma_res = collection.query(
        query_embeddings=[search_embedding],
        n_results=5,
        where={},
        )

    pprint(chroma_res)
    documents = chroma_res["documents"][0]
    metadata = chroma_res["metadatas"][0]
    distances = chroma_res["distances"][0]

    res = []

    for i in range(len(documents)):
        text = documents[i]
        video_id = metadata[i]["video_id"]
        start_time = metadata[i]["start_time"]
        distance = distances[i]
        link = f"https://youtu.be/{video_id}?t={time_to_secs(start_time)}"
        channel_name = get_channel_name_from_video_id(video_id)
        channel_id = metadata[i]["channel_id"]
        title = get_title_from_db(video_id)
        match = {
            "distance": distance,
            "channel_name": channel_name,
            "channel_id": channel_id, 
            "video_title": title,
            "subs": text,
            "start_time": start_time,
            "video_id": video_id,
            "link": link,
        }
        res.append(match)

    for match in res:
        pprint(match)


if __name__ == "__main__":
    main()