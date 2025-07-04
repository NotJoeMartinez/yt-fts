import sys
import textwrap
import traceback

from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from .get_embeddings import EmbeddingsHandler
from ..utils import time_to_secs
from ..config import get_chroma_client
from ..db_utils import (
    get_channel_id_from_input,
    get_channel_name_from_video_id,
    get_title_from_db
)


class LLMHandler:
    def __init__(self, openai_api_key: str, channel: str) -> None:
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.channel_id = get_channel_id_from_input(channel)
        self.chroma_client = get_chroma_client()
        self.console = Console()
        self.max_width = 80

    def init_llm(self, prompt: str) -> None:
        messages = self.start_llm(prompt)
        self.display_message(messages[-1]["content"], "assistant")

        while True:
            user_input = Prompt.ask("> ")
            if user_input.lower() == "exit":
                self.console.print("Bye!", style="bold red")
                sys.exit(0)
            messages.append({"role": "user", "content": user_input})
            messages = self.continue_llm(messages)
            self.display_message(messages[-1]["content"], "assistant")

    def display_message(self, content: str, role: str) -> None:
        if role == "assistant":
            wrapped_content = self.wrap_text(content)
            md = Markdown(wrapped_content)
            self.console.print(md)
        else:
            wrapped_content = self.wrap_text(content)
            self.console.print(Text(wrapped_content, style="bold blue"))

    def wrap_text(self, text: str) -> str:
        lines = text.split('\n')
        wrapped_lines = []

        for line in lines:
            # If the line is a code block, don't wrap it
            if line.strip().startswith('```') or line.strip().startswith('`'):
                wrapped_lines.append(line)
            else:
                # Wrap the line
                wrapped = textwrap.wrap(line, width=self.max_width, break_long_words=False, replace_whitespace=False)
                wrapped_lines.extend(wrapped)

        # Join the wrapped lines back together
        return "  \n".join(wrapped_lines)

    def start_llm(self, prompt: str) -> list:
        try:
            context = self.create_context(prompt)
            user_str = f"Context: {context}\n\n---\n\nQuestion: {prompt}\nAnswer:"
            system_prompt = """
                            Answer the question based on the context below, and if the question can't be answered based on the context, 
                            say \"I don't know\"\n\n
                            """
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_str},
            ]

            response_text = self.get_completion(messages)


            if response_text.lower().startswith("i don't know"):
                expanded_query = self.get_expand_context_query(messages)
                self.console.print(f"Expanding context with query: [italic]{expanded_query}[/italic]")
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
            self.display_error(e)

    def continue_llm(self, messages: list) -> list:
        try:
            response_text = self.get_completion(messages)

            if response_text.lower().startswith("i don't know"): 
                expanded_query = self.get_expand_context_query(messages)
                self.console.print(f"Expanding context with query: [italic]{expanded_query}[/italic]")
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
            self.display_error(e)

    def display_error(self, error: Exception) -> None:
        self.console.print(Panel(str(error), title="Error", border_style="red"))
        traceback.print_exc()
        sys.exit(1)

    def create_context(self, text: str) -> str:
        collection = self.chroma_client.get_collection(name="subEmbeddings")

        embeddings_handler = EmbeddingsHandler()
        search_embedding = embeddings_handler.get_embedding(text, "text-embedding-ada-002", self.openai_client)
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
            date_posted = metadata[i]["video_date"]
            title = get_title_from_db(video_id)

            match = {
                "date_posted": date_posted,
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
                            engine of youtube subtitles to find strings that can answer the question
                            asked in the previous message. Just respond with the question you would
                            ask to find the answer.
                            """
            formatted_context = self.format_message_history_context(messages)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": formatted_context},
            ]

            return self.get_completion(messages)

        except Exception as e:
            self.display_error(e)

    def get_completion(self, messages: list) -> str:
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.5,
                max_tokens=2000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
            )
            return response.choices[0].message.content

        except Exception as e:
            self.display_error(e)

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
                ---
                Video Title: {obj["video_title"]}
                Date Posted: {obj["date_posted"]}
                Link: {obj["link"]}
                ---

                {obj["subs"]}

                ----------------------------------------
            """

            formatted_context += tmp
        return formatted_context
