#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from urllib import parse
import logging
import json
import os

from dotenv import load_dotenv

def get_filename(url):
    url_obj = parse.urlparse(url)
    return url_obj.path.split('/')[-1]

def main():
    logging.basicConfig(
            level = logging.INFO,
                format = '%(asctime)s %(name)s %(levelname)s - %(message)s',
                )
    load_dotenv()
    output_dir = Path(os.getenv('OUTPUT_DIR'))
    new_meta = output_dir / 'meta.json'
    console = logging.getLogger('check')

    if not new_meta.exists():
        console.error("Mmetadata doesn't exist. Skipping.")
        return

    files = set(map(lambda x:get_filename(x['url']), json.load(open(new_meta))))

    all_ok = True

    for i in files:
        if not (output_dir / i).exists():
            all_ok = False
            console.warn('{i} does not exist in assets.')

    console.info('All files in meta.json is found.')

if __name__ == '__main__':
    main()
