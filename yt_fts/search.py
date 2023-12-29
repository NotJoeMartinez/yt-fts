
from .download import get_channel_id_from_input
from .db_utils import * 
from .utils import *
from rich.console import Console


# full text search
def fts_search(text, scope, channel_id=None, video_id=None, limit=None):
    """
    Calls search functions and prints the results 
    """
    console = Console()

    if scope == "all":
        res = search_all(text, limit)
    
    if scope == "channel":
        channel_id = get_channel_id_from_input(channel_id)
        res = search_channel(channel_id, text, limit)
    
    if scope == "video":
        res = search_video(video_id, text, limit)

    if len(res) == 0:
        console.print("- Try shortening the search to specific words")
        console.print("- Try using the wildcard operator [bold]*[/bold] to search for partial words")
        console.print("- Try using the [bold]OR[/bold] operator to search for multiple words")
        if len(text.split(" ")) > 1:
            example_or = text.replace(" ", " OR ")
            console.print(f"    - EX: \"[bold]{example_or}[/bold]\"")
        else: 
            console.print(f"    - EX: \"[bold]foo OR [bold]bar[/bold]\"")
        exit()

    return res


# pretty print search results
def print_fts_res(res, query):

    console = Console()

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

        quote_match["video_title"] = get_title_from_db(video_id)
        quote_match["subs"] = bold_query_matches(quote["text"].strip(), query)
        quote_match["time_stamp"] = time_stamp
        quote_match["video_id"] = video_id
        quote_match["link"] = link 

        fts_res.append(quote_match)

    # sort by channel name
    fts_res = sorted(fts_res, key=lambda x: x["channel_name"])

    console.print("")
    for quote in fts_res: 

        console.print(f"[magenta][italic]\"[link={quote['link']}]{quote['subs']}[/link]\"[/italic][/magenta]")
        console.print(f"    Channel: {quote['channel_name']}",style="none")
        console.print(f"    Title: {quote['video_title']}")
        console.print(f"    Time Stamp: {quote['time_stamp']}")
        console.print(f"    Video ID: {quote['video_id']}")
        console.print(f"    Link: {quote['link']}")
        console.print("")
    
    num_matches = len(res)
    num_channels = len(set(channel_names))  
    num_videos = len(set([quote["video_id"] for quote in res]))

    summary_str = f"Found [bold]{num_matches}[/bold] matches in [bold]{num_videos}[/bold] videos from [bold]{num_channels}[/bold] channel"

    if num_channels > 1:
        summary_str += "s"

    console.print(summary_str) 