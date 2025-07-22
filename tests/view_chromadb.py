import chromadb
import sys
from openai import OpenAI
from yt_fts.get_embeddings import get_embedding
from yt_fts.config import get_or_make_chroma_path
from yt_fts.utils import get_model_config, time_to_secs
from yt_fts.db_utils import get_channel_name_from_video_id, get_title_from_db
from pprint import pprint

def main():
    chroma_path = get_or_make_chroma_path() 
    view_collections(chroma_path)
    # search = "nural networks"
    # search_collections(chroma_path, search)

    # view_by_channel_id("")
    # delete_stuff()

def view_collections(chroma_path):
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_collection(name="subEmbeddings")
    print(collection.peek())
    print(collection.count())


def view_by_channel_id(channel_id):
    chroma_path = get_or_make_chroma_path()
    chroma_client = chromadb.PersistentClient(path=chroma_path)

    collection = chroma_client.get_collection(name="subEmbeddings")


    # collection.get({
    #     include: [ "documents" ]
    # })

    # chroma_res = collection.query(
    #     query_texts=["networks"],
    #     n_results=5,
    #     where={"channel_id": channel_id})
    
    # pprint(chroma_res)



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

    model = get_model_config()
    openai_client = OpenAI(api_key=model['api_key'], base_url=model['base_url'])
    search_embedding = get_embedding(text, model['embedding_model'], openai_client)


    chroma_res = collection.query(
        query_embeddings=[search_embedding],
        n_results=5,
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