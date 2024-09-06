import os
import sys
import sqlite3
import tempfile

import yt_dlp
from rich.console import Console
from rich.markdown import Markdown
from urllib.parse import urlparse, parse_qs

from .config import get_db_path
from .utils import parse_vtt

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
# https://youtu.be/YWClyxKcSG0?t=142


class SummarizeHandler:
    def __init__(self, openai_client, model, input_video):

        self.console = Console()
        self.model = model
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
        else:
            transcript_text = self.download_transcript()

        system_prompt = f"""
        Summarize the transcript of the YouTube video given below.
        Provide valid youtube timestamped urls for key points
        in the video using the format: https://youtu.be/{video_id}?t=[seconds]

        Transcript:
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript_text},
        ]

        summary_text = self.get_completion(messages)
        md = Markdown(summary_text)
        self.console.print(md)
    

    def get_completion(self, messages: list) -> str:
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                max_tokens=2000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
            )
            return response.choices[0].message.content

        except Exception as e:
            self.display_error(e)
        
    def download_transcript(self):
        console = self.console
        video_id = self.video_id
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            console.print(f"Downloading subtitles for: {video_url}")
            with tempfile.TemporaryDirectory() as tmp_dir:
                ydl_opts = {
                    'outtmpl': f'{tmp_dir}/%(id)s',
                    'writeinfojson': True,
                    'writeautomaticsub': True,
                    'subtitlesformat': 'vtt',
                    'skip_download': True,
                    'subtitleslangs': ['en', '-live_chat'],
                    'quiet': True,
                    'progress_hooks': [self.quiet_progress_hook],
                }

                # if self.cookies_from_browser is not None:
                #     ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                

                items = os.listdir(tmp_dir)
                file_paths = [os.path.join(tmp_dir, item) for item in items if item.endswith('.vtt')]

                if len(file_paths) == 0:
                    console.print("[red]Error:[/red] "
                                  "Failed to download subtitles.")
                    sys.exit(1)
                
                file_path = file_paths[0]
                vtt_json = parse_vtt(file_path)
                transcript = ""
                for subtitle in vtt_json:
                    start_time = subtitle['start_time'][:-4]
                    text = subtitle['text'].strip()
                    if len(text) == 0:
                        continue
                    transcript += f"{start_time}: {text}\n"

                return transcript

        except Exception as e:
            console.print(f"Failed to get: {video_id}\n{e}")
            sys.exit(1)

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

   
    def quiet_progress_hook(self, d):
        console = self.console
        if d['status'] == 'finished':
            console.print(f" -> \"{d['filename']}\"")

