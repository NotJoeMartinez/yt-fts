import sqlite3
import sys
import re

from sqlite_utils import Database
from rich.console import Console
from rich.table import Table

from .utils import show_message, get_date
from .config import get_db_path, get_chroma_client


def make_db(db_path: str) -> None:
    db = Database(db_path)

    db["Channels"].create({
        "channel_id": str,
        "channel_name": str,
        "channel_url": str,
    },
        pk="channel_id",
        not_null={"channel_name", "channel_url"},
        if_not_exists=True
    )

    db["Videos"].create({
        "video_id": str,
        "video_title": str,
        "video_url": str,
        "channel_id": str,
        "video_date": str,
    },
        pk="video_id",
        not_null={"video_title", "video_url"},
        if_not_exists=True,
        foreign_keys=[
            ("channel_id", "Channels")
        ]
    )

    db["Subtitles"].create(
        {
            "subtitle_id": int,
            "video_id": str,
            "start_time": str,
            "stop_time": str,
            "text": str
        },
        pk="subtitle_id",
        not_null={"start_time", "text"},
        if_not_exists=True,
        foreign_keys=[
            ("video_id", "Videos")
        ]
    ).enable_fts(
        ["text"],
        create_triggers=True,
        replace=True
    )

    db["SemanticSearchEnabled"].create(
        {
            "channel_id": str,
        },
        if_not_exists=True,
        foreign_keys=[
            ("channel_id", "Channels")
        ]

    )


def add_channel_info(channel_id: str, channel_name: str, channel_url: str) -> None:
    db = Database(get_db_path())

    db["Channels"].insert({
        "channel_id": channel_id,
        "channel_name": channel_name,
        "channel_url": channel_url
    })


def add_video(channel_id: str, video_id: str, video_title: str, video_url: str, video_date: str) -> None:
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    existing_video = cur.execute("SELECT * FROM Videos WHERE video_id = ?",
                                 (video_id,)).fetchone()

    if existing_video is None:
        cur.execute("""
                    INSERT INTO Videos (video_id, video_title, video_url, video_date, channel_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,(video_id, video_title, video_url, video_date, channel_id))
        conn.commit()

    else:
        print(f"{video_id} Video already exists in the database.")
    conn.close()


def add_subtitle(video_id: str, start_time: str, text: str) -> None:
    db = Database(get_db_path())

    db["Subtitles"].insert({
        "video_id": video_id,
        "timestamp": start_time,
        "text": text
    })


def get_channels() -> list[tuple[int, str, str, str]]:
    db = Database(get_db_path())

    return db.execute("SELECT ROWID, channel_id, channel_name, channel_url FROM Channels").fetchall()


def escape_fts5_query(query: str) -> str:
    special_chars = ['"', '*', '(', ')', '-', '+']
    for char in special_chars:
        query = query.replace(char, f'"{char}"')
    return query


def escape_fts5_term(term: str) -> str:
    special_chars = ['"', '*', '(', ')', '+', '-']
    for char in special_chars:
        term = term.replace(char, f'"{char}"')
    return f'"{term}"'


def parse_query(query: str) -> str:
    terms = re.findall(r'"[^"]*"|\S+', query)
    parsed_query = []
    for term in terms:
        if term in ('AND', 'OR'):
            parsed_query.append(term.upper())
        else:
            parsed_query.append(escape_fts5_term(term.strip('"')))
    return ' '.join(parsed_query)


def search_channel(channel_id: str, text: str, limit: int | None = None) -> list[dict[str, int | str]]:
    conn = sqlite3.connect(get_db_path())
    curr = conn.cursor()
    
    fts5_query = parse_query(text)

    query = """
        SELECT 
            s.rowid,
            s.subtitle_id,
            s.video_id,
            s.start_time,
            s.stop_time,
            s.text
        FROM 
            Subtitles_fts fts
        JOIN 
            Subtitles s ON fts.rowid = s.rowid
        JOIN 
            Videos v ON s.video_id = v.video_id
        WHERE 
            fts.text MATCH ?
            AND v.channel_id = ? 
        ORDER BY 
            rank
    """
    
    if limit is not None:
        query += " LIMIT ?"
        curr.execute(query, (fts5_query, channel_id, limit))
    else:
        curr.execute(query, (fts5_query, channel_id))

    res = curr.fetchall()
    formatted_res = []
    for row in res:
        formatted_res.append({
            "rowid": row[0],
            "subtitle_id": row[1],
            "video_id": row[2],
            "start_time": row[3],
            "stop_time": row[4],
            "text": row[5]
        })
    conn.close()

    return formatted_res


def search_video(video_id: str, text: str, limit: int | None = None) -> list[dict[str, int | str]]:
    try:
        conn = sqlite3.connect(get_db_path())
        curr = conn.cursor()

        fts5_query = parse_query(text)
        sql = """
        SELECT 
            s.rowid,
            s.subtitle_id,
            s.video_id,
            s.start_time,
            s.stop_time,
            s.text 
        FROM
            Subtitles_fts fts
        JOIN
            Subtitles s ON fts.rowid = s.rowid 
        WHERE
            s.video_id = ?
        AND
            fts.text MATCH ?
        """

        if limit is not None:
            sql += " LIMIT ?"
            curr.execute(sql, (video_id, fts5_query, limit))
        else:
            curr.execute(sql, (video_id, fts5_query))
        
        res = curr.fetchall()

        formatted_res = []

        for row in res:
            formatted_res.append({
                "rowid": row[0],
                "subtitle_id": row[1],
                "video_id": row[2],
                "start_time": row[3],
                "stop_time": row[4],
                "text": row[5]
            })
        
        conn.close()
        return formatted_res 

    except Exception as e:
        print(e)
        sys.exit(1)
    finally:
        conn.close()


def search_all(text: str, limit: int | None = None) -> list[dict[str, int | str]]:
    try:
        conn = sqlite3.connect(get_db_path())
        curr = conn.cursor()
        fts5_query = parse_query(text)

        sql = """
            SELECT 
                s.rowid,
                s.subtitle_id,
                s.video_id,
                s.start_time,
                s.stop_time,
                s.text
            FROM
                Subtitles_fts fts
            JOIN
                Subtitles s ON fts.rowid = s.rowid
            WHERE
                fts.text MATCH ?
            ORDER BY
                rank
        """

        if limit is not None:
            sql += " LIMIT ?"
            curr.execute(sql, (fts5_query, limit))
        else:
            curr.execute(sql, (fts5_query,))


        res = curr.fetchall()

        formatted_res = []

        for row in res:
            formatted_res.append({
                "rowid": row[0],
                "subtitle_id": row[1],
                "video_id": row[2],
                "start_time": row[3],
                "stop_time": row[4],
                "text": row[5]
            })

        conn.close()
        return formatted_res

    except Exception as e:
        print(e)
        sys.exit(1)
    
    finally:
        conn.close()


def get_title_from_db(video_id: str) -> str:
    db = Database(get_db_path())

    return db.execute(f"SELECT video_title FROM Videos WHERE video_id = ?", [video_id]).fetchone()[0]


def get_metadata_from_db(video_id: str) -> dict[str, any]:
    db = Database(get_db_path())

    metadata = db.execute_returning_dicts(f"SELECT * FROM Videos WHERE video_id = ?", [video_id])[0]
    metadata["video_date"] = get_date(metadata["video_date"])
    return metadata


def get_channel_name_from_id(channel_id: str) -> str:
    db = Database(get_db_path())

    return db.execute(f"SELECT channel_name FROM Channels WHERE channel_id = ?", [channel_id]).fetchone()[0]


def get_channel_name_from_video_id(video_id: str) -> str:
    db = Database(get_db_path())

    return db.execute(
        f"SELECT channel_name FROM Channels WHERE channel_id = (SELECT channel_id FROM Videos WHERE video_id = ?)",
        [video_id]).fetchone()[0]


# delete all videos, subtitles, and embeddings associated with channel
def delete_channel(channel_id: str) -> None:
    from .utils import check_ss_enabled

    if check_ss_enabled(channel_id):
        delete_channel_from_chroma(channel_id)

    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()

    cur.execute("DELETE FROM Channels WHERE channel_id = ?", (channel_id,))

    # make sure to delete all subtitles and embeddings before videos  
    cur.execute("DELETE FROM Subtitles WHERE video_id IN (SELECT video_id FROM Videos WHERE channel_id = ?)",
                (channel_id,))

    cur.execute("DELETE FROM Videos WHERE channel_id = ?", (channel_id,))

    cur.execute("DELETE FROM SemanticSearchEnabled WHERE channel_id = ?", (channel_id,))

    conn.commit()
    conn.close()


def delete_channel_from_chroma(channel_id: str) -> None:
    chroma_client = get_chroma_client()
    collection = chroma_client.get_collection(name="subEmbeddings")

    print(f"deleting channel {channel_id} from chroma")
    collection.delete(
        where={"channel_id": channel_id}
    )


def get_channel_id_from_rowid(rowid: str | int) -> str | None:
    db = Database(get_db_path())

    res = db.execute(f"SELECT channel_id FROM Channels WHERE ROWID = ?", [rowid]).fetchone()

    if res is None:
        return None
    else:
        return res[0]


def get_channel_id_from_name(channel_name: str) -> str | None:
    db = Database(get_db_path())

    res = db.execute(f"SELECT channel_id FROM Channels WHERE channel_name = ?", [channel_name]).fetchall()

    console = Console()
    if len(res) > 1:
        table = Table(header_style="bold magenta")
        table.add_column("id", style="dim", width=5)
        table.add_column("channel_name")
        table.add_column("channel_url")

        channels = db.execute(f"SELECT ROWID, channel_name, channel_url FROM Channels WHERE channel_name = ?",
                              [channel_name]).fetchall()
        for channel in channels:
            table.add_row(str(channel[0]), channel[1], channel[2])

        console.print(table)
        show_message("multiple_channels_found")
    if len(res) == 0:
        return None
    else:
        return res[0][0]


# for listing specific channel 
def get_channel_list_by_id(channel_id: str) -> list[tuple[int, str, str]]:
    db = Database(get_db_path())

    return db.execute(f"SELECT ROWID, channel_name, channel_url FROM Channels WHERE channel_id = ?",
                      [channel_id]).fetchall()


def check_if_channel_exists(channel_id: str) -> bool:
    """
    Check if channel exists in the database
    """

    db = Database(get_db_path())

    res = db.execute(f"SELECT channel_id FROM Channels WHERE channel_id = ?", [channel_id]).fetchall()
    if len(res) > 0:
        return True
    else:
        return False


def get_num_vids(channel_id: str) -> int:
    db = Database(get_db_path())

    return db.execute(f"SELECT COUNT(*) FROM Videos WHERE channel_id = ?", [channel_id]).fetchone()[0]


def get_vid_ids_by_channel_id(channel_id: str) -> list[tuple[str]]:
    db = Database(get_db_path())

    return db.execute(f"SELECT video_id FROM Videos WHERE channel_id = ?", [channel_id]).fetchall()


def get_all_subs_by_channel_id(channel_id: str) -> list[tuple[int, str, str, str, str, str]]:
    db = Database(get_db_path())

    parsed_subs = []
    subs = db.execute("""
        SELECT s.subtitle_id, s.video_id, s.start_time, s.stop_time, s.text, v.channel_id
        FROM Subtitles s
        JOIN Videos v ON s.video_id = v.video_id
        WHERE v.channel_id = ?
        """, [channel_id]).fetchall()

    for sub in subs:
        split_subs = sub[4].strip().split(" ")
        if len(split_subs) > 0:
            parsed_subs.append(sub)

    return parsed_subs


# get all subs where semantic search is enabled
def get_all_subs_by_channel_id_ss(channel_id: str) -> list[tuple[int, str, str, str]]:
    db = Database(get_db_path())

    parsed_subs = []
    subs = db.execute("""
        SELECT s.subtitle_id, s.video_id, s.timestamp, s.text 
        FROM Subtitles s
        JOIN Videos v ON s.video_id = v.video_id
        WHERE v.channel_id = ?
        """, [channel_id]).fetchall()

    for sub in subs:
        if len(sub[3].strip()) > 0:
            parsed_subs.append(sub)
    return parsed_subs


def get_transcript_by_video_id(video_id: str) -> list[tuple[str]]:
    db = Database(get_db_path())

    return db.execute(f"SELECT text FROM Subtitles WHERE video_id = ?", [video_id]).fetchall()


def get_subs_by_video_id(video_id: str) -> list[tuple[str, str, str]]:
    db = Database(get_db_path())

    return db.execute(f"SELECT start_time, stop_time, text FROM Subtitles WHERE video_id = ?",
                      [video_id]).fetchall()


def get_channel_id_from_input(channel_input: str | int) -> str:  # yt_fts, export, search, vector_search ... broken
    """
    Checks if the input is a rowid or a channel name and returns channel id
    """

    name_res = get_channel_id_from_name(str(channel_input))
    id_res = get_channel_id_from_rowid(channel_input)

    if id_res is not None:
        return id_res
    elif name_res is not None:
        return name_res
    else:
        show_message("channel_not_found")
        sys.exit(1)
