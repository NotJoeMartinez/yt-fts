import click, tempfile, requests, datetime, csv

from tabulate import tabulate

from yt_fts.db_scripts import *
from yt_fts.download_scripts import *
from yt_fts.utils import *

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


@click.command( help='search [channel_id] [search_text]')
@click.argument('search_text', required=True)
@click.option('--all', is_flag=True, help='Search in all channels')
@click.argument('channel_id', required=False)
def search(channel_id, search_text, all):
    if len(search_text) > 40:
        show_message("search_too_long")
        return

    if all:
        click.echo('Searching in all channels')
        get_text("all", search_text)
    else:
        if channel_id is None:
            click.echo('Error: Channel ID is required when not using --all option')
            return
        click.echo(f'Searching in channel {channel_id}')
        get_text(channel_id, search_text)


@click.command( help="export [channel_id] [search_text]")
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
        export_search("all", search_text, file_name)
    else:
        if channel_id is None:
            click.echo("Error: Channel ID is required when not using --all option")
            return
        file_name = f"{channel_id}_{timestamp}.csv"
        click.echo(f"Exporting search results to csv: {file_name}")
        export_search(channel_id, search_text, file_name)


@click.command( help="delete [channel_id]")
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
