import csv
import datetime
import os

from rich.console import Console

from .utils import time_to_secs, show_message
from .db_utils import (
    search_channel,
    search_video,
    search_all,
    get_channel_name_from_video_id,
    get_metadata_from_db,
    get_channel_id_from_input,
    get_vid_ids_by_channel_id,
    get_subs_by_video_id,
    get_channel_name_from_id
)


class ExportHandler:
    def __init__(self, scope: str ="channel", format: str ="txt", channel: str | None = None) -> None:
        self.console = Console()
        self.format = format
        self.scope = scope

        if channel is not None:
            self.channel_id = get_channel_id_from_input(channel)
            self.channel_name = get_channel_name_from_id(self.channel_id)
        else:
            self.channel_id = None
            self.channel_name = None

        
    def export(self) -> None:
        console = self.console
        output_dir = None

        with console.status(f"[bold green]Exporting {self.channel_name}...") as status:

            if self.format == "txt":
                output_dir = self.export_channel_to_txt(self.channel_id)
            if self.format == "vtt":
                output_dir = self.export_channel_to_vtt(self.channel_id)

        if output_dir is not None:
            console.print(f"Exported to [green][bold]{output_dir}[/bold][/green]")



    def export_fts(self, text: str, scope: str, channel_id: str | None = None, video_id: str | None = None) -> None:
        """
        Calls search functions and exports the results to a csv file
        """
        console = self.console

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        if scope == "all":
            file_name = f"all_{timestamp}.csv"
            res = search_all(text)
        if scope == "video":
            file_name = f"video_{video_id}_{timestamp}.csv"
            res = search_video(video_id, text)
        if scope == "channel":
            channel_id = get_channel_id_from_input(channel_id)
            file_name = f"channel_{channel_id}_{timestamp}.csv"
            res = search_channel(channel_id, text)

        if len(res) == 0:
            show_message("no_matches_found")
            return None

        with open(file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Channel Name', 'Video Title', 'Date', 'Quote', 'Time Stamp', 'Link'])

            for quote in res:
                video_id = quote["video_id"]
                channel_name = get_channel_name_from_video_id(video_id)
                metadata = get_metadata_from_db(video_id)
                time_stamp = quote["start_time"]
                subs = quote["text"]
                time = time_to_secs(time_stamp)

                writer.writerow([
                    channel_name,
                    metadata['video_title'],
                    metadata['video_date'],
                    subs.strip(),
                    time_stamp,
                    f"https://youtu.be/{video_id}?t={time}"
                ])


        console.print(f"[bold]{len(res)}[/bold] matches found for text: \"[italic]{text}[/italic]\"")
        console.print(f"Exported to [green][bold]{file_name}[/bold][/green]")


    def export_vector_search(self, res: list, search: str, scope: str) -> None:
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
            writer.writerow(['Channel Name', 'Video Title', 'Quote', 'Time Stamp', 'Link'])

            for quote in res:
                channel_name = quote["channel_name"]
                video_title = quote["video_title"]
                time_stamp = quote["start_time"]
                subs = quote["subs"]
                link = quote["link"]

                writer.writerow([channel_name, video_title, subs.strip(), time_stamp, link])

        console = Console()

        console.print(f"[bold]{len(res)}[/bold] matches found for text: \"[italic]{search}[/italic]\"")
        console.print(f"Exported to [green][bold]{file_name}[/bold][/green]")


    def export_channel_to_txt(self, channel_id: str) -> str | None:
        console = self.console

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


    def export_channel_to_vtt(self, channel_id: str) -> str | None:
        console = self.console

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
