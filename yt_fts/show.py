import sqlite3 

from rich.console import Console
from rich.table import Table


from yt_fts.db_utils import get_title_from_db 
from yt_fts.utils import time_to_secs, get_time_delta

def show_video_transcript(video_id):
    con = sqlite3.connect('subtitles.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM subtitles WHERE video_id=?", (video_id,))
    rows = cur.fetchall()

    console = Console()
    word_count = 0
    for row in rows:
        timestamp = row[2]
        time = time_to_secs(timestamp)
        url = f"https://www.youtube.com/watch?v={video_id}&t={time}s"
        text = row[3]
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
    con = sqlite3.connect('subtitles.db')
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