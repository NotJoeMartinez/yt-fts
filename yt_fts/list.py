import sqlite3 

from rich.console import Console
from rich.table import Table


from .db_utils import get_title_from_db 
from .utils import time_to_secs, get_time_delta

from .config import get_db_path

def show_video_transcript(video_id):
    con = sqlite3.connect(get_db_path())
    cur = con.cursor()
    cur.execute("SELECT * FROM subtitles WHERE video_id=?", (video_id,))
    rows = cur.fetchall()

    console = Console()
    word_count = 0
    for row in rows:
        timestamp = row[2]
        time = time_to_secs(timestamp)
        url = f"https://www.youtube.com/watch?v={video_id}&t={time}s"
        text = row[4]
        word_count += len(text.split())
        console.print(f"[link={url}]{timestamp[:-4]}[/link] - {text}")

    video_length = get_time_delta(rows[0][2], rows[-1][2])
    video_title = get_title_from_db(video_id)
    video_url = f"https://www.youtube.com/watch?v={video_id}"


    console.print(f"")
    console.print(f"Title: [bold][link={video_url}]{video_title}[/link][/bold]")
    console.print(f"Video Length: {video_length}")
    console.print(f"Word Count: {word_count}")

    con.close()


def show_video_list(channel_id):
    con = sqlite3.connect(get_db_path())
    cur = con.cursor()
    cur.execute("SELECT * FROM videos WHERE channel_id=?", (channel_id,))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Link", style="cyan")
    table.add_column("Video ID")
    table.add_column("Title")

    rows = cur.fetchall()
    for i, row in enumerate(rows):
        video_id = row[0]
        link = f"https://www.youtube.com/watch?v={video_id}"
        link_str = f"[link={link}]Link[/link]"
        title = get_title_from_db(video_id) 

        table.add_row(link_str,video_id, title)

        if i != len(rows) - 1:
            table.add_row("----","-" * len(video_id), "-" * len(title), style="dim")
    
    console = Console()
    console.print(table)

    console.print(f"\n[bold]Total videos: {len(rows)}[/bold]")



def list_channels(channel_id=None):
    from yt_fts.db_utils import get_channels, get_num_vids, get_channel_list_by_id

    table = Table( header_style="bold")
    table.add_column("ID", style="cyan")
    table.add_column("Name",  justify="left")
    table.add_column("Count")
    table.add_column("Channel ID", justify="left")

    if channel_id != None:
        channel = list(get_channel_list_by_id(channel_id)[0])
        channel_url = f"https://youtube.com/channel/{channel_id}"
        count = get_num_vids(channel_id)
        channel.insert(1, count)
        
        id_link = f"[link={channel_url}]{channel_id}[/link]"
        table.add_row(str(channel[0]), channel[2], str(channel[1]), id_link)

        console = Console()
        console.print("")
        console.print(table, justify="left")
        console.print("")
        return 

    raw_channels = get_channels()
    for i in raw_channels:
        row_id = i[0]
        channel_id = i[1]
        channel_name = i[2]

        if check_ss_enabled(channel_id) == True:
            channel_name += " (ss)"

        channel_url = f"https://youtube.com/channel/{channel_id}"
        count = get_num_vids(channel_id)
        id_link = f"[link={channel_url}]{channel_id}[/link]"

        table.add_row(str(row_id), channel_name, str(count), id_link)

    console = Console()
    console.print("")
    console.print(table, justify="left")
    console.print("")


#  not dry but for some reason importing from embeddings.py causes slow down 
def check_ss_enabled(channel_id=None):
    from yt_fts.config import get_db_path

    db_path = get_db_path() 
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    if channel_id is None:
        cur.execute(""" 
            SELECT channel_id FROM SemanticSearchEnabled 
            """)
    else:
        cur.execute(""" 
            SELECT channel_id FROM SemanticSearchEnabled 
            WHERE channel_id = ?
            """, [channel_id])

    res = cur.fetchone()
    if res is None:
        return False 
    else:
        return True 