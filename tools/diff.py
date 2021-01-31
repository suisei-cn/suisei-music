#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path
from urllib import parse
import logging
import json
import os
import hashlib

from dotenv import load_dotenv

class MusicMeta(object):
    __slots__ = [
        'datetime',
        'url',
        'title',
        'artist',
        'performer',
        'status',
        'source',
        'hash',
        'item'
    ]

    def __init__(self, item):
        self.item = item
        self.datetime = item['datetime']
        self.url = item['url']
        self.title = item['title']
        self.artist = item['artist']
        self.performer = item['performer']
        self.status = item['status']
        self.performer = item['performer']
        self.status = item['status']
        self.source = item['source']

        url = parse.urlparse(self.url)
        filename = url.path.split('/')[-1]
        xxid = filename.split('.')[0]
        self.hash = xxid

    def __hash__(self):
        return int(self.hash, 16)

    def __repr__(self):
        return f'Music(title={self.title}, artist={self.artist}, source={self.source})'

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

def main():
    logging.basicConfig(
            level = logging.INFO,
                format = '%(asctime)s %(name)s %(levelname)s - %(message)s',
                )
    load_dotenv()
    output_dir = Path(os.getenv('OUTPUT_DIR'))
    new_meta = output_dir / 'meta.json'
    old_meta = output_dir / 'meta.last.json'
    console = logging.getLogger('diff')

    if not old_meta.exists():
        console.error("Old metadata doesn't exist. Skipping.")
    if not new_meta.exists():
        console.error("New metadata doesn't exist. Skipping.")

    new_meta = set(map(lambda x:MusicMeta(x), json.load(open(new_meta))))
    old_meta = set(map(lambda x:MusicMeta(x), json.load(open(old_meta))))

    added = new_meta - old_meta
    removed = old_meta - new_meta

    changelog = {
            "added": list(map(lambda x: x.item, added)),
            "removed": list(map(lambda x: x.item, removed)),
            "last_updated": datetime.now().isoformat()
    }

    (output_dir / 'diff.json').write_text(json.dumps(changelog, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()

