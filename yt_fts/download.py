import yt_dlp
import shutil
import tempfile
import sys
import re
import os
import sqlite3
import json
import requests

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from .config import get_db_path
from .db_utils import add_video, add_channel_info, check_if_channel_exists
from .utils import parse_vtt, get_date, handle_reject_consent_cookie

from rich.progress import track
from rich.console import Console

class DownloadHandler:
    def __init__(self):
        self.console = Console()
        self.session = None

    def init_session(self, url):
        s = requests.session()
        handle_reject_consent_cookie(url, s)
        return s


    def get_channel_id(self, url):

        try:
            session = self.session
            res = session.get(url)
            if res.status_code == 200:
                html = res.text
                soup = BeautifulSoup(html, 'html.parser')
                meta_tag = soup.find('meta', property='og:url')
                if meta_tag:
                    content_url = meta_tag['content']
                else:
                    self.console.print('Error: Could not find channel url')
                    return None

                channel_id = content_url.split('/')[-1]
                return channel_id

        except Exception as e:
            self.console.print(f'Error: {e}')
            sys.exit(1)

    def get_channel_name(self, channel_id, s):
        res = s.get(f"https://www.youtube.com/channel/{channel_id}/videos")

        if res.status_code == 200:
            html = res.text
            soup = BeautifulSoup(html, 'html.parser')
            script = soup.find('script', type='application/ld+json')

            try:
                with self.console.status("[bold green]Parsing JSON...") as status:
                    data = json.loads(script.string)
            except:
                print("json parse failed retrying with escaped backslashes")
                script = script.string.replace('\\', '\\\\')
                data = json.loads(script)

            channel_name = data['itemListElement'][0]['item']['name']
            return channel_name
        else:
            print("we couldn't get the channel name")
            return None

    def get_videos_list(self, channel_url):
        with self.console.status("[bold green]Scraping video urls ...") as status:
            ydl_opts = {
                'extract_flat': True,
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                list_of_videos_urls = [entry['id'] for entry in info['entries']]

            streams_url = channel_url.replace("/videos", "/streams")
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    streams_info = ydl.extract_info(streams_url, download=False)
                    live_stream_urls = [entry['id'] for entry in streams_info['entries']]
                    if len(live_stream_urls) > 0:
                        list_of_videos_urls.extend(live_stream_urls)
            except Exception:
                self.console.print("[bold red]No streams found")

        return list_of_videos_urls

    def get_playlist_data(self, playlist_url):
        with self.console.status("[bold green]Scraping video urls...") as status:
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                playlist_data = []
                for entry in info['entries']:
                    vid_obj = {
                        'channel_name': entry['channel'],
                        'channel_id': entry['channel_id'],
                        'video_id': entry['id'],
                        'channel_url': f"https://www.youtube.com/channel/{entry['channel_id']}/videos",
                        'video_url': f"https://youtu.be/{entry['id']}"
                    }
                    playlist_data.append(vid_obj)

        return playlist_data

    def download_vtts(self, number_of_jobs, video_ids, language, tmp_dir):
        executor = ThreadPoolExecutor(number_of_jobs)
        futures = []

        for video_id in video_ids:
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            future = executor.submit(self.get_vtt, tmp_dir, video_url, language)
            futures.append(future)

        for i in range(len(video_ids)):
            futures[i].result()

    def quiet_progress_hook(self, d):
        if d['status'] == 'finished':
            print(f" -> {d['filename']}")

    def get_vtt(self, tmp_dir, video_url, language):
        try: 
            ydl_opts = {
                'outtmpl': f'{tmp_dir}/%(id)s',
                'writeinfojson': True,
                'writeautomaticsub': True,
                'subtitlesformat': 'vtt',
                'skip_download': True,
                'subtitleslangs': [language, '-live_chat'],
                'quiet': True,
                'progress_hooks': [self.quiet_progress_hook]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

        except Exception as e:
            self.console.print(f"Failed to get: {video_url}\n{e}")

    def vtt_to_db(self, dir_path):
        items = os.listdir(dir_path)
        file_paths = [os.path.join(dir_path, item) for item in items if item.endswith('.vtt')]

        con = sqlite3.connect(get_db_path())
        cur = con.cursor()

        for vtt in track(file_paths, description="Adding subtitles to database..."):
            base_name = os.path.basename(vtt)

            vid_id = base_name.split('.')[0]
            vid_url = f"https://youtu.be/{vid_id}"

            vid_json_path = os.path.join(os.path.dirname(vtt), f'{vid_id}.info.json')

            with open(vid_json_path, 'r', encoding='utf-8', errors='ignore') as f:
                vid_json = json.load(f)

            vid_title = vid_json['title']
            vid_date = get_date(vid_json['upload_date'])
            channel_id = vid_json['channel_id']

            add_video(channel_id, vid_id, vid_title, vid_url, vid_date)

            vtt_json = parse_vtt(vtt)

            for sub in vtt_json:
                start_time = sub['start_time']
                stop_time = sub['stop_time']
                text = sub['text']
                cur.execute(f"INSERT INTO Subtitles (video_id, start_time, stop_time, text) VALUES (?, ?, ?, ?)",
                            (vid_id, start_time, stop_time, text))

            con.commit()

        con.close()

    def validate_channel_url(self, channel_url):
        channel_url = channel_url.strip('/')
        parsed = urlparse(channel_url)
        domain = parsed.netloc
        path = parsed.path.split('/')

        if not domain.endswith('youtube.com'):
            self.console.print("")
            self.console.print(f"[bold red]Error:[/bold red] Invalid channel domain: [blue]{domain}[/blue]")
            self.console.print("")
            sys.exit(1)

        if len(path) < 2:
            self.console.print("")
            self.console.print(f"[bold red]Error:[/bold red] Invalid channel url: [blue]{channel_url}[/blue]")
            self.console.print("")
            sys.exit(1)

        if path[1].startswith("@"):
            return f"https://www.youtube.com/{path[1]}/videos"

        if path[1] == "channel":
            return f"https://www.youtube.com/channel/{path[2]}/videos"

        self.console.print("")
        self.console.print(f"[bold red]Error:[/bold red] Unknown url format: [blue]{channel_url}[/blue]")
        self.console.print("")
        self.console.print("Please use one of the following formats:")
        self.console.print("")
        self.console.print("    - https://www.youtube.com/[yellow]@channelname[/yellow]")
        self.console.print("    - https://www.youtube.com/channel/[yellow]channelId[/yellow]")
        self.console.print("")
        sys.exit(1)

    def download_channel(self, channel_id, channel_name, language, number_of_jobs, s):
        with tempfile.TemporaryDirectory() as tmp_dir:
            channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
            list_of_videos_urls = self.get_videos_list(channel_url)

            self.console.print(f"[green][bold]Downloading [red]{len(list_of_videos_urls)}[/red] vtt files[/bold][/green]\n")
            self.download_vtts(number_of_jobs, list_of_videos_urls, language, tmp_dir)
            add_channel_info(channel_id, channel_name, channel_url)
            self.vtt_to_db(tmp_dir)
        return True

    def download_playlist(self, playlist_url, s, language=None, number_of_jobs=None):
        playlist_data = self.get_playlist_data(playlist_url)

        for video in playlist_data:
            channel_name = video["channel_name"]
            channel_id = video["channel_id"]
            channel_url = video["channel_url"]
            if not check_if_channel_exists(channel_id):
                add_channel_info(channel_id, channel_name, channel_url)

        video_ids = list(set(video["video_id"] for video in playlist_data))

        with tempfile.TemporaryDirectory() as tmp_dir:
            self.console.print(f"[green][bold]Downloading [red]{len(playlist_data)}[/red] vtt files[/bold][/green]\n")
            self.download_vtts(number_of_jobs, video_ids, language, tmp_dir)
            self.vtt_to_db(tmp_dir)