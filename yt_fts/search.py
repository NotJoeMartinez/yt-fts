
from .download import get_channel_id_from_input
from .db_utils import * 
from .utils import *
from rich.console import Console


# full text search
def fts_search(text, scope, channel_id=None, video_id=None, limit=None):
    """
    Calls search functions and prints the results 
    """

    if scope == "all":
        res = search_all(text, limit)
    
    if scope == "channel":
        channel_id = get_channel_id_from_input(channel_id)
        res = search_channel(channel_id, text, limit)
    
    if scope == "video":
        res = search_video(video_id, text, limit)

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
        time_stamp = quote["start_time"]
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
    
    num_matches = len(res)
    num_channels = len(set(channel_names))  
    num_videos = len(set([quote["video_id"] for quote in res]))

    summary_str = f"Found [bold]{num_matches}[/bold] matches in [bold]{num_videos}[/bold] videos from [bold]{num_channels}[/bold] channel"

    if num_channels > 1:
        summary_str += "s"

    console.print(summary_str) 