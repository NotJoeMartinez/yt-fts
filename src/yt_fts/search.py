import sys
import textwrap

from rich.console import Console
from openai import OpenAI

from .llm.get_embeddings import EmbeddingsHandler
from .export import ExportHandler
from .config import get_chroma_client
from .utils import time_to_secs, bold_query_matches
from .db_utils import (
    search_all,
    get_channel_id_from_input,
    search_channel,
    search_video,
    get_channel_name_from_video_id,
    get_metadata_from_db,
    get_title_from_db,
)


class SearchHandler:
    def __init__(self,
                 scope: str = 'all',
                 channel: str | None = None,
                 video_id: str | None = None,
                 export: bool = False,
                 limit: int | None = None,
                 openai_client: OpenAI | None = None
                 ) -> None:

        self.console = Console()
        self.scope = scope
        self.channel = channel
        self.video_id = video_id
        self.export = export
        self.limit = limit
        self.channel_id: str | None = None
        self.query = ''
        self.response = []
        self.openai_client = openai_client
        self.max_width = 80

    def full_text_search(self, query: str) -> None:

        console = self.console
        self.query = query

        if self.scope == 'all':
            self.res = search_all(query, self.limit)

        if self.scope == 'channel':
            self.channel_id = get_channel_id_from_input(self.channel)
            self.res = search_channel(self.channel_id, self.query, self.limit)

        if self.scope == 'video':
            self.res = search_video(self.video_id, self.query, self.limit)

        if len(self.res) == 0:
            console.print(f"[yellow]No matches found[/yellow]\n"
                          "- Try shortening the search to specific words\n"
                          "- Try using the wildcard operator [bold]*[/bold] to search for partial words\n"
                          "- Try using the [bold]OR[/bold] operator to search for multiple words\n"
                          "   - EX: \"foo OR bar\"")
            sys.exit(1)

        self.print_fts_res()
        if self.export:
            export_handler = ExportHandler()
            export_handler.export_fts(self.query, self.scope, self.channel, self.video_id)

        console.print(f"Query '{self.query}' ")
        console.print(f"Scope: {self.scope}")

    def vector_search(self, query: str) -> None:
        console = self.console
        self.query = query
        scope_options = {}
        if self.scope == "all":
            scope_options = {}
        if self.scope == "channel":
            scope_options = {"channel_id": get_channel_id_from_input(self.channel)}
        if self.scope == "video":
            scope_options = {"video_id": self.video_id}

        chroma_client = get_chroma_client()
        collection = chroma_client.get_collection(name="subEmbeddings")

        embeddings_handler = EmbeddingsHandler()
        search_embedding = embeddings_handler.get_embedding(query, "text-embedding-ada-002", self.openai_client)
        chroma_res = collection.query(
            query_embeddings=[search_embedding],
            n_results=self.limit,
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

        self.res = res

        self.print_vector_search_results()
        if self.export:
            export_handler = ExportHandler()
            export_handler.export_vector_search(self.res, self.query, self.scope)

        console.print(f"Query '{self.query}' ")
        console.print(f"Scope: {self.scope}")

    def print_fts_res(self) -> None:
        console = Console()

        query = self.query
        res = self.res
        fts_res = []
        channel_names = []

        for quote in res:
            quote_match = {}
            video_id = quote["video_id"]
            time_stamp = quote["start_time"]
            time = time_to_secs(time_stamp)
            link = f"https://youtu.be/{video_id}?t={time}"

            quote_match["channel_name"] = get_channel_name_from_video_id(video_id)
            channel_names.append(quote_match["channel_name"])

            quote_match["metadata"] = get_metadata_from_db(video_id)
            quote_match["subs"] = bold_query_matches(quote["text"].strip(), query)
            quote_match["time_stamp"] = time_stamp
            quote_match["video_id"] = video_id
            quote_match["link"] = link

            fts_res.append(quote_match)

        fts_dict = {}
        for quote in fts_res:
            channel_name = quote["channel_name"]
            metadata = quote["metadata"]
            video_name = metadata["video_title"]
            video_date = metadata["video_date"]
            video_id = quote["video_id"]
            quote_data = {
                "quote": quote["subs"],
                "time_stamp": quote["time_stamp"],
                "link": quote["link"]
            }
            if channel_name not in fts_dict:
                fts_dict[channel_name] = {}
            if (video_name, video_date) not in fts_dict[channel_name]:
                fts_dict[channel_name][(video_name, video_date, video_id)] = []
            fts_dict[channel_name][(video_name, video_date, video_id)].append(quote_data)

        # Sort the list by the total number of quotes in each channel
        channel_list = list(fts_dict.items())
        channel_list.sort(key=lambda x: sum(len(quotes) for quotes in x[1].values()))

        for channel_name, videos in channel_list:
            console.print(f"[spring_green2][bold]{channel_name}[/bold][/spring_green2]")
            console.print("")

            # Sort the list by the number of quotes in each video
            video_list = list(videos.items())
            video_list.sort(key=lambda x: len(x[1]))

            for (video_name, video_date, video_id), quotes in video_list:
                console.print(f"{video_id} ({video_date}) \"[bold][blue]{video_name}[/blue][/bold]\"")
                console.print("")

                # Sort the quotes by timestamp
                quotes.sort(key=lambda x: x['time_stamp'])

                for quote in quotes:
                    link = quote["link"]
                    time_stamp = quote["time_stamp"]
                    words = quote["quote"]
                    console.print(f"       [grey62][link={link}]{time_stamp}[/link][/grey62] -> "
                                  f"[italic][white]\"{words}\"[/white][/italic]")
                console.print("")

        num_matches = len(res)
        num_channels = len(set(channel_names))
        num_videos = len(set([quote["video_id"] for quote in res]))

        summary_str = f"Found [bold]{num_matches}[/bold] matches in [bold]{num_videos}[/bold] "
        summary_str += f"videos from [bold]{num_channels}[/bold] channel"

        if num_channels > 1:
            summary_str += "s"

        console.print(summary_str)

    def print_vector_search_results(self) -> None:
        console = Console()

        channel_names = []

        res = self.res
        query = self.query

        for match in reversed(res):
            distance = match["distance"]
            link = match["link"]
            text = bold_query_matches(match["subs"], query)
            time_stamp = match["start_time"]
            channel_id = match["channel_id"]
            video_id = match["video_id"]
            title = match["video_title"]
            channel_name = match["channel_name"]
            channel_names.append(channel_name)

            console.print(f"[magenta][italic]\"[link={link}]{text}[/link]\"[/italic][/magenta]\n")
            console.print(f"    Distance: {distance}", style="none")
            console.print(f"    Channel: {channel_name} - ({channel_id})", style="none")
            console.print(f"    Title: {title}")
            console.print(f"    Time Stamp: {time_stamp}")
            console.print(f"    Video ID: {video_id}")
            console.print(f"    Link: {link}")
            console.print("")

        num_matches = len(res)
        num_channels = len(set(channel_names))
        num_videos = len(set([quote["video_id"] for quote in res]))

        summary_str = f"Found [bold]{num_matches}[/bold] matches in "
        summary_str += f"[bold]{num_videos}[/bold] videos from [bold]{num_channels}[/bold] channel"

        if num_channels > 1:
            summary_str += "s"

        console.print(summary_str)

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
 
