from yt_fts.db_utils import * 
from yt_fts.utils import *

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

    for quote in res:
        video_id = quote["video_id"]
        subs = quote["text"]
        time_stamp = quote["timestamp"]
        video_title = get_title_from_db(video_id)
        channel_name = get_channel_name_from_video_id(video_id)
        time = time_to_secs(time_stamp) 

        print("")
        print(f"{channel_name}: \"{video_title}\"")
        print(f"") 
        print(f"    Quote: \"{subs.strip()}\"")
        print(f"    Time Stamp: {time_stamp}")
        print(f"    Video ID: {video_id}")
        print(f"    Link: https://youtu.be/{video_id}?t={time}\n")


def get_text_by_video_id(video_id, text):
    res = search_video(video_id, text)
    if len(res) == 0:
        show_message("no_matches_found")
        exit()
    
    for quote in res:
        subs = quote["text"]
        time_stamp = quote["timestamp"]
        video_title = get_title_from_db(video_id)
        channel_name = get_channel_name_from_video_id(video_id)
        time = time_to_secs(time_stamp) 

        print("")
        print(f"{channel_name}: \"{video_title}\"")
        print(f"") 
        print(f"    Quote: \"{subs.strip()}\"")
        print(f"    Time Stamp: {time_stamp}")
        print(f"    Video ID: {video_id}")
        print(f"    Link: https://youtu.be/{video_id}?t={time}\n")


