import tempfile, os

from .download import get_videos_list, download_vtts, vtt_to_db
from .db_utils import get_num_vids, get_vid_ids_by_channel_id

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

        vtt_to_db(channel_id, tmp_dir, s)

        print(f"Added {len(vtt_to_parse)} new videos from \"{channel_name}\" to the database")


# I don't have a way to test this other than waiting for a channel to update

def update_embeddings(channel_id):
    import chromadb
    import OpenAI
    from .utils import split_subtitles
    from .config import get_or_make_chroma_path
    from .embeddings import add_embeddings_to_chroma

    sqlite_vids = get_vid_ids_by_channel_id(channel_id)

    chroma_path = get_or_make_chroma_path()
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    collection = chroma_client.get_collection(name="subEmbeddings")

    chroma_documents = collection.get(
        where={"channel_id": channel_id},
        )


    # make a list of video ids in chroma 
    chroma_vid_ids = []
    for meta in chroma_documents["metadatas"]:
        chroma_vid_ids.append(meta["video_id"])
    chroma_vid_ids = set(chroma_vid_ids)


    # make new list of video ids in sqlite but not chroma
    vids_to_update = []
    for vid in sqlite_vids:
        if vid[0] not in chroma_vid_ids:
            vids_to_update.append(vid[0])


    print(f"Found {len(vids_to_update)} videos to update in chroma")

    # essentially do the same as get-embeddings but with new vids
    new_chroma_subs = []
    for vid_id in vids_to_update:
        split_subs = split_subtitles(vid_id[0])
        if split_subs is None:
            continue
        for sub in split_subs:
            start_time = sub[0]
            text = sub[1]
            embedding_subs = (channel_id, vid_id[0], start_time, text)
            new_chroma_subs.append(embedding_subs)

    add_embeddings_to_chroma(new_chroma_subs, OpenAI())
