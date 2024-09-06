import sys
from urllib.parse import urlparse, parse_qs

from rich.console import Console

# determine if input_video is url or video id 
# if it's a url get the video id 
# check if the video id is in database
# if video id is in database get the full transcript
# if the video id is not in the database download the transcript
# feed the transcript to an llm and print the summary


class SummarizeHandler:
    def __init__(self, openai_client, input_video):

        self.console = Console()
        self.openai_client = openai_client
        self.input_video = input_video

        if "https" in input_video:
            self.video_id = self.get_video_id_from_url(input_video)
        else:
            self.video_id = input_video
 
    
    
    def summarize_video(self):
        console = self.console
        input_video = self.input_video

           

    def get_video_id_from_url(self, video_url):
        # https://www.youtube.com/watch?v=Xjk6d5fPs_k
        # https://youtu.be/Xjk6d5fPs_k?si=BBb2URutUT2gG4th
        # https://youtu.be/Xjk6d5fPs_k
        # https://www.youtube.com/watch?v=Xjk6d5fPs_k&si=BBb2URutUT2gG4th

        console = self.console
        video_url = video_url.strip('/')
        parsed = urlparse(video_url)
        domain = parsed.netloc
        path = parsed.path.split('/')
        query = parse_qs(parsed.query)

        valid_domains = ["youtube.com", "youtu.be", "www.youtube.com"]

        if domain not in valid_domains:
            console.print("[red]Error:[/red] "
                          f"Invalid URL, domain \"{domain}\" not supported.")
            sys.exit(1)

        
        if domain in ["youtube.com", "www.youtube.com"] and "watch" in path:
            video_id = query.get('v', [None])[0]
        elif domain == "youtu.be":
            video_id = path[-1]
        else:
            console.print("[red]Error:[/red] "
                          "Invalid URL, please provide a valid YouTube video URL.")
            sys.exit(1)

        if video_id:
            return video_id
        
        console.print("[red]Error:[/red] "
                      "Invalid URL, please provide a valid YouTube video URL.")
        sys.exit(1)

   