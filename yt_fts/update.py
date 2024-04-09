import tempfile, os

from .download import get_videos_list, download_vtts, vtt_to_db
from .db_utils import add_channel_info, get_num_vids, get_vid_ids_by_channel_id

def update_channel(channel_id, channel_name, language, number_of_jobs, s):
    """
    Downloads all the videos from a channel to a tmp directory
    """
    with tempfile.TemporaryDirectory() as tmp_dir:

        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"

        public_video_ids = get_videos_list(channel_url)
        num_public_vids = len(public_video_ids)
        num_local_vids = get_num_vids(channel_id)

        if num_public_vids == num_local_vids:
            print("No new videos to download")
            exit()

        local_vid_ids = get_vid_ids_by_channel_id(channel_id)
        local_vid_ids = [i[0] for i in local_vid_ids]


        fresh_videos = [i for i in public_video_ids if i not in local_vid_ids]

        print(f"Found {len(fresh_videos)} videos on \"{channel_name}\" not in the database")
        print(f"Downloading {len(fresh_videos)} new videos from \"{channel_name}\"")

        download_vtts(number_of_jobs, fresh_videos, language, tmp_dir)

        vtt_to_parse = os.listdir(tmp_dir)
        if len(vtt_to_parse) == 0:
            print("No new videos saved")
            print(f"{len(fresh_videos)} videos on \"{channel_name}\" do not have subtitles")
            exit()

        vtt_to_db(tmp_dir)

        print(f"Added {len(vtt_to_parse)} new videos from \"{channel_name}\" to the database")