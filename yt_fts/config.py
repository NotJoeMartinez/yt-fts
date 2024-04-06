
import sys 
import os

import chromadb
from chromadb.config import Settings


def get_config_path():

    platform = sys.platform

    if platform == 'win32':
        config_path = os.path.join(os.getenv('APPDATA'), 'yt-fts')
        if not os.path.exists(config_path):
            return None
        else:
            return config_path 

    if platform == 'darwin' or platform == 'linux':
        config_path = os.path.join(os.getenv('HOME'), '.config', 'yt-fts')
        if not os.path.exists(config_path):
            return None
        else:
            return config_path
    
    return None


def make_config_dir():
    platform = sys.platform

    try:
        if platform == 'win32':
            config_path = os.path.join(os.getenv('APPDATA'), 'yt-fts')
            # check if config dir exists
            if not os.path.exists(config_path):
                os.mkdir(config_path)
                return config_path
        
        if platform == 'darwin' or platform == 'linux':
            config_path = os.path.join(os.getenv('HOME'), '.config', 'yt-fts')
            # check if config dir exists
            if not os.path.exists(config_path):
                os.mkdir(config_path)
                return config_path
    except Exception as e:
        print(e)
        return None


def get_db_path():
    from .db_utils import make_db
    # make sure config path exists
    # if config path is none, make config path
    # this also means the db doesn't exist
    # make db in new config path

    config_path = get_config_path()
    if config_path is None:

        config_path = make_config_dir()

        # if config path is still none, that means we can't make a config path
        # use current directory
        if config_path is None:
            print("unable to make config path, using current directory")
            return "subtitles.db"
        

    platform = sys.platform

    if platform == 'win32':
        db_path = f"{config_path}/subtitles.db"

        if not os.path.exists(db_path):
            print("db path not found, making new db")
            make_db(db_path)
            return db_path
        else:
            return db_path 

    if platform == 'darwin' or platform == 'linux':
        db_path = f"{config_path}/subtitles.db"
        if not os.path.exists(db_path):
            print("db path not found, making new db")
            make_db(db_path)
            return db_path 
        else:
            return db_path 
    
    print("db path not found, using current directory")
    return "subtitles.db" 


def get_or_make_chroma_path():

    config_path = get_config_path()

    if config_path is None:
        config_path = make_config_dir()

        if config_path is None:
            print("unable to make config path, using current directory")
            return os.path.join(os.getcwd(), "chroma")
    
    chroma_path = os.path.join(config_path, "chroma")

    if not os.path.exists(chroma_path):
        os.mkdir(chroma_path)
        return chroma_path
    else:
        return chroma_path


def get_chroma_client():
    chroma_path = get_or_make_chroma_path()
    return chromadb.PersistentClient(path=chroma_path, 
                                     settings=Settings(anonymized_telemetry=False))
