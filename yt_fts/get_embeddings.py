

from typing import Optional, Any
from openai import OpenAI
from datetime import datetime

from pprint import pprint
from rich.progress import track
from rich.console import Console
from .config import get_chroma_client
from .utils import time_to_secs

from .db_utils import (
    get_subs_by_video_id,
    get_metadata_from_db,
    get_vid_ids_by_channel_id,
    get_channel_name_from_id
)

class EmbeddingsHandler:

    def __init__(self, interval: Optional[int]=10) -> None:

        self.interval = interval


    def add_embeddings_to_chroma(self, channel_id: str) -> None:

        channel_name = get_channel_name_from_id(channel_id)
        # channel_video_ids = get_vid_ids_by_channel_id(channel_id)

        channel_video_ids = [video_id[0] for video_id 
                             in get_vid_ids_by_channel_id(channel_id)]

        subs = []
        for video_id in channel_video_ids:

            video_meta_data = get_metadata_from_db(video_id)

            split_subs = self.split_subtitles(video_id)

            if split_subs is None:
                continue

            for sub in split_subs:

                text_with_meta_data = f"""
                    Channel Name: {channel_name}
                    Video Title: {video_meta_data['video_title']}
                    Video Date: {video_meta_data['video_date']}
                    Segment Start Time: {sub['start_time']}

                    Segment Text: 
                    ----------------
                    {sub['text']}
                """
                
                subs.append({
                    'channel_name': channel_name,
                    'channel_id': channel_id,
                    'video_title': video_meta_data['video_title'],
                    'video_date': video_meta_data['video_date'],
                    'video_id': video_id,
                    'start_time': sub['start_time'],
                    'text': sub['text'],
                    'text_with_meta_data': text
                })


        chroma_client = get_chroma_client()
        collection = chroma_client.get_or_create_collection(name="subEmbeddings")

        for sub in track(subs, description="Getting embeddings"):
            channel_id = sub['channel_id']
            video_id = sub['video_id']
            start_time = sub['start_time']
            text = sub['text'] 

            if text == '':
                continue

            embedding = self.get_embedding(text, "text-embedding-ada-002")

            meta_data = {
                "channel_id": channel_id,
                "video_id": video_id,
                "start_time": start_time,
            }

            collection.add(
                documents=[text],
                embeddings=[embedding],
                metadatas=[meta_data],
                ids=[video_id + "_" + str(start_time)],
            )


    def split_subtitles(self, video_id):
        
        subs = get_subs_by_video_id(video_id)
        total_seconds = time_to_secs(subs[-1][1])

        if len(subs) == 0:
            print("Video is too short to split")
            return None

        if total_seconds < self.interval:
            print("Video is too short to split")
            return None

        # Convert timestamps to seconds and store texts
        converted_data = []
        for start_timestamp, stop_timestamp, text in subs:
            converted_data.append({
                'start_timestamp': start_timestamp,
                'start_seconds': self.time_to_seconds(start_timestamp),
                'text': text
            })


        # Split texts into intervals based on self.interval
        interval_texts = {}
        for sub_obj in converted_data:
            split_interval = int(sub_obj['start_seconds'] // self.interval) * self.interval

            if split_interval not in interval_texts:
                interval_texts[split_interval] = {
                    'start_time': sub_obj['start_timestamp'],
                    'texts': []
                }

            interval_texts[split_interval]['texts'].append(sub_obj['text'])
            

        # Combine texts within each interval
        result = []
        for interval_obj in interval_texts.values():

            combined_text = ' '.join(interval_obj['texts']).strip()

            result.append({
                'start_time': interval_obj['start_time'],
                'text': combined_text
            })


        return result


    def get_embedding(self, text, model="text-embedding-ada-002", client=None):

        if client is None:
            client = OpenAI()

        text = text.replace("\n", " ")
        text_embedding = client.embeddings.create(input=[text], model=model).data[0].embedding

        return text_embedding
    

    def time_to_seconds(self, time_str):
        """ Convert time string to total seconds """
        time_obj = datetime.strptime(time_str, '%H:%M:%S.%f').time()
        return (time_obj.hour * 3600 +
                time_obj.minute * 60 +
                time_obj.second +
                    time_obj.microsecond / 1e6)

