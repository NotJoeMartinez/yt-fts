import csv, rich

from yt_fts.db_utils import (
    search_channel, search_video, search_all, 
    get_channel_name_from_video_id, get_title_from_db
    )

from yt_fts.utils import time_to_secs, show_message

def export_search(text, file_name, search_id="",scope=""):
    """
    Calls search functions and exports the results to a csv file
    """

    if scope == "all":
        res = search_all(text)

    if scope == "video":
        res = search_video(search_id, text)

    if scope == "channel":
        res = search_channel(search_id, text)

    if len(res) == 0:
        show_message("no_matches_found")
        exit()

    with open(file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Channel Name','Video Title', 'Quote', 'Time Stamp', 'Link'])
        
        for quote in res:
            video_id = quote["video_id"]
            channel_name = get_channel_name_from_video_id(video_id)
            video_title = get_title_from_db(video_id)
            time_stamp = quote["timestamp"]
            subs = quote["text"]
            time = time_to_secs(time_stamp) 

            writer.writerow([channel_name,video_title, subs.strip(), time_stamp, f"https://youtu.be/{video_id}?t={time}"])
    
    console = rich.console.Console()

    console.print(f"[bold]{len(res)}[/bold] matches found for text: \"[italic]{text}[/italic]\"")
    console.print(f"Exported to [green][bold]{file_name}[/bold][/green]")