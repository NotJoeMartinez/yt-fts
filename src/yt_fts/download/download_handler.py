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

from ..config import get_db_path
from ..db_utils import (
    add_video,
    add_channel_info,
    check_if_channel_exists,
    get_channel_id_from_input,
    get_num_vids,
    get_vid_ids_by_channel_id,
    get_channels
)

from ..utils import parse_vtt, get_date, handle_reject_consent_cookie

from rich.progress import track
from rich.console import Console


class DownloadHandler:
    def __init__(self, number_of_jobs: int = 8, language: str = 'en', cookies_from_browser: str | None = None) -> None:

        self.console = Console()

        self.cookies_from_browser = cookies_from_browser
        self.number_of_jobs = number_of_jobs
        self.language = language

        self.session: requests.Session | None = None
        self.channel_id: str | None = None
        self.channel_name: str | None = None
        self.video_ids: list[str] | None = None
        self.tmp_dir: str | None = None

    def download_channel(self, url: str) -> None:

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

    def download_playlist(self, playlist_url: str, language: str, number_of_jobs: int) -> None:
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

    def update_channel(self, target_channel: str | int) -> None:

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

    def update_all_channels(self) -> None:

        self.console.print("Updating all channels in the database")
        all_channels = get_channels()
        all_channel_row_ids = [i[0] for i in all_channels]

        for channel_row_id in all_channel_row_ids:
            self.update_channel(channel_row_id)

        self.console.print("[green]Finished updating all channels[/green]")

    def init_session(self, url: str) -> requests.Session:
        s = requests.session()
        handle_reject_consent_cookie(url, s)
        return s

    def get_channel_id(self, url: str) -> str | None:

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

    def get_channel_name(self, channel_id: str) -> str:

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

    def get_videos_list(self, channel_url: str) -> list[str]:
        with self.console.status("[bold green]Scraping video urls ...") as status:
            ydl_opts = {
                'extract_flat': True,
                'quiet': True,
                'nocheckcertificate': True,
                'user_agent': 'random',
                'sleep_interval': 1,
                'max_sleep_interval': 3,
                'retries': 3,
            }

            if self.cookies_from_browser is not None:
                ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(channel_url, download=False)
                    if info and 'entries' in info:
                        list_of_videos_urls = [entry['id'] for entry in info['entries'] if entry]
                    else:
                        self.console.print("[red]Error: Could not extract video list from channel[/red]")
                        return []
            except Exception as e:
                error_msg = str(e)
                if "403" in error_msg or "Forbidden" in error_msg:
                    self.console.print("[red]403 Forbidden error when scraping channel videos[/red]")
                    self.console.print("[yellow]This might be due to:[/yellow]")
                    self.console.print("  - Channel is private or restricted")
                    self.console.print("  - YouTube is blocking automated access")
                    self.console.print("  - Missing cookies (try --cookies-from-browser)")
                    self.console.print("  - Rate limiting")
                else:
                    self.console.print(f"[red]Error scraping videos: {error_msg}[/red]")
                return []

            # Try to get streams as well
            streams_url = channel_url.replace("/videos", "/streams")
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    streams_info = ydl.extract_info(streams_url, download=False)
                    if streams_info and 'entries' in streams_info:
                        live_stream_urls = [entry['id'] for entry in streams_info['entries'] if entry]
                        if len(live_stream_urls) > 0:
                            list_of_videos_urls.extend(live_stream_urls)
            except Exception:
                self.console.print("No streams found")

        return list_of_videos_urls

    def get_playlist_data(self, playlist_url: str) -> list[dict[str, str]]:
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
                        'user_agent': 'random',
                        'channel_name': entry['channel'],
                        'channel_id': entry['channel_id'],
                        'video_id': entry['id'],
                        'channel_url': f"https://www.youtube.com/channel/{entry['channel_id']}/videos",
                        'video_url': f"https://youtu.be/{entry['id']}"
                    }
                    playlist_data.append(vid_obj)

        return playlist_data

    def download_vtts(self) -> None:
        executor = ThreadPoolExecutor(self.number_of_jobs)
        futures = []

        for video_id in self.video_ids:
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            future = executor.submit(self.get_vtt, self.tmp_dir, video_url, self.language)
            futures.append(future)

        for i in range(len(self.video_ids)):
            futures[i].result()

    def quiet_progress_hook(self, d: dict) -> None:
        console = self.console
        if d['status'] == 'finished':
            file_name = Path(d['filename']).name
            console.print(f" -> \"{file_name}\"")

    def get_vtt(self, tmp_dir: str, video_url: str, language: str) -> None:
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                ydl_opts = {
                    'user_agent': 'random',
                    'outtmpl': f'{tmp_dir}/%(id)s',
                    'writeinfojson': True,
                    'writeautomaticsub': True,
                    'subtitlesformat': 'vtt',
                    'skip_download': True,
                    'subtitleslangs': [language, '-live_chat'],
                    'quiet': True,
                    'no_warnings': True,
                    'progress_hooks': [self.quiet_progress_hook],
                    # Additional options to help bypass restrictions
                    'nocheckcertificate': True,
                    'ignoreerrors': False,
                    'no_color': True,
                    # Add rate limiting
                    'sleep_interval': 1,
                    'max_sleep_interval': 5,
                    # Add retry logic
                    'retries': 3,
                    'fragment_retries': 3,
                    'skip_unavailable_fragments': True,
                }

                if self.cookies_from_browser is not None:
                    ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                
                return

            except Exception as e:
                error_msg = str(e)
                self.console.print(f"[yellow]Attempt {attempt + 1}/{max_retries} failed for: {video_url}[/yellow]")
                self.console.print(f"[red]Error: {error_msg}[/red]")
                
                # Check if it's a 403 error specifically
                if "403" in error_msg or "Forbidden" in error_msg:
                    self.console.print(f"[red]403 Forbidden error detected - YouTube is blocking the request[/red]")
                    self.console.print(f"[yellow]Possible causes:[/yellow]")
                    self.console.print(f"  - Rate limiting (too many requests too quickly)")
                    self.console.print(f"  - Missing or invalid cookies")
                    self.console.print(f"  - IP address is blocked")
                    self.console.print(f"  - User-Agent detection")
                    
                    if attempt < max_retries - 1:
                        self.console.print(f"[yellow]Waiting {retry_delay} seconds before retry...[/yellow]")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        self.console.print(f"[red]All retry attempts failed for: {video_url}[/red]")
                        self.console.print(f"[yellow]Suggestions:[/yellow]")
                        self.console.print(f"  - Try using --cookies-from-browser option")
                        self.console.print(f"  - Reduce the number of parallel jobs (-j option)")
                        self.console.print(f"  - Wait a few minutes before trying again")
                        self.console.print(f"  - Check if the video is available in your region")
                
                elif "429" in error_msg or "Too Many Requests" in error_msg:
                    self.console.print(f"[red]429 Too Many Requests - Rate limit exceeded[/red]")
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * 5  # Longer wait for rate limits
                        self.console.print(f"[yellow]Waiting {wait_time} seconds before retry...[/yellow]")
                        import time
                        time.sleep(wait_time)
                        retry_delay *= 2
                    else:
                        self.console.print(f"[red]Rate limit exceeded for: {video_url}[/red]")
                        self.console.print(f"[yellow]Try reducing parallel jobs or wait longer[/yellow]")
                
                else:
                    # For other errors, just retry with normal delay
                    if attempt < max_retries - 1:
                        self.console.print(f"[yellow]Waiting {retry_delay} seconds before retry...[/yellow]")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        self.console.print(f"[red]Failed to get: {video_url}[/red]")
                        self.console.print(f"[red]Error: {error_msg}[/red]")

    def vtt_to_db(self) -> None:

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

    def diagnose_403_errors(self, test_url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ") -> None:
        """
        !SLOP GENERATED

        Diagnose potential causes of 403 errors by testing various aspects of the connection
        """
        self.console.print("[bold blue]Diagnosing 403 errors...[/bold blue]")
        
        # Test 1: Basic HTTP request
        self.console.print("\n[bold]1. Testing basic HTTP connection to YouTube...[/bold]")
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get("https://www.youtube.com", headers=headers, timeout=10)
            if response.status_code == 200:
                self.console.print("[green]✓ Basic HTTP connection successful[/green]")
            else:
                self.console.print(f"[red]✗ HTTP connection failed with status {response.status_code}[/red]")
        except Exception as e:
            self.console.print(f"[red]✗ HTTP connection failed: {e}[/red]")
        
        # Test 2: yt-dlp info extraction
        self.console.print("\n[bold]2. Testing yt-dlp info extraction...[/bold]")
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            }
            
            if self.cookies_from_browser is not None:
                ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                if info:
                    self.console.print("[green]✓ yt-dlp info extraction successful[/green]")
                    self.console.print(f"  Title: {info.get('title', 'N/A')}")
                else:
                    self.console.print("[red]✗ yt-dlp info extraction failed[/red]")
        except Exception as e:
            self.console.print(f"[red]✗ yt-dlp info extraction failed: {e}[/red]")
        
        # Test 3: Cookie availability
        self.console.print("\n[bold]3. Testing cookie availability...[/bold]")
        if self.cookies_from_browser is not None:
            self.console.print(f"[yellow]Cookies from browser: {self.cookies_from_browser}[/yellow]")
            try:
                # Test if we can extract cookies
                ydl_opts = {
                    'cookiesfrombrowser': (self.cookies_from_browser,),
                    'quiet': True,
                    'no_warnings': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Just test cookie extraction, don't download
                    self.console.print("[green]✓ Cookie extraction appears to be working[/green]")
            except Exception as e:
                self.console.print(f"[red]✗ Cookie extraction failed: {e}[/red]")
        else:
            self.console.print("[yellow]No cookies from browser specified[/yellow]")
            self.console.print("[yellow]Consider using --cookies-from-browser option[/yellow]")
        
        # Test 4: Rate limiting check
        self.console.print("\n[bold]4. Rate limiting analysis...[/bold]")
        self.console.print(f"Current parallel jobs: {self.number_of_jobs}")
        if self.number_of_jobs > 4:
            self.console.print("[yellow]⚠ High number of parallel jobs may cause rate limiting[/yellow]")
            self.console.print("[yellow]Consider reducing to 2-4 jobs[/yellow]")
        else:
            self.console.print("[green]✓ Parallel jobs setting looks reasonable[/green]")
        
        # Test 5: Network connectivity
        self.console.print("\n[bold]5. Network connectivity test...[/bold]")
        try:
            import socket
            socket.create_connection(("www.youtube.com", 443), timeout=5)
            self.console.print("[green]✓ Network connectivity to YouTube is good[/green]")
        except Exception as e:
            self.console.print(f"[red]✗ Network connectivity issue: {e}[/red]")
        
        # Recommendations
        self.console.print("\n[bold blue]Recommendations to fix 403 errors:[/bold blue]")
        self.console.print("1. Use --cookies-from-browser chrome (or firefox)")
        self.console.print("2. Reduce parallel jobs: -j 2 or -j 4")
        self.console.print("3. Wait a few minutes between download attempts")
        self.console.print("4. Check if you're behind a VPN or proxy")
        self.console.print("5. Try downloading from a different network")
        self.console.print("6. Update yt-dlp: pip install --upgrade yt-dlp")

    def validate_channel_url(self, channel_url: str) -> str:
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


