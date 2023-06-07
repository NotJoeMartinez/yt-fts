import sys, os



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


def get_db_path():

    platform = sys.platform

    if platform == 'win32':
        db_path = f"{os.path.join(os.getenv('APPDATA'), 'yt-fts')}/subtitles.db"
        if not os.path.exists(db_path):
            print("db path not found, using current directory")
            return "subtitles.db" 
        else:
            return db_path 

    if platform == 'darwin' or platform == 'linux':
        db_path = f"{os.path.join(os.getenv('HOME'), '.config', 'yt-fts')}/subtitles.db"
        if not os.path.exists(db_path):
            print("db path not found, using current directory")
            return "subtitles.db" 
        else:
            return db_path 
    
    print("db path not found, using current directory")
    return "subtitles.db" 


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




