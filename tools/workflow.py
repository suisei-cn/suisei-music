#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import csv
import logging
import subprocess
import xxhash

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s %(name)s %(levelname)s - %(message)s',
)

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
        self.done = item['done']
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

class Processor(object):
    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)

    def filter(self, item):
        raise NotImplementedError

    def effect(self, item):
        raise NotImplementedError

    def process(self, items):
        for item in filter(self.filter, items):
            self.logger.debug(f'Process {item}')
            self.effect(item)
            self.logger.debug(f'Finish {item}')

class MetadataLinter(Processor):
    def __init__(self):
        super().__init__()
        self.music_artist = {}

    def filter(self, item):
        return True

    def effect(self, item):
        if any(map(lambda x: x.strip() != x, [item.title, item.artist, item.performer])):
            self.logger.error(f'Detect whitespace in metadata on {item}')
            raise RuntimeError('metadata format check failed')

        if item.title in self.music_artist and item.artist != self.music_artist[item.title]:
            self.logger.error(f'Detect inconsistent relationship on {item.title}')
            raise RuntimeError('metadata relationship check failed')
        else:
            self.music_artist[item.title] = item.artist

def main():
    with open('../suisei-music.csv') as f:
        items = set(map(Music, csv.DictReader(f)))

    MetadataLinter().process(items)

if __name__ == '__main__':
    main()
