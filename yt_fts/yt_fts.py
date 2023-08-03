import click
import requests

from .config import get_config_path, get_db_path, make_config_dir
from .db_utils import *
from .download import *
from .list import list_channels
from .search import get_text, get_text_by_video_id
from .update import update_channel
from .utils import *
from rich.console import Console

YT_FTS_VERSION = "0.1.31"

@click.group()
@click.version_option(YT_FTS_VERSION, message='yt_fts version: %(version)s')
def cli():

    config_path = get_config_path()
    if config_path is None:
        new_config_path = make_config_dir()
        if new_config_path is None:
            print("Error: Could not create config directory, database will be saved in current directory")
            make_db("subtitles.db")
        else:
            new_db_path = os.path.join(new_config_path, "subtitles.db") 
            make_db(new_db_path)
            print(f"Your subtitles database has been saved to: {new_db_path}")
    else:
        db_path = get_db_path()
        make_db(db_path)

    db_path = get_db_path()
    make_db(db_path)



# download
@cli.command( 
    help="""
    Download subtitles from a specified YouTube channel.

    You must provide the URL of the channel as an argument. The script will automatically extract the channel id from the URL.
    """
)
@click.argument("channel_url", required=True)
@click.option("-l", "--language", default="en", help="Language of the subtitles to download")
@click.option("-j", "--number-of-jobs", type=int, default=1, help="Optional number of jobs to parallelize the run")
def download(channel_url, language, number_of_jobs):
    console = Console()
    s = requests.session()


    # find out if the channel exists on the internet 
    with console.status("[bold green]Getting Channel ID...") as status:
        channel_url = validate_channel_url(channel_url)
        handle_reject_consent_cookie(channel_url, s)
        channel_id = get_channel_id(channel_url, s)
   
    if channel_id is None:
        console.print("[bold red]Error:[/bold red] Invalid channel URL or unable to extract channel ID.")
        return

    """__Schrodinger's Channel ID__

    Alright, Now that we know it exists on the internet, let's find out 
    if we had it all along to begin with! What's that you're saying? 
    We should have checked this before making the request? Well, that's 
    just because you're not thinking like a 10x developer.
    
    You see, I program in a state of quantum superposition. 
    
    While you might think it's more efficient to check if the data exists 
    in the local database before wasting bandwidth making a request to 
    the internet. A Superpositionist, such as myself, knows that the data 
    actually exists in both states at the same time! 
     
    However, it is only when we observe the data that it collapses into a 
    single state. And because our database was designed in such brilliant 
    way that we must first observe remote data to actually know if it exists,

    one might say that. 

    We are in a state of quantum entanglement with the data.
 
    """
    channel_exists = check_if_channel_exists(channel_id)

    if channel_exists:
        list_channels(channel_id)
        error = "[bold red]Error:[/bold red] Channel already exists in database."
        error += " Use update command to update the channel"
        console.print(error)
        return

    handle_reject_consent_cookie(channel_url, s)
    channel_name = get_channel_name(channel_id, s)
    
    if channel_name is None:
        console.print("[bold red]Error:[/bold red] The channel does not exist.")
        return

    download_channel(channel_id, channel_name, language, number_of_jobs, s)



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


# search
@cli.command(
        help="""
        Search for a specified text within a channel, a specific video, or across all channels.
        """
)
@click.argument("text", required=True)
@click.option("-c", "--channel", default=None, help="The name or id of the channel to search in. This is required unless the --all or --video options are used.")
@click.option("-v", "--video", default=None, help="The id of the video to search in. This is used instead of the channel option.")
@click.option("-a", "--all", is_flag=True, help="Search in all channels.")
@click.option("-s", "--semantic", is_flag=True, help="Use Semantic Search")
@click.option("-l", "--limit", default=5, help="Max number of results to return")
@click.option("-e", "--export", is_flag=True, help="Export search results to a CSV file.")
def search(text, channel, video, all, semantic, limit, export):

    from yt_fts.export import export_fts, export_semantic 

    if len(text) > 40:
        show_message("search_too_long")
        exit()

    if channel:
        scope = "channel"
        search_id = get_channel_id_from_input(channel)
    elif video:
        scope = "video"
        search_id = video 
    elif all:
        scope = "all"
        search_id = ""
    
    
    if export:
        if semantic:
            export_semantic(text, search_id, scope, limit)
        else:
            export_fts(text, search_id, scope)
        exit()


    if semantic:
        from yt_fts.search import semantic_search
        semantic_search(text, search_id, scope, limit)
        exit()


    if all:
        print('Searching in all channels')
        get_text("all", text)
    elif video:
        print(f"Searching in video {video}")
        get_text_by_video_id(video, text)
    elif channel:
        channel_id = get_channel_id_from_input(channel)
        get_text(channel_id, text)
    else:
        print("Error: Either --channel, --video, or --all option must be provided")
        exit()


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


# Show
@cli.command( 
    help="""
    View library, transcripts, channel video list and config settings.
    """
)

@click.option("-t", "--transcript", default=None, help="Show transcript for a video")
@click.option("-c", "--channel", default=None, help="Show list of videos for a channel")
@click.option("-l", "--library", is_flag=True, help="Show list of channels in library")
@click.option("--config", is_flag=True, help="Show path to config directory")
def list(transcript, channel, library, config):

    from yt_fts.list import show_video_list, show_video_transcript

    if transcript:
        show_video_transcript(transcript)
        exit()
    elif channel:
        channel_id = get_channel_id_from_input(channel)
        show_video_list(channel_id)
    elif library:
        list_channels()
    elif config:
        config_path = get_config_path()
        print(f"Config path: {config_path}")
        exit()
    else:
        list_channels()



# Generate embeddings
@cli.command( 
    help="""
    Generate embeddings for a channel using OpenAI's embeddings API.

    Requires an OpenAI API key to be set as an environment variable OPENAI_API_KEY.
    """
)
@click.option("-c", "--channel", default=None, help="The name or id of the channel to generate embeddings for")
@click.option("--api-key", default=None, help="OpenAI API key. If not provided, the script will attempt to read it from the OPENAI_API_KEY environment variable.")
def get_embeddings(channel, api_key):

    from yt_fts.embeddings import get_openai_embeddings
    from yt_fts.search import check_ss_enabled, enable_ss
    console = Console()
    

    channel_id = get_channel_id_from_input(channel)

    # verify that embeddings have not already been created for the channel
    if check_ss_enabled(channel_id) == True:
        console.print("\n\t[bold][red]Error:[/red][/bold] Embeddings already created for this channel.\n")
        return

    # get api key for openai
    if  api_key is None:
        api_key = get_api_key()

    if api_key is None:
        console.print("""
        [bold][red]Error:[/red][/bold] OPENAI_API_KEY environment variable not set, Run: 
                
                export OPENAI_API_KEY=<your_key> to set the key
                      """)
        return 

    channel_subs = get_all_subs_by_channel_id(channel_id)
    get_openai_embeddings(channel_subs, api_key)

    # mark the channel as enabled for semantic search 
    enable_ss(channel_id)
    console.print("[green]Embeddings generated[/green]")


