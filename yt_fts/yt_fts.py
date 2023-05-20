import click, re, sqlite3 
import os, tempfile, subprocess, requests, datetime, csv

from tabulate import tabulate
from progress.bar import Bar

from bs4 import BeautifulSoup
import json


from yt_fts.db_scripts import * 

YT_DLP='yt-dlp'

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
@click.option('--number-of-jobs', type=int, default=1, help='Optional number of jobs to parallelize the run')
def download(channel_url, channel_id, number_of_jobs):
    if channel_id is None:
        channel_id = get_channel_id(channel_url)
    if channel_id:
        download_channel(channel_id, channel_url, number_of_jobs)
    else:
        print("Error finding channel id try --channel-id option")


@click.command( help='search [channel id] [search text]')
@click.argument('channel_id', required=True)
@click.argument('search_text', required=True)
def search(channel_id, search_text):
    click.echo(f'Searching for quotes in channel {channel_id} for text {search_text}')
    get_quotes(channel_id, search_text)


@click.command( help='export [channel id] [search text] ')
@click.argument('channel_id', required=True)
@click.argument('search_text', required=True)
def export(channel_id, search_text):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f'{channel_id}_{timestamp}.csv'
    click.echo(f'Exporting search results to csv: {file_name}')
    search_to_csv(channel_id, search_text, file_name)



@click.command( help='delete [channel id]')
@click.argument('channel_id', required=True)
def delete(channel_id):
    channel_name = get_channel_name_from_db(channel_id) 
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

from concurrent.futures import ThreadPoolExecutor


def get_vtt(tmp_dir, video_url):
    cmd = [
        YT_DLP,
        "-o", f"{tmp_dir}/%(id)s.%(ext)s",  
        "--write-auto-sub",  
        "--convert-subs", "vtt",  
        "--skip-download",
        video_url
    ]
    subprocess.run(cmd)

def get_videos_list(channel_url):
    cmd = [
        YT_DLP,
        "--flat-playlist",
        "--print",
        "id",
        f"{channel_url}"
    ]
    res = subprocess.run(cmd, capture_output=True, check=True)
    list_of_videos_urls = res.stdout.decode().splitlines()
    return list_of_videos_urls

def download_vtts(number_of_jobs, list_of_videos_urls, tmp_dir):
    executor = ThreadPoolExecutor(number_of_jobs)
    futures = []
    for video_id in list_of_videos_urls:
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        future = executor.submit(get_vtt, tmp_dir, video_url)
        futures.append(future)
    
    for i in range(len(list_of_videos_urls)):
        futures[i].result()

def download_channel(channel_id, channel_url, number_of_jobs):
    print("Downloading channel")
    with tempfile.TemporaryDirectory() as tmp_dir:
        print('Saving vtt files to', tmp_dir)
        channel_name = get_channel_name(channel_id)
        list_of_videos_urls = get_videos_list(channel_url)
        print(f'Downloading vtt info of {len(list_of_videos_urls)} videos')
        download_vtts(number_of_jobs, list_of_videos_urls, tmp_dir)

        videos_url = f"https://www.youtube.com/channel/{channel_id}/videos"
        add_channel_info(channel_id, channel_name, videos_url)
        print("Adding VTT data to db")
        vtt_to_db(channel_id, tmp_dir)

def vtt_to_db(channel_id, dir_path):
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
        vid_title = get_vid_title(vid_url)
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
                end = re.search("--> (.*)",time_match.group(1))

                start_time = start.group(1)
                end_time = end.group(1)

                sub_titles = lines[count + 1]

                result.append({
                    'start_time': start_time,
                    'text': sub_titles.strip('\n'),
                })
        
    return result 


def get_vid_title(vid_url):
    res = requests.get(vid_url)
    if res.status_code == 200:
        html = res.text
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string
        return title 
    else:
        return None
        

 
def get_channel_id(url):
    res = requests.get(url)
    if res.status_code == 200:
        html = res.text
        channel_id = re.search('channelId":"(.{24})"', html).group(1)
        print(channel_id)
        return channel_id
    else:
        return None

def get_channel_name(channel_id):

    res = requests.get(f"https://www.youtube.com/channel/{channel_id}/videos")

    if res.status_code == 200:

        html = res.text
        soup = BeautifulSoup(html, 'html.parser')
        script = soup.find('script', type='application/ld+json')
        data = json.loads(script.string)
        channel_name = data['itemListElement'][0]['item']['name']
        print(channel_name)
        return channel_name 
    else:
        return None

def get_quotes(channel_id, text):
    res = search_channel(channel_id, text)

    if len(res) == 0:
        print("No matches found")
    else:

        shown_titles = []
        shown_stamps = []

        for quote in res: 
            sub_id = quote[0]
            vid_title = get_title_from_db(sub_id)
            vid_id = quote[1]
            time_stamp = quote[2]
            subs = quote[3]

            id_stamp =  vid_id + time_stamp[:-4]  

            time = time_to_secs(time_stamp) 

            if vid_title not in shown_titles:
                print(f"\nVideo title\"{vid_title}\"")
                shown_titles.append(vid_title)


            if id_stamp not in shown_stamps:
                print(f"\n") 
                print(f"    Quote: \"{subs.strip()}\"")
                print(f"    Time Stamp: {time_stamp}")
                print(f"    Link: https://youtu.be/{vid_id}?t={time}")
                shown_stamps.append(id_stamp)


def search_to_csv(channel_id, text, file_name):
    res = search_channel(channel_id, text)

    if len(res) == 0:
        print("No matches found")
    else:
        with open(file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Video Title', 'Quote', 'Time Stamp', 'Link'])
            
            shown_stamps = []

            for quote in res: 
                sub_id = quote[0]
                vid_title = get_title_from_db(sub_id)
                vid_id = quote[1]
                time_stamp = quote[2]
                subs = quote[3]
                id_stamp =  vid_id + time_stamp[:-4]  
                time = time_to_secs(time_stamp) 

                if id_stamp not in shown_stamps:
                    writer.writerow([vid_title, subs.strip(), time_stamp, f"https://youtu.be/{vid_id}?t={time}"])
                    shown_stamps.append(id_stamp)


def time_to_secs(time_str):

    time_rex = re.search("^(\d\d):(\d\d):(\d\d)",time_str )
    hours = int(time_rex.group(1)) * 3600 
    mins = int(time_rex.group(2)) * 60
    secs = int(time_rex.group(3)) 

    total_secs =  hours + mins + secs
    return total_secs - 3





if __name__ == '__main__':
    cli()
