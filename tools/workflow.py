#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dotenv import load_dotenv
from pathlib import Path
import csv
import logging
import os
import subprocess
import xxhash

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s %(name)s %(levelname)s - %(message)s',
)
load_dotenv()

class Music(object):
    __slots__ = [
        'date',
        'video_type',
        'video_id',
        'clip_start',
        'clip_end',
        'done',
        'title',
        'artist',
        'performer',
        'file_key',
    ]

    def __init__(self, item):
        self.date = item['date']
        self.video_type = item['video_type']
        self.video_id = item['video_id']
        self.clip_start = item['clip_start']
        self.clip_end = item['clip_end']
        self.done = item['done'] == 'TRUE'
        self.title = item['title']
        self.artist = item['artist']
        self.performer = item['performer']

        x = xxhash.xxh64(seed=0x67e67b2e)
        x.update(self.video_type.encode())
        x.update(self.video_id.encode())
        x.update(self.clip_start.encode())
        x.update(self.clip_end.encode())
        self.file_key = x.hexdigest()

    def __hash__(self):
        return hash((self.video_type, self.video_id, self.clip_start, self.clip_end))

    def __repr__(self):
        return f'Music(id={self.video_id}, title={self.title}, key={self.file_key})'

class Action(object):
    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)

    def filter(self, item):
        raise NotImplementedError

    def effect(self, item):
        raise NotImplementedError

    def process(self, items):
        for item in filter(self.filter, items):
            self.logger.debug(f'process {item}')
            self.effect(item)
            self.logger.debug(f'finish {item}')

class MetadataLinter(Action):
    def __init__(self):
        super().__init__()
        self.music_artist = {}

    def filter(self, item):
        return True

    def effect(self, item):
        if any(map(lambda x: x.strip() != x, [item.title, item.artist, item.performer])):
            self.logger.error(f'detect whitespace in metadata on {item}')
            raise RuntimeError('metadata format check failed')

        if item.title in self.music_artist and item.artist != self.music_artist[item.title]:
            self.logger.error(f'detect inconsistent relationship on {item.title}')
            raise RuntimeError('metadata relationship check failed')
        else:
            self.music_artist[item.title] = item.artist

class YoutubeClipper(Action):
    def __init__(self, format_code, source_dir, output_dir):
        super().__init__()
        self.format_code = format_code
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)

        self.source_ext = {140: 'mp4', 251: 'webm'}[format_code]
        self.output_ext = {140: 'm4a', 251: 'ogg'}[format_code]

    def filter(self, item):
        return item.video_type == 'YOUTUBE'

    def effect(self, item):
        source_path = self.source_dir / f'{item.video_id}.{self.format_code}.{self.source_ext}'
        output_path = self.output_dir / f'{item.file_key}.{self.output_ext}'

        if not source_path.exists():
            self.logger.info(f'download {source_path}')
            cmd = [
                '/usr/local/bin/youtube-dl',
                '-f', str(self.format_code),
                '-o', str(source_path),
                f'https://www.youtube.com/watch?v={item.video_id}',
            ]
            subprocess.run(cmd, check=True, capture_output=True)

        if item.done and not output_path.exists():
            self.logger.info(f'clip {output_path} for {item}')
            cmd = [
                '/usr/local/bin/ffmpeg',
                '-i', str(source_path),
                '-acodec', 'copy', '-vn'
            ]
            if item.clip_start:
                cmd += ['-ss', item.clip_start]
            if item.clip_end:
                cmd += ['-to', item.clip_end]
            cmd.append(str(output_path))
            subprocess.run(cmd, check=True, capture_output=True)

def main():
    with open('../suisei-music.csv') as f:
        items = frozenset(map(Music, csv.DictReader(f)))

    MetadataLinter().process(items)
    YoutubeClipper(251, os.getenv('SOURCE_DIR'), os.getenv('OUTPUT_DIR')).process(items)
    YoutubeClipper(140, os.getenv('SOURCE_DIR'), os.getenv('OUTPUT_DIR')).process(items)

if __name__ == '__main__':
    main()
