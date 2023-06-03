from tabulate import tabulate
from yt_fts.db_utils import get_channels, get_num_vids, get_channel_list_by_id
import sqlite3

def list_channels(channel_id=None):

    if channel_id != None:
        channel = list(get_channel_list_by_id(channel_id)[0])
        channel[2] = f"https://youtube.com/channel/{channel_id}"
        count = get_num_vids(channel_id)
        channel.insert(1, count)
        print(tabulate([channel], headers=["id", "count", "channel_name", "channel_url"]))
        exit()

    raw_channels = get_channels()
    channels = []
    for i in raw_channels:
        row_id = i[0]
        channel_id = i[1]
        channel_name = i[2]

        if check_ss_enabled(channel_id) == True:
            channel_name += " (ss)"

        channel_url = f"https://youtube.com/channel/{channel_id}"
        count = get_num_vids(channel_id)
        channels.append([row_id, count, channel_name, channel_url])

    print(tabulate(channels, headers=["id", "count", "channel_name", "channel_url"]))

#  not dry but for some reason importing from embeddings.py causes slow down 
def check_ss_enabled(channel_id=None):
    con = sqlite3.connect("subtitles.db")
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