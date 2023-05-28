from setuptools import setup, find_packages

with open('requirements.txt') as f:
    dependencies = f.read().splitlines()

entry_points = {
    'console_scripts': [
        'yt_fts=yt_fts.yt_fts:main',
    ],
}

setup(
    name='yt-fts', 
    version='0.1.2',
    description='yt-fts is a simple python script that uses yt-dlp to scrape all of a youtube channels subtitles and load them into an sqlite database that is searchable from the command line. It allows you to query a channel for specific key word or phrase and will generate time stamped youtube urls to the video containing the keyword.', 
    author='NotJoeMartinez',
    url='https://github.com/NotJoeMartinez/yt-fts',  
    packages=find_packages(),
    install_requires=dependencies,
    entry_points=entry_points,
    python_requires='>=3.11',
)