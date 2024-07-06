import sys

from openai import OpenAI

from .db_utils import (
    get_channel_id_from_input,
    get_channel_name_from_video_id,
    get_title_from_db
)

from .get_embeddings import get_embedding
from .utils import time_to_secs
from .config import get_chroma_client

def run_llm(openai_api_key: str, prompt: str, channel: str) -> None:

    channel_id = get_channel_id_from_input(channel)
    openai_client = OpenAI(api_key=openai_api_key)
    try:
        # Create a chat completion using the question and context
        context = create_context(
            text=prompt,
            channel_id=channel_id,
            openai_client=openai_client
        )


        user_str = f"Context: {context}\n\n---\n\nQuestion: {prompt}\nAnswer:"


        system_prompt = """
                        Answer the question based on the context below, The context are 
                        subtitles and timestamped links from videos related to the question. 
                        In your answer, provide the link to the video where the answer can 
                        be found. and if the question can't be answered based on the context, 
                        say \"I don't know\"\n\n
                        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_str},
            ]

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            max_tokens=2000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
        )

        response = response.choices[0].message.content
        print(response)
        sys.exit(0)

    except Exception as e:
        print(e)
        sys.exit(1)



def create_context(text: str, channel_id: str, openai_client) -> str:

    chroma_client = get_chroma_client()
    collection = chroma_client.get_collection(name="subEmbeddings")

    search_embedding = get_embedding(text, "text-embedding-ada-002", openai_client)

    scope_options = {}


    scope_options = {"channel_id": channel_id}

    chroma_res = collection.query(
        query_embeddings=[search_embedding],
        n_results=10,
        where=scope_options,
    )

    documents = chroma_res["documents"][0]
    metadata = chroma_res["metadatas"][0]
    distances = chroma_res["distances"][0]

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
            "distance": distances[i],
            "channel_name": channel_name,
            "channel_id": channel_id,
            "video_title": title,
            "subs": text,
            "start_time": start_time,
            "video_id": video_id,
            "link": link,
        }
        res.append(match)

    formatted_context = ""

    for obj in res:
        
        tmp = f"""
            Video Title: {obj["video_title"]}
            Text: {obj["subs"]}
            Time: {obj["start_time"]}
            Similarity: {obj["distance"]}
            Link: {obj["link"]}
            -------------------------
        """
        formatted_context += tmp

    return formatted_context 
