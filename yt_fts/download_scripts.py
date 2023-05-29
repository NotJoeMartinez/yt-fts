import subprocess, re, os, sqlite3, json

from progress.bar import Bar
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

from yt_fts.db_scripts import add_video
from yt_fts.utils import parse_vtt


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
        print(channel_id)
        return channel_id
    else:
        return None


def get_channel_name(channel_id, s):
    """
    Scrapes channel name from the channel page
    """
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


def get_videos_list(channel_url):
    """
    Scrapes list of all video urls from the channel
    """
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


def download_vtts(number_of_jobs, list_of_videos_urls, language ,tmp_dir):
    """
    Multi-threaded download of vtt files
    """
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


def vtt_to_db(channel_id, dir_path, s):
    """
    Iterates through all vtt files in the temp_dir, passes them to 
    the vtt parsing function, then inserts the data into the database.
    """
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


def get_vid_title(vid_url, s):
    """
    Scrapes video title from the video page
    """
    res = s.get(vid_url)
    if res.status_code == 200:
        html = res.text
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string
        return title 
    else:
        return None
