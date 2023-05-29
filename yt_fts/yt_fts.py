import click, re, sqlite3, json 
import os, tempfile, subprocess, requests, datetime, csv

from tabulate import tabulate
from progress.bar import Bar
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

from yt_fts.db_scripts import *

@click.group()
def cli():
    make_db()


@click.command(help="Lists channels")
def list():
    click.echo("Listing channels")
    channels = get_channels()
    print(tabulate(channels, headers=["channel_id","channel_name", "channel_url"]))


@click.command( help='download [channel url]')
@click.argument('channel_url', required=True)
@click.option('--channel-id', default=None, help='Optional channel id to override the one from the url')
@click.option('--language', default="en", help='Language of the subtitles to download')
@click.option('--number-of-jobs', type=int, default=1, help='Optional number of jobs to parallelize the run')
@click.option('--language', default="en", help='Language of the subtitles to download')
def download(channel_url, channel_id, language, number_of_jobs):
    s = requests.session()
    handle_reject_consent_cookie(channel_url, s)
    if channel_id is None:
        channel_id = get_channel_id(channel_url, s)
    
    channel_name = get_channel_name(channel_id, s)

    if channel_id:
        download_channel(channel_id, channel_name, language, number_of_jobs, s)
    else:
        print("Error finding channel id try --channel-id option")


@click.command( help='search [channel id] [search text]')
@click.argument('search_text', required=True)
@click.option('--all', is_flag=True, help='Search in all channels')
@click.argument('channel_id', required=False)
def search(channel_id, search_text, all):
    if len(search_text) > 40:
        show_message("search_too_long")
        return
    if all:
        click.echo('Searching in all channels')
        get_quotes("all", search_text)
    else:
        if channel_id is None:
            click.echo('Error: Channel ID is required when not using --all option')
            return
        click.echo(f'Searching in channel {channel_id}')
        get_quotes(channel_id, search_text)


@click.command( help="export [channel id] [search text]")
@click.argument("search_text", required=True)
@click.option("--all", is_flag=True, help="Export from all channels")
@click.argument("channel_id", required=False)
def export(channel_id, search_text, all):
    if len(search_text) > 40:
        show_message("search_too_long")
        return
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if all:
        file_name = f"all_{timestamp}.csv"
        click.echo(f"Exporting search results from all channels to csv: {file_name}")
        search_to_csv("all", search_text, file_name)
    else:
        if channel_id is None:
            click.echo("Error: Channel ID is required when not using --all option")
            return
        file_name = f"{channel_id}_{timestamp}.csv"
        click.echo(f"Exporting search results to csv: {file_name}")
        search_to_csv(channel_id, search_text, file_name)


@click.command( help="delete [channel id]")
@click.argument("channel_id", required=True)
def delete(channel_id):
    channel_name = get_channel_name_from_id(channel_id) 
    print(f"Deleting channel {channel_name}")
    print("Are you sure you want to delete this channel and all its data?")
    confirm = input("y/n: ")
    if confirm == "y":
        click.echo(f'deleting channel {channel_name}')
        delete_channel(channel_id)
    else:
        print("Aborting")


cli.add_command(list)
cli.add_command(download)
cli.add_command(search)
cli.add_command(delete)
cli.add_command(export)


def download_channel(channel_id, channel_name, language, number_of_jobs, s):
    print("Downloading channel")
    with tempfile.TemporaryDirectory() as tmp_dir:

        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
        list_of_videos_urls = get_videos_list(channel_url)

        download_vtts(number_of_jobs, list_of_videos_urls, language, tmp_dir)
        add_channel_info(channel_id, channel_name, channel_url)

        vtt_to_db(channel_id, tmp_dir, s)


def download_vtts(number_of_jobs, list_of_videos_urls, language ,tmp_dir):
    executor = ThreadPoolExecutor(number_of_jobs)
    futures = []
    for video_id in list_of_videos_urls:
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        future = executor.submit(get_vtt, tmp_dir, video_url, language)
        futures.append(future)
    
    for i in range(len(list_of_videos_urls)):
        futures[i].result()


def get_vtt(tmp_dir, video_url, language):
    subprocess.run([
        "yt-dlp",
        "-o", f"{tmp_dir}/%(id)s.%(ext)s",
        "--write-auto-sub",
        "--convert-subs", "vtt",
        "--skip-download",
        "--sub-langs", f"{language},-live_chat",
        video_url
    ])


def get_videos_list(channel_url):
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print",
        "id",
        f"{channel_url}"
    ]
    res = subprocess.run(cmd, capture_output=True, check=True)
    list_of_videos_urls = res.stdout.decode().splitlines()
    return list_of_videos_urls


def vtt_to_db(channel_id, dir_path, s):
    items = os.listdir(dir_path)

    file_paths = []

    for item in items:
        item_path = os.path.join(dir_path, item)
        if os.path.isfile(item_path):
            file_paths.append(item_path)    

    con = sqlite3.connect('subtitles.db')  
    cur = con.cursor()

    bar = Bar('Processing', max=len(file_paths))

    for vtt in file_paths:
        base_name = os.path.basename(vtt)
        vid_id = re.match(r'^([^.]*)', base_name).group(1)
        vid_url = f"https://youtu.be/{vid_id}"
        vid_title = get_vid_title(vid_url, s)
        add_video(channel_id, vid_id, vid_title, vid_url)

        vtt_json = parse_vtt(vtt)

        for sub in vtt_json:
            start_time = sub['start_time']
            text = sub['text']
            cur.execute(f"INSERT INTO Subtitles (video_id, timestamp, text) VALUES (?, ?, ?)", (vid_id, start_time, text))

        con.commit()
        bar.next()

    bar.finish() 
    con.close()


def parse_vtt(file_path):

    result = []

    time_pattern = "^(.*) align:start position:0%"

    with open(file_path, "r") as f:
        lines = f.readlines()

    for count, line in enumerate(lines):
        time_match = re.match(time_pattern, line)

        if time_match:
            start = re.search("^(.*) -->",time_match.group(1))
            start_time = start.group(1)
            sub_titles = lines[count + 1]

            # prevent duplicate entries
            if result and result[-1]['text'] == sub_titles.strip('\n'):
                continue
            else:   
                result.append({
                    'start_time': start_time,
                    'text': sub_titles.strip('\n'),
                })

    return result 


def get_quotes(channel_id, text):

    if channel_id == "all":
        res = search_all(text)
    else:
        res = search_channel(channel_id, text)

    if len(res) == 0:
        show_message("no_matches_found")
        exit()

    for quote in res:
        video_id = quote["video_id"]

        video_title = get_title_from_db(video_id)

        channel_name = get_channel_name_from_video_id(video_id)

        time_stamp = quote["timestamp"]
        subs = quote["text"]

        time = time_to_secs(time_stamp) 

        print("")
        print(f"{channel_name}: \"{video_title}\"")
        print(f"") 
        print(f"    Quote: \"{subs.strip()}\"")
        print(f"    Time Stamp: {time_stamp}")
        print(f"    Link: https://youtu.be/{video_id}?t={time}\n")


def search_to_csv(channel_id, text, file_name):
    if channel_id == "all":
        res = search_all(text)
    else:
        res = search_channel(channel_id, text)

    if len(res) == 0:
        show_message("no_matches_found")
        exit()

    with open(file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Channel Name','Video Title', 'Quote', 'Time Stamp', 'Link'])
        
        for quote in res:
            video_id = quote["video_id"]

            channel_name = get_channel_name_from_video_id(video_id)

            video_title = get_title_from_db(video_id)

            time_stamp = quote["timestamp"]
            subs = quote["text"]

            time = time_to_secs(time_stamp) 

            writer.writerow([channel_name,video_title, subs.strip(), time_stamp, f"https://youtu.be/{video_id}?t={time}"])


def time_to_secs(time_str):

    time_rex = re.search("^(\d\d):(\d\d):(\d\d)",time_str)
    hours = int(time_rex.group(1)) * 3600 
    mins = int(time_rex.group(2)) * 60
    secs = int(time_rex.group(3)) 

    total_secs =  hours + mins + secs
    return total_secs - 3


def get_vid_title(vid_url, s):
    res = s.get(vid_url)
    if res.status_code == 200:
        html = res.text
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string
        return title 
    else:
        return None
        
 
def get_channel_id(url, s):
    res = s.get(url)
    if res.status_code == 200:
        html = res.text
        channel_id = re.search('channelId":"(.{24})"', html).group(1)
        print(channel_id)
        return channel_id
    else:
        return None


def get_channel_name(channel_id, s):

    res = s.get(f"https://www.youtube.com/channel/{channel_id}/videos")

    if res.status_code == 200:

        html = res.text
        soup = BeautifulSoup(html, 'html.parser')
        script = soup.find('script', type='application/ld+json')

        # Hot fix for channels with special characters in the name
        try:
            print("Trying to parse json normally")
            data = json.loads(script.string)
        except:
            print("json parse failed retrying with escaped backslashes")
            script = script.string.replace('\\', '\\\\')
            data = json.loads(script)

        channel_name = data['itemListElement'][0]['item']['name']
        print(channel_name)
        return channel_name 
    else:
        return None


def handle_reject_consent_cookie(channel_url, s):
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


def show_message(code):
    error_dict = {
        "search_too_long": "Error: Search text must be less than 40 characters",
        "no_matches_found": "No matches found.\n- Try shortening the search text or use wildcards to match partial words."
    }

    print(error_dict[code])
