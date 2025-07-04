import yt_dlp
import tempfile
import sys
import os
import sqlite3
import json
import requests

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from xml.etree import ElementTree

from .config import get_db_path
from .db_utils import (
    add_video,
    add_channel_info,
    check_if_channel_exists,
    get_channel_id_from_input,
    get_num_vids,
    get_vid_ids_by_channel_id,
    get_channels
)

from .utils import parse_vtt, get_date, handle_reject_consent_cookie

from rich.progress import track
from rich.console import Console


class DownloadHandler:
    def __init__(self, number_of_jobs=8, language='en', cookies_from_browser=None):

        self.console = Console()

        self.cookies_from_browser = cookies_from_browser
        self.number_of_jobs = number_of_jobs
        self.language = language

        self.session = None
        self.channel_id = None
        self.channel_name = None
        self.video_ids = None
        self.tmp_dir = None

    def download_channel(self, url):

        self.validate_channel_url(url)
        self.session = self.init_session(url)
        self.channel_id = self.get_channel_id(url)
        self.channel_name = self.get_channel_name(self.channel_id)

        if check_if_channel_exists(self.channel_id):
            self.console.print(f"[yellow]Channel '{self.channel_name}' already exists in database. Updating instead...[/yellow]")
            self.update_channel(self.channel_id)
            return

        with tempfile.TemporaryDirectory() as tmp_dir:
            self.tmp_dir = tmp_dir
            channel_url = f"https://www.youtube.com/channel/{self.channel_id}/videos"
            self.video_ids = self.get_videos_list(channel_url)

            self.console.print(
                f"[green]Downloading [red]{len(self.video_ids)}[/red] "
                "vtt files[/green]"
            )

            self.download_vtts()
            add_channel_info(self.channel_id, self.channel_name, channel_url)
            self.vtt_to_db()

        self.console.print(f"[green]Finished downloading subtitles for {self.channel_name}[/green]")

    def download_playlist(self, playlist_url, language, number_of_jobs):
        self.language = language
        self.number_of_jobs = number_of_jobs

        playlist_data = self.get_playlist_data(playlist_url)

        for video in playlist_data:
            channel_name = video["channel_name"]
            channel_id = video["channel_id"]
            channel_url = video["channel_url"]
            if not check_if_channel_exists(channel_id):
                add_channel_info(channel_id, channel_name, channel_url)

        self.video_ids = list(set(video["video_id"] for video in playlist_data))

        with tempfile.TemporaryDirectory() as tmp_dir:
            self.console.print(f"[green][bold]Downloading [red]{len(playlist_data)}[/red] "
                               "vtt files[/bold][/green]\n")
            self.tmp_dir = tmp_dir
            self.download_vtts()
            self.vtt_to_db()

    def update_channel(self, target_channel):

        with tempfile.TemporaryDirectory() as tmp_dir:
            self.tmp_dir = tmp_dir
            
            # Handle both channel_id and target_channel (rowid/name)
            if isinstance(target_channel, str) and len(target_channel) == 24:  # YouTube channel IDs are 24 chars
                self.channel_id = target_channel
            else:
                self.channel_id = get_channel_id_from_input(target_channel)
                
            channel_url = f"https://www.youtube.com/channel/{self.channel_id}/videos"
            self.session = self.init_session(channel_url)
            self.channel_name = self.get_channel_name(self.channel_id)
            self.console.print(f"Updating channel: {self.channel_name}")
            public_video_ids = self.get_videos_list(channel_url)
            num_public_vids = len(public_video_ids)
            num_local_vids = get_num_vids(self.channel_id)

            if num_public_vids == num_local_vids:
                self.console.print("[yellow]No new videos to download[/yellow]")
                return

            local_vid_ids = get_vid_ids_by_channel_id(self.channel_id)
            local_vid_ids = [i[0] for i in local_vid_ids]

            fresh_videos = [i for i in public_video_ids if i not in local_vid_ids]
            self.video_ids = fresh_videos

            self.console.print(f"Found {len(fresh_videos)} videos on \"{self.channel_name}\" not in the database")
            self.console.print(f"Downloading {len(fresh_videos)} new videos from \"{self.channel_name}\"")

            self.download_vtts()

            vtt_to_parse = os.listdir(self.tmp_dir)

            if len(vtt_to_parse) == 0:
                self.console.print("No new videos saved")
                self.console.print(f"{len(fresh_videos)} videos on \"{self.channel_name}\" do not have subtitles")
                return

            self.vtt_to_db()

            self.console.print(f"Added {len(vtt_to_parse)} new videos from \"{self.channel_name}\" to the database")

    def update_all_channels(self):

        self.console.print("Updating all channels in the database")
        all_channels = get_channels()
        all_channel_row_ids = [i[0] for i in all_channels]

        for channel_row_id in all_channel_row_ids:
            self.update_channel(channel_row_id)

        self.console.print("[green]Finished updating all channels[/green]")

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

    def get_channel_name(self, channel_id):

        session = self.session
        res = session.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")

        if res.status_code == 200:
            with self.console.status("[bold green]Parsing Feed...") as status:
                tree = ElementTree.fromstring(res.content)
                channel_name = tree.find('./{*}author/{*}name').text
                return channel_name
        else:
            self.console.print("[red]Error:[/red] "
                               "couldn't get the channel name or channel doesn't exist")
            sys.exit(1)

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
                self.console.print("No streams found")

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

    def download_vtts(self):
        executor = ThreadPoolExecutor(self.number_of_jobs)
        futures = []

        for video_id in self.video_ids:
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            future = executor.submit(self.get_vtt, self.tmp_dir, video_url, self.language)
            futures.append(future)

        for i in range(len(self.video_ids)):
            futures[i].result()

    def quiet_progress_hook(self, d):
        console = self.console
        if d['status'] == 'finished':
            file_name = Path(d['filename']).name
            console.print(f" -> \"{file_name}\"")

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
                'no_warnings': True,
                'progress_hooks': [self.quiet_progress_hook],
            }

            if self.cookies_from_browser is not None:
                ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

        except Exception as e:
            self.console.print(f"Failed to get: {video_url}\n{e}")

    def vtt_to_db(self):

        tmp_dir = self.tmp_dir

        items = os.listdir(tmp_dir)
        file_paths = [os.path.join(tmp_dir, item) for item in items if item.endswith('.vtt')]

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
                cur.execute("""
                            INSERT INTO Subtitles (video_id, start_time, stop_time, text) 
                            VALUES (?, ?, ?, ?)
                            """, (vid_id, start_time, stop_time, text))

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


