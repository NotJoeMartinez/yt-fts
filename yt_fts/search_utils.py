from yt_fts.db_utils import * 
from yt_fts.utils import *
from rich.console import Console


def print_search_results(res):

    """
    format of res:
    [
        {
            "channel_name": "channel_name",
            "video_title": "video_title",
            "subs": "subs",
            "time_stamp": "time_stamp",
            "video_id": "video_id",
            "link": "link"
        }
    ]
    """
    # sort by channel name
    res = sorted(res, key=lambda x: x["channel_name"])

    console = Console()

    console.print("")
    for quote in res: 

        console.print(f"[magenta][italic]\"[bold][link={quote['link']}]{quote['subs']}[/link][/bold]\"[/italic][/magenta]", style="magenta")
        print("")
        console.print(f"    Channel: {quote['channel_name']}",style="none")
        print(f"    Title: {quote['video_title']}")
        print(f"    Time Stamp: {quote['time_stamp']}")
        console.print(f"    Video ID: {quote['video_id']}")
        console.print(f"    Link: {quote['link']}")
        console.print("")
            


def get_text(channel_id, text):
    """
    Calls search functions and prints the results 
    """
    if channel_id == "all":
        res = search_all(text)
    else:
        res = search_channel(channel_id, text)

    if len(res) == 0:
        show_message("no_matches_found")
        exit()

    fts_res = []
    for quote in res:

        quote_match = {}

        video_id = quote["video_id"]
        time_stamp = quote["timestamp"]
        time = time_to_secs(time_stamp)
        link = f"https://youtu.be/{video_id}?t={time}"

        quote_match["channel_name"] = get_channel_name_from_video_id(video_id)
        quote_match["video_title"] = get_title_from_db(video_id)
        quote_match["subs"] = quote["text"].strip()
        quote_match["time_stamp"] = time_stamp
        quote_match["video_id"] = video_id
        quote_match["link"] = link 

        fts_res.append(quote_match)

    print_search_results(fts_res)

def get_text_by_video_id(video_id, text):
    res = search_video(video_id, text)
    if len(res) == 0:
        show_message("no_matches_found")
        exit()

    fts_res = []
    for quote in res:

        quote_match = {}

        video_id = quote["video_id"]
        time_stamp = quote["timestamp"]
        time = time_to_secs(time_stamp)
        link = f"https://youtu.be/{video_id}?t={time}"

        quote_match["channel_name"] = get_channel_name_from_video_id(video_id)
        quote_match["video_title"] = get_title_from_db(video_id)
        quote_match["subs"] = quote["text"].strip()
        quote_match["time_stamp"] = time_stamp
        quote_match["video_id"] = video_id
        quote_match["link"] = link 

        fts_res.append(quote_match)

    print_search_results(fts_res)
