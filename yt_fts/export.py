import csv, datetime, os

from rich.console import Console

from .db_utils import (
    search_channel, search_video, search_all, 
    get_channel_name_from_video_id, get_title_from_db
    )

from .utils import time_to_secs, show_message

def export_fts(text, scope, channel_id=None, video_id=None):
    """
    Calls search functions and exports the results to a csv file
    """

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    if scope == "all":
        file_name = f"all_{timestamp}.csv"
        res = search_all(text)
    if scope == "video":
        file_name = f"video_{video_id}_{timestamp}.csv"
        res = search_video(video_id, text)
    if scope == "channel":
        from .download import get_channel_id_from_input
        channel_id = get_channel_id_from_input(channel_id)
        file_name = f"channel_{channel_id}_{timestamp}.csv"
        res = search_channel(channel_id, text)


    if len(res) == 0:
        show_message("no_matches_found")
        return None

    with open(file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Channel Name','Video Title', 'Quote', 'Time Stamp', 'Link'])
        
        for quote in res:
            video_id = quote["video_id"]
            channel_name = get_channel_name_from_video_id(video_id)
            video_title = get_title_from_db(video_id)
            time_stamp = quote["start_time"]
            subs = quote["text"]
            time = time_to_secs(time_stamp) 

            writer.writerow([channel_name,video_title, subs.strip(), time_stamp, f"https://youtu.be/{video_id}?t={time}"])
    
    console = Console()

    console.print(f"[bold]{len(res)}[/bold] matches found for text: \"[italic]{text}[/italic]\"")
    console.print(f"Exported to [green][bold]{file_name}[/bold][/green]")


def export_vector_search(res, search, scope):

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # run semantic search based on scope
    if scope == "all":
        file_name = f"all_{timestamp}.csv"
    if scope == "video":
        file_name = f"video_{timestamp}.csv"
    if scope == "channel":
        channel_id = res[0]["channel_id"]
        file_name = f"channel_{channel_id}_{timestamp}.csv"

    with open(file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Channel Name','Video Title', 'Quote', 'Time Stamp', 'Link'])
        
        for quote in res:
            channel_name = quote["channel_name"] 
            video_title = quote["video_title"] 
            time_stamp = quote["start_time"]
            subs = quote["subs"]
            link = quote["link"]

            writer.writerow([channel_name,video_title, subs.strip(), time_stamp, link])
    
    console = Console()

    console.print(f"[bold]{len(res)}[/bold] matches found for text: \"[italic]{search}[/italic]\"")
    console.print(f"Exported to [green][bold]{file_name}[/bold][/green]")



def export_transcripts(channel_id):
    """
    Exports video transcripts from a channel to a text file 
    """

    console = Console()

    from .download import get_channel_id_from_input
    channel_id = get_channel_id_from_input(channel_id)

    from .db_utils import get_vid_ids_by_channel_id, get_transcript_by_video_id 
    videos = get_vid_ids_by_channel_id(channel_id)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"channel_{channel_id}_{timestamp}.csv"

    for video in videos:

        video_id = video[0]
        transcript = get_transcript_by_video_id(video_id)
        str_transcript = ""
        for i in transcript:
            str_transcript += i[0] + "\n"
        with open(f"{video_id}.txt", "w") as f:
            f.write(str_transcript)


def export_channel_to_txt(channel_id):
    from .db_utils import  get_vid_ids_by_channel_id, get_subs_by_video_id
    console = Console()

    output_dir = f"{channel_id}_txt"

    if not os.path.exists(output_dir):
        os.mkdir(output_dir) 
    else:
        console.print(f"[red]Erorr:[/red] Directory [yellow]{output_dir}[/yellow] already exists")
        return None

    vid_ids = get_vid_ids_by_channel_id(channel_id)

    for vid_id in vid_ids:
        vid_id = vid_id[0]
        subs = get_subs_by_video_id(vid_id)
        str_subs = ""
        for sub in subs:
            str_subs += sub[2] + "\n"
        with open(f"{output_dir}/{vid_id}.txt", "w") as f:
            f.write(str_subs)

    return output_dir


def export_channel_to_vtt(channel_id):
    console = Console()
    from .db_utils import  get_vid_ids_by_channel_id, get_subs_by_video_id

    output_dir = f"{channel_id}_vtt"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    else:
        console.print(f"[red]Erorr:[/red] Directory [yellow]{output_dir}[/yellow] already exists")
        return None



    vid_ids = get_vid_ids_by_channel_id(channel_id)

    for vid_id in vid_ids:
        vid_id = vid_id[0]
        subs = get_subs_by_video_id(vid_id)

        with open(f"{output_dir}/{vid_id}.vtt", "w") as f:
            f.write("WEBVTT\n\n")

        for sub in subs:
            start_time = sub[0]
            end_time = sub[1]
            text = sub[2]

            with open(f"{output_dir}/{vid_id}.vtt", "a") as f:
                f.write(f"{start_time} --> {end_time}\n{text}\n\n")

    return output_dir