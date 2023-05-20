import click, re, sqlite3
import os, tempfile, subprocess
import requests 
from bs4 import BeautifulSoup
import json


@click.group()
def cli():
    make_db()

@click.command(help="Lists channels")
def list():
    click.echo("Listing channels")

@click.command( help='download [channel url]')
@click.argument('channel_url', required=True)
@click.option('--channel-id', default=None, help='Optional channel id to override the one from the url')
def download(channel_url, channel_id):
    if channel_id is None:
        channel_id = get_channel_id(channel_url)
    if channel_id:
        download_channel(channel_id)
    else:
        print("Error finding channel id try --channel-id option")


@click.command( help='search [channel id] [search text]')
@click.argument('channel_id', required=True)
@click.argument('search_text', required=True)
def search(channel_id, search_text):
    click.echo(f'Searching for quotes in channel {channel_id} for text {search_text}')
    get_quotes(channel_id, search_text)

cli.add_command(list)
cli.add_command(download)
cli.add_command(search)



def download_channel(channel_id):
    print("Downloading channel")
    with tempfile.TemporaryDirectory() as tmp_dir:
        print('Saving vtt files to', tmp_dir)

        channel_name = get_channel_name(channel_id)
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
        subprocess.run([
            "yt-dlp",
            "-o", f"{tmp_dir}/%(id)s.%(ext)s",  
            "--write-auto-sub",  
            "--convert-subs", "vtt",  
            "--skip-download",  
            channel_url
        ])
        add_channel_info(channel_id, channel_name, channel_url)
        vtt_to_db(channel_id, tmp_dir)

def vtt_to_db(channel_id, dir_path):
    items = os.listdir(dir_path)

    file_paths = []

    for item in items:
        item_path = os.path.join(dir_path, item)
        if os.path.isfile(item_path):
            file_paths.append(item_path)    

    for i in file_paths:
        print(i)



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

def get_quotes(channel_id, search_text):
    con = sqlite3.connect("subtitles.db")
    cur = con.cursor()
    cur.execute(f"SELECT * FROM {channel_id} WHERE sub_titles LIKE ?", ('%'+search_text+'%',))
    res = cur.fetchall()
    con.close()

    if len(res) == 0:
        print("No matches found")
    else:

        shown_titles = []
        shown_stamps = []

        for quote in res: 
            vid_id = quote[0]
            vid_title = quote[1]
            start = quote[2]
            end = quote[3]
            subs = quote[4]

            #  should look like: 6C7vx4Ot2qk01:28:00
            id_stamp =  vid_id + start[:-4]  

            time = time_to_secs(start) 

            if vid_title not in shown_titles:
                print(f"\nMatches found in: \"{vid_title}\"")
                shown_titles.append(vid_title)


            if id_stamp not in shown_stamps:
                print(f"\n") 
                print(f"    Quote: \"{subs.strip()}\"")
                print(f"    Time Stamp: {start}")
                print(f"    Link: https://youtu.be/{vid_id}?t={time}")
                shown_stamps.append(id_stamp)



def time_to_secs(time_str):

    time_rex = re.search("^(\d\d):(\d\d):(\d\d)",time_str )
    hours = int(time_rex.group(1)) * 3600 
    mins = int(time_rex.group(2)) * 60
    secs = int(time_rex.group(3)) 

    total_secs =  hours + mins + secs
    return total_secs - 3


def add_channel_info(channel_id, channel_name, channel_url):
    con = sqlite3.connect('subtitles.db')  
    cur = con.cursor()  

    cur.execute(f"INSERT INTO Channels VALUES (?, ?, ?)", (channel_id, channel_name, channel_url))
    con.commit()
    con.close()

def make_db():
    con = sqlite3.connect('subtitles.db')  
    cur = con.cursor()  

    cur.execute('''
        CREATE TABLE IF NOT EXISTS Channels (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT NOT NULL,
            channel_url TEXT NOT NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS Videos (
            video_id TEXT PRIMARY KEY,
            video_title TEXT NOT NULL,
            video_url TEXT NOT NULL,
            channel_id TEXT,
            FOREIGN KEY(channel_id) REFERENCES Channels(channel_id)
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS Subtitles (
            subtitle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            timestamp TEXT NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY(video_id) REFERENCES Videos(video_id)
        );
    ''')

    con.commit()
    con.close()


if __name__ == '__main__':
    cli()
