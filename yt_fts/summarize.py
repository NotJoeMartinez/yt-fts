import sys
import sqlite3
from urllib.parse import urlparse, parse_qs

from rich.console import Console
from .config import get_db_path

# determine if input_video is url or video id 
# if it's a url get the video id 
# check if the video id is in database
# if video id is in database get the full transcript
# if the video id is not in the database download the transcript
# feed the transcript to an llm and print the summary

# https://www.youtube.com/watch?v=Xjk6d5fPs_k
# https://youtu.be/Xjk6d5fPs_k?si=BBb2URutUT2gG4th
# https://youtu.be/Xjk6d5fPs_k
# https://www.youtube.com/watch?v=Xjk6d5fPs_k&si=BBb2URutUT2gG4th


class SummarizeHandler:
    def __init__(self, openai_client, input_video):

        self.console = Console()
        self.openai_client = openai_client
        self.input_video = input_video

        if "https" in input_video:
            self.video_id = self.get_video_id_from_url(input_video)
        else:
            self.video_id = input_video
 
    def summarize_video(self):
        console = self.console
        video_id = self.video_id

        if self.video_in_database(video_id):

            transcript_text = self.get_transcript_from_database(video_id)


        

    def get_transcript_from_database(self, video_id) -> str:

        console = self.console
        try:
            conn = sqlite3.connect(get_db_path())
            curr = conn.cursor()
            curr.execute(
                """
                SELECT 
                    start_time, text
                FROM
                    Subtitles
                WHERE
                    video_id = ?
                """, (video_id,)
            )
            res = curr.fetchall()
            transcript = ""
            for row in res:
                start_time, text = row
                text = text.strip()
                if len(text) == 0:
                    continue
                transcript += f"{start_time[:-4]}: {text}\n"
            conn.close()
            return transcript
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)
        finally:
            conn.close()

    def video_in_database(self, video_id) -> bool:
        console = self.console
        try:
            conn = sqlite3.connect(get_db_path())
            curr = conn.cursor()
            curr.execute(
                """
                SELECT 
                    count(*)
                FROM
                    Videos
                WHERE
                    video_id = ?
                """, (video_id,)
            )
            count = curr.fetchone()[0]
            conn.close()
            if count > 0:
                return True
            return False
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)
        finally:
            conn.close()
        

    def get_video_id_from_url(self, video_url):
        console = self.console
        video_url = video_url.strip('/')
        parsed = urlparse(video_url)
        domain = parsed.netloc
        path = parsed.path.split('/')
        query = parse_qs(parsed.query)

        valid_domains = ["youtube.com", "youtu.be", "www.youtube.com"]

        if domain not in valid_domains:
            console.print("[red]Error:[/red] "
                          f"Invalid URL, domain \"{domain}\" not supported.")
            sys.exit(1)

        
        if domain in ["youtube.com", "www.youtube.com"] and "watch" in path:
            video_id = query.get('v', [None])[0]
        elif domain == "youtu.be":
            video_id = path[-1]
        else:
            console.print("[red]Error:[/red] "
                          "Invalid URL, please provide a valid YouTube video URL.")
            sys.exit(1)

        if video_id:
            return video_id
        
        console.print("[red]Error:[/red] "
                      "Invalid URL, please provide a valid YouTube video URL.")
        sys.exit(1)

   