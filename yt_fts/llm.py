# llm_class.py

import sys
import traceback
from openai import OpenAI
from .db_utils import (
    get_channel_id_from_input,
    get_channel_name_from_video_id,
    get_title_from_db
)
from .get_embeddings import get_embedding
from .utils import time_to_secs
from .config import get_chroma_client


class LLMHandler:
    def __init__(self, openai_api_key: str, channel: str):
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.channel_id = get_channel_id_from_input(channel)
        self.chroma_client = get_chroma_client()

    def init_llm(self, prompt: str):
        messages = self.start_llm(prompt)
        print(messages[-1]["content"])
        
        while True:
            user_input = input("> ")
            if user_input == "exit":
                sys.exit(0)
            messages.append({"role": "user", "content": user_input})
            messages = self.continue_llm(messages)
            print(messages[-1]["content"])

    def start_llm(self, prompt: str) -> list:
        try:
            context = self.create_context(prompt)
            user_str = f"Context: {context}\n\n---\n\nQuestion: {prompt}\nAnswer:"
            system_prompt = """
                            Answer the question based on the context below, The context are 
                            subtitles and timestamped links from videos related to the question. 
                            In your answer, provide the link to the video where the answer can 
                            be found. and if the question can't be answered based on the context, 
                            say \"I don't know\" AND ONLY I don't know\n\n
                            """
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_str},
            ]
            
            response_text = self.get_completion(messages)
            
            if "i don't know" in response_text.lower():
                expanded_query = self.get_expand_context_query(messages)
                expanded_context = self.create_context(expanded_query)
                messages.append({
                    "role": "user",
                    "content": f"Okay here is some more context:\n---\n\n{expanded_context}\n\n---"
                })
                response_text = self.get_completion(messages)
            
            messages.append({
                "role": "assistant",
                "content": response_text
            })
            return messages
        
        except Exception as e:
            traceback.print_exc()
            print(f"Error: {e}")
            sys.exit(1)

    def continue_llm(self, messages: list) -> list:
        try:
            response_text = self.get_completion(messages)
            
            if "i don't know" in response_text.lower():
                expanded_query = self.get_expand_context_query(messages)
                print(f"Expanded query: {expanded_query}")
                expanded_context = self.create_context(expanded_query)
                messages.append({
                    "role": "user",
                    "content": f"Okay here is some more context:\n---\n\n{expanded_context}\n\n---"
                })
                response_text = self.get_completion(messages)
            
            messages.append({
                "role": "assistant",
                "content": response_text
            })
            return messages
        
        except Exception as e:
            traceback.print_exc()
            print(f"Error: {e}")
            sys.exit(1)

    def create_context(self, text: str) -> str:
        collection = self.chroma_client.get_collection(name="subEmbeddings")
        search_embedding = get_embedding(text, "text-embedding-ada-002", self.openai_client)
        scope_options = {"channel_id": self.channel_id}
        
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
        
        return self.format_context(res)

    def get_expand_context_query(self, messages: list) -> str:
        try:
            system_prompt = """
                            Your task is to generate a question to input into a vector search 
                            engine of youtube subitles to find strings that can answer the question
                            asked in the previous message.
                            """
            formatted_context = self.format_message_history_context(messages)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": formatted_context},
            ]
            
            return self.get_completion(messages)
        
        except Exception as e:
            traceback.print_exc()
            print(e)
            sys.exit(1)

    def get_completion(self, messages: list) -> str:
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0,
                max_tokens=2000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
            )
            return response.choices[0].message.content
        
        except Exception as e:
            traceback.print_exc()
            print(f"Error: {e}")
            sys.exit(1)

    @staticmethod
    def format_message_history_context(messages: list) -> str:
        formatted_context = ""
        for message in messages:
            if message["role"] == "system":
                continue
            role = message["role"]
            content = message["content"]
            formatted_context += f"{role}: {content}\n"
        return formatted_context

    @staticmethod
    def format_context(chroma_res: list) -> str:
        formatted_context = ""
        for obj in chroma_res:
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
