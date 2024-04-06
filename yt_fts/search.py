from pprint import pprint
from .download import get_channel_id_from_input
from .db_utils import * 
from .utils import *
from rich.console import Console
from rich.text import Text


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


    """
    need to resturcutre the data to be able to print it in a nice way

    fts_dict = {
        "channel_name": {
            "video_name": [
                {
                    "quote": "quote",
                    "time_stamp": "time_stamp",
                    "link": "link"
                }
            ]
        }
    }

    original format is:
    fts_res = [
        {
            "channel_name": "channel_name",
            "video_name": "video_name",
            "quote": "quote",
            "time_stamp": "time_stamp",
            "link": "link"
        }
    ]
    """

    fts_dict = {}
    for quote in fts_res:
        channel_name = quote["channel_name"]
        video_name = quote["video_title"]
        quote_data = {
            "quote": quote["subs"],
            "time_stamp": quote["time_stamp"],
            "link": quote["link"]
        }
        if channel_name not in fts_dict:
            fts_dict[channel_name] = {}
        if video_name not in fts_dict[channel_name]:
            fts_dict[channel_name][video_name] = []
        fts_dict[channel_name][video_name].append(quote_data)
    

    # Sort the list by the total number of quotes in each channel
    channel_list = list(fts_dict.items())
    channel_list.sort(key=lambda x: sum(len(quotes) for quotes in x[1].values()))

    for channel_name, videos in channel_list:
        console.print(f"[spring_green2][bold]{channel_name}[/bold][/spring_green2]")
        console.print("")

        # Sort the list by the number of quotes in each video
        video_list = list(videos.items())
        video_list.sort(key=lambda x: len(x[1]))

        for video_name, quotes in video_list:
            console.print(f"    [bold][blue]{video_name}[/blue][/bold]")
            console.print("")

            # Sort the quotes by timestamp
            quotes.sort(key=lambda x: x['time_stamp'])

            for quote in quotes:
                link = quote["link"]
                time_stamp = quote["time_stamp"]
                words = quote["quote"]
                console.print(f"       [grey62][link={link}]{time_stamp}[/link][/grey62] -> [italic][white]\"{words}\"[/white][/italic]")
            console.print("")

    num_matches = len(res)
    num_channels = len(set(channel_names))  
    num_videos = len(set([quote["video_id"] for quote in res]))

    summary_str = f"Found [bold]{num_matches}[/bold] matches in [bold]{num_videos}[/bold] videos from [bold]{num_channels}[/bold] channel"

    if num_channels > 1:
        summary_str += "s"

    console.print(summary_str) 