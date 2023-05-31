import click, tempfile, requests, datetime, csv

from tabulate import tabulate

from yt_fts.db_scripts import *
from yt_fts.download_scripts import *
from yt_fts.utils import *

YT_FTS_VERSION = "0.1.12"

@click.group()
@click.version_option(YT_FTS_VERSION, message='yt_fts version: %(version)s')
def cli():
    make_db()


@click.command(help="Lists channels")
def list():
    channels = get_channels()
    print(tabulate(channels, headers=["id", "channel_name", "channel_url"]))


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


@click.command(help="Search for a specified text within a channel or all channels. SEARCH_TEXT is the text to search for. CHANNEL is the name or id of the channel to search in. CHANNEL is required unless the '--all' option is specified.")
@click.argument('search_text', required=True)
@click.option('--all', is_flag=True, help='Search in all channels. If ied, a channel name or id is required.')
@click.argument('channel', required=False)
def search(channel, search_text, all):

    if len(search_text) > 40:
        show_message("search_too_long")
        exit()

    if all == True:
        print('Searching in all channels')
        get_text("all", search_text)
    elif channel == None:
        print('Error: Channel name or id is required when not using --all option')
        exit()
    else:
        channel_id = get_channel_id_from_input(channel)
        channel_name = get_channel_name_from_id(channel_id)
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
        print(f"Searching in channel \"{channel_name}\": {channel_url}")
        get_text(channel_id, search_text)


@click.command( help="export [channel_id] [search_text]")
@click.argument("search_text", required=True)
@click.option("--all", is_flag=True, help="Export from all channels")
@click.argument('channel', required=False)
def export(channel, search_text, all):
    if len(search_text) > 40:
        show_message("search_too_long")
        exit() 

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    if all:
        file_name = f"all_{timestamp}.csv"
        click.echo(f"Exporting search results from all channels to csv: {file_name}")
        export_search("all", search_text, file_name)
    else:
        channel_id = get_channel_id_from_input(channel)
        file_name = f"{channel_id}_{timestamp}.csv"
        click.echo(f"Exporting search results to csv: {file_name}")
        export_search(channel_id, search_text, file_name)


@click.command( help="delete [id] or [\"channel_name\"]")
@click.argument("channel", required=True)
def delete(channel):

    channel_id = get_channel_id_from_input(channel)
    channel_name = get_channel_name_from_id(channel_id) 
    channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"

    print(f"Deleting channel {channel_name}: {channel_url}")
    print("Are you sure you want to delete this channel and all its data?")
    confirm = input("y/n: ")

    if confirm == "y":
        delete_channel(channel_id)
        print(f"Deleted channel {channel_name}: {channel_url}")
    else:
        print("Exiting")


commands = [list, download, search, delete, export]

for command in commands:
    cli.add_command(command)


def download_channel(channel_id, channel_name, language, number_of_jobs, s):
    """
    Downloads all the videos from a channel to a tmp directory
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
        list_of_videos_urls = get_videos_list(channel_url)
        download_vtts(number_of_jobs, list_of_videos_urls, language, tmp_dir)
        add_channel_info(channel_id, channel_name, channel_url)
        vtt_to_db(channel_id, tmp_dir, s)


def get_text(channel_id, text):
    """
    Calls search functions and prints the results 
    """
    if channel_id == "all":
        res = search_all(text)
    else:
        res = search_channel(channel_id, text)

    if len(res) == 0:
        show_message("no_matches_found")
        exit()

    for quote in res:
        video_id = quote["video_id"]
        subs = quote["text"]
        time_stamp = quote["timestamp"]
        video_title = get_title_from_db(video_id)
        channel_name = get_channel_name_from_video_id(video_id)
        time = time_to_secs(time_stamp) 

        print("")
        print(f"{channel_name}: \"{video_title}\"")
        print(f"") 
        print(f"    Quote: \"{subs.strip()}\"")
        print(f"    Time Stamp: {time_stamp}")
        print(f"    Link: https://youtu.be/{video_id}?t={time}\n")


def export_search(channel_id, text, file_name):
    """
    Calls search functions and exports the results to a csv file
    """
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


def get_channel_id_from_input(channel_input):
    """
    Checks if the input is a rowid or a channel name and returns channel id
    """
    name_res = get_channel_id_from_name(channel_input) 
    id_res = get_channel_id_from_rowid(channel_input) 

    if id_res != None:
        return id_res
    elif name_res != None: 
        return name_res
    else:
        show_message("channel_not_found")
        exit()
    