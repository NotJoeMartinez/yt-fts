from tabulate import tabulate

from yt_fts.db_utils import get_channels, get_num_vids, get_channel_list_by_id

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
        channel_url = f"https://youtube.com/channel/{channel_id}"
        count = get_num_vids(channel_id)
        channels.append([row_id, count, channel_name, channel_url])

    print(tabulate(channels, headers=["id", "count", "channel_name", "channel_url"]))
