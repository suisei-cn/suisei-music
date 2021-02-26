#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from mod import Music

from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path
from time import sleep
import argparse
import csv
import logging
import os
import subprocess
import sys
import json
import Levenshtein

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s %(name)s %(levelname)s - %(message)s',
)
load_dotenv()

def get_args():
    parser = argparse.ArgumentParser(description='Helper script for suisei-music.',
                                     allow_abbrev=False)
    parser.add_argument('--check-only','-c' , action='store_true',
                                       help='only check for typos')
    parser.add_argument('--noconfirm', action='store_true',
                                       help='never ask for interarctive action')
    parser.add_argument('--save-failed', help='save failed video ids to a file')
    return parser.parse_args()

args = get_args()
wrapped_input = (lambda _:False) if args.noconfirm else input

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
        return self

class MetadataLinter(Action):
    def __init__(self):
        super().__init__()
        self.music_artist = {}

    def effect(self, item):
        if any(map(lambda x: x.strip() != x, [item.title, item.artist, item.performer])):
            self.logger.error(f'detect whitespace in metadata on {item}')
            raise RuntimeError('metadata format check failed')

        if item.clip_start and item.clip_end and float(item.clip_start) > float(item.clip_end):
            self.logger.error(f'detect bad clip timing on {item}')
            raise RuntimeError('metadata timing check failed')

        if item.title in self.music_artist:
            if item.artist != self.music_artist[item.title]:
                self.logger.warning(f'detect inconsistent relationship on {item.title}')
                wrapped_input('continue ?')
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
                    wrapped_input('continue ?')

            self.cache[i] = item

class VideoClipper(Action):
    def __init__(self, video_type, url_template, format_code, source_ext, output_ext):
        super().__init__()
        self.video_type = video_type
        self.url_template = url_template
        self.format_code = format_code
        self.source_ext = source_ext
        self.output_ext = output_ext
        self.blacklisted_videoids = []
        self.source_dir = Path(os.getenv('SOURCE_DIR'))
        self.output_dir = Path(os.getenv('OUTPUT_DIR'))

    def get_blacklist(self):
        return list(map(lambda x:f'{self.video_type}:{x}', self.blacklisted_videoids))

    def filter(self, item):
        return item.video_type == self.video_type

    def effect(self, item):
        source_path = self.source_dir / f'{item.video_id}.{self.source_ext}'
        source_part_path = Path(f'{source_path}.part')
        output_path = self.output_dir / f'{item.hash}.{self.output_ext}'

        if item.status and (int(item.status) & 8 > 0):
            self.logger.info(f'Source of {output_path} ({item.video_id}) is member-only, skipping.')
            return

        if not item.video_id:
            return

        if output_path.exists():
            self.logger.debug(f'{output_path} is found, skipping.')
            return

        if item.video_id in self.blacklisted_videoids:
            self.logger.info(f'{output_path} skipped because we failed to fetch the source ({item.video_id}).')
            return

        download_finished = True

        while source_part_path.exists():
            self.logger.info(f"{source_part_path} is downloading. Waiting for 15 seconds and recheck.")
            sleep(15)

        if not source_path.exists():
            self.logger.info(f'download {source_path}')
            cmd = [
                'youtube-dl',
                '-f', str(self.format_code),
                '-o', str(source_path),
                self.url_template.format(item.video_id),
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f'Error fetching {item.video_id}, skipping.')
                self.logger.error("Logs:\n" + e.output.decode())
                self.blacklisted_videoids.append(item.video_id)
                download_finished = False
        else:
            self.logger.debug(f'{source_path} is found, skipping.')

        if not download_finished:
            self.logger.info(f'Download of {source_path} is not finished, clipping skipped.')
            self.logger.info(f'Clipping of {output_path} failed because of download problems.')
            return

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

class JsonRender(Action):
    def __init__(self, url_template):
        super().__init__()
        self.output_dir = Path(os.getenv('OUTPUT_DIR'))
        self.url_template = url_template

    def process(self, items):
        items = filter(lambda x: x.status, items)
        items = filter(lambda x: int(x.status) & 0xA == 0, items)

        result = []

        for item in items:
            pubdate = timedelta(seconds=int(float(item.clip_start)) if item.clip_start else 0)
            pubdate = datetime.fromisoformat(item.datetime) + pubdate
            pubdate = pubdate.isoformat()

            source = {
                'YOUTUBE': 'https://youtu.be/{}',
                'TWITTER': 'https://www.twitter.com/i/status/{}',
                'BILIBILI': 'https://www.bilibili.com/video/{}',
            }[item.video_type].format(item.video_id)

            if item.clip_start:
                source += f'?t={int(float(item.clip_start))}'

            result.append({
                'url': self.url_template.format(item.hash),
                'datetime': pubdate,
                'title': item.title,
                'artist': item.artist,
                'performer': item.performer,
                'status': int(item.status),
                'source': source,
            })

        (self.output_dir / 'meta.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))

class TrashCheck(Action):
    def __init__(self):
        super().__init__()
        self.output_dir = Path(os.getenv('OUTPUT_DIR'))

    def process(self, items):
        result = set(map(lambda x: x.hash, items))
        for i in (self.output_dir).iterdir():
            if i.stem not in result:
                print(f'outdated file {i}')

def main():
    with open('../suisei-music.csv') as f:
        items = map(Music, csv.DictReader(f))
        items = sorted(items, key=lambda x: (x.datetime, x.clip_start))

    MetadataLinter().process(items)

    TypoCheck(lambda x: [x.title]).process(items)
    TypoCheck(lambda x: x.artist.split(',')).process(items)
    TypoCheck(lambda x: x.performer.split(',')).process(items)

    if args.check_only:
        return

    failed_videos = []

    failed_videos.extend(VideoClipper('YOUTUBE', 'https://www.youtube.com/watch?v={}', 'bestaudio[ext=m4a]', 'mp4', 'm4a').process(items).get_blacklist())
    failed_videos.extend(VideoClipper('TWITTER', 'https://www.twitter.com/i/status/{}', 'best[ext=mp4]', 'mp4', 'm4a').process(items).get_blacklist())
    failed_videos.extend(VideoClipper('BILIBILI', 'https://www.bilibili.com/video/{}', 'best[ext=flv]', 'flv', 'm4a').process(items).get_blacklist())\
    
    if args.save_failed:
        with open(args.save_failed, 'w') as f:
            f.write('\n'.join(failed_videos))

    JsonRender('https://suisei-podcast.outv.im/{}.m4a').process(list(items))

    TrashCheck().process(items)

if __name__ == '__main__':
    main()
