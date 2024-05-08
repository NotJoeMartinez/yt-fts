import click
import requests

from .config import get_config_path, get_db_path, get_or_make_chroma_path 
from .db_utils import *
from .download import *
from .list import list_channels
from .update import update_channel
from .utils import *
from rich.console import Console

YT_FTS_VERSION = "0.1.48"

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(YT_FTS_VERSION, message='yt_fts version: %(version)s')
def cli():
    config_path = get_config_path()
    db_path = get_db_path()


# download
@cli.command( 
    help="""
    Download subtitles from a specified YouTube channel.

    You must provide the URL of the channel as an argument. The script will automatically extract the channel id from the URL.
    """
)
@click.argument("url", required=True)
@click.option("-p", "--playlist", is_flag=True, required=False)
@click.option("-l", "--language", default="en", help="Language of the subtitles to download")
@click.option("-j", "--number-of-jobs", type=int, default=1, help="Optional number of jobs to parallelize the run")
def download(url, playlist, language, number_of_jobs):

    console = Console()
    s = requests.session()
    handle_reject_consent_cookie(url, s)

    if playlist == True:
        download_playlist(url, s, language, number_of_jobs)
        return

    # find out if the channel exists on the internet 
    with console.status("[bold green]Getting Channel ID...") as status:
        url = validate_channel_url(url)
        channel_id = get_channel_id(url, s)
   
    if channel_id == None:
        console.print("[bold red]Error:[/bold red] Invalid channel URL or unable to extract channel ID.")
        return

    channel_exists = check_if_channel_exists(channel_id)

    if channel_exists:
        list_channels(channel_id)
        error = "[bold red]Error:[/bold red] Channel already exists in database."
        error += " Use update command to update the channel"
        console.print(error)
        return

    channel_name = get_channel_name(channel_id, s)
    
    if channel_name is None:
        console.print("[bold red]Error:[/bold red] The channel does not exist.")
        return

    dl_status = download_channel(channel_id, channel_name, language, number_of_jobs, s)

    if dl_status is None:
        console.print("[bold red]Error:[/bold red] Unable to download channel.")
        return
    else:
        console.print("[green]Download complete[/green]")


# list 
@cli.command( 
    help="""
    View library, transcripts and channel video list 
    """
)
@click.option("-t", "--transcript", default=None, help="Show transcript for a video")
@click.option("-c", "--channel", default=None, help="Show list of videos for a channel")
@click.option("-l", "--library", is_flag=True, help="Show list of channels in library")
def list(transcript, channel, library):

    from yt_fts.list import show_video_list, show_video_transcript

    if transcript:
        show_video_transcript(transcript)
        exit()
    elif channel:
        channel_id = get_channel_id_from_input(channel)
        show_video_list(channel_id)
    elif library:
        list_channels()
    else:
        list_channels()


# update
@cli.command( 
    help="""
    Updates a specified YouTube channel.

    You must provide the ID of the channel as an argument.
    Keep in mind some might not have subtitles enabled. This command
    will still attempt to download subtitles as subtitles are sometimes added later.
    """
)
@click.option("-c", "--channel", default=None, required=True, help="The name or id of the channel to update.")
@click.option("-l", "--language", default="en", help="Language of the subtitles to download")
@click.option("-j", "--number-of-jobs", type=int, default=1, help="Optional number of jobs to parallelize the run")
def update(channel, language, number_of_jobs):

    channel_id = get_channel_id_from_input(channel)
    channel_url = f"https://www.youtube.com/channel/{channel_id}/videos" 

    s = requests.session()
    handle_reject_consent_cookie(channel_url, s)

    channel_name = get_channel_name(channel_id, s)

    update_channel(channel_id, channel_name, language, number_of_jobs, s)


# Delete
@cli.command( 
    help="""
    Delete a channel and all its data. 

    You must provide the name or the id of the channel you want to delete as an argument. 

    The command will ask for confirmation before performing the deletion. 
    """
)
@click.option("-c", "--channel", default=None, required=True, help="The name or id of the channel to delete")
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


@cli.command(
        help="""
        export transcripts
        """
)
@click.option("-c", "--channel", default=None, required=True, help="The name or id of the channel to export transcripts for")
@click.option("-f", "--format", default="txt", help="The format to export transcripts to. Supported formats: txt, vtt")
def export(channel, format):

    from .export import export_channel_to_txt, export_channel_to_vtt
    console = Console()

    channel_id = get_channel_id_from_input(channel)

    if format == "txt":
        output_dir = export_channel_to_txt(channel_id)
    
    if format == "vtt":
        output_dir = export_channel_to_vtt(channel_id)

    if output_dir != None:
        console.print(f"Exported to [green][bold]{output_dir}[/bold][/green]")

# search
@cli.command(
        help="""
        Search for a specified text within a channel, a specific video, or across all channels.
        """
)
@click.argument("text", required=True)
@click.option("-c", "--channel", default=None, help="The name or id of the channel to search in.")
@click.option("-v", "--video", default=None, help="The id of the video to search in.")
@click.option("-l", "--limit", default=None, type=int, help="Number of results to return")
@click.option("-e", "--export", is_flag=True, help="Export search results to a CSV file.")
def search(text, channel, video, export, limit):

    from yt_fts.search import fts_search, print_fts_res  
    from yt_fts.export import export_fts 

    console = Console()

    if len(text) > 40:
        show_message("search_too_long")
        return

    if channel:
        scope = "channel"
    elif video:
        scope = "video"
    else:
        scope = "all"

    res = fts_search(text, scope, channel_id=channel, video_id=video, limit=limit)
    print_fts_res(res, text)

    if export:
        export_fts(text, scope, channel_id=channel, video_id=video)

    console.print(f"Query '{text}' ")
    console.print(f"Scope: {scope}")


# vsearch
@cli.command(
        help="""
            Vector search. Requires embeddings to be generated for the channel and environment variable OPENAI_API_KEY to be set.
        """
)
@click.argument("text", required=True)
@click.option("-c", "--channel", default=None, help="The name or id of the channel to search in")
@click.option("-v", "--video", default=None, help="The id of the video to search in.")
@click.option("-l", "--limit", default=10, help="Number of results to return")
@click.option("-e", "--export", is_flag=True, help="Export search results to a CSV file.")
@click.option("--openai-api-key", default=None, help="OpenAI API key. If not provided, the script will attempt to read it from the OPENAI_API_KEY environment variable.")
def vsearch(text, channel, video, limit, export, openai_api_key): 
    from openai import OpenAI
    from yt_fts.vector_search import search_chroma_db, print_vector_search_results
    from yt_fts.export import export_vector_search

    console = Console()

    if len(text) > 80:
        show_message("search_too_long")
        exit()

    # get api key for openai
    if  openai_api_key is None:
        openai_api_key = os.environ.get("OPENAI_API_KEY") 

    if openai_api_key is None:
        console.print("""
        [bold][red]Error:[/red][/bold] OPENAI_API_KEY environment variable not set, Run: 
                
                export OPENAI_API_KEY=<your_key> to set the key
                      """)
        return 

    openai_client = OpenAI(api_key=openai_api_key)


    if channel:
        scope = "channel"
    elif video:
        scope = "video"
    else:
        scope = "all"
    
    res = search_chroma_db(text, 
                           scope, 
                           channel_id=channel, 
                           video_id=video, 
                           limit=limit, 
                           openai_client=openai_client)
    
    print_vector_search_results(res, query=text)

    if export:    
        export_vector_search(res, text, scope)

    console.print(f"Query '{text}' ")
    console.print(f"Scope: {scope}")


# get-embeddings 
@cli.command( 
    help="""
    Generate embeddings for a channel using OpenAI's embeddings API.

    Requires an OpenAI API key to be set as an environment variable OPENAI_API_KEY.
    """
)
@click.option("-c", "--channel", default=None, help="The name or id of the channel to generate embeddings for")
@click.option("--openai-api-key", default=None, help="OpenAI API key. If not provided, the script will attempt to read it from the OPENAI_API_KEY environment variable.")
def get_embeddings(channel, openai_api_key):

    from yt_fts.db_utils import get_vid_ids_by_channel_id
    from yt_fts.embeddings import add_embeddings_to_chroma 
    from yt_fts.utils import split_subtitles, check_ss_enabled, enable_ss
    from openai import OpenAI

    console = Console()

    channel_id = get_channel_id_from_input(channel)

    # verify that embeddings have not already been created for the channel
    if check_ss_enabled(channel_id) == True:
        console.print("\n\t[bold][red]Error:[/red][/bold] Embeddings already created for this channel.\n")
        return


    # get api key for openai
    if  openai_api_key is None:
        openai_api_key = os.environ.get("OPENAI_API_KEY") 

    if openai_api_key is None:
        console.print("""
        [bold][red]Error:[/red][/bold] OPENAI_API_KEY environment variable not set, Run: 
                
                export OPENAI_API_KEY=<your_key> to set the key
                      """)
        return 

    openai_client = OpenAI(api_key=openai_api_key)

    channel_video_ids = get_vid_ids_by_channel_id(channel_id) 

    channel_subs = []
    for vid_id in channel_video_ids:
        split_subs = split_subtitles(vid_id[0])
        if split_subs is None:
            continue
        for sub in split_subs:
            start_time = sub[0]
            text = sub[1]
            embedding_subs = (channel_id, vid_id[0], start_time, text)
            channel_subs.append(embedding_subs)



    add_embeddings_to_chroma(channel_subs, openai_client)

    # mark the channel as enabled for semantic search 
    enable_ss(channel_id)
    console.print("[green]Embeddings generated[/green]")


# connfig
@cli.command(
    help = """
    Show config settings
    """
)
def config():
    config_path = get_config_path()
    db_path = get_db_path()
    chroma_path = get_or_make_chroma_path()

    console = Console()

    config_path = get_config_path()

    console.print(f"\nConfig directory: {config_path}\n")
    console.print(f"Database path: {db_path}\n")
    console.print(f"Chroma path: {chroma_path}\n")