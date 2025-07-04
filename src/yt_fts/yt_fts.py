import os
import sys
import click

from openai import OpenAI
from rich.console import Console

from .download.download_handler import DownloadHandler
from .llm.summarize import SummarizeHandler
from .export import ExportHandler 
from .search import SearchHandler

from .list import list_channels
from .utils import show_message
from .config import (
    get_config_path,
    get_db_path,
    get_or_make_chroma_path
)
from .db_utils import (
    get_channel_id_from_input,
    get_channel_name_from_id,
    delete_channel
)
from . import __version__ as YT_FTS_VERSION

console = Console()

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(YT_FTS_VERSION, message='yt_fts version: %(version)s')
def cli() -> None:
    pass


@cli.command(
    name="download",
    help="""
    Download subtitles from a specified YouTube channel.

    You must provide the URL of the channel as an argument. 
    The script will automatically extract the channel id from the URL.
    """
)
@click.argument("url", required=True)
@click.option("-p", "--playlist", is_flag=True, required=False,
              help="Download all videos from a playlist")
@click.option("-l", "--language", default="en",
              help="Language of the subtitles to download")
@click.option("-j", "--jobs", type=int, default=8,
              help="Number of parallel download jobs (default: 8, recommended: 4-16 for most users)")
@click.option("--cookies-from-browser", default=None,
              help="Browser to extract cookies from. Ex: chrome, firefox")
def download(url: str, playlist: bool, language: str, jobs: int, cookies_from_browser: str | None) -> None:
    download_handler = DownloadHandler(
        number_of_jobs=jobs,
        language=language,
        cookies_from_browser=cookies_from_browser
    )

    if playlist:
        if "playlist?" not in url:
            console.print(f"\n[bold red]Error:[/bold red] Invalid playlist url {url}\n")
            console.print("YouTube playlists have this format: "
                          "\"https://www.youtube.com/playlist?list=<playlist_id>\"\n")
            sys.exit(1)
        download_handler.download_playlist(url, language, jobs)
        sys.exit(0)

    download_handler.download_channel(url)
    sys.exit(0)


@cli.command(
    name="diagnose",
    help="""
    Diagnose 403 errors and other download issues.
    
    This command will test various aspects of the connection to YouTube
    and provide recommendations for fixing common issues.
    """
)
@click.option("-u", "--test-url", default="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
@click.option("--cookies-from-browser", default=None,
              help="Browser to extract cookies from. Ex: chrome, firefox")
@click.option("-j", "--jobs", type=int, default=8,
              help="Number of parallel download jobs to test with")
def diagnose(test_url: str, cookies_from_browser: str | None, jobs: int) -> None:
    from .download.download_handler import DownloadHandler
    
    download_handler = DownloadHandler(
        number_of_jobs=jobs,
        cookies_from_browser=cookies_from_browser
    )
    
    download_handler.diagnose_403_errors(test_url)
    sys.exit(0)


@cli.command(
    name="list",
    help="""
    View library, transcripts and channel video list 
    """
)
@click.option("-t", "--transcript", default=None, help="Show transcript for a video")
@click.option("-c", "--channel", default=None, help="Show list of videos for a channel")
@click.option("-l", "--library", is_flag=True, help="Show list of channels in library")
def list(transcript: str | None, channel: str | None, library: bool) -> None:
    from .list import show_video_list, show_video_transcript

    if transcript:
        show_video_transcript(transcript)
    elif channel:
        channel_id = get_channel_id_from_input(channel)
        show_video_list(channel_id)
    elif library:
        list_channels()
    else:
        list_channels()

    sys.exit(0)


@cli.command(
    name="update",
    help="""
    Update subtitles for all channels in the library or a specific channel. 
    
    Keep in mind some might not have subtitles enabled. This command will 
    still attempt to download subtitles as subtitles are sometimes added later.
    """
)
@click.option("-c", "--channel",
              default=None, help="The name or id of the channel to update.")
@click.option("-l", "--language",
              default="en", help="Language of the subtitles to download")
@click.option("-j", "jobs",
              type=int, default=8, help="Number of parallel download jobs (default: 8, recommended: 4-16 for most users)")
@click.option("--cookies-from-browser",
              default=None,
              help="Browser to extract cookies from. Ex: chrome, firefox")
def update(channel: str | None, language: str, jobs: int, cookies_from_browser: str | None) -> None:
    update_handler = DownloadHandler(
        language=language,
        number_of_jobs=jobs,
        cookies_from_browser=cookies_from_browser
    )

    if channel is not None:
        update_handler.update_channel(channel)
        sys.exit(0)

    update_handler.update_all_channels()

    sys.exit(0)


@cli.command(
    name="delete",
    help="""
    Delete a channel and all its data. 

    You must provide the name or the id of the channel you want to delete as an argument. 
    The command will ask for confirmation before performing the deletion. 
    """
)
@click.option("-c", "--channel", default=None, required=True, help="The name or id of the channel to delete")
def delete(channel: str) -> None:
    channel_id = get_channel_id_from_input(channel)
    channel_name = get_channel_name_from_id(channel_id)
    channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"

    console.print(f"Deleting channel [bold]\"{channel_name}\"[/bold]: {channel_url}")
    console.print("[bold]Are you sure you want to delete this channel and all its data?[/bold]")
    confirm = input("(Y/n): ")

    if confirm.lower() == "y":
        delete_channel(channel_id)
        console.print(f"Deleted channel \"{channel_name}\": \"{channel_url}\"")
    else:
        print("Exiting")

    sys.exit(0)


@cli.command(
    name="export",
    help="""
        export transcripts
        """
)
@click.option("-c", "--channel", default=None, required=True,
              help="The name or id of the channel to export transcripts for")
@click.option("-f", "--format", default="txt",
              help="The format to export transcripts to. Supported formats: txt, vtt")
def export(channel: str, format: str) -> None:

    export_handler = ExportHandler(
        scope = "channel",
        format=format,
        channel=channel
    )
    
    export_handler.export()



@cli.command(
    name="search",
    help="""
        Search for a specified text within a channel, a specific video, or across all channels.
        """
)
@click.argument("text", required=True)
@click.option("-c", "--channel", default=None, help="The name or id of the channel to search in.")
@click.option("-v", "--video-id", default=None, help="The id of the video to search in.")
@click.option("-l", "--limit", default=10, type=int, help="Number of results to return")
@click.option("-e", "--export", is_flag=True, help="Export search results to a CSV file.")
def search(text: str, channel: str | None, video_id: str | None, export: bool, limit: int) -> None:

    if len(text) > 40:
        show_message("search_too_long")
        sys.exit(1)

    if channel:
        scope = "channel"
    elif video_id:
        scope = "video"
    else:
        scope = "all"

    search_handler = SearchHandler(
        scope=scope,
        video_id=video_id,
        channel=channel,
        export=export,
        limit=limit
    )

    search_handler.full_text_search(text)
    sys.exit(0)


@cli.command(
    name="vsearch",
    help="""
            Vector search. Requires embeddings to be generated for the channel
            and environment variable OPENAI_API_KEY to be set.
        """
)
@click.argument("text", required=True)
@click.option("-c", "--channel", default=None, help="The name or id of the channel to search in")
@click.option("-v", "--video-id", default=None, help="The id of the video to search in.")
@click.option("-l", "--limit", default=10, help="Number of results to return")
@click.option("-e", "--export", is_flag=True, help="Export search results to a CSV file.")
@click.option("--openai-api-key", default=None,
              help="OpenAI API key. If not provided, the script will attempt to read it from the OPENAI_API_KEY "
                   "environment variable.")
def vsearch(text: str, channel: str | None, video_id: str | None, limit: int, export: bool, openai_api_key: str | None) -> None:

    if openai_api_key is None:
        openai_api_key = os.environ.get("OPENAI_API_KEY")

    if openai_api_key is None:
        console.print("[red]Error:[/red] OPENAI_API_KEY environment variable not set\n"
                      "To set the key run: export \"OPENAI_API_KEY=<your_key>\" or pass "
                      "one in with --openai-api-key")
        sys.exit(1)

    if channel:
        scope = "channel"
    elif video_id:
        scope = "video"
    else:
        scope = "all"

    openai_client = OpenAI(api_key=openai_api_key)

    vsearch_handler = SearchHandler(
        scope=scope,
        channel=channel,
        video_id=video_id,
        export=export,
        limit=limit,
        openai_client=openai_client
    )

    vsearch_handler.vector_search(query=text)

    sys.exit(0)


@cli.command(
    name="embeddings",
    help="""
    Generate embeddings for a channel using OpenAI's embeddings API.
    Requires an OpenAI API key to be set as an environment variable OPENAI_API_KEY.
    """
)
@click.option("-c", "--channel", default=None,
              help="The name or id of the channel to generate embeddings for")
@click.option("--openai-api-key", default=None,
              help="OpenAI API key. If not provided, the script will attempt to read it from"
                   " the OPENAI_API_KEY environment variable.")
@click.option("-i", "--interval", default=30, type=int,
              help="Interval in seconds to split the transcripts into chunks. Default 30s.")
def embeddings(channel: str | None, openai_api_key: str | None, interval: int = 30) -> None:
    from .llm.get_embeddings import EmbeddingsHandler
    from .utils import check_ss_enabled, enable_ss

    channel_id = get_channel_id_from_input(channel)

    # verify that embeddings have not already been created for the channel
    if check_ss_enabled(channel_id):
        console.print("\n\t[bold][red]Error:[/red][/bold] Embeddings already created for this channel.\n")
        sys.exit(1)

    # get api key for openai
    if openai_api_key is None:
        openai_api_key = os.environ.get("OPENAI_API_KEY")

    if openai_api_key is None:
        console.print("""
        [bold][red]Error:[/red][/bold] OPENAI_API_KEY environment variable not set, Run: 
                
                export OPENAI_API_KEY=<your_key> to set the key
                      """)
        sys.exit(1)

    embeddings_handler = EmbeddingsHandler(interval=interval)
    embeddings_handler.add_embeddings_to_chroma(channel_id)

    # mark the channel as enabled for semantic search
    enable_ss(channel_id)
    console.print("[green]Embeddings generated[/green]")
    sys.exit(0)


@cli.command(
    name="llm",
    help="""
        Interactive LLM/RAG chat bot, needs to be run on a channel with 
        Embeddings.
    """
)
@click.argument("prompt", required=True)
@click.option("-c", "--channel", default=None, required=True,
              help="The name or id of the channel to generate embeddings for")
@click.option("--openai-api-key", default=None,
              help="OpenAI API key. If not provided, the script will attempt to read it from"
                   " the OPENAI_API_KEY environment variable.")
def llm(prompt: str, channel: str, openai_api_key: str | None = None) -> None:
    from .llm.chatbot import LLMHandler

    if openai_api_key is None:
        openai_api_key = os.environ.get("OPENAI_API_KEY")

    if openai_api_key is None:
        console.print("""
        [bold][red]Error:[/red][/bold] OPENAI_API_KEY environment variable not set, Run: 
                
                export OPENAI_API_KEY=<your_key> to set the key
                      """)
        sys.exit(1)

    llm_handler = LLMHandler(openai_api_key, channel)
    llm_handler.init_llm(prompt)

    sys.exit(0)


@cli.command(
    name="summarize",
    help="summarize a youtube video"
)
@click.argument("video", required=True)
@click.option("--model", "-m", default="gpt-4o",
              help="Model to use in summary")
@click.option("--openai-api-key", default=None,
              help="OpenAI API key. If not provided, the script will attempt to read it from"
                   " the OPENAI_API_KEY environment variable.")
def summarize(video: str, model: str, openai_api_key: str | None) -> None:
    if openai_api_key is None:
        openai_api_key = os.environ.get("OPENAI_API_KEY")

    if openai_api_key is None:
        console.print("[red]Error:[/red] OPENAI_API_KEY environment variable not set\n"
                      "To set the key run: export \"OPENAI_API_KEY=<your_key>\" or pass "
                      "one in with --openai-api-key")
        sys.exit(1)
        
    openai_client = OpenAI(api_key=openai_api_key)

    summarize_handler = SummarizeHandler(
        openai_client,
        model=model,
        input_video=video
        )
    summarize_handler.summarize_video()


@cli.command(
    help="""
    Show config settings
    """
)
def config() -> None:
    db_path = get_db_path()
    chroma_path = get_or_make_chroma_path()
    config_path = get_config_path()

    console.print(f"Config directory: {config_path}")
    console.print(f"Database path: {db_path}")
    console.print(f"Chroma path: {chroma_path}")
    sys.exit(0)
