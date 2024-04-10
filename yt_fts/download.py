
import tempfile
import subprocess, re, os, sqlite3, json

from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from .config import get_db_path
from .db_utils import add_video
from .utils import parse_vtt
from urllib.parse import urlparse 

from rich.progress import track
from rich.console import Console

def handle_reject_consent_cookie(channel_url, s):
    """
    Auto rejects the consent cookie if request is redirected to the consent page
    """
    r = s.get(channel_url)
    if "https://consent.youtube.com" in r.url:
        m = re.search(r"<input type=\"hidden\" name=\"bl\" value=\"([^\"]*)\"", r.text)
        if m:
            data = {
                "gl":"DE",
                "pc":"yt",
                "continue":channel_url,
                "x":"6",
                "bl":m.group(1),
                "hl":"de",
                "set_eom":"true"
            }
            s.post("https://consent.youtube.com/save", data=data)


def get_channel_id(url, s):
    """
    Scrapes channel id from the channel page
    """
    res = s.get(url)
    if res.status_code == 200:
        html = res.text
        channel_id = re.search('channelId":"(.{24})"', html).group(1)
        return channel_id
    else:
        return None


def get_channel_name(channel_id, s):
    """
    Scrapes channel name from the channel page
    """
    console = Console()
    res = s.get(f"https://www.youtube.com/channel/{channel_id}/videos")

    if res.status_code == 200:

        html = res.text
        soup = BeautifulSoup(html, 'html.parser')
        script = soup.find('script', type='application/ld+json')

        # "Hot fix" for channels with special characters in the name
        try:
            with console.status("[bold green]Parsing JSON...") as status:
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


def get_videos_list(channel_url):
    """
    Scrapes list of all video urls from the channel
    """
    console = Console()

    with console.status("[bold green]Scraping video urls, this might take a little...") as status:
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--print",
            "id",
            f"{channel_url}"
        ]
        res = subprocess.run(cmd, capture_output=True, check=True)
        list_of_videos_urls = res.stdout.decode().splitlines()

        streams_url = channel_url.replace("/videos", "/streams") 
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--print",
            "id",
            streams_url
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, check=True)
            live_stream_urls = res.stdout.decode().splitlines()
            if len(live_stream_urls) > 0:
                list_of_videos_urls.extend(live_stream_urls)
        except subprocess.CalledProcessError:
            console.print("[bold red]No streams tab found or error fetching streams.")


    return list_of_videos_urls 


def get_playlist_data(playlist_url):
    """
    Returns a list of channel ids and video ids from a playlist
    [
        ['channel_id', 'video_id'],
    ]
    """

    console = Console()

    with console.status("[bold green]Scraping video urls, this might take a little...") as status:
        cmd = [
            "yt-dlp",
            "--print",
            "%(channel)s,%(channel_id)s,%(id)s",
            f"{playlist_url}"
        ]
        res = subprocess.run(cmd, capture_output=True, check=True)
        data = res.stdout.decode().splitlines()

        playlist_data = []

        for vid in data:
            vid = vid.split(',')
            vid_obj = {
                'channel_name': vid[0],
                'channel_id': vid[1],
                'video_id': vid[2],
                'channel_url': f"https://www.youtube.com/channel/{vid[1]}/videos",
                'video_url': f"https://youtu.be/{vid[2]}"
            }
            playlist_data.append(vid_obj)

    return playlist_data 


def download_vtts(number_of_jobs, video_ids, language ,tmp_dir):
    """
    Multi-threaded download of vtt files
    """

    # showing progress on a multi-threaded task might be more trouble than it's worth
    # console = Console()

    executor = ThreadPoolExecutor(number_of_jobs)
    futures = []

    for video_id in video_ids:
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        future = executor.submit(get_vtt, tmp_dir, video_url, language)
        futures.append(future)
    
    for i in range(len(video_ids)):
        futures[i].result()


def get_vtt(tmp_dir, video_url, language):
    subprocess.run([
        "yt-dlp",
        "-o", f"{tmp_dir}/%(id)s",
        "--write-info-json",
        "--write-auto-sub",
        "--convert-subs", "vtt",
        "--skip-download",
        "--sub-langs", f"{language},-live_chat",
        video_url
    ])


def vtt_to_db(dir_path):
    """
    Iterates through all vtt files in the temp_dir, passes them to 
    the vtt parsing function, then inserts the data into the database.
    """
    items = os.listdir(dir_path)
    file_paths = []

    for item in items:
        # ignore other files e.g. info.json files
        if not item.endswith('.vtt'):
            continue

        item_path = os.path.join(dir_path, item)
        if os.path.isfile(item_path):
            file_paths.append(item_path)    

    con = sqlite3.connect(get_db_path())  
    cur = con.cursor()


    for vtt in track(file_paths, description="Adding subtitles to database..."):
        base_name = os.path.basename(vtt)
        
        vid_id = base_name.split('.')[0]
        vid_url = f"https://youtu.be/{vid_id}"

        vid_json_path = os.path.join(os.path.dirname(vtt), f'{vid_id}.info.json')

        with open(vid_json_path, 'r', encoding='utf-8', errors='ignore') as f:
            vid_json = json.load(f)

        vid_title =  vid_json['title']
        channel_id = vid_json['channel_id']

        add_video(channel_id, vid_id, vid_title, vid_url)

        vtt_json = parse_vtt(vtt)

        for sub in vtt_json:
            start_time = sub['start_time']
            stop_time = sub['stop_time']
            text = sub['text']
            cur.execute(f"INSERT INTO Subtitles (video_id, start_time, stop_time, text) VALUES (?, ?, ?, ?)", 
                        (vid_id, start_time, stop_time, text))

        con.commit()

    con.close()


def validate_channel_url(channel_url):
    """
    valid patterns
    https://www.youtube.com/channel/channelID
    https://www.youtube.com/@channelname

    https://www.youtube.com/@channelname/*
    https://www.youtube.com/channel/channelID/*
    """
    from rich.console import Console
    console = Console()

    channel_url = channel_url.strip('/')
    parsed = urlparse(channel_url)
    domain = parsed.netloc
    path = parsed.path.split('/')

    if not domain.endswith('youtube.com'):
        console.print("")
        console.print(f"[bold red]Error:[/bold red] Invalid channel domain: [blue]{domain}[/blue]")
        console.print("")
        exit()
    
    if len(path) < 2:
        console.print("")
        console.print(f"[bold red]Error:[/bold red] Invalid channel url: [blue]{channel_url}[/blue]")
        console.print("")
        exit()

    if path[1].startswith("@"):
        return f"https://www.youtube.com/{path[1]}/videos"

    if path[1] == "channel":
        return f"https://www.youtube.com/channel/{path[2]}/videos"

    console.print("")
    console.print(f"[bold red]Error:[/bold red] Unknown url format: [blue]{channel_url}[/blue]")
    console.print("")
    console.print("Please use one of the following formats:")
    console.print("")
    console.print("    - https://www.youtube.com/[yellow]@channelname[/yellow]")
    console.print("    - https://www.youtube.com/channel/[yellow]channelId[/yellow]")
    console.print("")
    exit()


def download_channel(channel_id, channel_name, language, number_of_jobs, s):
    """
    Downloads all the videos from a channel to a tmp directory
    """

    import tempfile
    from yt_fts.db_utils import add_channel_info

    console = Console() 

    with tempfile.TemporaryDirectory() as tmp_dir:
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
        list_of_videos_urls = get_videos_list(channel_url)

        console.print(f"[green][bold]Downloading [red]{len(list_of_videos_urls)}[/red] vtt files[/bold][/green]\n")
        console.print("[green]I would normally show a progress bar here, but multithreading and progress bars don't play nice.[/green]\n")

        download_vtts(number_of_jobs, list_of_videos_urls, language, tmp_dir)
        add_channel_info(channel_id, channel_name, channel_url)
        vtt_to_db(tmp_dir)
    return True


def download_playlist(playlist_url, s, language=None, number_of_jobs=None):
    """
        Downloads all subtitles from playlist, making new channels where needed
    """

    from yt_fts.db_utils import add_channel_info, check_if_channel_exists

    playlist_data = get_playlist_data(playlist_url)

    console = Console()

    # add missing stuff to db before multi threading? 
    for video in playlist_data:
        channel_name = video["channel_name"] 
        channel_id = video["channel_id"] 
        channel_url = video["channel_url"] 
        if not check_if_channel_exists(channel_id):
            add_channel_info(channel_id, channel_name, channel_url)
        

    video_ids = list(set(video["video_id"] for video in playlist_data))


    with tempfile.TemporaryDirectory() as tmp_dir:
        console.print(f"[green][bold]Downloading [red]{len(playlist_data)}[/red] vtt files[/bold][/green]\n")
        download_vtts(number_of_jobs, video_ids, language, tmp_dir)
        vtt_to_db(tmp_dir)
            

def get_channel_id_from_input(channel_input):
    """
    Checks if the input is a rowid or a channel name and returns channel id
    """

    from yt_fts.db_utils import (
        get_channel_id_from_rowid, 
        get_channel_id_from_name
    )

    from yt_fts.utils import show_message

    name_res = get_channel_id_from_name(channel_input) 
    id_res = get_channel_id_from_rowid(channel_input) 


    
    if id_res != None:
        return id_res
    elif name_res != None: 
        return name_res
    else:
        show_message("channel_not_found")
        exit()
    