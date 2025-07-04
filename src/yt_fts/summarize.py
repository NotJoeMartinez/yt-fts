import os
import json
import sys
import sqlite3
import tempfile
import textwrap

import yt_dlp
from rich.console import Console
from rich.markdown import Markdown
from urllib.parse import urlparse, parse_qs

from .config import get_db_path
from .utils import parse_vtt
from .db_utils import get_title_from_db, get_channel_name_from_video_id

class SummarizeHandler:
    def __init__(self, openai_client, model, input_video):

        self.console = Console()
        self.model = model
        self.openai_client = openai_client
        self.input_video = input_video
        self.max_width = 80

        self.video_title = ''
        self.channel_name = ''

        if "https" in input_video:
            self.video_id = self.get_video_id_from_url(input_video)
        else:
            self.video_id = input_video
        
        if not self.video_in_database(self.video_id):
            self.transcript_text = self.download_transcript()
        else:
            self.video_title = get_title_from_db(self.video_id)
            self.channel_name = get_channel_name_from_video_id(self.video_id)
            self.transcript_text = self.get_transcript_from_database(self.video_id)
 
    def summarize_video(self):
        console = self.console
        video_id = self.video_id


        system_prompt = f"""
        Summarize the transcript of the YouTube video given below.
        - Provide valid youtube timestamped urls for key points in the video 
            using the format: [timestamp](https://youtu.be/{video_id}?t=[seconds])


        Video Title: {self.video_title}
        Channel Name: {self.channel_name}
        Transcript:
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self.transcript_text},
        ]


        with console.status("[green]Generating summary..."):
            summary_text = self.get_completion(messages)
            md = Markdown(summary_text)
            console.print("")
            console.print(md)
    

    def get_completion(self, messages: list) -> str:
        console = self.console
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

            response_text = response.choices[0].message.content
            wrapped_text = self.wrap_text(response_text)
            return wrapped_text

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)
        
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
                    'no_warnings': True,
                    'progress_hook': [self.quiet_progress_hook],
                }

                # if self.cookies_from_browser is not None:
                #     ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                

                items = os.listdir(tmp_dir)
                vtt_files = [os.path.join(tmp_dir, item) for item in items if item.endswith('.vtt')]
                json_files = [os.path.join(tmp_dir, item) for item in items if item.endswith('.info.json')]

                if len(vtt_files) == 0:
                    console.print("[red]Error:[/red] "
                                  "Failed to download subtitles.")
                    sys.exit(1)

                try:
                    with open(json_files[0], 'r') as f:
                        data = json.load(f)
                        title = data['title']
                        channel = data['uploader']
                        self.video_title = title
                        self.channel_name = channel
                except Exception as e:
                    console.print(f"[yellow]Warning:[/yellow] {e}")
                    pass

                
                vtt_file_path = vtt_files[0]
                vtt_json = parse_vtt(vtt_file_path)
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

    def wrap_text(self, text: str) -> str:
        lines = text.split('\n')
        wrapped_lines = []

        for line in lines:
            # If the line is a code block, don't wrap it
            if line.strip().startswith('```') or line.strip().startswith('`'):
                wrapped_lines.append(line)
            else:
                # Wrap the line
                wrapped = textwrap.wrap(line, width=self.max_width, break_long_words=False, replace_whitespace=False)
                wrapped_lines.extend(wrapped)

        # Join the wrapped lines back together
        return "  \n".join(wrapped_lines)

