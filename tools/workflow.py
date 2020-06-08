#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dotenv import load_dotenv
from pathlib import Path
import csv
import logging
import os
import subprocess
import xxhash
import Levenshtein

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
        'status',
        'title',
        'artist',
        'performer',
        'hash',
    ]

    def __init__(self, item):
        self.date = item['date']
        self.video_type = item['video_type']
        self.video_id = item['video_id']
        self.clip_start = item['clip_start']
        self.clip_end = item['clip_end']
        self.status = item['status']
        self.title = item['title']
        self.artist = item['artist']
        self.performer = item['performer']

        self.hash = xxhash.xxh64(''.join([
            self.video_type,
            self.video_id,
            self.clip_start,
            self.clip_end,
            self.title,
            self.artist,
            self.performer
        ]), seed=0x9f88f860).hexdigest()

    def __hash__(self):
        return int(self.hash, 16)

    def __repr__(self):
        return f'Music(id={self.video_id}, title={self.title}, key={self.hash})'

class Action(object):
    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)

    def filter(self, item):
        return True

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

    def effect(self, item):
        if any(map(lambda x: x.strip() != x, [item.title, item.artist, item.performer])):
            self.logger.error(f'detect whitespace in metadata on {item}')
            raise RuntimeError('metadata format check failed')

        if item.title in self.music_artist:
            if item.artist != self.music_artist[item.title]:
                self.logger.warning(f'detect inconsistent relationship on {item.title}')
        else:
            self.music_artist[item.title] = item.artist

class TypoCheck(Action):
    def __init__(self, getter, threshold=0.75):
        super().__init__()
        self.getter = getter
        self.cache = {}

    def effect(self, item):
        for i in self.getter(item):
            if i in self.cache:
                continue

            for t in self.cache:
                if Levenshtein.ratio(t, i) > 0.75:
                    self.logger.warning(f'detect similar metadata {t} & {i} on {self.cache[t]} & {item}')

            self.cache[i] = item

class VideoClipper(Action):
    def __init__(self, video_type, url_template, format_code, source_ext, output_ext):
        super().__init__()
        self.video_type = video_type
        self.url_template = url_template
        self.format_code = format_code
        self.source_ext = source_ext
        self.output_ext = output_ext
        self.source_dir = Path(os.getenv('SOURCE_DIR'))
        self.output_dir = Path(os.getenv('OUTPUT_DIR'))

    def filter(self, item):
        return item.video_type == self.video_type

    def effect(self, item):
        source_path = self.source_dir / f'{item.video_id}.{self.source_ext}'
        output_path = self.output_dir / f'{item.hash}.{self.output_ext}'

        if not source_path.exists():
            self.logger.info(f'download {source_path}')
            cmd = [
                'youtube-dl',
                '-f', str(self.format_code),
                '-o', str(source_path),
                self.url_template.format(item.video_id),
            ]
            subprocess.run(cmd, check=True, capture_output=True)

        if item.status and not output_path.exists():
            self.logger.info(f'clip {output_path} for {item}')
            cmd = [
                'ffmpeg',
                '-i', str(source_path),
                '-acodec', 'copy',
                '-metadata', f'title={item.title} / {item.artist}',
                '-metadata', f'artist={item.performer}',
                '-vn',
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

    TypoCheck(lambda x: [x.title]).process(items)
    TypoCheck(lambda x: x.artist.split(',')).process(items)
    TypoCheck(lambda x: x.performer.split(',')).process(items)

    VideoClipper('YOUTUBE', 'https://www.youtube.com/watch?v={}', 'bestaudio[ext=m4a]', 'mp4', 'm4a').process(items)
    VideoClipper('TWITTER', 'https://www.twitter.com/i/status/{}', 'best[ext=mp4]', 'mp4', 'm4a').process(items)
    VideoClipper('BILIBILI', 'https://www.bilibili.com/video/{}', 'best[ext=flv]', 'flv', 'm4a').process(items)

    for i in items:
        print(f'{i.hash} -- {i.video_id} -- {i.title} -- {i.artist}')

    result = [i.hash for i in items]
    for i in Path(os.getenv('OUTPUT_DIR')).iterdir():
        if i.stem not in result:
            print(i)

if __name__ == '__main__':
    main()
