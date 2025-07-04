import uuid
from openai import OpenAI
from datetime import datetime
from rich.progress import track
from rich.console import Console
from ..config import get_chroma_client
from ..utils import time_to_secs

from ..db_utils import (
    get_subs_by_video_id,
    get_metadata_from_db,
    get_vid_ids_by_channel_id,
    get_channel_name_from_id
)


class EmbeddingsHandler:

    def __init__(self, interval: int = 10) -> None:

        self.interval = interval
        self.console = Console()

    def add_embeddings_to_chroma(self, channel_id: str) -> None:

        channel_name = get_channel_name_from_id(channel_id)
        channel_video_ids = [video_id[0] for video_id
                             in get_vid_ids_by_channel_id(channel_id)]

        formatted_segments = []
        for video_id in channel_video_ids:

            split_subs = self.split_subtitles(video_id)
            video_meta_data = get_metadata_from_db(video_id)

            if split_subs is None:
                continue

            for segment in split_subs:
                text_with_meta_data = self.add_meta_data_to_text(
                    channel_name,
                    video_meta_data['video_title'],
                    video_meta_data['video_date'],
                    segment
                )
                formatted_segments.append({
                    'channel_name': channel_name,
                    'channel_id': channel_id,
                    'video_title': video_meta_data['video_title'],
                    'video_date': video_meta_data['video_date'].strftime('%Y-%m-%d'),
                    'video_id': video_id,
                    'start_time': segment['start_time'],
                    'text': segment['text'],
                    'text_with_meta_data': text_with_meta_data,
                })

        chroma_client = get_chroma_client()
        collection = chroma_client.get_or_create_collection(name="subEmbeddings")

        for segment_object in track(formatted_segments, description="Getting embeddings"):
            if segment_object['text'] == '':
                continue

            embedding = self.get_embedding(
                segment_object['text_with_meta_data'],
                "text-embedding-ada-002"
            )

            meta_data = {
                "channel_id": segment_object['channel_id'],
                "channel_name": segment_object['channel_name'],
                "video_id": segment_object['video_id'],
                "start_time": segment_object['start_time'],
                "video_title": segment_object['video_title'],
                "video_date": segment_object['video_date'],
            }

            collection.add(
                documents=[segment_object['text']],
                embeddings=[embedding],
                metadatas=[meta_data],
                ids=[f"{uuid.uuid4()}"],
            )

    def add_meta_data_to_text(self,
                              channel_name: str,
                              video_title: str,
                              video_date: datetime.date,
                              segment: dict[str, str]) -> str:
        metadata = {
            "video_title": video_title,
            "channel_name": channel_name,
            "video_date": video_date,
            "segment_start_time": segment['start_time']
        }

        text_with_metadata = "---\n"
        text_with_metadata += "\n".join([f"{key}: {value}" for key, value in metadata.items()])
        text_with_metadata += f"\n---\n\nContent:\n\n{segment['text']}"

        return text_with_metadata

    def split_subtitles(self, video_id: str) -> list[dict[str, str]] | None:

        raw_subtitles = get_subs_by_video_id(video_id)

        if len(raw_subtitles) == 0:
            print(f"Error: No subtitles found for video: {video_id}")
            return None

        total_seconds = time_to_secs(raw_subtitles[-1][1])

        if total_seconds < self.interval:
            self.console.print(f"https://youtu.be/{video_id} is too short to split with the given interval.")
            return None

        # Convert timestamps to seconds and store texts
        segments_with_seconds = []
        for start_timestamp, stop_timestamp, text in raw_subtitles:
            segments_with_seconds.append({
                'start_timestamp': start_timestamp,
                'start_seconds': self.time_to_seconds(start_timestamp),
                'text': text
            })

        # Split texts into intervals based on self.interval
        segment_intervals = {}
        for sub_obj in segments_with_seconds:

            split_interval = int(sub_obj['start_seconds'] // self.interval) * self.interval

            if split_interval not in segment_intervals:
                segment_intervals[split_interval] = {
                    'start_time': sub_obj['start_timestamp'],
                    'texts': []
                }

            segment_intervals[split_interval]['texts'].append(sub_obj['text'])

        # Combine texts within each interval
        combined_intervals = []
        for interval_obj in segment_intervals.values():
            combined_text = ' '.join(interval_obj['texts']).strip()

            combined_intervals.append({
                'start_time': interval_obj['start_time'],
                'text': combined_text
            })

        return combined_intervals

    def get_embedding(self, text: str, model: str = "text-embedding-ada-002", client: OpenAI | None = None) -> list[float]:

        if client is None:
            client = OpenAI()

        text = text.replace("\n", " ")
        text_embedding = client.embeddings.create(input=[text], model=model).data[0].embedding

        return text_embedding

    def time_to_seconds(self, time_str: str) -> float:
        """ Convert time string to total seconds """
        time_obj = datetime.strptime(time_str, '%H:%M:%S.%f').time()
        return (time_obj.hour * 3600 +
                time_obj.minute * 60 +
                time_obj.second +
                time_obj.microsecond / 1e6)
