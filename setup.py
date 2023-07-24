from setuptools import setup, find_packages


def read_version():
    with open('yt_fts/yt_fts.py', 'r') as file:
        for line in file:
            if line.startswith('YT_FTS_VERSION'):
                # Extract version and remove quotes
                return line.split('=')[1].strip().strip('\'"')


with open('requirements.txt') as f:
    dependencies = f.read().splitlines()

with open('README.md', 'r') as f:
    long_description = f.read()


entry_points = {
    'console_scripts': [
        'yt-fts=yt_fts.yt_fts:cli',
    ],
}

setup(
    name='yt-fts', 
    version=read_version(),
    description='yt-fts is a simple python script that uses yt-dlp to scrape all of a youtube channels subtitles and load them into an sqlite database that is searchable from the command line. It allows you to query a channel for specific key word or phrase and will generate time stamped youtube urls to the video containing the keyword.',
    long_description=long_description,
    long_description_content_type='text/markdown', 
    author='NotJoeMartinez',
    url='https://github.com/NotJoeMartinez/yt-fts',  
    packages=find_packages(),
    install_requires=dependencies,
    entry_points=entry_points,
    python_requires='>=3.8',
)